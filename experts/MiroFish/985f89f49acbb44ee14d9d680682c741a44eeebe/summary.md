# MiroFish — Summary

## Repository Purpose and Goals

MiroFish is a next-generation AI-powered swarm intelligence prediction engine. Its core goal is to allow users to upload real-world "seed" materials (news articles, policy drafts, research reports, novels, or any document), describe a prediction requirement in natural language, and receive:

1. A detailed analytical prediction report.
2. A deeply interactive high-fidelity digital simulation world populated by AI agents.

The project's guiding philosophy is "rehearse the future in a digital sandbox, and win decisions after countless simulations." It aims to break the limitations of traditional prediction by capturing collective emergence triggered by individual agent interactions.

## Key Features and Capabilities

- **GraphRAG-based knowledge construction**: Uploaded documents are chunked, analyzed, and ingested into a Zep Cloud knowledge graph. An LLM-driven ontology generator first identifies entity types and relationship types specific to the domain, then guides how Zep populates the graph.
- **Automatic agent persona generation**: Graph entities are read back from Zep and converted into rich OASIS agent profiles complete with personality (MBTI, age, gender, profession, interests), platform statistics (followers, karma), and behavioral tendencies.
- **Dual-platform parallel simulation**: Simulations run simultaneously on Twitter-like and Reddit-like virtual social platforms via the OASIS (camel-oasis) framework. Agents post, reply, like, follow, and interact according to their generated personas.
- **Dynamic temporal memory updates**: During simulation, each agent's actions are narrated in natural language and fed back into the Zep graph as new episodes, enriching the knowledge graph over time.
- **ReACT-style Report Agent**: After simulation, a dedicated Report Agent uses multi-round tool-augmented reasoning (InsightForge deep retrieval, PanoramaSearch, QuickSearch, Interview) to write a structured analysis report.
- **Deep interaction mode**: Users can interview individual agents post-simulation or chat with the Report Agent for follow-up questions.
- **File-based inter-process communication (IPC)**: The Flask backend communicates with the independently running simulation subprocess via a command/response filesystem protocol.

## Primary Use Cases and Target Audience

- **Decision makers and policy analysts**: Testing policy or PR strategies at zero risk in a simulated public opinion environment.
- **Financial and political analysts**: Predicting public or market reaction to events.
- **Researchers**: Studying emergent collective behavior in multi-agent social systems.
- **Creative users**: Exploring narrative deductions — e.g., predicting lost novel endings or "what-if" historical scenarios.

## High-Level Architecture Overview

MiroFish is a full-stack web application split into three layers:

- **Frontend (Vue 3 + Vite)**: A single-page application with a step-by-step wizard UI. Five main workflow steps are represented as large Vue components. The frontend communicates with the backend via a proxied Axios HTTP client.

- **Backend (Python / Flask)**: A REST API server organized into three Flask Blueprints (`/api/graph`, `/api/simulation`, `/api/report`). Business logic lives in a services layer. Data models manage project and task state on the filesystem. Long-running operations (graph building, simulation, report generation) run in background threads or subprocesses.

- **External Services**:
  - **Zep Cloud**: Provides the persistent knowledge graph (GraphRAG). All entity/relationship data, simulation episode memory, and graph search capabilities are hosted here.
  - **LLM API** (any OpenAI SDK-compatible provider, default: Alibaba Qwen via Bailian): Powers ontology generation, agent profile creation, simulation configuration, and report writing.
  - **OASIS / camel-ai**: Provides the multi-agent social simulation runtime (Twitter and Reddit environments).

## Related Projects and Dependencies

| Dependency | Version | Role |
|---|---|---|
| camel-oasis | 0.2.5 | Multi-agent social simulation framework (Twitter/Reddit) |
| camel-ai | 0.2.78 | CAMEL agent framework underlying OASIS |
| zep-cloud | 3.13.0 | Knowledge graph memory and GraphRAG |
| openai | >=1.0.0 | Unified LLM client (OpenAI SDK format) |
| flask | >=3.0.0 | Backend web framework |
| flask-cors | >=6.0.0 | CORS support |
| pydantic | >=2.0.0 | Data validation |
| PyMuPDF | >=1.24.0 | PDF text extraction |
| python-dotenv | >=1.0.0 | Environment variable loading |
| Vue 3 | ^3.5.24 | Frontend reactive framework |
| vue-router | ^4.6.3 | Frontend routing |
| axios | ^1.13.2 | HTTP client |
| d3 | ^7.9.0 | Graph visualization |
| vite | ^7.2.4 | Frontend build tool |
| concurrently | ^9.1.2 | Parallel dev server runner |

The project acknowledges OASIS (Open Agent Social Interaction Simulations) by the CAMEL-AI team as its core simulation engine and is incubated by Shanda Group.
