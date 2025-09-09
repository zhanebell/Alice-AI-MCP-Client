from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from ..models.database import get_db
from ..services.ai_service import AIService
from ..schemas import SyllabusParseRequest, SyllabusParseResponse, AIGenerateRequest, AIGenerateResponse

router = APIRouter()

def get_ai_service():
    """Get AIService instance - initialized on each request to ensure env vars are loaded."""
    return AIService()

@router.post("/parse-syllabus", response_model=SyllabusParseResponse)
def parse_syllabus(request: SyllabusParseRequest, db: Session = Depends(get_db), ai_service: AIService = Depends(get_ai_service)):
    """
    Parse a syllabus text using AI to extract classes and assignments.
    """
    try:
        created_classes, created_pending_assignments = ai_service.parse_syllabus(request.syllabus_text, db)
        
        return SyllabusParseResponse(
            classes_created=created_classes,
            pending_assignments_created=created_pending_assignments,
            assignments_created=[],  # Keep for backward compatibility
            message=f"Successfully parsed syllabus: {len(created_classes)} classes and {len(created_pending_assignments)} pending assignments created"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing syllabus: {str(e)}")

@router.post("/generate-assignments", response_model=AIGenerateResponse)
def generate_assignments(request: AIGenerateRequest, db: Session = Depends(get_db), ai_service: AIService = Depends(get_ai_service)):
    """
    Generate assignments based on a natural language prompt.
    """
    try:
        created_pending_assignments = ai_service.generate_assignments(request.prompt, request.class_id, db)
        
        return AIGenerateResponse(
            pending_assignments_created=created_pending_assignments,
            assignments_created=[],  # Keep for backward compatibility
            message=f"Successfully generated {len(created_pending_assignments)} pending assignments"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating assignments: {str(e)}")

@router.get("/status")
def ai_status(ai_service: AIService = Depends(get_ai_service)):
    """
    Check the status of AI services.
    """
    groq_available = ai_service.client is not None
    return {
        "groq_connected": groq_available,
        "api_key_configured": ai_service.groq_api_key != "dummy_key_for_now",
        "mock_mode": not groq_available
    }

# Chat schemas
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    action_taken: bool
    data: dict = {}

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatMessage, db: Session = Depends(get_db), ai_service: AIService = Depends(get_ai_service)):
    """
    Chat with AI assistant using agentic system
    """
    try:
        print(f"\n=== CHAT ENDPOINT ===")
        print(f"Incoming Message: {request.message}")
        
        response, agent_used, action_taken, data = ai_service.chat(request.message, db)
        
        print(f"Final Response: {response}")
        print(f"Agent Used: {agent_used}")
        print(f"Action Taken: {action_taken}")
        print(f"Data: {data}")
        print(f"====================\n")
        
        return ChatResponse(
            response=response,
            agent_used=agent_used,
            action_taken=action_taken,
            data=data
        )
    except Exception as e:
        print(f"CHAT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
