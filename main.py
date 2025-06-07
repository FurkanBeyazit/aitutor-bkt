from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from router import router
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="Exam Platform API",
    description="API that parses PDF questions and answers, provides student level tests and question explanations.",
    version="1.0.0"
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (should be restricted in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add main router
app.include_router(router)

# Root endpoint - to check if API is running
@app.get("/")
async def root():
    return {
        "message": "Exam Platform API is running",
        "status": "active",
        "documentation": "/docs"
    }

# Run the app directly
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)