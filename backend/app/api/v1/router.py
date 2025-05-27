"""
Router for API v1
"""
from fastapi import APIRouter
from app.api.v1.endpoints import chat_endpoint
from app.api.v1.endpoints import auth_endpoint
from app.api.v1.endpoints import benchmark_endpoint
from app.api.v1.endpoints import thread_endpoint


api_router_v1 = APIRouter()

# Include chat endpoints
api_router_v1.include_router(chat_endpoint.router, tags=["AIChat"])

api_router_v1.include_router(auth_endpoint.router, prefix="/auth", tags=["Auth"])

# Include benchmark endpoints
api_router_v1.include_router(benchmark_endpoint.router, prefix="/benchmark", tags=["Benchmark"])

# Include thread endpoints
api_router_v1.include_router(thread_endpoint.router, tags=["Thread"])


