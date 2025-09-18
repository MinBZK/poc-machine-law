import asyncio
import pprint
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, Any, TypedDict

import nest_asyncio
import uvicorn
from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from fastmcp import Client
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


# FastAPI lifespan event handler
@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    # Startup
    await initialize_mcp_client()
    await initialize_model_with_tools()
    await initialize_workflow()
    yield
    # Shutdown
    global mcp_client
    if mcp_client:
        try:
            await mcp_client.__aexit__(None, None, None)
        except:
            pass


app = FastAPI(lifespan=lifespan)
router = APIRouter()

# Initialize MCP client
mcp_client = None
dynamic_tools = []


async def initialize_mcp_client():
    global mcp_client
    if mcp_client is None:
        mcp_client = Client("https://ui.lac.apps.digilab.network/mcp/")
        await mcp_client.__aenter__()
    return mcp_client


async def create_dynamic_tools() -> list:
    """Dynamically create tools from MCP endpoint"""
    global dynamic_tools

    try:
        client = await initialize_mcp_client()

        # Get available tools from MCP
        mcp_tools = await client.list_tools()
        dynamic_tools = []

        print(f"📋 Found {len(mcp_tools)} tools from MCP endpoint")

        for mcp_tool in mcp_tools:
            tool_name = mcp_tool.name
            tool_description = getattr(mcp_tool, "description", f"MCP tool: {tool_name}")

            print(f"🔨 Creating dynamic tool: {tool_name}")

            # Create a dynamic tool function
            def create_tool_function(name: str, description: str):
                async def dynamic_tool_function(**kwargs) -> str:
                    """Dynamically created MCP tool"""
                    try:
                        await send_debug_message(f"🔧 Dynamic tool called: {name} with args={kwargs}")

                        client = await initialize_mcp_client()

                        # First, unwrap kwargs if they're wrapped
                        actual_kwargs = kwargs["kwargs"] if len(kwargs) == 1 and "kwargs" in kwargs else kwargs

                        # Format arguments based on the tool type
                        if name == "execute_law":
                            # For execute_law, restructure to expected format
                            service = actual_kwargs.get("service")
                            law = actual_kwargs.get("law")

                            # Put all other parameters into the parameters object
                            parameters = {k: v for k, v in actual_kwargs.items() if k not in ["service", "law"]}

                            arguments = {"service": service, "law": law, "parameters": parameters}
                        else:
                            # For other tools, pass arguments directly
                            arguments = actual_kwargs

                        # Send debug message about MCP request
                        await send_debug_message(f"📡 Making MCP request: {name} with arguments={arguments}")

                        # Use the MCP client to call the tool
                        result = await client.call_tool(name, arguments=arguments)

                        # Send debug message about MCP response
                        result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                        await send_debug_message(f"📥 MCP response received: {result_preview}")

                        # Handle different response formats from MCP
                        if hasattr(result, "content") and result.content and len(result.content) > 0:
                            content_item = result.content[0]
                            if hasattr(content_item, "text"):
                                return str(content_item.text)
                            else:
                                return str(content_item)
                        return str(result)
                    except Exception as e:
                        await send_debug_message(f"❌ Error in dynamic tool {name}: {str(e)}")
                        return f"Error calling {name}: {str(e)}"

                # Set function attributes for tool decorator
                dynamic_tool_function.__name__ = name
                dynamic_tool_function.__doc__ = description

                return dynamic_tool_function

            # Create and decorate the function as a tool
            tool_func = create_tool_function(tool_name, tool_description)
            decorated_tool = tool(tool_func)
            dynamic_tools.append(decorated_tool)

        print(f"✅ Successfully created {len(dynamic_tools)} dynamic tools")
        return dynamic_tools

    except Exception as e:
        print(f"❌ Error creating dynamic tools: {str(e)}")
        # Return empty list if tool creation fails
        return []


model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0, max_retries=2, max_tokens_to_sample=4000)

# Global variable to store current thread_id for debug messages
current_thread_id = None


async def send_debug_message(content: str):
    """Send debug message to current WebSocket connection"""
    global current_thread_id
    try:
        if current_thread_id and manager:
            await manager.send_debug_message(content, current_thread_id)
        else:
            # If no WebSocket connection, just print to console
            print(f"Debug: {content}")
    except Exception as e:
        print(f"Debug message error: {e}")


# Dynamic tools will be created at startup
tools = []
model_with_tools = None


