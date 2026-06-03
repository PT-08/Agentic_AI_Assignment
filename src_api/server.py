import os
import sys
from pathlib import Path

# Ensure the workspace root is in sys.path for imports to work
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from src_api.routes import router

app = FastAPI(
    title="Household Energy Workflow API",
    description="FastAPI wrapper for the Agentic AI Assignment langgraph workflows.",
    version="1.0.0",
)

app.include_router(router)


@app.get("/")
def root() -> dict:
    return {
        "status": "ok",
        "message": "Household Energy Workflow API is running.",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src_api.server:app", host="0.0.0.0", port=port, reload=False)
