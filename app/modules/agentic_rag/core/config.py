"""
Configuration for the Agentic RAG module.
"""

import os
from pydantic import BaseModel

# Check if running in Docker environment
DOCKER_ENVIRONMENT = os.getenv('DOCKER_ENVIRONMENT', 'False').lower() == 'true'

# Qdrant configuration
# In Docker, use the service name; otherwise use localhost
QDRANT_HOST = 'qdrant' if DOCKER_ENVIRONMENT else 'localhost'
# Important: Use port 6334 for HTTP API (not 6333 which is for gRPC)
QDRANT_URL = os.getenv('QDRANT_URL', f'http://{QDRANT_HOST}:6334')
QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', '')
QDRANT_COLLECTION = os.getenv('QDRANT_COLLECTION', 'agentic_rag_kb')

# Embedding configuration
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/embedding-001')


class QdrantConfig(BaseModel):
	"""Qdrant configuration."""

	QdrantUrl: str = QDRANT_URL
	QdrantApiKey: str = QDRANT_API_KEY
	QdrantCollection: str = QDRANT_COLLECTION

	class Config:
		env_prefix = 'QDRANT_'


settings = QdrantConfig()
