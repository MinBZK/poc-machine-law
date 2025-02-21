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


class State(TypedDict):
    messages: Annotated[list, add_messages]
    law: str
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
    return {"messages": [AIMessage(msg)]}  # Note: we reset the messages


def ask_human(state: State, config: Dict) -> Dict:
    print("----> ask_human")

    thread_id = config["configurable"]["thread_id"]

    asyncio.get_event_loop().create_task(
        manager.send_message(
            WebSocketMessage(
                content="Ben je het hiermee eens?", quick_replies=["Ja", "Nee"]
            ),
            thread_id,
        )
    )

    resp = interrupt("ask_human")
    print("----> resumed:", resp)
    state["messages"].append(HumanMessage(resp))
    return {"messages": state["messages"]}


def retrieve_law_url(state: State) -> Dict:
    print("----> retrieve_law_url")
    pprint.pprint(state)


# Add nodes
workflow.add_node("ask_law", ask_law)
workflow.add_node("ask_human", ask_human)
workflow.add_node("retrieve_law_url", retrieve_law_url)

# Add edges
workflow.set_entry_point("ask_law")
workflow.add_edge("ask_law", "ask_human")
workflow.add_edge("ask_human", "retrieve_law_url")


# Initialize memory to persist state between graph runs
checkpointer = MemorySaver()

# Compile the graph
graph = workflow.compile(
    checkpointer,
    # interrupt_before=[
    #     "retrieve_law_url", # IMPROVE: use interrupt_after instead?
    # ],
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