async def initialize_model_with_tools():
    """Initialize model with dynamically created tools"""
    global model_with_tools, tools

    if model_with_tools is None:
        # Create dynamic tools from MCP endpoint
        tools = await create_dynamic_tools()

        if tools:
            model_with_tools = model.bind_tools(tools)
            print(f"🤖 Model initialized with {len(tools)} dynamic tools")
        else:
            # Fallback to model without tools if no tools available
            model_with_tools = model
            print("⚠️ Model initialized without tools (no MCP tools available)")

    return model_with_tools


class State(TypedDict):
    messages: Annotated[list[Any], add_messages]


class WebSocketMessage(TypedDict):
    id: str
    type: str  # E.g. "debug". Default: chunk
    content: str
    quick_replies: list[str]


# Initialize the graph
workflow = StateGraph(state_schema=State)

# Get the event loop and enable nesting, see https://pypi.org/project/nest-asyncio/
nest_asyncio.apply()
loop = asyncio.get_event_loop()


async def chatbot(state: State):
    # Ensure model is initialized with tools
    current_model = await initialize_model_with_tools()

    # Add system prompt
    system_prompt = """Je bent een behulpzame assistent die Nederlandse burgers helpt met vragen over uitkeringen, toeslagen en andere overheidsregelingen.

    Je hebt toegang tot MCP tools waarmee je Nederlandse wetten kunt uitvoeren en controleren. Gebruik deze tools om accurate informatie te geven.

    Belangrijke tools:
    - execute_law: Voer een specifieke wet uit voor gegeven parameters
    - check_eligibility: Controleer of iemand recht heeft op een uitkering/toeslag

    Veel voorkomende wetten en services:
    - Huurtoeslag: service="TOESLAGEN", law="wet_op_de_huurtoeslag"
    - Zorgtoeslag: service="TOESLAGEN", law="zorgtoeslagwet"
    - AOW: service="SVB", law="algemene_ouderdomswet"
    - WPM (voor bedrijven): service="RVO", law="omgevingswet/werkgebonden_personenmobiliteit" (gebruik KVK_NUMMER i.p.v. BSN)

    Voor `execute_law` gebruik je altijd een `service` (bijvoorbeeld "TOESLAGEN" of "RVO").
    Als een gebruiker een BSN noemt, gebruik dat in de parameters: {"BSN": "123456789"}

    Geef altijd vriendelijke, duidelijke uitleg in het Nederlands."""

    messages = state["messages"]
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=system_prompt)] + messages

    result = await current_model.ainvoke(messages)
    return {"messages": [result]}


# Add nodes
workflow.add_node("chatbot", chatbot)


# Tool node will be created dynamically after tools are initialized
async def create_tool_node():
    """Create tool node with dynamic tools"""
    if tools:
        return ToolNode(tools)
    else:
        # Return a dummy tool node if no tools available
        return ToolNode([])


# We'll initialize the tool node when the workflow is compiled


# Initialize workflow after lifespan startup
async def initialize_workflow():
    """Initialize workflow with dynamic tools"""
    global workflow, graph

    # Create and add the tool node with dynamic tools
    tool_node = await create_tool_node()
    workflow.add_node("tools", tool_node)

    # Add edges
    workflow.set_entry_point("chatbot")
    workflow.add_conditional_edges("chatbot", tools_condition)
    workflow.add_edge("tools", "chatbot")

    # Compile the graph
    graph = workflow.compile(checkpointer)

    return graph


# Initialize memory to persist state between graph runs. IMPROVE: store persistently in Postgres
checkpointer = MemorySaver()

