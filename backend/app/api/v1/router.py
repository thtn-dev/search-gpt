from fastapi import APIRouter
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import user

api_router_v1 = APIRouter()

# Include chat endpoints
api_router_v1.include_router(chat.router, tags=["chat"])

api_router_v1.include_router(user.router, tags=["user"])

