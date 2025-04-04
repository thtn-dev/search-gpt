from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.v1.search import search_router
import uvicorn

app = FastAPI(
    title="Search API",
    description="API for searching URLs",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api/v1")

@app.get("/", tags=["root"])
async def root() -> dict:
    """
    Root endpoint
    """
    return {"message": "Welcome to the Search API!"}

@app.get("/health", tags=["health"])
async def health() -> dict:
    """
    Health check endpoint
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    # Run the app using uvicorn
    uvicorn.run(
        "main:app",  # Đường dẫn đến ứng dụng FastAPI
        host="127.0.0.1",  # Địa chỉ host
        port=8000,         # Cổng chạy ứng dụng
        reload=True        # Tự động tải lại khi có thay đổi (chỉ dùng trong dev)
    )


