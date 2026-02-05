import asyncio
import json
import os
import pprint
import re
import uuid
from typing import Annotated, Literal, TypedDict

import jsonschema
import nest_asyncio
import yaml
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from jsonschema import validate
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.utils import (
    convert_to_secret_str,
    get_from_dict_or_env,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

from script.validate import (
    collect_defined_variables,
    collect_service_outputs,
    collect_service_references,
    find_variables_in_dict,
)

# If this is a production environment, we use more resources / tokens
is_production = os.getenv("IS_PRODUCTION", "false").lower() == "true"

router = APIRouter(prefix="/importer", tags=["importer"])

# Initialize model without API key initially - will be set dynamically when needed
model = ChatAnthropic(
    model="claude-3-7-sonnet-latest",
    temperature=0,
    max_retries=2,
    max_tokens_to_sample=4000,  # Note: default is 1024 tokens
)

# Initialize retriever without API key initially - will be set dynamically when needed
retriever = TavilySearchAPIRetriever(
    k=1,
    include_domains=["wetten.overheid.nl"],
)  # Limit to 1 result


class State(TypedDict):
    messages: Annotated[list, add_messages]
    law: str
    should_retry: bool
    law_url: str
    law_url_approved: bool | None  # Can be True, False, or None
    anthropic_api_key: str | None  # Optional, can be None if not provided by the user. Also below
    tavily_api_key: str | None


class WebSocketMessage(TypedDict):
    id: str
    type: str  # E.g. "progress". Default: chunk
    content: str | int
    quick_replies: list[str]


# Initialize the graph
workflow = StateGraph(state_schema=State)

# Lazy initialization for nest_asyncio and event loop
# We delay applying nest_asyncio until it's actually needed to avoid
# conflicts with uvicorn's startup (which uses loop_factory in 0.40.0+)
_nest_asyncio_applied = False
_loop = None


def get_event_loop():
    """Get or create the event loop with nest_asyncio applied."""
    global _nest_asyncio_applied, _loop
    if not _nest_asyncio_applied:
        nest_asyncio.apply()
        _nest_asyncio_applied = True
    if _loop is None:
        _loop = asyncio.get_event_loop()
    return _loop


def validate_schema(yaml_data: any) -> str | None:
    """Validate a YAML file against the JSON schema."""
    schema = json.loads(schema_content)

    try:
        validate(instance=yaml_data, schema=schema)
        return None
    except jsonschema.exceptions.ValidationError as err:
        return str(err.message)


# Get all law YAML files
laws_dir = os.path.join(os.path.dirname(__file__), "../../laws")
examples = []
for root, _, files in os.walk(laws_dir):
    for file in files:
        if file.endswith(".yaml"):  # Return only YAML files
            # law_files.append(os.path.relpath(os.path.join(root, file), laws_dir))
            with open(os.path.join(root, file)) as f:
                examples.append(f.read())


def validate_service_references(
    yaml_data: any,
) -> list[str]:  # Note: somewhat similar to the function with the same name in script/validate
    """Validate that all service references have corresponding outputs."""

    # Collect references from this block
    references = collect_service_references(yaml_data)

    # Collect outputs from this block file and existing files
    all_outputs = collect_service_outputs(yaml_data)
    for example in examples:
        example_data = yaml.safe_load(example)
        all_outputs.update(collect_service_outputs(example_data))

    # Check for missing references
    missing_references = references - all_outputs

    return list(
        {
            f"non-existing output that is referenced: {service}.{field} (law: {law})"
            for service, law, field in sorted(missing_references)
        }
    )  # Return as a list for consistency with the function signature


def validate_variable_definitions(
    yaml_data: any,
) -> list[str]:  # Note: somewhat similar to the function with the same name in script/validate
    """Validate that all $VARIABLES are defined."""

    defined = collect_defined_variables(yaml_data)
    referenced = find_variables_in_dict(yaml_data)

    # calculation_date is implicitly defined
    referenced.discard("$calculation_date")

    undefined = {v.replace("$", "") for v in referenced} - defined

    return list(
        {f"undefined variable: {var}" for var in sorted(undefined)}
    )  # Return as a list for consistency with the function signature


def ask_law(state: State, config: RunnableConfig) -> dict:
    print("----> ask_law")

    thread_id = config["configurable"]["thread_id"]

    # Ask the user for the law name
    msg = "Wat is de naam van de wet?"
    get_event_loop().run_until_complete(
        manager.send_message(WebSocketMessage(id=str(uuid.uuid4()), content=msg), thread_id)
    )

    return {"messages": []}  # Note: we reset the messages


def check_law_input(state: State, config: RunnableConfig) -> dict:
    print("----> check_law_input")

    resp = interrupt("check_law_input")

    thread_id = config["configurable"]["thread_id"]

    if len(resp) < 4:
        get_event_loop().run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    content="De wetnaam moet minimaal 4 tekens bevatten.",
                ),
                thread_id,
            )
        )
        return {"should_retry": True, "law": resp}

    # If the API keys are unset or empty, return an error message
    anthropic_key = state.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY")
    tavily_key = state.get("tavily_api_key") or os.getenv("TAVILY_API_KEY")

    if (not anthropic_key) or (not tavily_key):
        get_event_loop().run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    content="Je moet eerst hierboven API-keys invoeren om verder te kunnen.",
                ),
                thread_id,
            )
        )
        return {"should_retry": True, "law": resp}

    # Send a mesage to the frontend to update the progress to the next step
    get_event_loop().run_until_complete(
        manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                type="progress",
                content=1,
            ),
            thread_id,
        )
    )

    return {"should_retry": False, "law": resp}


