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
from jsonschema import validate
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Command, interrupt

router = APIRouter(prefix="/importer", tags=["importer"])


model = ChatAnthropic(
    model="claude-3-5-sonnet-latest",
    temperature=0,
    max_retries=2,
    max_tokens_to_sample=4000,  # Note: default is 1024 tokens
)

# Retriever to find the specified law online
retriever = TavilySearchAPIRetriever(
    k=1, include_domains=["wetten.overheid.nl"]
)  # Limit to 1 result


class State(TypedDict):
    messages: Annotated[list, add_messages]
    law: str
    should_retry: bool
    law_url: str
    law_url_approved: bool | None  # Can be True, False, or None


class WebSocketMessage(TypedDict):
    id: str
    content: str
    quick_replies: list[str]


# Initialize the graph
workflow = StateGraph(state_schema=State)

# Get the event loop and enable nesting, see https://pypi.org/project/nest-asyncio/
nest_asyncio.apply()
loop = asyncio.get_event_loop()


def validate_schema(yaml_content: str) -> str | None:
    """Validate a YAML file against the JSON schema."""
    schema = json.loads(schema_content)

    yaml_data = yaml.safe_load(yaml_content)

    try:
        validate(instance=yaml_data, schema=schema)
        return None
    except jsonschema.exceptions.ValidationError as err:
        return f"Error: {err.message}"


def ask_law(state: State, config: dict) -> dict:
    print("----> ask_law")

    thread_id = config["configurable"]["thread_id"]

    # Ask the user for the law name
    msg = "Wat is de naam van de wet?"
    loop.run_until_complete(
        manager.send_message(
            WebSocketMessage(id=str(uuid.uuid4()), content=msg), thread_id
        )
    )

    return {"messages": []}  # Note: we reset the messages


def check_law_input(state: State, config: dict) -> dict:
    print("----> check_law_input")

    resp = interrupt("check_law_input")

    if len(resp) < 4:
        thread_id = config["configurable"]["thread_id"]
        loop.run_until_complete(
            manager.send_message(
                WebSocketMessage(
                    id=str(uuid.uuid4()),
                    content="De wetnaam moet minimaal 4 tekens bevatten.",
                ),
                thread_id,
            )
        )
        return {"should_retry": True, "law": resp}

    return {"should_retry": False, "law": resp}


def ask_law_confirmation(state: State, config: dict) -> dict:
    print("----> ask_law_confirmation")

    # Find the law URL
    docs = retriever.invoke(state["law"])

    if len(docs) == 0:
        return {"law_url": None}

    metadata = docs[0].metadata
    url = metadata["source"]  # IMPROVE: handle the case where no docs are found

    thread_id = config["configurable"]["thread_id"]

    loop.run_until_complete(
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


def handle_law_confirmation(state: State, config: dict) -> dict:
    print("----> handle_law_confirmation")

    if state["law_url"] is None:
        thread_id = config["configurable"]["thread_id"]
        loop.run_until_complete(
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

    return {"law_url_approved": is_approved}


def fetch_and_format_data(url: str) -> str:
    docs = WebBaseLoader(
        url
    ).load()  # IMPROVE: compare to UnstructuredLoader and DoclingLoader
    return "\n\n".join(doc.page_content for doc in docs)


# Get the schema content
with open("schema/v0.1.3/schema.json") as sf:
    schema_content = sf.read()

# Get all law YAML files
laws_dir = os.path.join(os.path.dirname(__file__), "../../law")
examples = []
for root, _, files in os.walk(laws_dir):
    for file in files:
        if file.endswith(".yaml"):  # Return only YAML files
            # law_files.append(os.path.relpath(os.path.join(root, file), laws_dir))
            with open(os.path.join(root, file)) as f:
                examples.append(
                    {
                        "type": "document",
                        "title": "Voorbeeld",
                        "text": f.read(),
                    }
                )

# Limit to 2 YAML files for testing purposes to reduce costs. TODO: remove this
if len(examples) > 2:
    examples = examples[:2]

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
                *examples,  # Use the * operator to unpack the examples list
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


def process_law(state: State, config: dict) -> dict:
    print("----> process_law")

    thread_id = config["configurable"]["thread_id"]

    loop.run_until_complete(
        manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                content="De wettekst wordt nu opgehaald en geanalyseerd, dit kan even duren…",
                quick_replies=[],
            ),
            thread_id,
        )
    )

    # Fetch the law content
    content = fetch_and_format_data(state["law_url"])

    # Remove duplicate whitespace from the content
    content = re.sub(r"\s+", " ", content)

    # Cap the law content for testing purposes to reduce costs. TODO: remove this
    if len(content) > 1000:
        content = content[:1000]

    # Add a human message to process the law
    result = model.invoke(
        analyize_law_prompt.format_messages(
            schema_content=schema_content,
            content=content,
        )
    )

    return {"messages": [result]}


def process_law_feedback(state: State, config: dict) -> dict:
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
            err = validate_schema(block)

            if err:
                validation_errors.append(err)

        if validation_errors:
            user_input = f"Er zijn fouten gevonden in de YAML output:\n```\n{'\n'.join(validation_errors)}\n```"
        else:
            user_input = "De YAML output lijkt correct."  # IMPROVE: validate agains the Girkin tables

    thread_id = config["configurable"]["thread_id"]

    loop.run_until_complete(
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


workflow.add_conditional_edges(
    "handle_law_confirmation", handle_law_confirmation_result
)

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

    async def broadcast(self, message: WebSocketMessage):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)

    async def send_message(self, message: WebSocketMessage, thread_id: uuid.UUID):
        if thread_id in self.active_connections:
            await self.active_connections[thread_id].send_text(json.dumps(message))


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    thread_id = await manager.connect(websocket)

    try:
        while True:
            user_input = await websocket.receive_text()

            # Process the received data through the workflow
            print("message received:", user_input)

            contains_yaml = False
            chunk_content_so_far = ""
            for chunk, _ in graph.stream(
                Command(resume=user_input),
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
                        id=chunk.id, content=chunk.content, quick_replies=quick_replies
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