# Graph will be compiled after tools are initialized
graph = None


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[uuid.UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        thread_id = uuid.uuid4()
        self.active_connections[thread_id] = websocket

        return thread_id

    def disconnect(self, thread_id: uuid.UUID):
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]

    async def send_message(self, message: dict, thread_id: uuid.UUID):
        if thread_id in self.active_connections:
            await self.active_connections[thread_id].send_json(message)

    async def send_debug_message(self, content: str, thread_id: uuid.UUID):
        debug_message = {
            "id": str(uuid.uuid4()),
            "type": "debug",
            "content": content,
            "quick_replies": [],
        }
        await self.send_message(debug_message, thread_id)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global current_thread_id
    thread_id = await manager.connect(websocket)
    current_thread_id = thread_id
    # IMPROVE: implement functionality similar to the 'Stop generating' functionality in ChatGPT. Use an AbortController, so the API will actually stop generating? See https://community.openai.com/t/chatgpts-stop-generating-function-how-to-implement/235121 and https://developer.mozilla.org/en-US/docs/Web/API/AbortController

    try:
        async for user_input in websocket.iter_json():
            # # Process the received data through the workflow
            # print("message received:", user_input)

            if user_input.get("type") == "keys":
                # Store the keys in the state
                graph.update_state(
                    {"configurable": {"thread_id": thread_id}},
                    {
                        "anthropic_api_key": user_input["anthropicApiKey"],
                        "tavily_api_key": user_input["tavilyApiKey"],
                    },
                )

            elif user_input.get("type") == "text":
                # Ensure graph is initialized
                if graph is None:
                    await initialize_workflow()

                contains_yaml = False
                chunk_content_so_far = ""

                # Add the user message to the conversation
                user_message = HumanMessage(content=user_input.get("content"))

                try:
                    async for event in graph.astream(
                        {"messages": [user_message]},
                        {"configurable": {"thread_id": thread_id}},
                    ):
                        for node_name, node_output in event.items():
                            if "messages" in node_output:
                                for message in node_output["messages"]:
                                    # Check if this is a tool result message
                                    is_tool_result = (
                                        hasattr(message, "__class__") and message.__class__.__name__ == "ToolMessage"
                                    ) or node_name == "tools"

                                    # Extract text content from different message formats
                                    content_str = ""

                                    if hasattr(message, "content"):
                                        if isinstance(message.content, list):
                                            # Handle list format - extract text from each item
                                            text_items = []
                                            for item in message.content:
                                                if isinstance(item, dict):
                                                    if item.get("type") == "text" and "text" in item:
                                                        text_items.append(item["text"])
                                                    # Skip tool_use and other non-text items
                                                elif hasattr(item, "text"):
                                                    text_items.append(str(item.text))
                                            content_str = " ".join(text_items)
                                        elif isinstance(message.content, str):
                                            content_str = message.content
                                        else:
                                            content_str = str(message.content)

                                    # Only process if we have actual text content
                                    if content_str.strip():
                                        if is_tool_result:
                                            # Send tool results as debug messages
                                            await manager.send_debug_message(f"Tool result: {content_str}", thread_id)
                                        else:
                                            # Split content into chunks for streaming effect
                                            words = content_str.strip().split()
                                            chunk_size = 5  # Send 5 words at a time

                                            for i in range(0, len(words), chunk_size):
                                                word_chunk = " ".join(words[i : i + chunk_size])

                                                if not contains_yaml:
                                                    chunk_content_so_far += word_chunk + " "
                                                    if "```yaml" in chunk_content_so_far:
                                                        contains_yaml = True

                                                # Only add quick replies on the last chunk
                                                quick_replies = []
                                                if i + chunk_size >= len(words):
                                                    stop_reason = getattr(message, "response_metadata", {}).get(
                                                        "stop_reason"
                                                    )
                                                    if stop_reason == "max_tokens":
                                                        quick_replies = ["Ga door"]
                                                    elif contains_yaml and stop_reason == "end_turn":
                                                        quick_replies = ["Analyseer deze YAML-code"]

                                                await manager.send_message(
                                                    {
                                                        "id": getattr(message, "id", str(uuid.uuid4())),
                                                        "type": "chunk",
                                                        "content": word_chunk
                                                        + (" " if i + chunk_size < len(words) else ""),
                                                        "quick_replies": quick_replies,
                                                    },
                                                    thread_id,
                                                )

                                                # Small delay for streaming effect
                                                await asyncio.sleep(0.05)
                except Exception as stream_error:
                    await manager.send_message(
                        {
                            "id": str(uuid.uuid4()),
                            "type": "error",
                            "content": f"Fout bij het verwerken van het bericht: {str(stream_error)}",
                            "quick_replies": [],
                        },
                        thread_id,
                    )

    except WebSocketDisconnect:
        manager.disconnect(thread_id)

    except Exception as e:
        print(f"Error: {pprint.pformat(e)}")

        # Send an error message to the user
        await manager.send_message(
            {
                "id": str(uuid.uuid4()),
                "type": "error",
                "content": f"Er is een fout opgetreden:\n```\n{e}\n```",
                "quick_replies": [],
            },
            thread_id,
        )

    finally:
        current_thread_id = None
        manager.disconnect(thread_id)


# Include the router in the FastAPI app
app.include_router(router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)