def ask_law_confirmation(state: State, config: RunnableConfig) -> dict:
    print("----> ask_law_confirmation")

    # Find the law URL
    retriever.api_key = get_from_dict_or_env(state, "tavily_api_key", "TAVILY_API_KEY")
    docs = retriever.invoke(state["law"])

    if len(docs) == 0:
        return {"law_url": None}

    metadata = docs[0].metadata
    url = metadata["source"]  # IMPROVE: handle the case where no docs are found

    thread_id = config["configurable"]["thread_id"]

    get_event_loop().run_until_complete(
        manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                content=f"Is dit de wet die je bedoelt?\n\n{metadata['title']}\n[{url}]({url})",
                quick_replies=["Ja", "Nee"],
            ),
            thread_id,
        )
    )

    return {"law_url": url}


def handle_law_confirmation(state: State, config: RunnableConfig) -> dict:
    print("----> handle_law_confirmation")

    thread_id = config["configurable"]["thread_id"]

    if state["law_url"] is None:
        get_event_loop().run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    content="Geen resultaten gevondem voor deze wetnaam.",
                ),
                thread_id,
            )
        )
        return {"law_url_approved": False}

    resp = interrupt("handle_law_confirmation")

    # Parse the response
    is_approved = False
    if resp.lower() in ("ja", "j"):
        is_approved = True

        # Send a mesage to the frontend to update the progress to the next step
        get_event_loop().run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    type="progress",
                    content=2,
                ),
                thread_id,
            )
        )

    return {"law_url_approved": is_approved}


def fetch_and_format_data(url: str) -> str:
    docs = WebBaseLoader(url).load()  # IMPROVE: compare to UnstructuredLoader and DoclingLoader
    return "\n\n".join(doc.page_content for doc in docs)


# Get the schema content
from pathlib import Path
_schema_path = Path(__file__).resolve().parent.parent.parent / "schema" / "v0.1.7" / "schema.json"
with open(_schema_path) as sf:
    schema_content = sf.read()

analyize_law_prompt = ChatPromptTemplate(
    [
        SystemMessage(
            "Je bent een AI-agent die wetteksten kan analyseren en omzetten naar YAML-formaat. Tutoyeer de gebruiker. Je YAML output moet gebaseerd zijn op dit JSON schema: ```json\n{schema_content}\n```\nReturn de output direct, *in YAML-formaat*, zonder uitleg of aanvullende tekst. Begin de YAML output met ```yaml.",
        ),
        (
            "user",
            [
                {
                    "type": "text",
                    "text": "Ik heb deze wetten zo gemodelleerd in YAML.",
                },
                *[  # Use the * operator to unpack the examples list
                    {
                        "type": "document",
                        "title": "Voorbeeld",
                        "text": example,
                    }
                    for example in (
                        examples
                        if is_production
                        else examples[:2]  # Limit to the first 2 examples for testing purposes to reduce tokens / costs
                    )
                ],
            ],
        ),
        (
            "user",
            [
                {
                    "type": "text",
                    "text": "Ik wil nu hetzelfde doen voor de volgende wettekst. Analyseer de wet grondig! Ik wil graag per uitvoeringsorganisatie een YAML file die de wet modelleert, precies zoals de voorbeelden (verzin geen nieuwe velden/operations/...).",
                },
                {
                    "type": "document",
                    "title": "Wettekst",
                    "text": "{content}",
                },
            ],
        ),
    ]
)


