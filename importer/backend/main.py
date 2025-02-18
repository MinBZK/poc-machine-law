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

# import uuid

# Set up the state
from langgraph.graph import MessagesState, START
from langgraph.types import Command, interrupt

# from langchain_core.tools import tool
# from langgraph.prebuilt import ToolNode
# from pydantic import BaseModel
import asyncio


model = ChatAnthropic(model="claude-3-5-sonnet-latest", temperature=0, max_retries=2)


def fetch_data(url):
    loader = WebBaseLoader(  # IMPROVE: compare to UnstructuredLoader and DoclingLoader
        url
    )
    docs = loader.load()
    return docs


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def get_first_source(docs):
    return docs[0].metadata["source"]


# Find the specified law online
retriever = TavilySearchAPIRetriever(
    k=1, include_domains=["wetten.overheid.nl"]
)  # Limit to 1 result


class State(TypedDict):
    messages: Annotated[list, add_messages]
    law: str
    law_url: str
    law_url_approved: Optional[bool]  # Can be True, False, or None


# Analyze the law content
analyize_law_prompt = ChatPromptTemplate(
    [
        # (
        #     "user",
        #     [
        #         {
        #             "type": "text",
        #             "text": "Ik heb deze wetten zo gemodelleerd in YAML.",
        #         },
        #         {
        #             "type": "document",
        #             "title": "voorbeeld 1",
        #             "text": format_docs(
        #                 fetch_data(
        #                     "https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/law/zvw/RVZ-2024-01-01.yaml"
        #                 )
        #             ),
        #         },
        #         {
        #             "type": "document",
        #             "title": "voorbeeld 2",
        #             "text": format_docs(
        #                 fetch_data(
        #                     "https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/law/handelsregisterwet/KVK-2024-01-01.yaml"
        #                 )
        #             ),
        #         },
        #     ],
        # ),
        (
            "user",
            [
                {
                    "type": "text",
                    "text": "Ik wil nu hetzelfde doen voor de volgende wettekst. Analyseer de wet grondig! Dan wil ik graag eerst stap voor stap zien wat de wet doet. Wie het uitvoert. Waar de wet van afhankelijk is. En dan graag per uitvoeringsorganisatie een YAML file precies zoals de voorbeelden (verzin geen nieuwe velden/operations/...).",
                    # "text": "Vat de volgende wettekst samen in 10 woorden.",
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


# Initialize the graph
workflow = StateGraph(state_schema=State)


def ask_law(state: State) -> Dict:
    print("----> ask_law")

    # If a law is already provided, we skip this step
    if state.get("law"):
        return {}

    # Check if the last message is a user message. If so, store the law name in the graph state
    if state["messages"] and isinstance(state["messages"][-1], HumanMessage):
        law = state["messages"][-1].content
        return {"messages": state["messages"], "law": law}

    # Otherwise, ask the user for the law name
    msg = "Wat is de naam van de wet?"
    asyncio.get_event_loop().create_task(
        manager.broadcast(msg)
    )  # TODO: do not broadcast to all clients, but only the one from the config
    return {"messages": [model.invoke([AIMessage(msg)])]}  # Note: we reset the messages


def search_law(state: State) -> Dict:
    print("----> search_law")
    # pprint.pprint(state)

    # Check if the last message is a user message. If so, set the approval flag
    last_message = state["messages"][-1]
    if isinstance(last_message, HumanMessage) and last_message.content.lower() in (
        "ja",
        "j",
    ):
        return {"law_url_approved": True}

    if state.get("law_url"):
        # Reset the law, its URL, and the messages, since we are going back to the law input
        return {"messages": [], "law": None, "law_url": None, "law_url_approved": False}

    # Else...
    law = state["law"]
    docs = retriever.invoke(law)
    state["law_url"] = get_first_source(docs)  # TODO: handle if no URL is found

    # Ask the user to approve the URL. Note: no need to send a message by WebSocket manually, since the user is already connected
    state["messages"].append(
        AIMessage(
            f"Eens met de volgende URL?\n\n{state['law_url']}\n\nTyp 'j' of 'ja' om verder te gaan."
        )
    )

    return {"messages:": state["messages"], "law_url": state["law_url"]}


def fetch_and_analyze_law(state: State) -> Dict:
    print("----> fetch_and_analyze_law")
    # pprint.pprint(state)
    content = format_docs(fetch_data(state["law_url"]))
    response = model.invoke(analyize_law_prompt.format_messages(content=content))

    state["messages"].append(response)

    # Return the state
    return {"messages": state["messages"]}


def handle_law_input(state: State) -> str:
    print("----> handle_law_input")

    # If the state contains a law, we continue
    if state.get("law"):
        return "search_law"

    # Otherwise, we wait for the user to provide the law input
    return END


def handle_law_approval(state: State) -> str:
    print("----> handle_law_approval")

    # If the state contains that the law URL is approved, we continue
    if state.get("law_url_approved"):
        return "fetch_and_analyze_law"

    # If the state contains a law URL that is not approved, we loop back to the law input
    if (
        state.get("law_url_approved") is not None
        and state.get("law_url_approved") is False
    ):
        return "ask_law"

    # Otherwise, we wait for the user to provide the law URL approval
    return END


# Add nodes
workflow.add_node("ask_law", ask_law)
workflow.add_node("search_law", search_law)
workflow.add_node("fetch_and_analyze_law", fetch_and_analyze_law)

# Add edges
workflow.set_entry_point("ask_law")
workflow.add_conditional_edges("ask_law", handle_law_input)
workflow.add_conditional_edges("search_law", handle_law_approval)


# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Compile the graph
graph = workflow.compile(checkpointer)

config = {"configurable": {"thread_id": "1"}}  # IMPROVE: thread_id not hardcoded

# Initialize a FastAPI web server
app = FastAPI()


@app.get("/")
async def get():
    return FileResponse("workflow_graph.png")  # TODO: other response


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        # Generate a thread ID
        # thread_id = str(uuid.uuid4())
        self.active_connections.append(websocket)
        graph.invoke({"messages": []}, config)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            print("--> sending message")
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            user_input = await websocket.receive_text()

            # Process the received data through the workflow
            print("message received:", user_input)

            for event in graph.stream(
                {"messages": [HumanMessage(user_input)]},
                config,
                stream_mode="values",
            ):
                # In case of an AI message, send it back to the client
                # pprint.pprint(event["messages"])
                msg = event["messages"][-1]
                if isinstance(msg, AIMessage):
                    await websocket.send_text(msg.content)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"Error: {pprint.pformat(e)}")
    finally:
        manager.disconnect(websocket)


def main():
    # Generate a Mermaid graph of the workflow
    # display(Image(graph.get_graph().draw_mermaid_png()))
    with open("workflow_graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
