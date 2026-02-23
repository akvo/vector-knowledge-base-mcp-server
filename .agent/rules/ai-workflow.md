# AI Workflow Rules

Guidelines for implementing AI agents and workflows using LangGraph and LangChain.

## LangGraph Orchestration

1. **State Management**: Clearly define the `State` object for every graph. State should be immutable where possible.
2. **Node Responsibility**: Each node in the graph should have a single, well-defined responsibility.
3. **Edge Conditions**: Use conditional edges for complex branching logic based on agent reasoning.
4. **Persistence**: Use LangGraph checkpointers for persisting agent state across sessions.

## LangChain Integration

1. **Prompt Templates**: Store prompts in separate files or as structured constants. Avoid inline string interpolation for prompts.
2. **Tool Definition**: Use `@tool` decorator or Pydantic classes to define tools for agents.
3. **LLM Configuration**: Modularize LLM initialization to easily switch between providers (OpenAI, Anthropic, Ollama).

## Vector Database (Chroma)

1. **Collection Naming**: Consistent naming convention for Chroma collections.
2. **Embedding Consistency**: Ensure the same embedding model is used for both ingestion and retrieval.

## Object Storage (Minio)

1. **Bucket Lifecycle**: Automated bucket creation on application startup if not exists.
2. **File References**: Store file keys in the database or agent state, not raw URLs.
