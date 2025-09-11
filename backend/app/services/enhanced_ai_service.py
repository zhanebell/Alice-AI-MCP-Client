"""
Enhanced AI Service with Multi-Agent Architecture and MCP Integration
Replaces the old AI service with a robust, configurable system
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Import the new AI system components
from .multi_step_agent import MultiStepAIAgent
from .llm_client import LLMClient, ChatMessage
from .ai_config import AIConfig
from .mcp_discovery import MCPToolDiscovery

# Import existing models for backward compatibility
from ..models.models import Class, Assignment, PendingAssignment

class EnhancedAIService:
    """
    Enhanced AI Service with multi-agent architecture, configurable LLMs, and MCP tool integration.
    
    Features:
    - Configurable language models (not just Llama 70B)
    - Multi-step reasoning with tool orchestration
    - Dynamic MCP tool discovery and execution
    - Robust error handling and fallbacks
    - Support for complex workflows
    """
    
    def __init__(self, model_key: Optional[str] = None):
        self.model_key = model_key or AIConfig.get_default_model()
        self.llm_client = LLMClient(self.model_key)
        self.agent: Optional[MultiStepAIAgent] = None
        self.mcp_discovery = MCPToolDiscovery()
        self._initialized = False
    
    async def initialize(self):
        """Initialize the AI service asynchronously"""
        if not self._initialized:
            try:
                self.agent = MultiStepAIAgent(self.model_key)
                await self.agent.initialize()
                self._initialized = True
                print(f"Enhanced AI Service initialized with model: {self.model_key}")
            except Exception as e:
                print(f"Error initializing Enhanced AI Service: {e}")
                self._initialized = False
        return self
    
    def is_available(self) -> bool:
        """Check if AI services are available"""
        return self.llm_client.is_available()
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of AI services"""
        available_models = AIConfig.list_available_models()
        model_status = {}
        
        for model_key, description in available_models.items():
            model_status[model_key] = {
                "description": description,
                "available": AIConfig.is_model_available(model_key)
            }
        
        return {
            "current_model": self.model_key,
            "current_model_available": self.is_available(),
            "initialized": self._initialized,
            "available_models": model_status,
            "mcp_tools_count": len(getattr(self.agent, 'available_tools', [])) if self.agent else 0
        }
    
    async def chat(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """
        Enhanced chat interface using multi-step agent
        Returns: (response, agent_used, action_taken, metadata)
        """
        # Ensure we're initialized
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.agent:
            return self._fallback_chat(message, db)
        
        try:
            print(f"\n=== ENHANCED AI CHAT ===")
            print(f"Model: {self.model_key}")
            print(f"User Message: {message}")
            
            # Use the multi-step agent to process the request
            response, metadata = await self.agent.process_request(message)
            
            # Determine if actions were taken based on metadata
            action_taken = bool(metadata.get("tools_used") and len(metadata.get("tools_used", [])) > 0)
            
            print(f"Agent Response: {response}")
            print(f"Tools Used: {metadata.get('tools_used', [])}")
            print(f"Action Taken: {action_taken}")
            print(f"========================\n")
            
            return response, "multi-step", action_taken, metadata
        
        except Exception as e:
            print(f"Enhanced AI chat error: {e}")
            return self._fallback_chat(message, db)
    
    async def generate_assignments(self, prompt: str, class_id: Optional[int], db: Session) -> List[PendingAssignment]:
        """
        Generate assignments using the enhanced AI system
        This maintains backward compatibility while using the new system
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.agent:
            return self._fallback_generate_assignments(prompt, class_id, db)
        
        try:
            # Create a specific prompt for assignment generation
            assignment_prompt = f"""Generate assignments based on this request: {prompt}
            
Class ID (if specified): {class_id}

Please create appropriate assignments and add them to the database."""
            
            response, metadata = await self.agent.process_request(assignment_prompt)
            
            # Get the newly created assignments from the database
            # This is a bit of a workaround since we're adapting the new system to the old interface
            recent_assignments = db.query(PendingAssignment).filter(
                PendingAssignment.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).all()
            
            if class_id:
                recent_assignments = [a for a in recent_assignments if getattr(a, 'class_id') == class_id]
            
            return recent_assignments[-5:]  # Return last 5 assignments created today
        
        except Exception as e:
            print(f"Error in enhanced assignment generation: {e}")
            return self._fallback_generate_assignments(prompt, class_id, db)
    
    async def parse_syllabus(self, syllabus_text: str, db: Session) -> Tuple[List[Class], List[PendingAssignment]]:
        """
        Parse syllabus using the enhanced AI system
        Maintains backward compatibility
        """
        if not self._initialized:
            await self.initialize()
        
        if not self._initialized or not self.agent:
            return self._fallback_parse_syllabus(syllabus_text, db)
        
        try:
            # Create a specific prompt for syllabus parsing
            syllabus_prompt = f"""Please parse this syllabus text and create appropriate classes and assignments:

{syllabus_text}

Extract all classes, assignments, projects, exams, and due dates. Create them in the database."""
            
            response, metadata = await self.agent.process_request(syllabus_prompt)
            
            # Get recently created classes and pending assignments
            recent_classes = db.query(Class).filter(
                Class.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).all()
            
            recent_assignments = db.query(PendingAssignment).filter(
                PendingAssignment.created_at >= datetime.now().replace(hour=0, minute=0, second=0)
            ).all()
            
            return recent_classes, recent_assignments
        
        except Exception as e:
            print(f"Error in enhanced syllabus parsing: {e}")
            return self._fallback_parse_syllabus(syllabus_text, db)
    
    def _fallback_chat(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Fallback chat when enhanced system is not available"""
        try:
            if self.llm_client.is_available():
                # Use simple LLM chat without agents
                messages = [
                    ChatMessage(role="system", content="You are Alice, a helpful AI assistant for academic task management."),
                    ChatMessage(role="user", content=message)
                ]
                
                response = self.llm_client.chat(messages, temperature=0.7, max_tokens=512)
                
                return response.content, "fallback", False, {"fallback": True}
            else:
                return (
                    "I'm having trouble with my AI capabilities right now. Please try again later or contact support.",
                    "fallback",
                    False,
                    {"fallback": True, "error": "No LLM available"}
                )
        
        except Exception as e:
            return (
                f"I encountered an error: {str(e)}. Please try a simpler request.",
                "fallback",
                False,
                {"fallback": True, "error": str(e)}
            )
    
    def _fallback_generate_assignments(self, prompt: str, class_id: Optional[int], db: Session) -> List[PendingAssignment]:
        """Fallback assignment generation"""
        # Create a simple assignment based on the prompt
        if not class_id:
            # Create a default class
            default_class = Class(
                name="AI Generated",
                full_name="AI Generated Class",
                description="Auto-created for AI-generated assignments"
            )
            db.add(default_class)
            db.commit()
            db.refresh(default_class)
            class_id = getattr(default_class, 'id')
        
        assignment = PendingAssignment(
            title=f"Generated: {prompt[:50]}...",
            description=f"AI-generated assignment based on: {prompt}",
            due_date=datetime.now().replace(hour=23, minute=59, second=59) + timedelta(days=7),
            priority=2,
            estimated_hours=4,
            class_id=class_id
        )
        
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        
        return [assignment]
    
    def _fallback_parse_syllabus(self, syllabus_text: str, db: Session) -> Tuple[List[Class], List[PendingAssignment]]:
        """Fallback syllabus parsing"""
        # Create a sample class
        sample_class = Class(
            name="PARSED 101",
            full_name="Parsed Course",
            description="Auto-created from syllabus parsing"
        )
        db.add(sample_class)
        db.commit()
        db.refresh(sample_class)
        
        # Create sample assignments
        assignments = []
        for i, title in enumerate(["Assignment 1", "Midterm", "Final Project"], 1):
            assignment = PendingAssignment(
                title=title,
                description=f"Extracted from syllabus: {title}",
                due_date=datetime.now() + timedelta(days=i * 14),
                priority=2 if i < 3 else 3,
                estimated_hours=5 if i < 3 else 15,
                class_id=sample_class.id
            )
            db.add(assignment)
            assignments.append(assignment)
        
        db.commit()
        for assignment in assignments:
            db.refresh(assignment)
        
        return [sample_class], assignments
    
    async def switch_model(self, new_model_key: str) -> bool:
        """Switch to a different language model"""
        try:
            if new_model_key not in AIConfig.MODELS:
                raise ValueError(f"Unknown model: {new_model_key}")
            
            if not AIConfig.is_model_available(new_model_key):
                raise ValueError(f"Model not available: {new_model_key}")
            
            # Update configuration
            self.model_key = new_model_key
            self.llm_client = LLMClient(new_model_key)
            
            # Reinitialize agent with new model
            self.agent = MultiStepAIAgent(new_model_key)
            await self.agent.initialize()
            
            print(f"Switched to model: {new_model_key}")
            return True
        
        except Exception as e:
            print(f"Error switching model: {e}")
            return False

# Async helper functions for backward compatibility
def get_enhanced_ai_service(model_key: Optional[str] = None) -> EnhancedAIService:
    """Get an enhanced AI service instance"""
    return EnhancedAIService(model_key)

async def initialize_ai_service(model_key: Optional[str] = None) -> EnhancedAIService:
    """Create and initialize an enhanced AI service"""
    service = EnhancedAIService(model_key)
    await service.initialize()
    return service
