from langchain_anthropic import ChatAnthropic
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_community.document_loaders import WebBaseLoader
from langgraph.graph import END, StateGraph, MessagesState
from typing import Dict, Optional, TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
from IPython.display import Image, display, HTML
import pprint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
import uuid
import json

# Set up the state
from langgraph.graph import MessagesState, START
from langgraph.types import Command, interrupt

# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
# from pydantic import BaseModel
import asyncio


model = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0, max_retries=2)

# Retriever to find the specified law online
retriever = TavilySearchAPIRetriever(
    k=1, include_domains=["wetten.overheid.nl"]
)  # Limit to 1 result


class State(TypedDict):
    messages: Annotated[list, add_messages]
    law: str
    should_retry: bool
    law_url: str
    law_url_approved: Optional[bool]  # Can be True, False, or None


class WebSocketMessage(TypedDict):
    content: str
    quick_replies: List[str]


# Initialize the graph
workflow = StateGraph(state_schema=State)


def ask_law(state: State, config: Dict) -> Dict:
    print("----> ask_law")

    thread_id = config["configurable"]["thread_id"]

    # Ask the user for the law name
    msg = "Wat is de naam van de wet?"
    asyncio.get_event_loop().create_task(
        manager.send_message(WebSocketMessage(content=msg), thread_id)
    )

    return {"messages": []}  # Note: we reset the messages


def check_law_input(state: State, config: Dict) -> Dict:
    print("----> check_law_input")

    resp = interrupt("check_law_input")

    if len(resp) < 4:
        thread_id = config["configurable"]["thread_id"]
        asyncio.get_event_loop().create_task(
            manager.send_message(
                WebSocketMessage(
                    content="De wetnaam moet minimaal 4 karakters bevatten."
                ),
                thread_id,
            )
        )
        return {"should_retry": True, "law": resp}

    return {"should_retry": False, "law": resp}


def ask_law_confirmation(state: State, config: Dict) -> Dict:
    print("----> ask_law_confirmation")

    # Find the law URL
    docs = retriever.invoke(state["law"])

    metadata = docs[0].metadata
    url = metadata["source"]  # IMPROVE: handle the case where no docs are found

    thread_id = config["configurable"]["thread_id"]

    asyncio.get_event_loop().create_task(
        manager.send_message(
            WebSocketMessage(
                content=f"Is dit de wet die je bedoelt? \n\n{metadata["title"]}\n{url}",
                quick_replies=["Ja", "Nee"],
            ),
            thread_id,
        )
    )

    return {"law_url": url}


def handle_law_confirmation(state: State) -> Dict:
    print("----> handle_law_confirmation")

    resp = interrupt("handle_law_confirmation")

    # Parse the response
    is_approved = False
    if resp.lower() in ("ja", "j"):
        is_approved = True

    return {"law_url_approved": is_approved}


def continuing(state: State, config: Dict) -> Dict:
    print("----> continuing")

    return {}


# Add nodes
workflow.add_node("ask_law", ask_law)
workflow.add_node("check_law_input", check_law_input)
workflow.add_node("ask_law_confirmation", ask_law_confirmation)
workflow.add_node("handle_law_confirmation", handle_law_confirmation)
workflow.add_node("continuing", continuing)

# Add edges
workflow.set_entry_point("ask_law")
workflow.add_edge("ask_law", "check_law_input")
workflow.add_conditional_edges(
    "check_law_input",
    lambda state: "ask_law" if state["should_retry"] else "ask_law_confirmation",
)
workflow.add_edge("ask_law_confirmation", "handle_law_confirmation")
workflow.add_conditional_edges(
    "handle_law_confirmation",
    lambda state: "continuing" if state["law_url_approved"] else "ask_law",
)


# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Compile the graph
graph = workflow.compile(
    checkpointer,
    # interrupt_after=["ask_law", "handle_law_confirmation"]
)

# Initialize a FastAPI web server
app = FastAPI()


@app.get("/")
async def get():
    return FileResponse("workflow_graph.png")  # TODO: other response


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[uuid.UUID, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        thread_id = uuid.uuid4()
        self.active_connections[thread_id] = websocket

        # Invoke the graph
        graph.invoke({"messages": []}, {"configurable": {"thread_id": thread_id}})

        return thread_id

    def disconnect(self, thread_id: uuid.UUID):
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]

    async def broadcast(self, message: WebSocketMessage):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)

    async def send_message(self, message: WebSocketMessage, thread_id: uuid.UUID):
        if thread_id in self.active_connections:
            await self.active_connections[thread_id].send_text(json.dumps(message))


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    thread_id = await manager.connect(websocket)

    try:
        while True:
            user_input = await websocket.receive_text()

            # Process the received data through the workflow
            print("message received:", user_input)

            for event in graph.stream(
                # {"messages": [HumanMessage(user_input)]},
                Command(resume=user_input),
                {"configurable": {"thread_id": thread_id}},
                stream_mode="values",
            ):
                # In case of an AI message, send it back to the client
                # pprint.pprint(event["messages"])
                if event["messages"]:
                    msg = event["messages"][-1]
                    if isinstance(msg, AIMessage):
                        await manager.send_message(
                            WebSocketMessage(content=msg.content),
                            thread_id,
                        )

    except WebSocketDisconnect:
        manager.disconnect(thread_id)

    except Exception as e:
        print(f"Error: {pprint.pformat(e)}")

    finally:
        manager.disconnect(thread_id)


def main():
    # Generate a Mermaid graph of the workflow
    # display(Image(graph.get_graph().draw_mermaid_png()))
    with open("workflow_graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
