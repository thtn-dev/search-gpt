```markdown
# Running FastAPI with Uvicorn

To run a FastAPI application using Uvicorn, follow these steps:

1. **Install Dependencies**:
    Make sure you have FastAPI and Uvicorn installed. You can install them using pip:
    ```bash
    pip install fastapi uvicorn
    ```

2. **Create Your FastAPI Application**:
    Ensure you have a Python file (e.g., `main.py`) with your FastAPI app. Example:
    ```python
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    def read_root():
         return {"Hello": "World"}
    ```

3. **Run the Application**:
    Use the following command to run the application with Uvicorn:
    ```bash
    uvicorn main:app --reload
    ```
    - Replace `main` with the name of your Python file (without the `.py` extension).
    - The `--reload` flag enables auto-reloading for development.

4. **Access the Application**:
    Open your browser and navigate to `http://127.0.0.1:8000` to see your FastAPI app in action.

5. **Interactive API Docs**:
    FastAPI provides interactive API documentation:
    - Swagger UI: `http://127.0.0.1:8000/docs`
    - ReDoc: `http://127.0.0.1:8000/redoc`
```