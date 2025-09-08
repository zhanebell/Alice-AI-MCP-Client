from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..models.database import get_db
from ..models.models import PendingAssignment, Assignment, Class, PendingAssignmentStatus
from ..schemas import (
    PendingAssignmentCreate, 
    PendingAssignmentResponse, 
    PendingAssignmentUpdate,
    AssignmentResponse
)

router = APIRouter()

@router.post("/", response_model=PendingAssignmentResponse)
def create_pending_assignment(assignment_data: PendingAssignmentCreate, db: Session = Depends(get_db)):
    """Create a new pending assignment."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == assignment_data.class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    db_pending_assignment = PendingAssignment(
        title=assignment_data.title,
        description=assignment_data.description,
        due_date=assignment_data.due_date,
        class_id=assignment_data.class_id,
        priority=assignment_data.priority,
        estimated_hours=assignment_data.estimated_hours
    )
    db.add(db_pending_assignment)
    db.commit()
    db.refresh(db_pending_assignment)
    return db_pending_assignment

@router.get("/", response_model=List[PendingAssignmentResponse])
def get_pending_assignments(
    status: Optional[PendingAssignmentStatus] = None,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get pending assignments with optional filtering."""
    query = db.query(PendingAssignment).join(Class)
    
    if status:
        query = query.filter(PendingAssignment.status == status)
    
    if class_id:
        query = query.filter(PendingAssignment.class_id == class_id)
    
    return query.order_by(PendingAssignment.due_date).all()

@router.get("/{pending_assignment_id}", response_model=PendingAssignmentResponse)
def get_pending_assignment(pending_assignment_id: int, db: Session = Depends(get_db)):
    """Get a specific pending assignment by ID."""
    pending_assignment = db.query(PendingAssignment).filter(PendingAssignment.id == pending_assignment_id).first()
    if not pending_assignment:
        raise HTTPException(status_code=404, detail="Pending assignment not found")
    return pending_assignment

@router.put("/{pending_assignment_id}", response_model=PendingAssignmentResponse)
def update_pending_assignment(
    pending_assignment_id: int, 
    assignment_data: PendingAssignmentUpdate, 
    db: Session = Depends(get_db)
):
    """Update a pending assignment."""
    db_pending_assignment = db.query(PendingAssignment).filter(PendingAssignment.id == pending_assignment_id).first()
    if not db_pending_assignment:
        raise HTTPException(status_code=404, detail="Pending assignment not found")
    
    for field, value in assignment_data.dict(exclude_unset=True).items():
        setattr(db_pending_assignment, field, value)
    
    db_pending_assignment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_pending_assignment)
    return db_pending_assignment

@router.post("/{pending_assignment_id}/approve", response_model=AssignmentResponse)
def approve_pending_assignment(pending_assignment_id: int, db: Session = Depends(get_db)):
    """Approve a pending assignment and convert it to a regular assignment."""
    db_pending = db.query(PendingAssignment).filter(PendingAssignment.id == pending_assignment_id).first()
    if not db_pending:
        raise HTTPException(status_code=404, detail="Pending assignment not found")
    
    if db_pending.status != PendingAssignmentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Assignment is not in pending status")
    
    # Create the actual assignment
    db_assignment = Assignment(
        title=db_pending.title,
        description=db_pending.description,
        due_date=db_pending.due_date,
        class_id=db_pending.class_id,
        priority=db_pending.priority,
        estimated_hours=db_pending.estimated_hours
    )
    db.add(db_assignment)
    
    # Update pending assignment status
    db_pending.status = PendingAssignmentStatus.APPROVED
    db_pending.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.post("/{pending_assignment_id}/reject")
def reject_pending_assignment(pending_assignment_id: int, db: Session = Depends(get_db)):
    """Reject a pending assignment."""
    db_pending = db.query(PendingAssignment).filter(PendingAssignment.id == pending_assignment_id).first()
    if not db_pending:
        raise HTTPException(status_code=404, detail="Pending assignment not found")
    
    if db_pending.status != PendingAssignmentStatus.PENDING:
        raise HTTPException(status_code=400, detail="Assignment is not in pending status")
    
    db_pending.status = PendingAssignmentStatus.REJECTED
    db_pending.updated_at = datetime.utcnow()
    
    db.commit()
    return {"message": f"Pending assignment {pending_assignment_id} rejected"}

@router.post("/approve-all", response_model=List[AssignmentResponse])
def approve_all_pending_assignments(class_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Approve all pending assignments, optionally filtered by class."""
    query = db.query(PendingAssignment).filter(PendingAssignment.status == PendingAssignmentStatus.PENDING)
    
    if class_id:
        query = query.filter(PendingAssignment.class_id == class_id)
    
    pending_assignments = query.all()
    
    if not pending_assignments:
        raise HTTPException(status_code=404, detail="No pending assignments found")
    
    approved_assignments = []
    
    for pending in pending_assignments:
        # Create the actual assignment
        db_assignment = Assignment(
            title=pending.title,
            description=pending.description,
            due_date=pending.due_date,
            class_id=pending.class_id,
            priority=pending.priority,
            estimated_hours=pending.estimated_hours
        )
        db.add(db_assignment)
        
        # Update pending assignment status
        pending.status = PendingAssignmentStatus.APPROVED
        pending.updated_at = datetime.utcnow()
        
        approved_assignments.append(db_assignment)
    
    db.commit()
    
    # Refresh all assignments
    for assignment in approved_assignments:
        db.refresh(assignment)
    
    return approved_assignments

@router.post("/reject-all")
def reject_all_pending_assignments(class_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Reject all pending assignments, optionally filtered by class."""
    query = db.query(PendingAssignment).filter(PendingAssignment.status == PendingAssignmentStatus.PENDING)
    
    if class_id:
        query = query.filter(PendingAssignment.class_id == class_id)
    
    pending_assignments = query.all()
    
    if not pending_assignments:
        raise HTTPException(status_code=404, detail="No pending assignments found")
    
    for pending in pending_assignments:
        pending.status = PendingAssignmentStatus.REJECTED
        pending.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Rejected {len(pending_assignments)} pending assignments"}

@router.delete("/{pending_assignment_id}")
def delete_pending_assignment(pending_assignment_id: int, db: Session = Depends(get_db)):
    """Delete a pending assignment."""
    db_pending = db.query(PendingAssignment).filter(PendingAssignment.id == pending_assignment_id).first()
    if not db_pending:
        raise HTTPException(status_code=404, detail="Pending assignment not found")
    
    db.delete(db_pending)
    db.commit()
    return {"message": f"Pending assignment {pending_assignment_id} deleted successfully"}
