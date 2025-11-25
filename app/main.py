from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.routes import tasks
import os
import traceback

app = FastAPI(
    title="Prodloop Task API",
    description="Task Management API with Pub/Sub integration",
    version="1.0.0"
)

app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (422)"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors (500)"""
    print(f"Unexpected error: {str(exc)}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
