from langchain_anthropic import ChatAnthropic
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_community.document_loaders import WebBaseLoader
from langgraph.graph import StateGraph
from typing import Dict, Literal, Optional, TypedDict, Annotated, List
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import pprint
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
import uuid
import json
from langgraph.types import Command, interrupt
import asyncio
import nest_asyncio


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
    id: str
    content: str
    quick_replies: List[str]


# Initialize the graph
workflow = StateGraph(state_schema=State)

# Get the event loop and enable nesting, see https://pypi.org/project/nest-asyncio/
nest_asyncio.apply()
loop = asyncio.get_event_loop()


def ask_law(state: State, config: Dict) -> Dict:
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


def check_law_input(state: State, config: Dict) -> Dict:
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


def ask_law_confirmation(state: State, config: Dict) -> Dict:
    print("----> ask_law_confirmation")

    # Find the law URL
    docs = retriever.invoke(state["law"])

    metadata = docs[0].metadata
    url = metadata["source"]  # IMPROVE: handle the case where no docs are found

    thread_id = config["configurable"]["thread_id"]

    loop.run_until_complete(
        manager.send_message(
            WebSocketMessage(
                id=str(uuid.uuid4()),
                content=f"Is dit de wet die je bedoelt?\n\n{metadata["title"]}\n[{url}]({url})",
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


def fetch_and_format_data(url: str) -> str:
    docs = WebBaseLoader(
        url
    ).load()  # IMPROVE: compare to UnstructuredLoader and DoclingLoader
    return "\n\n".join(doc.page_content for doc in docs)


analyize_law_prompt = ChatPromptTemplate(
    [
        (
            "user",
            [
                {
                    "type": "text",
                    "text": "Ik heb deze wetten zo gemodelleerd in YAML.",
                },
                {
                    "type": "document",
                    "title": "voorbeeld 1",
                    "text": fetch_and_format_data(
                        "https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/law/zvw/RVZ-2024-01-01.yaml"
                    ),
                },
                {
                    "type": "document",
                    "title": "voorbeeld 2",
                    "text": fetch_and_format_data(
                        "https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/law/handelsregisterwet/KVK-2024-01-01.yaml"
                    ),
                },
            ],
        ),
        (
            "user",
            [
                {
                    "type": "text",
                    # "text": "Zet de volgende wettekst om naar YAML-formaat:",
                    "text": "Ik wil nu hetzelfde doen voor de volgende wettekst. Analyseer de wet grondig! Dan wil ik graag eerst stap voor stap zien wat de wet doet. Wie het uitvoert. Waar de wet van afhankelijk is. En dan graag per uitvoeringsorganisatie een YAML file precies zoals de voorbeelden (verzin geen nieuwe velden/operations/...).",
                },
                {
                    "type": "document",
                    "title": "wettekst",
                    "text": "{content}",
                },
            ],
        ),
    ]
)


def process_law(state: State, config: Dict) -> Dict:
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

    # Clip the law content to 100 characters for testing purposes. TODO: remove this
    if len(content) > 100:
        content = content[:100]

    # Add a human message to process the law
    result = model.invoke(analyize_law_prompt.format_messages(content=content))

    return {"messages": [result]}


def process_law_feedback(state: State, config: Dict) -> Dict:
    print("----> process_law_feedback")

    user_input = interrupt("process_law_feedback")
    state["messages"].append(HumanMessage(user_input))

    return {"messages": model.invoke(state["messages"])}


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

            for chunk, _ in graph.stream(
                Command(resume=user_input),
                {"configurable": {"thread_id": thread_id}},
                stream_mode="messages",
            ):
                await manager.send_message(
                    WebSocketMessage(id=chunk.id, content=chunk.content),
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
