from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, date
import os
import sys
import signal
import asyncio
from dotenv import load_dotenv

from app.models.database import get_db, engine
from app.models.models import Base, Class, Assignment, AssignmentStatus, PendingAssignment
from app.services.ai_service import AIService
from app.routers import classes, assignments, ai, pending_assignments

# Load environment variables from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Assignment Tracker API",
    description="A comprehensive assignment tracking system with AI integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(classes.router, prefix="/api/classes", tags=["classes"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(pending_assignments.router, prefix="/api/pending-assignments", tags=["pending-assignments"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Assignment Tracker API is running!", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    """Detailed health check with database connectivity."""
    try:
        # Test database connection
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/shutdown")
async def shutdown_app():
    """Shutdown the application gracefully."""
    try:
        def shutdown_server():
            # Kill current process
            os._exit(0)
        
        # Schedule shutdown after sending response
        asyncio.get_event_loop().call_later(1.0, shutdown_server)
        
        return {"message": "Application shutdown initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during shutdown: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
