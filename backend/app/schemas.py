from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from enum import Enum

class AssignmentStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class PendingAssignmentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

# Class schemas
class ClassBase(BaseModel):
    name: str = Field(..., description="Class code (e.g., 'ICS 211')")
    full_name: Optional[str] = Field(None, description="Full class name")
    description: Optional[str] = Field(None, description="Class description")
    color: str = Field("#3B82F6", description="Hex color code for UI")

class ClassCreate(ClassBase):
    pass

class ClassUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None

class ClassResponse(ClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Assignment schemas
class AssignmentBase(BaseModel):
    title: str = Field(..., description="Assignment title")
    description: Optional[str] = Field(None, description="Assignment description")
    due_date: datetime = Field(..., description="Due date and time")
    priority: int = Field(1, ge=1, le=3, description="Priority level (1=Low, 2=Medium, 3=High)")
    estimated_hours: Optional[int] = Field(None, ge=0, description="Estimated hours to complete")

class AssignmentCreate(AssignmentBase):
    class_id: int = Field(..., description="ID of the class this assignment belongs to")

class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[AssignmentStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    class_id: Optional[int] = None

class AssignmentResponse(AssignmentBase):
    id: int
    status: AssignmentStatus
    actual_hours: Optional[int]
    class_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # Related class info
    class_ref: Optional[ClassResponse] = None

    class Config:
        from_attributes = True

# Calendar view schema
class CalendarView(BaseModel):
    assignments_by_date: Dict[str, List[AssignmentResponse]]

# AI schemas
class SyllabusParseRequest(BaseModel):
    syllabus_text: str = Field(..., description="The syllabus or assignment text to parse")
    class_name: Optional[str] = Field(None, description="Existing class name or new class to create")
    default_class_id: Optional[int] = Field(None, description="Default class ID if no class specified")

class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., description="AI prompt for generating assignments")
    class_id: Optional[int] = Field(None, description="Class ID to associate with generated assignments")

# Pending Assignment schemas
class PendingAssignmentBase(BaseModel):
    title: str = Field(..., description="Assignment title")
    description: Optional[str] = Field(None, description="Assignment description")
    due_date: datetime = Field(..., description="Due date and time")
    priority: int = Field(1, ge=1, le=3, description="Priority level (1=Low, 2=Medium, 3=High)")
    estimated_hours: Optional[int] = Field(None, ge=0, description="Estimated hours to complete")

class PendingAssignmentCreate(PendingAssignmentBase):
    class_id: int = Field(..., description="ID of the class this assignment belongs to")

class PendingAssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    priority: Optional[int] = Field(None, ge=1, le=3)
    estimated_hours: Optional[int] = Field(None, ge=0)
    class_id: Optional[int] = None
    status: Optional[PendingAssignmentStatus] = None

class PendingAssignmentResponse(PendingAssignmentBase):
    id: int
    status: PendingAssignmentStatus
    class_id: int
    created_at: datetime
    updated_at: datetime
    
    # Related class info
    class_ref: Optional[ClassResponse] = None

    class Config:
        from_attributes = True

# Updated AI schemas to work with pending assignments
class SyllabusParseResponse(BaseModel):
    classes_created: List[ClassResponse]
    pending_assignments_created: List[PendingAssignmentResponse]
    assignments_created: List[AssignmentResponse]  # Keep for backward compatibility
    message: str

class AIGenerateResponse(BaseModel):
    pending_assignments_created: List[PendingAssignmentResponse]
    assignments_created: List[AssignmentResponse]  # Keep for backward compatibility
    message: str
