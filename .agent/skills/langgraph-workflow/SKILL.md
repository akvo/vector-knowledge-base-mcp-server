---
name: langgraph-workflow
description: Guide to creating and modifying LangGraph workflows in this stack.
---

# LangGraph Workflow Patterns

Structured guide for developing AI agents.

## 1. Define State

Always use a typed `State` object (e.g., using `TypedDict` or Pydantic).

```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
```

## 2. Create Nodes

Define single-responsibility functions for your nodes.

```python
def call_model(state: State):
    # node logic here
    return {"messages": [response]}
```

## 3. Build Graph

Use `StateGraph` and compile it with a checkpointer if persistence is needed.

```python
from langgraph.graph import StateGraph

workflow = StateGraph(State)
workflow.add_node("agent", call_model)
workflow.set_entry_point("agent")
app = workflow.compile()
```

## 4. Integration with FastAPI

Expose the graph via a router.

```python
@router.post("/chat")
async def chat(request: ChatRequest):
    async for event in agent.astream(request.input):
        # handle events
```
