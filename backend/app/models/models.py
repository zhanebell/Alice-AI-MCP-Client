from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum

class AssignmentStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class PendingAssignmentStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class Class(Base):
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)  # e.g., "ICS 211"
    full_name = Column(String, nullable=True)  # e.g., "Introduction to Computer Science II"
    description = Column(Text, nullable=True)
    color = Column(String, default="#3B82F6")  # Hex color for UI
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to assignments
    assignments = relationship("Assignment", back_populates="class_ref", cascade="all, delete-orphan")
    pending_assignments = relationship("PendingAssignment", back_populates="class_ref", cascade="all, delete-orphan")

class Assignment(Base):
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.NOT_STARTED)
    priority = Column(Integer, default=1)  # 1=Low, 2=Medium, 3=High
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationship to class
    class_ref = relationship("Class", back_populates="assignments")

class PendingAssignment(Base):
    __tablename__ = "pending_assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    priority = Column(Integer, default=1)  # 1=Low, 2=Medium, 3=High
    estimated_hours = Column(Integer, nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    status = Column(Enum(PendingAssignmentStatus), default=PendingAssignmentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to class
    class_ref = relationship("Class", back_populates="pending_assignments")
