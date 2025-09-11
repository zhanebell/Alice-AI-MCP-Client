from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import os

from ..models.database import get_db
from ..services.enhanced_ai_service import EnhancedAIService, initialize_ai_service
from ..services.ai_config import AIConfig
from ..schemas import SyllabusParseRequest, SyllabusParseResponse, AIGenerateRequest, AIGenerateResponse

router = APIRouter()

# Global AI service instance (will be initialized asynchronously)
_ai_service_instance: Optional[EnhancedAIService] = None

async def get_ai_service() -> EnhancedAIService:
    """Get Enhanced AI Service instance - initialized once and reused."""
    global _ai_service_instance
    
    if _ai_service_instance is None:
        try:
            _ai_service_instance = await initialize_ai_service()
            print("✅ Enhanced AI Service initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Enhanced AI Service: {e}")
            # Create a fallback service that can still handle basic operations
            _ai_service_instance = EnhancedAIService()
            print("⚠️  Using fallback AI service (limited functionality)")
    
    return _ai_service_instance

@router.post("/parse-syllabus", response_model=SyllabusParseResponse)
async def parse_syllabus(request: SyllabusParseRequest, db: Session = Depends(get_db)):
    """
    Parse a syllabus text using AI to extract classes and assignments.
    """
    try:
        ai_service = await get_ai_service()
        created_classes, created_pending_assignments = await ai_service.parse_syllabus(request.syllabus_text, db)
        
        # Convert database models to response models
        from ..schemas import ClassResponse, PendingAssignmentResponse
        class_responses = [ClassResponse.from_orm(cls) for cls in created_classes]
        assignment_responses = [PendingAssignmentResponse.from_orm(pa) for pa in created_pending_assignments]
        
        return SyllabusParseResponse(
            classes_created=class_responses,
            pending_assignments_created=assignment_responses,
            assignments_created=[],  # Keep for backward compatibility
            message=f"Successfully parsed syllabus: {len(created_classes)} classes and {len(created_pending_assignments)} pending assignments created"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing syllabus: {str(e)}")

@router.post("/generate-assignments", response_model=AIGenerateResponse)
async def generate_assignments(request: AIGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate assignments based on a natural language prompt.
    """
    try:
        ai_service = await get_ai_service()
        created_pending_assignments = await ai_service.generate_assignments(request.prompt, request.class_id, db)
        
        # Convert database models to response models
        from ..schemas import PendingAssignmentResponse
        assignment_responses = [PendingAssignmentResponse.from_orm(pa) for pa in created_pending_assignments]
        
        return AIGenerateResponse(
            pending_assignments_created=assignment_responses,
            assignments_created=[],  # Keep for backward compatibility
            message=f"Successfully generated {len(created_pending_assignments)} pending assignments"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating assignments: {str(e)}")

@router.get("/status")
async def ai_status():
    """
    Check the status of AI services and available models.
    """
    try:
        ai_service = await get_ai_service()
        status = ai_service.get_status()
        
        # Add some additional diagnostic info
        status["api_keys_configured"] = {}
        for model_key in AIConfig.MODELS.keys():
            config = AIConfig.MODELS[model_key]
            if config.api_key_env:
                api_key = os.getenv(config.api_key_env)
                status["api_keys_configured"][config.api_key_env] = bool(api_key and api_key.strip())
        
        return status
    except Exception as e:
        print(f"Error getting AI status: {e}")
        return {
            "error": str(e),
            "initialized": False,
            "current_model": None,
            "available_models": AIConfig.list_available_models(),
            "api_keys_configured": {}
        }

# Chat schemas
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    agent_used: str
    action_taken: bool
    data: dict = {}

# Model management schemas
class SwitchModelRequest(BaseModel):
    model_key: str

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatMessage, db: Session = Depends(get_db)):
    """
    Chat with AI assistant using enhanced multi-step agent system
    """
    try:
        print(f"\n=== ENHANCED CHAT ENDPOINT ===")
        print(f"Incoming Message: {request.message}")
        
        ai_service = await get_ai_service()
        response, agent_used, action_taken, data = await ai_service.chat(request.message, db)
        
        print(f"Final Response: {response}")
        print(f"Agent Used: {agent_used}")
        print(f"Action Taken: {action_taken}")
        print(f"Data: {data}")
        print(f"==============================\n")
        
        return ChatResponse(
            response=response,
            agent_used=agent_used,
            action_taken=action_taken,
            data=data
        )
    except Exception as e:
        print(f"ENHANCED CHAT ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@router.post("/switch-model")
async def switch_model(request: SwitchModelRequest):
    """
    Switch the AI service to use a different language model
    """
    try:
        ai_service = await get_ai_service()
        success = await ai_service.switch_model(request.model_key)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully switched to model: {request.model_key}",
                "current_model": request.model_key
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to switch to model: {request.model_key}")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error switching model: {str(e)}")

@router.get("/models")
async def list_models():
    """
    List all available AI models and their status
    """
    try:
        ai_service = await get_ai_service()
        return ai_service.get_status()
    except Exception as e:
        return {
            "error": str(e),
            "available_models": AIConfig.list_available_models()
        }


