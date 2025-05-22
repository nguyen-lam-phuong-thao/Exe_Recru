
# Agentic RAG Module

This module provides an implementation of a Retrieval-Augmented Generation (RAG) system with more advanced agent-like capabilities.

## Components

### Knowledge Base

- **KB Repository**: Interface for managing documents in a vector database (Qdrant)
- **KB Routes**: REST API endpoints for CRUD operations on the knowledge base

### RAG Operations

- **RAG Repository**: Implementation of RAG operations using LangChain
- **RAG Routes**: Endpoints for generating responses with document retrieval

### Agent-based RAG

- **RAG Agent Graph**: LangGraph-based implementation of an agent workflow for RAG
- **Agent Routes**: Endpoints for using the agent-based approach

## Usage

### Adding Documents

```python
import requests

url = "http://localhost:8000/api/v1/kb/documents"
headers = {
    "Content-Type": "application/json",
    "lang": "en"  # or "vi" for Vietnamese
}
payload = {
    "documents": [
        {
            "id": "doc1",
            "content": "This is a sample document about AI technology.",
            "metadata": {"source": "manual", "category": "technology"}
        }
    ]
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### Querying the Knowledge Base

```python
import requests

url = "http://localhost:8000/api/v1/kb/query"
headers = {
    "Content-Type": "application/json",
    "lang": "en"
}
payload = {
    "query": "What do you know about AI?",
    "top_k": 5
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### Generating RAG Responses

```python
import requests

url = "http://localhost:8000/api/v1/rag/generate"
headers = {
    "Content-Type": "application/json",
    "lang": "en"
}
payload = {
    "query": "Explain AI technology",
    "top_k": 5,
    "temperature": 0.7
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### Using the Agent

```python
import requests

url = "http://localhost:8000/api/v1/agent/answer"
headers = {
    "Content-Type": "application/json",
    "lang": "en"
}
payload = {
    "query": "Give me detailed information about AI technology",
    "top_k": 5,
    "temperature": 0.7
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

## Environment Variables

- `QDRANT_URL`: URL for the Qdrant vector database (default: `http://localhost:6333`)
- `QDRANT_API_KEY`: API key for Qdrant
- `QDRANT_COLLECTION`: Name of the collection in Qdrant (default: `agentic_rag_kb`)
- `GOOGLE_API_KEY`: API key for Google Generative AI services
- `EMBEDDING_MODEL`: Embedding model to use (default: `models/embedding-001`)