def process_law(state: State, config: RunnableConfig) -> dict:
    print("----> process_law")

    thread_id = config["configurable"]["thread_id"]

    get_event_loop().run_until_complete(
        manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                content="De wettekst wordt nu opgehaald en geïnterpreteerd, dit kan even duren…",
                quick_replies=[],
            ),
            thread_id,
        )
    )

    # Fetch the law content
    content = fetch_and_format_data(state["law_url"])

    # Remove duplicate whitespace from the content
    content = re.sub(r"\s+", " ", content)

    # Cap the law content for testing purposes to reduce costs when not on pro
    if (not is_production) and len(content) > 1000:
        content = content[:1000]

    # Add a human message to process the law
    model.anthropic_api_key = convert_to_secret_str(
        get_from_dict_or_env(state, "anthropic_api_key", "ANTHROPIC_API_KEY")
    )
    result = model.invoke(
        analyize_law_prompt.format_messages(
            schema_content=schema_content,
            content=content,
        )
    )

    # Send a mesage to the frontend to update the progress to the next step
    get_event_loop().run_until_complete(
        manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                type="progress",
                content=3,
            ),
            thread_id,
        )
    )

    return {"messages": [result]}


def process_law_feedback(state: State, config: RunnableConfig) -> dict:
    print("----> process_law_feedback")

    user_input = interrupt("process_law_feedback")

    # If the user wants to analyze the law, validate it against the schema
    if "analyseer" in user_input.lower():
        print("----> analyzing YAML content")

        validation_errors = []

        # Find all substrings between ```yaml and ```
        pattern = r"```yaml\n(.*?)(```|$)"

        # re.DOTALL flag makes '.' match newlines as well
        matches = re.finditer(pattern, state["messages"][-1].content, re.DOTALL)

        # Extract just the YAML content (without the delimiters)
        yaml_blocks = [match.group(1) for match in matches]
        for block in yaml_blocks:
            print("----> YAML block found")

            yaml_data = yaml.safe_load(block)

            # If the YAML data is not a dictionary, skip it (since it is most likely a subset of a larger block, included as explanation)
            if not isinstance(yaml_data, dict):
                print("----> skipping YAML block, not a dictionary")
                continue

            err = validate_schema(yaml_data)
            if err:
                validation_errors.append(err)

            validation_errors.extend(validate_service_references(yaml_data))
            validation_errors.extend(validate_variable_definitions(yaml_data))

        if validation_errors:
            user_input = f"Er zijn fouten gevonden in de YAML output:\n```\n{'\n'.join(f'- {error}' for error in validation_errors)}\n```"
        else:
            user_input = "De YAML output lijkt correct."  # IMPROVE: validate agains the Girkin tables

        thread_id = config["configurable"]["thread_id"]

        # Send a mesage to the frontend to update the progress to the next step
        get_event_loop().run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    type="progress",
                    content=4,
                ),
                thread_id,
            )
        )

        get_event_loop().run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    content=user_input,
                    quick_replies=[],
                ),
                thread_id,
            )
        )  # IMPROVE: send/show this as user message instead of AI message in the frontend

    state["messages"].append(HumanMessage(user_input))

    model.anthropic_api_key = convert_to_secret_str(
        get_from_dict_or_env(state, "anthropic_api_key", "ANTHROPIC_API_KEY")
    )
    result = model.invoke(state["messages"])

    return {"messages": result}


# Add nodes
workflow.add_node("ask_law", ask_law)
workflow.add_node("check_law_input", check_law_input)
workflow.add_node("ask_law_confirmation", ask_law_confirmation)
workflow.add_node("handle_law_confirmation", handle_law_confirmation)
workflow.add_node("process_law", process_law)
workflow.add_node("process_law_feedback", process_law_feedback)


# Add edges
workflow.set_entry_point("ask_law")
workflow.add_edge("ask_law", "check_law_input")


