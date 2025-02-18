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


class State(TypedDict):
    messages: Annotated[list, add_messages]
    law: str
    law_url: str
    law_url_approved: Optional[bool]  # Can be True, False, or None


# Initialize the graph
workflow = StateGraph(state_schema=State)


def ask_law(state: State) -> Dict:
    print("----> ask_law")

    # Ask the user for the law name
    msg = "Wat is de naam van de wet?"
    asyncio.get_event_loop().create_task(
        manager.broadcast(msg)
    )  # TODO: do not broadcast to all clients, but only the one from the config
    return {"messages": [AIMessage(msg)]}  # Note: we reset the messages


def retrieve_law_url(state: State) -> Dict:
    print("----> retrieve_law_url")
    pprint.pprint(state)


# Add nodes
workflow.add_node("ask_law", ask_law)
workflow.add_node("retrieve_law_url", retrieve_law_url)

# Add edges
workflow.set_entry_point("ask_law")
workflow.add_edge("ask_law", "retrieve_law_url")


# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Compile the graph
graph = workflow.compile(
    checkpointer,
    interrupt_before=[
        "retrieve_law_url", # IMPROVE: use interrupt_after instead
    ],
)

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
                # {"messages": [HumanMessage(user_input)]},
                Command(resume={"data": user_input}),
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
