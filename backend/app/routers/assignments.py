from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, date

from ..models.database import get_db
from ..models.models import Assignment, Class, AssignmentStatus
from ..schemas import AssignmentCreate, AssignmentResponse, AssignmentUpdate, CalendarView

router = APIRouter()

@router.post("/", response_model=AssignmentResponse)
def create_assignment(assignment_data: AssignmentCreate, db: Session = Depends(get_db)):
    """Create a new assignment."""
    # Verify class exists
    db_class = db.query(Class).filter(Class.id == assignment_data.class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    db_assignment = Assignment(
        title=assignment_data.title,
        description=assignment_data.description,
        due_date=assignment_data.due_date,
        class_id=assignment_data.class_id,
        priority=assignment_data.priority,
        estimated_hours=assignment_data.estimated_hours
    )
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.get("/", response_model=List[AssignmentResponse])
def get_assignments(
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    status: Optional[AssignmentStatus] = Query(None, description="Filter by status"),
    include_completed: bool = Query(False, description="Include completed assignments"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """Get assignments with optional filtering."""
    query = db.query(Assignment).join(Class)
    
    if class_id:
        query = query.filter(Assignment.class_id == class_id)
    
    if status:
        query = query.filter(Assignment.status == status)
    
    if not include_completed:
        query = query.filter(Assignment.status != AssignmentStatus.COMPLETED)
    
    if start_date:
        query = query.filter(Assignment.due_date >= start_date)
    
    if end_date:
        query = query.filter(Assignment.due_date <= end_date)
    
    return query.order_by(Assignment.due_date).all()

@router.get("/calendar", response_model=CalendarView)
def get_calendar_view(
    start_date: Optional[date] = Query(None, description="Start date (defaults to today)"),
    end_date: Optional[date] = Query(None, description="End date (defaults to 30 days from start)"),
    include_completed: bool = Query(False, description="Include completed assignments"),
    db: Session = Depends(get_db)
):
    """Get assignments organized by date for calendar view."""
    if not start_date:
        start_date = date.today()
    if not end_date:
        from datetime import timedelta
        end_date = start_date + timedelta(days=30)
    
    query = db.query(Assignment).join(Class).filter(
        and_(
            Assignment.due_date >= start_date,
            Assignment.due_date <= end_date
        )
    )
    
    if not include_completed:
        query = query.filter(Assignment.status != AssignmentStatus.COMPLETED)
    
    assignments = query.order_by(Assignment.due_date).all()
    
    # Group by date
    calendar_data = {}
    for assignment in assignments:
        date_key = assignment.due_date.date().isoformat()
        if date_key not in calendar_data:
            calendar_data[date_key] = []
        calendar_data[date_key].append(assignment)
    
    return {"assignments_by_date": calendar_data}

@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Get a specific assignment by ID."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(assignment_id: int, assignment_data: AssignmentUpdate, db: Session = Depends(get_db)):
    """Update an assignment."""
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    for field, value in assignment_data.dict(exclude_unset=True).items():
        setattr(db_assignment, field, value)
    
    db_assignment.updated_at = datetime.utcnow()
    
    # Set completed_at if status is completed
    if assignment_data.status == AssignmentStatus.COMPLETED:
        db_assignment.completed_at = datetime.utcnow()
    elif hasattr(assignment_data, 'status') and assignment_data.status != AssignmentStatus.COMPLETED:
        db_assignment.completed_at = None
    
    db.commit()
    db.refresh(db_assignment)
    return db_assignment

@router.patch("/{assignment_id}/status")
def update_assignment_status(
    assignment_id: int, 
    status: AssignmentStatus,
    actual_hours: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Update assignment status specifically."""
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db_assignment.status = status
    db_assignment.updated_at = datetime.utcnow()
    
    if status == AssignmentStatus.COMPLETED:
        db_assignment.completed_at = datetime.utcnow()
        if actual_hours:
            db_assignment.actual_hours = actual_hours
    else:
        db_assignment.completed_at = None
    
    db.commit()
    db.refresh(db_assignment)
    return {"message": f"Assignment status updated to {status.value}", "assignment": db_assignment}

@router.delete("/{assignment_id}")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Delete an assignment."""
    db_assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not db_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(db_assignment)
    db.commit()
    return {"message": f"Assignment {assignment_id} deleted successfully"}
