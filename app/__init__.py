"""Main init"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import SECRET_KEY
from app.exceptions.handlers import setup_exception_handlers
from app.middleware.localization_middleware import LocalizationMiddleware
from app.middleware.translation_manager import _
from app.modules import route as api_routers


def custom_openapi(app: FastAPI):
    """Create custom OpenAPI schema (used for Swagger UI)"""
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=_("api_description"),
        routes=app.routes,
    )
    # Add Bearer token auth for Swagger UI
    openapi_schema['components']['securitySchemes'] = {
        'Bearer': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }
    }
    openapi_schema['security'] = [{'Bearer': []}]
    app.openapi_schema = openapi_schema
    return openapi_schema


def create_app():
    """Create main FastAPI app"""
    app = FastAPI(
        title=_("api_title"),
        version="2.0.0",
        description=_("api_description"),
    )

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        session_cookie='cgsem_session',
        same_site='lax',
    )

    app.add_middleware(LocalizationMiddleware)

    # Debug middleware for OAuth (Google login, etc.)
    @app.middleware('http')
    async def debug_oauth_middleware(request, call_next):
        if 'google' in request.url.path:
            print(f'[OAuth Debug] Path: {request.url.path}')
            try:
                print(f'[OAuth Debug] Session before: {request.session}')
            except:
                print('[OAuth Debug] No session available')
            print(f'[OAuth Debug] Cookies: {request.cookies}')
        response = await call_next(request)
        if 'google' in request.url.path:
            try:
                print(f'[OAuth Debug] Session after: {request.session}')
            except:
                print('[OAuth Debug] No session available after')
        return response

    # Routes
    app.include_router(api_routers, prefix='/api')

    # Override default OpenAPI schema
    app.openapi = lambda: custom_openapi(app)

    # Custom exception handlers
    setup_exception_handlers(app)

    # Optional root endpoint with version info
    @app.get("/", tags=["Root"])
    async def root():
        return {
            "message": "Welcome to the API",
            "version": app.version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }

    return app
