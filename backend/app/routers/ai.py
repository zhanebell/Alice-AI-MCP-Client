from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

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
