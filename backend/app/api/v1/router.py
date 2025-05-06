from fastapi import APIRouter
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import benchmark


api_router_v1 = APIRouter()

# Include chat endpoints
api_router_v1.include_router(chat.router, tags=["AIChat"])

api_router_v1.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Include benchmark endpoints
api_router_v1.include_router(benchmark.router, prefix="/benchmark", tags=["Benchmark"])
