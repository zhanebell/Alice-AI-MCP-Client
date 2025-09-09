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
            
            ai_response = response.choices[0].message.content or ""
            print(f"\n=== SYLLABUS PARSING AI RESPONSE ===")
            print(f"Model Response: {ai_response}")
            print(f"======================================\n")
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
            
            ai_response = (response.choices[0].message.content or "").strip()
            print(f"\n=== ASSIGNMENT GENERATION AI RESPONSE ===")
            print(f"User Prompt: {prompt}")
            print(f"Model Response: {ai_response}")
            print(f"==========================================\n")
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
                    if class_id is None:
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

    def chat(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """
        Chat with AI using agentic system.
        Returns tuple of (response, agent_used, action_taken, data).
        """
        try:
            # Determine which agent to use - do this even without AI client for better routing
            if self.client:
                # Use AI for routing
                agent_prompt = self._build_agent_routing_prompt(message)
                
                routing_response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an intelligent routing agent that determines which specialized agent should handle a user's request."},
                        {"role": "user", "content": agent_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=256
                )
                
                routing_result = routing_response.choices[0].message.content or ""
                agent_choice = self._parse_agent_choice(routing_result)
                
                print(f"\n=== AGENT ROUTING (AI) ===")
                print(f"User Message: {message}")
                print(f"Routing Response: {routing_result}")
                print(f"Selected Agent: {agent_choice}")
                print(f"==========================\n")
            else:
                # Use simple keyword-based routing when no AI client
                agent_choice = self._simple_agent_routing(message)
                print(f"\n=== AGENT ROUTING (Simple) ===")
                print(f"User Message: {message}")
                print(f"Selected Agent: {agent_choice}")
                print(f"==============================\n")
            
            # Route to appropriate agent
            if agent_choice == "general":
                return self._handle_general_chat(message, db)
            elif agent_choice == "query":
                return self._handle_query_agent(message, db)
            elif agent_choice == "create":
                return self._handle_create_agent(message, db)
            else:
                return self._handle_general_chat(message, db)
                
        except Exception as e:
            print(f"Chat error: {e}")
            return self._mock_chat(message, db)

    def _build_agent_routing_prompt(self, message: str) -> str:
        """Build prompt for agent routing."""
        return f"""
Analyze this user message and determine which agent should handle it:

Message: "{message}"

Available agents:
1. "general" - For casual conversation, greetings, general questions that don't require database actions
2. "query" - For retrieving information about existing assignments, classes, or data analysis
3. "create" - For creating new assignments, classes, or parsing syllabi

Respond with ONLY one word: "general", "query", or "create"

Examples:
- "Hello, how are you?" -> general
- "What assignments do I have due this week?" -> query  
- "Show me all my computer science classes" -> query
- "Create a new assignment for my math class" -> create
- "Parse this syllabus text..." -> create
- "Generate 5 programming assignments" -> create
"""

    def _parse_agent_choice(self, response: str) -> str:
        """Parse the agent choice from AI response."""
        response = response.strip().lower()
        if "general" in response:
            return "general"
        elif "query" in response:
            return "query"
        elif "create" in response:
            return "create"
        else:
            return "general"

    def _simple_agent_routing(self, message: str) -> str:
        """Simple keyword-based agent routing when AI is not available."""
        message_lower = message.lower()
        
        # Keywords that indicate query requests
        query_keywords = [
            "what", "show", "list", "tell me", "how many", "which", "due", "overdue", 
            "today", "tomorrow", "this week", "next week", "upcoming", "assignment", 
            "class", "progress", "complete", "statistics", "stats"
        ]
        
        # Keywords that indicate creation requests
        create_keywords = [
            "create", "generate", "make", "add", "new", "syllabus", "parse", "extract"
        ]
        
        # Keywords that indicate general conversation
        general_keywords = [
            "hello", "hi", "hey", "how are you", "thanks", "thank you", "help"
        ]
        
        # Check for creation keywords first (more specific)
        for keyword in create_keywords:
            if keyword in message_lower:
                return "create"
        
        # Check for query keywords
        for keyword in query_keywords:
            if keyword in message_lower:
                return "query"
        
        # Check for general keywords
        for keyword in general_keywords:
            if keyword in message_lower:
                return "general"
        
        # Default to query for question-like messages
        if "?" in message or message_lower.startswith(("what", "how", "when", "where", "why", "which", "show", "tell")):
            return "query"
        
        # Default to general
        return "general"

    def _handle_general_chat(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Handle general conversation."""
        try:
            if not self.client:
                return "I'm having trouble processing that right now. How can I help you with your assignments?", "general", False, {}
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Alice, a friendly and helpful AI assistant for managing academic assignments. Be conversational, warm, and helpful. Keep responses concise but personable."},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=512
            )
            
            ai_response = response.choices[0].message.content or "I'm here to help!"
            print(f"\n=== GENERAL CHAT AGENT ===")
            print(f"User Message: {message}")
            print(f"AI Response: {ai_response}")
            print(f"===========================\n")
            return ai_response, "general", False, {}
            
        except Exception as e:
            return "I'm having trouble processing that right now. How can I help you with your assignments?", "general", False, {}

    def _handle_query_agent(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Handle queries about existing data with dynamic database querying."""
        
        # Get raw database data for AI to work with
        database_context = self._get_dynamic_database_context(db, message)
        
        query_prompt = f"""
You are Alice, a highly intelligent AI assistant specializing in academic assignment management and data analysis.

The user has asked: "{message}"

Here is the current database information:
{database_context}

Your task:
1. Analyze the user's question carefully
2. Use the provided database information to answer their question accurately
3. Provide specific details including names, dates, counts, status, priorities, etc.
4. If the question involves time-based queries (today, this week, overdue), calculate and present the relevant information
5. Be conversational, helpful, and detailed in your response
6. If no relevant data exists for their question, explain what you found instead and suggest how they could add the missing data

Important: Base your response ONLY on the actual database data provided. Be accurate and specific.
"""

        try:
            if not self.client:
                # Use enhanced mock response that can handle any query
                return self._enhanced_query_response(message, db, database_context)
            
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are Alice, a knowledgeable AI assistant who analyzes academic assignment data. Always provide accurate, detailed responses based on the provided database information."},
                    {"role": "user", "content": query_prompt}
                ],
                temperature=0.2,
                max_tokens=1200
            )
            
            ai_response = response.choices[0].message.content or "I couldn't analyze that data."
            
            # Get comprehensive statistics
            stats = self._calculate_comprehensive_stats(db)
            
            data = {
                **stats,
                "query_type": self._classify_query_type(message),
                "database_context_length": len(database_context)
            }
            
            print(f"\n=== DYNAMIC QUERY AGENT ===")
            print(f"User Message: {message}")
            print(f"Query Type: {data['query_type']}")
            print(f"Context Length: {data['database_context_length']} chars")
            print(f"AI Response Length: {len(ai_response)} chars")
            print(f"===============================\n")
            
            return ai_response, "query", False, data
            
        except Exception as e:
            print(f"Query agent error: {e}")
            return self._enhanced_query_response(message, db, database_context)

    def _handle_create_agent(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Handle creation of new assignments or classes."""
        # Determine if this is syllabus parsing or assignment generation
        is_syllabus = any(keyword in message.lower() for keyword in ["syllabus", "parse", "extract"])
        print(f"\n=== CREATE AGENT ===")
        print(f"User Message: {message}")
        print(f"Detected Type: {'Syllabus Parsing' if is_syllabus else 'Assignment Generation'}")
        print(f"====================\n")
        
        if is_syllabus:
            return self._handle_syllabus_parsing(message, db)
        else:
            return self._handle_assignment_generation(message, db)

    def _handle_syllabus_parsing(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Handle syllabus parsing requests."""
        # Extract syllabus text from message
        # This is a simplified approach - in practice, you might want more sophisticated extraction
        try:
            created_classes, created_pending_assignments = self.parse_syllabus(message, db)
            
            response = f"Great! I've analyzed your syllabus and created:\n"
            response += f"• {len(created_classes)} new classes\n"
            response += f"• {len(created_pending_assignments)} pending assignments\n\n"
            response += "Please review the pending assignments and approve the ones you'd like to add to your schedule!"
            
            data = {
                "classes_created": len(created_classes),
                "pending_assignments_created": len(created_pending_assignments),
                "classes": [{"id": c.id, "name": c.name, "full_name": c.full_name} for c in created_classes],
                "pending_assignments": [{"id": p.id, "title": p.title, "due_date": p.due_date.isoformat()} for p in created_pending_assignments]
            }
            
            print(f"\n=== SYLLABUS PARSING HANDLER ===")
            print(f"Created {len(created_classes)} classes, {len(created_pending_assignments)} pending assignments")
            print(f"Response: {response}")
            print(f"================================\n")
            
            return response, "create", True, data
            
        except Exception as e:
            return "I had trouble parsing that syllabus. Could you make sure it includes assignment names and dates?", "create", False, {}

    def _handle_assignment_generation(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Handle assignment generation requests."""
        try:
            created_pending_assignments = self.generate_assignments(message, None, db)
            
            response = f"Perfect! I've generated {len(created_pending_assignments)} new assignments based on your request.\n\n"
            response += "These are now in your pending assignments for review. You can approve, edit, or reject them as needed!"
            
            data = {
                "pending_assignments_created": len(created_pending_assignments),
                "pending_assignments": [{"id": p.id, "title": p.title, "due_date": p.due_date.isoformat()} for p in created_pending_assignments]
            }
            
            print(f"\n=== ASSIGNMENT GENERATION HANDLER ===")
            print(f"Generated {len(created_pending_assignments)} pending assignments")
            print(f"Response: {response}")
            print(f"=====================================\n")
            
            return response, "create", True, data
            
        except Exception as e:
            return "I had trouble generating those assignments. Could you provide more specific details about what you need?", "create", False, {}

    def _get_dynamic_database_context(self, db: Session, message: str) -> str:
        """Get dynamic database context based on the user's question."""
        context = ""
        now = datetime.now()
        
        try:
            # Always include basic counts
            classes_count = db.query(Class).count()
            assignments_count = db.query(Assignment).count() 
            pending_count = db.query(PendingAssignment).count()
            
            context += f"=== DATABASE OVERVIEW ===\n"
            context += f"Total classes: {classes_count}\n"
            context += f"Total assignments: {assignments_count}\n"
            context += f"Total pending assignments: {pending_count}\n"
            context += f"Current date/time: {now.strftime('%Y-%m-%d %H:%M')}\n\n"
            
            # Analyze the message to determine what data to include
            message_lower = message.lower()
            
            # Always include class information (it's lightweight)
            if classes_count > 0:
                context += "=== ALL CLASSES ===\n"
                classes = db.query(Class).all()
                for cls in classes:
                    try:
                        class_assignments = db.query(Assignment).filter(Assignment.class_id == cls.id).count()
                        class_pending = db.query(PendingAssignment).filter(PendingAssignment.class_id == cls.id).count()
                        completed_in_class = db.query(Assignment).filter(
                            Assignment.class_id == cls.id,
                            Assignment.status == AssignmentStatus.COMPLETED
                        ).count()
                        
                        context += f"• Class: {cls.name} - {cls.full_name or 'No description'}\n"
                        context += f"  Total assignments: {class_assignments} (completed: {completed_in_class})\n"
                        context += f"  Pending assignments: {class_pending}\n"
                        context += f"  Description: {cls.description or 'None'}\n\n"
                    except Exception as e:
                        context += f"• Class: {cls.name} - Error loading details\n\n"
            
            # Include assignment details based on the query
            if assignments_count > 0:
                # Determine what assignments to show based on the query
                if any(word in message_lower for word in ["today", "due today"]):
                    context += self._get_today_assignments_context(db, now)
                elif any(word in message_lower for word in ["week", "this week", "next week"]):
                    context += self._get_week_assignments_context(db, now)
                elif any(word in message_lower for word in ["overdue", "late", "past due"]):
                    context += self._get_overdue_assignments_context(db, now)
                elif any(word in message_lower for word in ["upcoming", "future", "next"]):
                    context += self._get_upcoming_assignments_context(db, now)
                elif any(word in message_lower for word in ["completed", "finished", "done"]):
                    context += self._get_completed_assignments_context(db)
                elif any(word in message_lower for word in ["progress", "in progress", "working on"]):
                    context += self._get_in_progress_assignments_context(db)
                elif any(word in message_lower for word in ["priority", "urgent", "important"]):
                    context += self._get_priority_assignments_context(db)
                elif any(word in message_lower for word in ["statistics", "stats", "summary", "overview"]):
                    context += self._get_statistics_context(db, now)
                else:
                    # For general queries, show recent assignments and key stats
                    context += self._get_recent_assignments_context(db, now)
                    context += self._get_statistics_context(db, now)
            
            # Include pending assignments if relevant
            if pending_count > 0 and any(word in message_lower for word in ["pending", "approval", "review", "waiting"]):
                context += self._get_pending_assignments_context(db)
            
        except Exception as e:
            context += f"Error accessing database: {str(e)}\n"
        
        return context
    
    def _get_today_assignments_context(self, db: Session, now: datetime) -> str:
        """Get assignments due today."""
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        try:
            today_assignments = db.query(Assignment).filter(
                Assignment.due_date >= today_start,
                Assignment.due_date < today_end
            ).all()
            
            if not today_assignments:
                return "=== ASSIGNMENTS DUE TODAY ===\nNo assignments due today.\n\n"
            
            context = f"=== ASSIGNMENTS DUE TODAY ({len(today_assignments)} total) ===\n"
            for a in today_assignments:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                status = str(a.status) if hasattr(a, 'status') and a.status is not None else "not_started"
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Due: {a.due_date.strftime('%Y-%m-%d %H:%M')}\n"
                context += f"  Status: {status}, Priority: {a.priority}/3\n"
                
                try:
                    if hasattr(a, 'estimated_hours') and a.estimated_hours is not None:
                        context += f"  Estimated hours: {a.estimated_hours}\n"
                except:
                    pass
                    
                try:
                    if hasattr(a, 'description') and a.description is not None:
                        desc = str(a.description)[:100]
                        context += f"  Description: {desc}{'...' if len(str(a.description)) > 100 else ''}\n"
                except:
                    pass
                    
                context += "\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== ASSIGNMENTS DUE TODAY ===\nError: {str(e)}\n\n"
    
    def _get_week_assignments_context(self, db: Session, now: datetime) -> str:
        """Get assignments due this week."""
        week_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        try:
            week_assignments = db.query(Assignment).filter(
                Assignment.due_date >= week_start,
                Assignment.due_date <= week_end
            ).order_by(Assignment.due_date).all()
            
            if not week_assignments:
                return "=== ASSIGNMENTS DUE THIS WEEK ===\nNo assignments due this week.\n\n"
            
            context = f"=== ASSIGNMENTS DUE THIS WEEK ({len(week_assignments)} total) ===\n"
            for a in week_assignments:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                status = str(a.status) if hasattr(a, 'status') and a.status is not None else "not_started"
                days_until = (a.due_date - now).days
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Due: {a.due_date.strftime('%Y-%m-%d')} ({days_until} days from now)\n"
                context += f"  Status: {status}, Priority: {a.priority}/3\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== ASSIGNMENTS DUE THIS WEEK ===\nError: {str(e)}\n\n"
    
    def _get_overdue_assignments_context(self, db: Session, now: datetime) -> str:
        """Get overdue assignments."""
        try:
            overdue_assignments = db.query(Assignment).filter(
                Assignment.due_date < now,
                Assignment.status != AssignmentStatus.COMPLETED
            ).order_by(Assignment.due_date).all()
            
            if not overdue_assignments:
                return "=== OVERDUE ASSIGNMENTS ===\nNo overdue assignments. Great job!\n\n"
            
            context = f"=== OVERDUE ASSIGNMENTS ({len(overdue_assignments)} total) ===\n"
            for a in overdue_assignments:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                status = str(a.status) if hasattr(a, 'status') and a.status is not None else "not_started"
                days_overdue = (now - a.due_date).days
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Was due: {a.due_date.strftime('%Y-%m-%d')} ({days_overdue} days ago)\n"
                context += f"  Status: {status}, Priority: {a.priority}/3\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== OVERDUE ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _get_upcoming_assignments_context(self, db: Session, now: datetime) -> str:
        """Get upcoming assignments."""
        try:
            upcoming = db.query(Assignment).filter(
                Assignment.due_date > now,
                Assignment.status != AssignmentStatus.COMPLETED
            ).order_by(Assignment.due_date).limit(15).all()
            
            if not upcoming:
                return "=== UPCOMING ASSIGNMENTS ===\nNo upcoming assignments.\n\n"
            
            context = f"=== UPCOMING ASSIGNMENTS (Next {len(upcoming)}) ===\n"
            for a in upcoming:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                status = str(a.status) if hasattr(a, 'status') and a.status is not None else "not_started"
                days_until = (a.due_date - now).days
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Due: {a.due_date.strftime('%Y-%m-%d')} (in {days_until} days)\n"
                context += f"  Status: {status}, Priority: {a.priority}/3\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== UPCOMING ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _get_completed_assignments_context(self, db: Session) -> str:
        """Get completed assignments."""
        try:
            completed = db.query(Assignment).filter(
                Assignment.status == AssignmentStatus.COMPLETED
            ).order_by(Assignment.completed_at.desc()).limit(10).all()
            
            if not completed:
                return "=== COMPLETED ASSIGNMENTS ===\nNo completed assignments yet.\n\n"
            
            context = f"=== COMPLETED ASSIGNMENTS (Last {len(completed)}) ===\n"
            for a in completed:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Was due: {a.due_date.strftime('%Y-%m-%d')}\n"
                if hasattr(a, 'completed_at') and a.completed_at is not None:
                    context += f"  Completed: {a.completed_at.strftime('%Y-%m-%d')}\n"
                context += f"  Priority: {a.priority}/3\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== COMPLETED ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _get_in_progress_assignments_context(self, db: Session) -> str:
        """Get in-progress assignments."""
        try:
            in_progress = db.query(Assignment).filter(
                Assignment.status == AssignmentStatus.IN_PROGRESS
            ).order_by(Assignment.due_date).all()
            
            if not in_progress:
                return "=== IN-PROGRESS ASSIGNMENTS ===\nNo assignments currently in progress.\n\n"
            
            context = f"=== IN-PROGRESS ASSIGNMENTS ({len(in_progress)} total) ===\n"
            for a in in_progress:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Due: {a.due_date.strftime('%Y-%m-%d')}\n"
                context += f"  Priority: {a.priority}/3\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== IN-PROGRESS ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _get_priority_assignments_context(self, db: Session) -> str:
        """Get high priority assignments."""
        try:
            high_priority = db.query(Assignment).filter(
                Assignment.priority == 3,
                Assignment.status != AssignmentStatus.COMPLETED
            ).order_by(Assignment.due_date).all()
            
            context = f"=== HIGH PRIORITY ASSIGNMENTS ({len(high_priority)} total) ===\n"
            if not high_priority:
                context += "No high priority assignments.\n\n"
                return context
            
            for a in high_priority:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                status = str(a.status) if hasattr(a, 'status') and a.status is not None else "not_started"
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Due: {a.due_date.strftime('%Y-%m-%d')}\n"
                context += f"  Status: {status}\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== HIGH PRIORITY ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _get_statistics_context(self, db: Session, now: datetime) -> str:
        """Get comprehensive statistics."""
        try:
            total = db.query(Assignment).count()
            completed = db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count()
            in_progress = db.query(Assignment).filter(Assignment.status == AssignmentStatus.IN_PROGRESS).count()
            not_started = db.query(Assignment).filter(Assignment.status == AssignmentStatus.NOT_STARTED).count()
            
            overdue = db.query(Assignment).filter(
                Assignment.due_date < now,
                Assignment.status != AssignmentStatus.COMPLETED
            ).count()
            
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            due_today = db.query(Assignment).filter(
                Assignment.due_date >= today_start,
                Assignment.due_date < today_end,
                Assignment.status != AssignmentStatus.COMPLETED
            ).count()
            
            week_end = now + timedelta(days=7)
            due_this_week = db.query(Assignment).filter(
                Assignment.due_date >= now,
                Assignment.due_date <= week_end,
                Assignment.status != AssignmentStatus.COMPLETED
            ).count()
            
            high_priority = db.query(Assignment).filter(
                Assignment.priority == 3,
                Assignment.status != AssignmentStatus.COMPLETED
            ).count()
            
            context = "=== ASSIGNMENT STATISTICS ===\n"
            context += f"Total assignments: {total}\n"
            completion_percent = (completed/total*100) if total > 0 else 0
            context += f"Completed: {completed} ({completion_percent:.1f}%)\n"
            context += f"In progress: {in_progress}\n"
            context += f"Not started: {not_started}\n"
            context += f"Overdue: {overdue}\n"
            context += f"Due today: {due_today}\n"
            context += f"Due this week: {due_this_week}\n"
            context += f"High priority pending: {high_priority}\n\n"
            
            return context
        except Exception as e:
            return f"=== ASSIGNMENT STATISTICS ===\nError: {str(e)}\n\n"
    
    def _get_recent_assignments_context(self, db: Session, now: datetime) -> str:
        """Get recent assignments for general queries."""
        try:
            recent = db.query(Assignment).order_by(Assignment.created_at.desc()).limit(8).all()
            
            if not recent:
                return "=== RECENT ASSIGNMENTS ===\nNo assignments found.\n\n"
            
            context = f"=== RECENT ASSIGNMENTS (Last {len(recent)}) ===\n"
            for a in recent:
                class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                status = str(a.status) if hasattr(a, 'status') and a.status is not None else "not_started"
                
                days_until = None
                if hasattr(a, 'due_date') and a.due_date is not None:
                    days_until = (a.due_date - now).days
                    
                if days_until is not None:
                    if days_until < 0:
                        due_text = f"overdue by {abs(days_until)} days"
                    elif days_until == 0:
                        due_text = "due today"
                    else:
                        due_text = f"due in {days_until} days"
                else:
                    due_text = "no due date"
                
                context += f"• {a.title} (Class: {class_name})\n"
                context += f"  Status: {status}, Priority: {a.priority}/3, {due_text}\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== RECENT ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _get_pending_assignments_context(self, db: Session) -> str:
        """Get pending assignments context."""
        try:
            pending = db.query(PendingAssignment).limit(10).all()
            
            if not pending:
                return "=== PENDING ASSIGNMENTS ===\nNo pending assignments.\n\n"
            
            context = f"=== PENDING ASSIGNMENTS ({len(pending)} awaiting approval) ===\n"
            for p in pending:
                class_obj = db.query(Class).filter(Class.id == p.class_id).first()
                class_name = class_obj.name if class_obj else "Unknown"
                
                context += f"• {p.title} (Class: {class_name})\n"
                context += f"  Due: {p.due_date.strftime('%Y-%m-%d')}\n"
                context += f"  Priority: {p.priority}/3\n\n"
                
            return context + "\n"
        except Exception as e:
            return f"=== PENDING ASSIGNMENTS ===\nError: {str(e)}\n\n"
    
    def _calculate_comprehensive_stats(self, db: Session) -> Dict[str, Any]:
        """Calculate comprehensive statistics."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        try:
            stats = {
                "classes_count": db.query(Class).count(),
                "assignments_count": db.query(Assignment).count(),
                "pending_assignments_count": db.query(PendingAssignment).count(),
                "completed_assignments": db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count(),
                "in_progress_assignments": db.query(Assignment).filter(Assignment.status == AssignmentStatus.IN_PROGRESS).count(),
                "not_started_assignments": db.query(Assignment).filter(Assignment.status == AssignmentStatus.NOT_STARTED).count(),
                "overdue_assignments": db.query(Assignment).filter(
                    Assignment.due_date < now,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count(),
                "due_today": db.query(Assignment).filter(
                    Assignment.due_date >= today_start,
                    Assignment.due_date < today_end,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count(),
                "due_this_week": db.query(Assignment).filter(
                    Assignment.due_date >= now,
                    Assignment.due_date <= now + timedelta(days=7),
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count(),
                "high_priority_pending": db.query(Assignment).filter(
                    Assignment.priority == 3,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count()
            }
            return stats
        except Exception as e:
            return {
                "classes_count": 0,
                "assignments_count": 0,
                "pending_assignments_count": 0,
                "error": str(e)
            }
    
    def _classify_query_type(self, message: str) -> str:
        """Classify the type of query for analytics."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["today", "due today"]):
            return "today"
        elif any(word in message_lower for word in ["week", "this week"]):
            return "week"
        elif any(word in message_lower for word in ["overdue", "late"]):
            return "overdue"
        elif any(word in message_lower for word in ["upcoming", "future"]):
            return "upcoming"
        elif any(word in message_lower for word in ["completed", "finished"]):
            return "completed"
        elif any(word in message_lower for word in ["progress", "working"]):
            return "progress"
        elif any(word in message_lower for word in ["class", "classes"]):
            return "classes"
        elif any(word in message_lower for word in ["priority", "urgent"]):
            return "priority"
        elif any(word in message_lower for word in ["statistics", "stats"]):
            return "statistics"
        else:
            return "general"
    
    def _enhanced_query_response(self, message: str, db: Session, database_context: str) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Enhanced query response that works without AI client but provides intelligent responses."""
        
        # Use the database context to provide intelligent responses
        message_lower = message.lower()
        stats = self._calculate_comprehensive_stats(db)
        
        # Parse the context to extract key information
        if "No assignments due today" in database_context:
            if "today" in message_lower:
                response = "Great news! You don't have any assignments due today. 🎉"
            else:
                response = self._generate_contextual_response(message_lower, database_context, stats)
        else:
            response = self._generate_contextual_response(message_lower, database_context, stats)
        
        return response, "query", False, stats
    
    def _generate_contextual_response(self, message_lower: str, database_context: str, stats: Dict[str, Any]) -> str:
        """Generate contextual response based on database context."""
        
        # Extract key information from context
        lines = database_context.split('\n')
        
        if "today" in message_lower:
            # Find today's assignments in context
            in_today_section = False
            today_assignments = []
            for line in lines:
                if "=== ASSIGNMENTS DUE TODAY" in line:
                    in_today_section = True
                    continue
                elif "===" in line and in_today_section:
                    break
                elif in_today_section and line.strip().startswith("•"):
                    today_assignments.append(line.strip())
            
            if today_assignments:
                response = f"You have {len(today_assignments)} assignment(s) due today:\n\n"
                response += "\n".join(today_assignments[:5])  # Limit for readability
            else:
                response = "Great news! You don't have any assignments due today. 🎉"
                
        elif "week" in message_lower:
            response = f"Based on your current data:\n"
            response += f"• {stats.get('due_this_week', 0)} assignments due this week\n"
            response += f"• {stats.get('overdue_assignments', 0)} assignments are overdue\n"
            response += f"• {stats.get('completed_assignments', 0)} assignments completed\n"
            
        elif "overdue" in message_lower:
            overdue_count = stats.get('overdue_assignments', 0)
            if overdue_count > 0:
                response = f"You have {overdue_count} overdue assignment(s). Here's what I found:\n"
                # Extract overdue assignments from context
                in_overdue_section = False
                for line in lines:
                    if "=== OVERDUE ASSIGNMENTS" in line:
                        in_overdue_section = True
                        continue
                    elif "===" in line and in_overdue_section:
                        break
                    elif in_overdue_section and line.strip():
                        response += line + "\n"
            else:
                response = "Good job! You don't have any overdue assignments."
                
        elif any(word in message_lower for word in ["class", "classes"]):
            response = f"You have {stats.get('classes_count', 0)} classes:\n\n"
            # Extract class information from context
            in_class_section = False
            for line in lines:
                if "=== ALL CLASSES ===" in line:
                    in_class_section = True
                    continue
                elif "===" in line and in_class_section:
                    break
                elif in_class_section and line.strip():
                    response += line + "\n"
                    
        elif any(word in message_lower for word in ["progress", "statistics", "stats", "summary"]):
            response = "Your Assignment Overview:\n"
            response += f"• Total classes: {stats.get('classes_count', 0)}\n"
            response += f"• Total assignments: {stats.get('assignments_count', 0)}\n"
            response += f"• Completed: {stats.get('completed_assignments', 0)}\n"
            response += f"• In progress: {stats.get('in_progress_assignments', 0)}\n"
            response += f"• Not started: {stats.get('not_started_assignments', 0)}\n"
            response += f"• Due today: {stats.get('due_today', 0)}\n"
            response += f"• Overdue: {stats.get('overdue_assignments', 0)}\n"
            response += f"• Pending approval: {stats.get('pending_assignments_count', 0)}\n"
            
        else:
            # General response with key highlights
            response = "Here's your assignment overview:\n"
            response += f"• {stats.get('due_today', 0)} assignments due today\n"
            response += f"• {stats.get('due_this_week', 0)} assignments due this week\n"
            response += f"• {stats.get('overdue_assignments', 0)} assignments overdue\n"
            response += f"• {stats.get('completed_assignments', 0)} assignments completed\n\n"
            response += "Ask me about specific timeframes like 'assignments due today', 'overdue assignments', or 'class information' for more details!"
            
        return response

    def _get_comprehensive_database_info(self, db: Session) -> str:
        """Get comprehensive database information for AI context."""
        context = ""
        now = datetime.now()
        
        try:
            # Get basic counts first
            classes_count = db.query(Class).count()
            assignments_count = db.query(Assignment).count()
            pending_count = db.query(PendingAssignment).count()
            
            context += f"=== DATABASE OVERVIEW ===\n"
            context += f"Total classes: {classes_count}\n"
            context += f"Total active assignments: {assignments_count}\n"
            context += f"Total pending assignments: {pending_count}\n\n"
            
            # Get class information
            if classes_count > 0:
                context += "=== CLASSES ===\n"
                classes = db.query(Class).all()
                for cls in classes:
                    try:
                        class_assignments = db.query(Assignment).filter(Assignment.class_id == cls.id).count()
                        class_pending = db.query(PendingAssignment).filter(PendingAssignment.class_id == cls.id).count()
                        context += f"• {cls.name}: {cls.full_name or 'No description'}\n"
                        context += f"  Active: {class_assignments}, Pending: {class_pending}\n"
                    except Exception as e:
                        context += f"• {cls.name}: (Error loading details)\n"
                context += "\n"
            
            # Get assignment statistics
            if assignments_count > 0:
                context += "=== ASSIGNMENT STATISTICS ===\n"
                try:
                    completed = db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count()
                    in_progress = db.query(Assignment).filter(Assignment.status == AssignmentStatus.IN_PROGRESS).count()
                    not_started = db.query(Assignment).filter(Assignment.status == AssignmentStatus.NOT_STARTED).count()
                    
                    context += f"Completed: {completed}\n"
                    context += f"In Progress: {in_progress}\n"
                    context += f"Not Started: {not_started}\n"
                    
                    # Get overdue count
                    try:
                        overdue = db.query(Assignment).filter(
                            Assignment.due_date < now,
                            Assignment.status != AssignmentStatus.COMPLETED
                        ).count()
                        context += f"Overdue: {overdue}\n"
                    except:
                        context += f"Overdue: Unable to calculate\n"
                        
                    # Get upcoming assignments (next 7 days)
                    try:
                        next_week = now + timedelta(days=7)
                        upcoming = db.query(Assignment).filter(
                            Assignment.due_date >= now,
                            Assignment.due_date <= next_week,
                            Assignment.status != AssignmentStatus.COMPLETED
                        ).count()
                        context += f"Due in next 7 days: {upcoming}\n"
                    except:
                        context += f"Due in next 7 days: Unable to calculate\n"
                        
                except Exception as e:
                    context += f"Error calculating assignment statistics: {str(e)}\n"
                context += "\n"
            
            # Get specific assignment details (limited to avoid token overflow)
            if assignments_count > 0:
                context += "=== RECENT ASSIGNMENTS (Last 10) ===\n"
                try:
                    recent_assignments = db.query(Assignment).order_by(Assignment.created_at.desc()).limit(10).all()
                    for assignment in recent_assignments:
                        try:
                            # Get class name safely
                            class_obj = db.query(Class).filter(Class.id == assignment.class_id).first()
                            class_name = class_obj.name if class_obj else "Unknown"
                            
                            # Format due date safely
                            due_str = "No due date"
                            try:
                                due_str = assignment.due_date.strftime('%Y-%m-%d')
                                days_until = (assignment.due_date - now).days
                                if days_until < 0:
                                    due_str += f" (overdue by {abs(days_until)} days)"
                                elif days_until == 0:
                                    due_str += " (due today)"
                                else:
                                    due_str += f" (in {days_until} days)"
                            except:
                                pass
                            
                            # Get status safely
                            status_str = "unknown"
                            try:
                                if hasattr(assignment.status, 'value'):
                                    status_str = assignment.status.value
                                else:
                                    status_str = str(assignment.status)
                            except:
                                status_str = "not_started"
                            
                            context += f"• {assignment.title}\n"
                            context += f"  Class: {class_name}, Due: {due_str}, Status: {status_str}\n"
                            
                        except Exception as e:
                            context += f"• Assignment {assignment.id} (Error loading details)\n"
                except Exception as e:
                    context += f"Error loading recent assignments: {str(e)}\n"
                context += "\n"
            
            # Get pending assignments info
            if pending_count > 0:
                context += "=== PENDING ASSIGNMENTS (Awaiting Approval) ===\n"
                try:
                    pending_assignments = db.query(PendingAssignment).limit(10).all()
                    for assignment in pending_assignments:
                        try:
                            class_obj = db.query(Class).filter(Class.id == assignment.class_id).first()
                            class_name = class_obj.name if class_obj else "Unknown"
                            
                            try:
                                due_str = assignment.due_date.strftime('%Y-%m-%d') if assignment.due_date is not None else "No due date"
                            except:
                                due_str = "No due date"
                            context += f"• {assignment.title} (Class: {class_name}, Due: {due_str})\n"
                        except Exception as e:
                            context += f"• Pending assignment {assignment.id} (Error loading details)\n"
                except Exception as e:
                    context += f"Error loading pending assignments: {str(e)}\n"
                context += "\n"
                
        except Exception as e:
            print(f"Error in _get_comprehensive_database_info: {e}")
            context = f"Error accessing database: {str(e)}\n"
            context += "The database may have connectivity issues or data integrity problems."
        
        if not context.strip():
            context = "No data found in the database. The database appears to be empty."
        
        return context

    def _mock_query_response(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Mock response for query agent when AI is not available."""
        try:
            classes = db.query(Class).all()
        except:
            classes = []
            
        try:
            assignments = db.query(Assignment).all()
        except:
            assignments = []
            
        try:
            pending_assignments = db.query(PendingAssignment).all()
        except:
            pending_assignments = []
        
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Analyze the message to provide contextual responses
        message_lower = message.lower()
        
        if "today" in message_lower or "due today" in message_lower:
            # Get assignments due today
            try:
                today_assignments = db.query(Assignment).filter(
                    Assignment.due_date >= today_start,
                    Assignment.due_date < today_end,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).all()
                
                if today_assignments:
                    response = f"You have {len(today_assignments)} assignment(s) due today:\n\n"
                    for a in today_assignments:
                        class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                        class_name = class_obj.name if class_obj else "Unknown Class"
                        status_str = a.status.value if hasattr(a.status, 'value') else str(a.status)
                        response += f"• {a.title} (Class: {class_name})\n"
                        response += f"  Status: {status_str}, Priority: {a.priority}/3\n"
                        try:
                            est_hours = getattr(a, 'estimated_hours', None)
                            if est_hours and est_hours > 0:
                                response += f"  Estimated time: {est_hours} hours\n"
                        except:
                            pass
                        response += "\n"
                else:
                    response = "Great news! You don't have any assignments due today. 🎉"
            except Exception as e:
                response = f"I'm having trouble accessing today's assignments. Error: {str(e)}"
                
        elif "this week" in message_lower or "week" in message_lower:
            # Get assignments due this week
            try:
                week_end = now + timedelta(days=7)
                week_assignments = db.query(Assignment).filter(
                    Assignment.due_date >= now,
                    Assignment.due_date <= week_end,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).all()
                
                if week_assignments:
                    response = f"You have {len(week_assignments)} assignment(s) due this week:\n\n"
                    for a in week_assignments:
                        class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                        class_name = class_obj.name if class_obj else "Unknown Class"
                        days_until = (a.due_date - now).days
                        due_text = "today" if days_until == 0 else f"in {days_until} day(s)"
                        response += f"• {a.title} (Class: {class_name}) - Due {due_text}\n"
                else:
                    response = "You don't have any assignments due this week!"
            except Exception as e:
                response = f"I'm having trouble accessing this week's assignments. Error: {str(e)}"
        
        elif "overdue" in message_lower:
            # Get overdue assignments
            try:
                overdue_assignments = db.query(Assignment).filter(
                    Assignment.due_date < now,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).all()
                
                if overdue_assignments:
                    response = f"You have {len(overdue_assignments)} overdue assignment(s):\n\n"
                    for a in overdue_assignments:
                        class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                        class_name = class_obj.name if class_obj else "Unknown Class"
                        days_overdue = (now - a.due_date).days
                        response += f"• {a.title} (Class: {class_name}) - Overdue by {days_overdue} day(s)\n"
                else:
                    response = "Good job! You don't have any overdue assignments."
            except Exception as e:
                response = f"I'm having trouble accessing overdue assignments. Error: {str(e)}"
                
        elif "upcoming" in message_lower or ("assignment" in message_lower and "due" in message_lower):
            # Get upcoming assignments
            try:
                upcoming = db.query(Assignment).filter(
                    Assignment.due_date > now,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).order_by(Assignment.due_date).limit(10).all()
                
                if upcoming:
                    response = f"Your next {len(upcoming)} upcoming assignments:\n\n"
                    for a in upcoming:
                        class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                        class_name = class_obj.name if class_obj else "Unknown Class"
                        days_until = (a.due_date - now).days
                        due_text = "tomorrow" if days_until == 1 else f"in {days_until} days"
                        response += f"• {a.title} (Class: {class_name}) - Due {due_text}\n"
                else:
                    response = "You don't have any upcoming assignments."
            except Exception as e:
                response = f"I'm having trouble accessing upcoming assignments. Error: {str(e)}"
                
        elif "class" in message_lower:
            if classes:
                response = f"You have {len(classes)} classes:\n\n"
                for c in classes:
                    try:
                        class_assignments = db.query(Assignment).filter(Assignment.class_id == c.id).count()
                        class_pending = db.query(PendingAssignment).filter(PendingAssignment.class_id == c.id).count()
                        full_name = getattr(c, 'full_name', None) or 'No description'
                        response += f"• {c.name}: {full_name}\n"
                        response += f"  Active assignments: {class_assignments}, Pending: {class_pending}\n\n"
                    except:
                        response += f"• {c.name}: {getattr(c, 'full_name', 'No description')}\n\n"
            else:
                response = "You don't have any classes set up yet."
                
        elif "complete" in message_lower or "progress" in message_lower:
            try:
                completed = db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count()
                in_progress = db.query(Assignment).filter(Assignment.status == AssignmentStatus.IN_PROGRESS).count()
                not_started = db.query(Assignment).filter(Assignment.status == AssignmentStatus.NOT_STARTED).count()
                total = len(assignments)
                
                if total > 0:
                    completion_rate = (completed / total) * 100
                    response = f"Progress Summary:\n"
                    response += f"• Completed: {completed} ({completion_rate:.1f}%)\n"
                    response += f"• In Progress: {in_progress}\n"
                    response += f"• Not Started: {not_started}\n"
                    response += f"• Total: {total} assignments"
                else:
                    response = "You don't have any assignments yet."
            except Exception as e:
                response = f"I'm having trouble accessing your progress data. Error: {str(e)}"
                
        elif "statistics" in message_lower or "stats" in message_lower:
            try:
                # Get comprehensive stats
                completed = db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count()
                overdue = db.query(Assignment).filter(
                    Assignment.due_date < now,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count()
                due_today = db.query(Assignment).filter(
                    Assignment.due_date >= today_start,
                    Assignment.due_date < today_end,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count()
                
                response = f"Your Assignment Statistics:\n"
                response += f"• Total classes: {len(classes)}\n"
                response += f"• Total assignments: {len(assignments)}\n"
                response += f"• Completed: {completed}\n"
                response += f"• Due today: {due_today}\n"
                response += f"• Overdue: {overdue}\n"
                response += f"• Pending approval: {len(pending_assignments)}"
            except Exception as e:
                response = f"I'm having trouble generating statistics. Error: {str(e)}"
        else:
            # Default comprehensive response
            try:
                completed = db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count()
                overdue = db.query(Assignment).filter(
                    Assignment.due_date < now,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count()
                due_today = db.query(Assignment).filter(
                    Assignment.due_date >= today_start,
                    Assignment.due_date < today_end,
                    Assignment.status != AssignmentStatus.COMPLETED
                ).count()
                
                response = f"Your Assignment Overview:\n"
                response += f"• You have {len(classes)} classes and {len(assignments)} assignments\n"
                response += f"• {due_today} assignments due today\n"
                response += f"• {completed} assignments completed\n"
                response += f"• {overdue} assignments overdue\n"
                response += f"• {len(pending_assignments)} pending assignments awaiting approval\n\n"
                response += "Ask me about 'assignments due today', 'overdue assignments', or 'upcoming assignments' for more details!"
            except Exception as e:
                response = f"I found {len(classes)} classes, {len(assignments)} assignments, and {len(pending_assignments)} pending assignments in your database."
        
        # Calculate comprehensive data for response
        try:
            completed_count = db.query(Assignment).filter(Assignment.status == AssignmentStatus.COMPLETED).count()
            overdue_count = db.query(Assignment).filter(
                Assignment.due_date < now,
                Assignment.status != AssignmentStatus.COMPLETED
            ).count()
            due_today_count = db.query(Assignment).filter(
                Assignment.due_date >= today_start,
                Assignment.due_date < today_end,
                Assignment.status != AssignmentStatus.COMPLETED
            ).count()
        except:
            completed_count = overdue_count = due_today_count = 0
        
        data = {
            "classes_count": len(classes),
            "assignments_count": len(assignments),
            "pending_assignments_count": len(pending_assignments),
            "completed_assignments": completed_count,
            "overdue_assignments": overdue_count,
            "due_today": due_today_count
        }
        
        return response, "query", False, data

    def _build_data_context(self, classes: List[Class], assignments: List[Assignment], pending_assignments: List[PendingAssignment]) -> str:
        """Build context string from current data."""
        context = ""
        
        if classes:
            context += "CLASSES:\n"
            for cls in classes:
                context += f"- {cls.name}: {cls.full_name}\n"
            context += "\n"
        
        if assignments:
            context += "ASSIGNMENTS:\n"
            for assignment in assignments[:10]:  # Limit to prevent token overflow
                status = assignment.status.name if hasattr(assignment.status, 'name') else "not_started"
                context += f"- {assignment.title} (Due: {assignment.due_date.strftime('%Y-%m-%d')}, Status: {status})\n"
            if len(assignments) > 10:
                context += f"  ... and {len(assignments) - 10} more assignments\n"
            context += "\n"
        
        if pending_assignments:
            context += "PENDING ASSIGNMENTS:\n"
            for assignment in pending_assignments[:5]:  # Limit to prevent token overflow
                context += f"- {assignment.title} (Due: {assignment.due_date.strftime('%Y-%m-%d')})\n"
            if len(pending_assignments) > 5:
                context += f"  ... and {len(pending_assignments) - 5} more pending assignments\n"
        
        return context

    def _mock_chat(self, message: str, db: Session) -> Tuple[str, str, bool, Dict[str, Any]]:
        """Mock chat response when AI is not available."""
        if any(keyword in message.lower() for keyword in ["hello", "hi", "hey", "how are you"]):
            return "Hello! I'm Alice, your AI assignment assistant. I'm currently running in mock mode, but I'm here to help you manage your assignments!", "general", False, {}
        elif any(keyword in message.lower() for keyword in ["assignment", "due", "class", "homework"]):
            return "I'd love to help you with your assignments! I can help you query existing assignments, create new ones, or parse syllabi. What would you like to do?", "query", False, {}
        else:
            return "I'm here to help with your academic assignments! You can ask me about your current assignments, create new ones, or parse syllabi.", "general", False, {}
