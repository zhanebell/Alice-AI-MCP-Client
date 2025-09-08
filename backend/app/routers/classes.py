from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..models.database import get_db
from ..models.models import Class
from ..schemas import ClassCreate, ClassResponse, ClassUpdate

router = APIRouter()

@router.post("/", response_model=ClassResponse)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    """Create a new class."""
    db_class = Class(
        name=class_data.name,
        full_name=class_data.full_name,
        description=class_data.description,
        color=class_data.color
    )
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return db_class

@router.get("/", response_model=List[ClassResponse])
def get_classes(db: Session = Depends(get_db)):
    """Get all classes."""
    return db.query(Class).order_by(Class.name).all()

@router.get("/{class_id}", response_model=ClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    """Get a specific class by ID."""
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    return db_class

@router.put("/{class_id}", response_model=ClassResponse)
def update_class(class_id: int, class_data: ClassUpdate, db: Session = Depends(get_db)):
    """Update a class."""
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    for field, value in class_data.dict(exclude_unset=True).items():
        setattr(db_class, field, value)
    
    db_class.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_class)
    return db_class

@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    """Delete a class and all its assignments."""
    db_class = db.query(Class).filter(Class.id == class_id).first()
    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    db.delete(db_class)
    db.commit()
    return {"message": f"Class {class_id} deleted successfully"}
