import json
import os
from functools import lru_cache

from dotenv import load_dotenv  # type: ignore
from pydantic import BaseModel

load_dotenv()

PROJECT_NAME = 'MEOBEO.AI'
API_V1_STR = '/api/v1'
API_V2_STR = '/api/v2'

# Force host.docker.internal when running in Docker

SMTP_USERNAME = os.getenv('SMTP_USERNAME')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')


SERVICE = 'gemini'
MODEL_NAME = 'model/gemini-2.0-flash-exp'

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

SECRET_KEY = os.getenv('SECRET_KEY', '-extremely-secret-and-very-long-key')
TOKEN_ISSUER = os.getenv('TOKEN_ISSUER', 'frecord-api')
TOKEN_AUDIENCE = os.getenv('TOKEN_AUDIENCE', 'frecord-client')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))

FERNET_KEY = os.getenv('FERNET_KEY', '4pI2ZAxB7X8N9sM5R8k_AfF4PLbJnvYsV2gJJei8BjI=')

# MinIO Settings
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET_NAME = os.getenv('MINIO_BUCKET_NAME', 'meobeo')
MINIO_SECURE = False  # Using boolean instead of string

CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# API pricing per million tokens (in USD)
INPUT_PRICE_PER_MILLION = float(os.getenv('INPUT_PRICE_PER_MILLION', '0.10'))
OUTPUT_PRICE_PER_MILLION = float(os.getenv('OUTPUT_PRICE_PER_MILLION', '0.40'))
CONTEXT_PRICE_PER_MILLION = float(os.getenv('CONTEXT_PRICE_PER_MILLION', '0.025'))

class Settings(BaseModel):
	PROJECT_NAME: str = PROJECT_NAME
	API_V1_STR: str = API_V1_STR
	API_V2_STR: str = API_V2_STR

	# JWT Settings
	SECRET_KEY: str = SECRET_KEY
	TOKEN_ISSUER: str = TOKEN_ISSUER
	TOKEN_AUDIENCE: str = TOKEN_AUDIENCE
	ACCESS_TOKEN_EXPIRE_MINUTES: int = ACCESS_TOKEN_EXPIRE_MINUTES
	REFRESH_TOKEN_EXPIRE_DAYS: int = REFRESH_TOKEN_EXPIRE_DAYS

	# MinIO Settings
	MINIO_ENDPOINT: str = MINIO_ENDPOINT
	MINIO_ACCESS_KEY: str = MINIO_ACCESS_KEY
	MINIO_SECRET_KEY: str = MINIO_SECRET_KEY
	MINIO_BUCKET_NAME: str = MINIO_BUCKET_NAME
	MINIO_SECURE: bool = MINIO_SECURE
	CELERY_BROKER_URL: str = CELERY_BROKER_URL
	CELERY_RESULT_BACKEND: str = CELERY_RESULT_BACKEND


@lru_cache()
def get_settings():
	return Settings()
