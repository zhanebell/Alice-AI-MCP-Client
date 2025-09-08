import os
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import groq
from sqlalchemy.orm import Session

from ..models.models import Class, Assignment, AssignmentStatus, PendingAssignment

class AIService:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY", "dummy_key_for_now")
        
        if self.groq_api_key != "dummy_key_for_now":
            try:
                self.client = groq.Groq(api_key=self.groq_api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Groq client: {e}")
                self.client = None
        else:
            self.client = None

    def parse_syllabus(self, syllabus_text: str, db: Session) -> Tuple[List[Class], List[PendingAssignment]]:
        """
        Parse a syllabus text and extract classes and assignments using AI.
        Returns tuple of (created_classes, created_pending_assignments).
        """
        if not self.client:
            return self._mock_parse_syllabus(syllabus_text, db)

        try:
            prompt = self._build_syllabus_prompt(syllabus_text)
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are an expert at parsing academic syllabi and extracting structured assignment information."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            ai_response = response.choices[0].message.content
            return self._process_ai_response(ai_response, db)
            
        except Exception as e:
            print(f"AI parsing error: {e}")
            return self._mock_parse_syllabus(syllabus_text, db)

    def generate_assignments(self, prompt: str, class_id: Optional[int], db: Session) -> List[PendingAssignment]:
        """
        Generate assignments based on a natural language prompt.
        """
        if not self.client:
            return self._mock_generate_assignments(prompt, class_id, db)

        try:
            system_prompt = """You are an expert academic assistant that creates detailed assignment structures. 
            Generate realistic assignments based on the user's prompt. 
            
            IMPORTANT: Return ONLY a valid JSON array with no additional text, markdown, or explanation.
            
            Each assignment should have this exact structure:
            {
                "title": "Assignment title (keep it concise)",
                "description": "Detailed description of what the student needs to do",
                "due_date": "YYYY-MM-DD",
                "priority": 1-3 (1=low, 2=medium, 3=high),
                "estimated_hours": number
            }
            
            Make assignments realistic and appropriately spaced in time. Generate 2-4 assignments maximum."""
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate assignments for: {prompt}"}
                ],
                temperature=0.3,
                max_tokens=1024
            )
            
            ai_response = response.choices[0].message.content.strip()
            return self._process_assignment_generation(ai_response, class_id, db)
            
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._mock_generate_assignments(prompt, class_id, db)

    def _build_syllabus_prompt(self, syllabus_text: str) -> str:
        """Build the prompt for syllabus parsing."""
        return f"""
        Analyze this syllabus and extract structured information about the course and assignments.
        
        IMPORTANT: Return ONLY a valid JSON object with no additional text, markdown, or explanation.
        
        Use this exact structure:
        {{
            "class_info": {{
                "name": "Course code (e.g., 'SUST 115')",
                "full_name": "Full course name",
                "description": "Brief course description"
            }},
            "assignments": [
                {{
                    "title": "Assignment title (concise)",
                    "description": "What the student needs to do",
                    "due_date": "YYYY-MM-DD",
                    "priority": 2,
                    "estimated_hours": 3
                }}
            ]
        }}
        
        Guidelines:
        - Extract ALL assignments, projects, exams, and deliverables
        - Use dates from the syllabus; if not specified, estimate reasonable dates
        - Priority: 1=low, 2=medium, 3=high (exams are usually high priority)
        - Estimate realistic hours based on assignment complexity
        - Keep titles concise and descriptions clear
        
        Syllabus text:
        {syllabus_text}
        """

    def _process_ai_response(self, ai_response: str, db: Session) -> Tuple[List[Class], List[PendingAssignment]]:
        """Process the AI response and create database entries with robust validation."""
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Try to find JSON object in the response
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}')
            
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON object found in response")
            
            json_str = cleaned_response[json_start:json_end + 1]
            data = json.loads(json_str)
            
            created_classes = []
            created_assignments = []
            
            # Process class information
            class_id = None
            if "class_info" in data and isinstance(data["class_info"], dict):
                class_info = data["class_info"]
                class_name = class_info.get("name", "Imported Class")
                full_name = class_info.get("full_name", class_name)
                description = class_info.get("description", "Class imported from syllabus")
                
                # Check if class already exists
                existing_class = db.query(Class).filter(Class.name == class_name).first()
                if not existing_class:
                    new_class = Class(
                        name=class_name[:50],  # Limit length
                        full_name=full_name[:200],
                        description=description[:500]
                    )
                    db.add(new_class)
                    db.commit()
                    db.refresh(new_class)
                    created_classes.append(new_class)
                    class_id = new_class.id
                else:
                    class_id = existing_class.id
            
            # Process assignments
            if "assignments" in data and isinstance(data["assignments"], list):
                for i, assignment_data in enumerate(data["assignments"]):
                    if not isinstance(assignment_data, dict):
                        print(f"Skipping invalid assignment data at index {i}: not a dictionary")
                        continue
                    
                    # If we don't have a class, create a default one
                    if not class_id:
                        default_class = Class(name="Imported Assignments", description="Auto-created from syllabus")
                        db.add(default_class)
                        db.commit()
                        db.refresh(default_class)
                        created_classes.append(default_class)
                        class_id = default_class.id
                    
                    # Validate and extract assignment data
                    title = assignment_data.get("title", f"Assignment {i + 1}")
                    description = assignment_data.get("description", "Assignment from syllabus")
                    
                    # Parse due date
                    due_date_str = assignment_data.get("due_date", "")
                    try:
                        if due_date_str:
                            if "T" in due_date_str:
                                due_date = datetime.fromisoformat(due_date_str.replace("Z", ""))
                            else:
                                due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                        else:
                            # Default to spaced dates starting one week from now
                            due_date = datetime.now() + timedelta(days=7 + i * 7)
                    except Exception as date_error:
                        print(f"Error parsing date '{due_date_str}': {date_error}")
                        due_date = datetime.now() + timedelta(days=7 + i * 7)
                    
                    # Validate priority
                    priority = assignment_data.get("priority", 2)
                    if not isinstance(priority, int) or priority < 1 or priority > 3:
                        priority = 2
                    
                    # Validate estimated hours
                    estimated_hours = assignment_data.get("estimated_hours")
                    if estimated_hours is not None and not isinstance(estimated_hours, (int, float)):
                        estimated_hours = None
                    
                    assignment = PendingAssignment(
                        title=title[:200],  # Limit title length
                        description=description[:1000],  # Limit description length
                        due_date=due_date,
                        priority=priority,
                        estimated_hours=estimated_hours,
                        class_id=class_id
                    )
                    db.add(assignment)
                    created_assignments.append(assignment)
                
                if created_assignments:
                    db.commit()
                    for assignment in created_assignments:
                        db.refresh(assignment)
            
            return created_classes, created_assignments
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error in syllabus response: {e}")
            print(f"Response was: {ai_response[:500]}...")
            return self._mock_parse_syllabus(ai_response, db)
        except Exception as e:
            print(f"Error processing AI response: {e}")
            return self._mock_parse_syllabus(ai_response, db)

    def _process_assignment_generation(self, ai_response: str, class_id: Optional[int], db: Session) -> List[PendingAssignment]:
        """Process AI-generated assignments with robust JSON parsing."""
        try:
            # Handle case where no class_id is provided - create a default class
            if not class_id:
                from ..models.models import Class
                default_class = Class(
                    name="AI Generated", 
                    full_name="AI Generated Class",
                    description="Auto-created for AI-generated assignments"
                )
                db.add(default_class)
                db.commit()
                db.refresh(default_class)
                class_id = default_class.id
                print(f"Created default class with ID: {class_id}")
            
            # Clean the response - remove markdown code blocks if present
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Try to find JSON array in the response
            json_start = cleaned_response.find('[')
            json_end = cleaned_response.rfind(']')
            
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON array found in response")
            
            json_str = cleaned_response[json_start:json_end + 1]
            assignments_data = json.loads(json_str)
            
            if not isinstance(assignments_data, list):
                raise ValueError("Response is not a JSON array")
            
            created_assignments = []
            
            for i, assignment_data in enumerate(assignments_data):
                if not isinstance(assignment_data, dict):
                    print(f"Skipping invalid assignment data at index {i}: not a dictionary")
                    continue
                
                # Validate required fields
                title = assignment_data.get("title", f"Generated Assignment {i + 1}")
                description = assignment_data.get("description", "AI-generated assignment")
                
                # Parse due date with better error handling
                due_date_str = assignment_data.get("due_date", "")
                try:
                    if due_date_str:
                        if "T" in due_date_str:
                            due_date = datetime.fromisoformat(due_date_str.replace("Z", ""))
                        else:
                            due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                    else:
                        # Default to one week from now
                        due_date = datetime.now() + timedelta(days=7 + i * 7)  # Space assignments a week apart
                except Exception as date_error:
                    print(f"Error parsing date '{due_date_str}': {date_error}")
                    due_date = datetime.now() + timedelta(days=7 + i * 7)
                
                # Validate priority
                priority = assignment_data.get("priority", 2)
                if not isinstance(priority, int) or priority < 1 or priority > 3:
                    priority = 2
                
                # Validate estimated hours
                estimated_hours = assignment_data.get("estimated_hours")
                if estimated_hours is not None and not isinstance(estimated_hours, (int, float)):
                    estimated_hours = None
                
                assignment = PendingAssignment(
                    title=title[:200],  # Limit title length
                    description=description[:1000],  # Limit description length
                    due_date=due_date,
                    priority=priority,
                    estimated_hours=estimated_hours,
                    class_id=class_id
                )
                db.add(assignment)
                created_assignments.append(assignment)
            
            if created_assignments:
                db.commit()
                for assignment in created_assignments:
                    db.refresh(assignment)
            else:
                print("No valid assignments found in AI response")
                return self._create_fallback_assignments(class_id, db)
            
            return created_assignments
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {ai_response[:500]}...")
            return self._create_fallback_assignments(class_id, db)
        except Exception as e:
            print(f"Error processing assignment generation: {e}")
            return self._create_fallback_assignments(class_id, db)

    def _create_fallback_assignments(self, class_id: Optional[int], db: Session) -> List[PendingAssignment]:
        """Create fallback assignments when AI parsing fails."""
        # Handle case where no class_id is provided - create a default class
        if not class_id:
            from ..models.models import Class
            default_class = Class(
                name="AI Generated", 
                full_name="AI Generated Class",
                description="Auto-created for AI-generated assignments"
            )
            db.add(default_class)
            db.commit()
            db.refresh(default_class)
            class_id = default_class.id
            print(f"Created default class for fallback assignments with ID: {class_id}")
        
        fallback_assignments = [
            PendingAssignment(
                title="Assignment 1",
                description="Complete the first assignment as outlined in the course materials.",
                due_date=datetime.now() + timedelta(days=7),
                priority=2,
                estimated_hours=3,
                class_id=class_id
            ),
            PendingAssignment(
                title="Assignment 2", 
                description="Complete the second assignment as outlined in the course materials.",
                due_date=datetime.now() + timedelta(days=14),
                priority=2,
                estimated_hours=4,
                class_id=class_id
            )
        ]
        
        for assignment in fallback_assignments:
            db.add(assignment)
        
        db.commit()
        for assignment in fallback_assignments:
            db.refresh(assignment)
            
        return fallback_assignments

    def _mock_parse_syllabus(self, syllabus_text: str, db: Session) -> Tuple[List[Class], List[PendingAssignment]]:
        """Mock implementation for when AI is not available."""
        # Create a sample class
        mock_class = Class(
            name="DEMO 101",
            full_name="Demo Course",
            description="Auto-created demo class from syllabus parsing"
        )
        db.add(mock_class)
        db.commit()
        db.refresh(mock_class)
        
        # Create sample assignments
        sample_assignments = [
            {
                "title": "Assignment 1: Introduction",
                "description": "Introductory assignment extracted from syllabus",
                "days_offset": 7,
                "priority": 2,
                "estimated_hours": 3
            },
            {
                "title": "Midterm Project",
                "description": "Major project identified in syllabus",
                "days_offset": 30,
                "priority": 3,
                "estimated_hours": 15
            },
            {
                "title": "Final Assignment",
                "description": "Final deliverable from syllabus",
                "days_offset": 60,
                "priority": 3,
                "estimated_hours": 20
            }
        ]
        
        created_assignments = []
        for assignment_data in sample_assignments:
            assignment = PendingAssignment(
                title=assignment_data["title"],
                description=assignment_data["description"],
                due_date=datetime.now() + timedelta(days=assignment_data["days_offset"]),
                priority=assignment_data["priority"],
                estimated_hours=assignment_data["estimated_hours"],
                class_id=mock_class.id
            )
            db.add(assignment)
            created_assignments.append(assignment)
        
        db.commit()
        for assignment in created_assignments:
            db.refresh(assignment)
        
        return [mock_class], created_assignments

    def _mock_generate_assignments(self, prompt: str, class_id: Optional[int], db: Session) -> List[PendingAssignment]:
        """Mock implementation for assignment generation."""
        if not class_id:
            # Create a default class
            default_class = Class(name="AI Generated", description="Auto-created for AI assignments")
            db.add(default_class)
            db.commit()
            db.refresh(default_class)
            class_id = default_class.id
        
        # Create sample assignments based on prompt keywords
        assignments = []
        if "project" in prompt.lower():
            assignments.append(PendingAssignment(
                title="Generated Project",
                description=f"AI-generated project based on: {prompt}",
                due_date=datetime.now() + timedelta(days=14),
                priority=3,
                estimated_hours=10,
                class_id=class_id
            ))
        
        if "assignment" in prompt.lower() or "homework" in prompt.lower():
            assignments.append(PendingAssignment(
                title="Generated Assignment",
                description=f"AI-generated assignment based on: {prompt}",
                due_date=datetime.now() + timedelta(days=7),
                priority=2,
                estimated_hours=5,
                class_id=class_id
            ))
        
        if "exam" in prompt.lower() or "test" in prompt.lower():
            assignments.append(PendingAssignment(
                title="Generated Exam",
                description=f"AI-generated exam based on: {prompt}",
                due_date=datetime.now() + timedelta(days=21),
                priority=3,
                estimated_hours=3,
                class_id=class_id
            ))
        
        # Default assignment if no keywords match
        if not assignments:
            assignments.append(PendingAssignment(
                title="AI Generated Task",
                description=f"Generated from prompt: {prompt}",
                due_date=datetime.now() + timedelta(days=7),
                priority=2,
                estimated_hours=4,
                class_id=class_id
            ))
        
        for assignment in assignments:
            db.add(assignment)
        
        db.commit()
        for assignment in assignments:
            db.refresh(assignment)
        
        return assignments