def should_retry_law_input(
    state: State,
) -> Literal[
    "ask_law", "ask_law_confirmation"
]:  # Note: instead of a lambda function, in order to use type hints for the workflow graph, also below
    return "ask_law" if state["should_retry"] else "ask_law_confirmation"


workflow.add_conditional_edges(
    "check_law_input",
    should_retry_law_input,
)
workflow.add_edge("ask_law_confirmation", "handle_law_confirmation")


def handle_law_confirmation_result(state: State) -> Literal["process_law", "ask_law"]:
    return "process_law" if state["law_url_approved"] else "ask_law"


workflow.add_conditional_edges("handle_law_confirmation", handle_law_confirmation_result)

workflow.add_edge("process_law", "process_law_feedback")
workflow.add_edge("process_law_feedback", "process_law_feedback")


# Initialize memory to persist state between graph runs. IMPROVE: store persistently in Postgres
checkpointer = MemorySaver()

# Compile the graph
graph = workflow.compile(
    checkpointer,
    # interrupt_after=["ask_law", "handle_law_confirmation"]
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[uuid.UUID, WebSocket] = {}

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

    # async def broadcast(self, message: WebSocketMessage):
    #     for websocket in self.active_connections.values():
    #         await websocket.send_json(message)

    async def send_message(self, message: WebSocketMessage, thread_id: uuid.UUID):
        if thread_id in self.active_connections:
            await self.active_connections[thread_id].send_json(message)


manager = ConnectionManager()


@router.get("/api-keys-status")
async def get_api_keys_status():
    """Check which API keys are available via environment variables."""
    return JSONResponse(
        {
            "anthropic_available": bool(os.getenv("ANTHROPIC_API_KEY")),
            "tavily_available": bool(os.getenv("TAVILY_API_KEY")),
        }
    )


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    thread_id = await manager.connect(websocket)
    # IMPROVE: implement functionality similar to the 'Stop generating' functionality in ChatGPT. Use an AbortController, so the API will actually stop generating? See https://community.openai.com/t/chatgpts-stop-generating-function-how-to-implement/235121 and https://developer.mozilla.org/en-US/docs/Web/API/AbortController

    try:
        async for user_input in websocket.iter_json():
            # # Process the received data through the workflow
            # print("message received:", user_input)

            if user_input.get("type") == "keys":
                # Store the keys in the state (only if provided)
                state_update = {}
                if "anthropicApiKey" in user_input and user_input["anthropicApiKey"]:
                    state_update["anthropic_api_key"] = user_input["anthropicApiKey"]
                if "tavilyApiKey" in user_input and user_input["tavilyApiKey"]:
                    state_update["tavily_api_key"] = user_input["tavilyApiKey"]

                if state_update:
                    graph.update_state(
                        {"configurable": {"thread_id": thread_id}},
                        state_update,
                    )

            elif user_input.get("type") == "text":
                contains_yaml = False
                chunk_content_so_far = ""

                async for chunk, _ in graph.astream(
                    Command(resume=user_input.get("content")),
                    {"configurable": {"thread_id": thread_id}},
                    stream_mode="messages",
                ):
                    if not contains_yaml:
                        chunk_content_so_far += chunk.content
                        if "```yaml" in chunk_content_so_far:
                            contains_yaml = True

                    # If the chunk contains response_metadata.stop_reason "max_tokens", then add a quick reply to continue
                    quick_replies = []
                    stop_reason = chunk.response_metadata.get("stop_reason")
                    if stop_reason == "max_tokens":
                        quick_replies = ["Ga door"]
                    elif contains_yaml and stop_reason == "end_turn":
                        quick_replies = ["Analyseer deze YAML-code"]

                    await manager.send_message(
                        WebSocketMessage(
                            id=chunk.id,
                            content=chunk.content,
                            quick_replies=quick_replies,
                        ),
                        thread_id,
                    )

    except WebSocketDisconnect:
        manager.disconnect(thread_id)

    except Exception as e:
        print(f"Error: {pprint.pformat(e)}")

        # Send an error message to the user
        await manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                content=f"Er is een fout opgetreden:\n```\n{e}\n```",
                quick_replies=[],
            ),
            thread_id,
        )

    finally:
        manager.disconnect(thread_id)
