"""
MCP Tool Discovery and Execution System
Dynamically discovers and executes MCP tools for database operations
"""

import json
import asyncio
import subprocess
import sys
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import sqlite3
import os

# Add SQLAlchemy imports for proper database handling
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from ..models.database import get_db, engine
from ..models.models import Class, Assignment

@dataclass
class MCPTool:
    """Represents an MCP tool with its schema"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    
    def get_parameters(self) -> List[str]:
        """Get required parameter names"""
        properties = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])
        return list(properties.keys())
    
    def get_required_parameters(self) -> List[str]:
        """Get required parameter names"""
        return self.input_schema.get("required", [])

@dataclass
class MCPToolResult:
    """Result from executing an MCP tool"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None

class MCPToolDiscovery:
    """Discovers and manages MCP tools"""
    
    def __init__(self, mcp_server_path: Optional[str] = None):
        self.mcp_server_path = mcp_server_path or self._find_mcp_server()
        self.tools: List[MCPTool] = []
        
        # Set database path - try multiple locations
        if self.mcp_server_path:
            self.db_path = os.path.join(os.path.dirname(self.mcp_server_path), '..', 'assignments.db')
        else:
            # Fallback database paths for Docker/different environments
            possible_db_paths = [
                "/app/assignments.db",
                os.path.join(os.path.dirname(__file__), "..", "..", "..", "assignments.db"),
                os.path.join(os.path.dirname(__file__), "..", "..", "assignments.db"),
                "./assignments.db"
            ]
            self.db_path = None
            for db_path in possible_db_paths:
                abs_path = os.path.abspath(db_path)
                if os.path.exists(abs_path):
                    self.db_path = abs_path
                    break
            
            if not self.db_path:
                self.db_path = "/app/assignments.db"  # Default for Docker
        
        self._discovered = False
    
    def _find_mcp_server(self) -> str:
        """Find the MCP server script"""
        # Try multiple possible locations for the MCP server
        possible_paths = [
            # Docker container path
            "/app/mcp_server/server.py",
            # Development path (from backend/app/services)
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "mcp_server", "server.py"),
            # Alternative development path
            os.path.join(os.path.dirname(__file__), "..", "..", "mcp_server", "server.py"),
        ]
        
        for server_path in possible_paths:
            abs_path = os.path.abspath(server_path)
            if os.path.exists(abs_path):
                return abs_path
        
        # If we can't find the MCP server, use fallback mode
        print("⚠️  MCP server not found, using fallback database operations")
        return ""
    
    async def discover_tools(self) -> List[MCPTool]:
        """Discover available MCP tools by querying the server"""
        if self._discovered:
            return self.tools
        
        # If no MCP server path, use fallback tools immediately
        if not self.mcp_server_path or not os.path.exists(self.mcp_server_path):
            print("Using fallback MCP tools (server not available)")
            return self._get_fallback_tools()
        
        try:
            # Start the MCP server process
            process = await asyncio.create_subprocess_exec(
                sys.executable, self.mcp_server_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            if process.stdin is None or process.stdout is None:
                raise RuntimeError("Failed to create subprocess pipes")
            
            # Send list_tools request
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/list"
            }
            
            request_json = json.dumps(request) + "\n"
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
            
            # Read response
            response_line = await process.stdout.readline()
            process.terminate()
            await process.wait()
            
            if response_line:
                response = json.loads(response_line.decode().strip())
                if "result" in response and "tools" in response["result"]:
                    self.tools = [
                        MCPTool(
                            name=tool["name"],
                            description=tool["description"],
                            input_schema=tool.get("inputSchema", {})
                        )
                        for tool in response["result"]["tools"]
                    ]
                    self._discovered = True
                    return self.tools
            
        except Exception as e:
            print(f"Error discovering MCP tools: {e}")
            # Fallback to manual tool definitions if discovery fails
            return self._get_fallback_tools()
        
        return self._get_fallback_tools()
    
    def _get_fallback_tools(self) -> List[MCPTool]:
        """Fallback tool definitions if discovery fails"""
        fallback_tools = [
            MCPTool(
                name="create_class",
                description="Create a new class/subject for organizing assignments",
                input_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Class code (e.g., 'ICS 211')"},
                        "full_name": {"type": "string", "description": "Full class name (optional)"},
                        "description": {"type": "string", "description": "Class description (optional)"},
                        "color": {"type": "string", "description": "Hex color code for UI (optional)"}
                    },
                    "required": ["name"]
                }
            ),
            MCPTool(
                name="get_classes",
                description="Get all classes/subjects",
                input_schema={"type": "object", "properties": {}, "required": []}
            ),
            MCPTool(
                name="create_assignment",
                description="Create a new assignment for a class",
                input_schema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Assignment title"},
                        "description": {"type": "string", "description": "Assignment description (optional)"},
                        "due_date": {"type": "string", "description": "Due date in ISO format (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)"},
                        "class_id": {"type": "integer", "description": "ID of the class this assignment belongs to"},
                        "priority": {"type": "integer", "description": "Priority level (1=Low, 2=Medium, 3=High, defaults to 1)"},
                        "estimated_hours": {"type": "integer", "description": "Estimated hours to complete (optional)"}
                    },
                    "required": ["title", "due_date", "class_id"]
                }
            ),
            MCPTool(
                name="get_assignments",
                description="Get assignments with optional filtering",
                input_schema={
                    "type": "object",
                    "properties": {
                        "class_id": {"type": "integer", "description": "Filter by class ID (optional)"},
                        "status": {"type": "string", "description": "Filter by status: not_started, in_progress, completed (optional)"},
                        "include_completed": {"type": "boolean", "description": "Include completed assignments (defaults to false)"},
                        "start_date": {"type": "string", "description": "Start date for filtering (ISO format, optional)"},
                        "end_date": {"type": "string", "description": "End date for filtering (ISO format, optional)"}
                    },
                    "required": []
                }
            ),
            MCPTool(
                name="update_assignment_status",
                description="Update the status of an assignment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "assignment_id": {"type": "integer", "description": "ID of the assignment to update"},
                        "status": {"type": "string", "description": "New status: not_started, in_progress, completed"},
                        "actual_hours": {"type": "integer", "description": "Actual hours spent (optional, for completed assignments)"}
                    },
                    "required": ["assignment_id", "status"]
                }
            ),
            MCPTool(
                name="get_calendar_view",
                description="Get assignments organized by date for calendar view",
                input_schema={
                    "type": "object",
                    "properties": {
                        "start_date": {"type": "string", "description": "Start date (ISO format, defaults to today)"},
                        "end_date": {"type": "string", "description": "End date (ISO format, defaults to 30 days from start)"},
                        "include_completed": {"type": "boolean", "description": "Include completed assignments (defaults to false)"}
                    },
                    "required": []
                }
            ),
            MCPTool(
                name="delete_assignment",
                description="Delete an assignment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "assignment_id": {"type": "integer", "description": "ID of the assignment to delete"}
                    },
                    "required": ["assignment_id"]
                }
            ),
            MCPTool(
                name="delete_class",
                description="Delete a class and all its assignments",
                input_schema={
                    "type": "object",
                    "properties": {
                        "class_id": {"type": "integer", "description": "ID of the class to delete"}
                    },
                    "required": ["class_id"]
                }
            )
        ]
        
        self.tools = fallback_tools
        self._discovered = True
        return self.tools
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute an MCP tool with given arguments"""
        start_time = datetime.now()
        
        # Find the tool
        tool = None
        for t in self.tools:
            if t.name == tool_name:
                tool = t
                break
        
        if not tool:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool '{tool_name}' not found"
            )
        
        try:
            # For now, execute directly against database since MCP server might be complex to integrate
            # In production, you'd want to use the actual MCP protocol
            result = self._execute_tool_direct(tool_name, arguments)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return MCPToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                execution_time=execution_time
            )
    
    def _execute_tool_direct(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute tool directly against database using SQLAlchemy for proper synchronization"""
        # Use SQLAlchemy session for consistent database access
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            if tool_name == "create_class":
                new_class = Class(
                    name=arguments["name"],
                    full_name=arguments.get("full_name"),
                    description=arguments.get("description"),
                    color=arguments.get("color", "#3B82F6")
                )
                db.add(new_class)
                db.commit()
                db.refresh(new_class)
                return {"id": new_class.id, "message": f"Created class '{arguments['name']}'"}
            
            elif tool_name == "get_classes":
                classes = db.query(Class).order_by(Class.name).all()
                return [{"id": c.id, "name": c.name, "full_name": c.full_name, "description": c.description, "color": c.color, "created_at": c.created_at.isoformat() if c.created_at is not None else None, "updated_at": c.updated_at.isoformat() if c.updated_at is not None else None} for c in classes]
            
            elif tool_name == "create_assignment":
                # Parse due date
                due_date_str = arguments["due_date"]
                if "T" in due_date_str or " " in due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace("T", " ").replace("Z", ""))
                else:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                
                new_assignment = Assignment(
                    title=arguments["title"],
                    description=arguments.get("description"),
                    due_date=due_date,
                    class_id=arguments["class_id"],
                    priority=arguments.get("priority", 1),
                    estimated_hours=arguments.get("estimated_hours")
                )
                db.add(new_assignment)
                db.commit()
                db.refresh(new_assignment)
                return {"id": new_assignment.id, "message": f"Created assignment '{arguments['title']}'"}
            
            elif tool_name == "get_assignments":
                query = db.query(Assignment).join(Class)
                
                if arguments.get("class_id"):
                    query = query.filter(Assignment.class_id == arguments["class_id"])
                
                if arguments.get("status"):
                    query = query.filter(Assignment.status == arguments["status"])
                
                if not arguments.get("include_completed", False):
                    query = query.filter(Assignment.status != "completed")
                
                if arguments.get("start_date"):
                    query = query.filter(Assignment.due_date >= arguments["start_date"])
                
                if arguments.get("end_date"):
                    query = query.filter(Assignment.due_date <= arguments["end_date"])
                
                assignments = query.order_by(Assignment.due_date).all()
                
                result = []
                for a in assignments:
                    class_obj = db.query(Class).filter(Class.id == a.class_id).first()
                    result.append({
                        "id": a.id,
                        "title": a.title,
                        "description": a.description,
                        "due_date": a.due_date.isoformat() if a.due_date is not None else None,
                        "class_id": a.class_id,
                        "priority": a.priority,
                        "estimated_hours": a.estimated_hours,
                        "status": a.status.value if a.status is not None else "not_started",
                        "actual_hours": a.actual_hours,
                        "completed_at": a.completed_at.isoformat() if a.completed_at is not None else None,
                        "created_at": a.created_at.isoformat() if a.created_at is not None else None,
                        "updated_at": a.updated_at.isoformat() if a.updated_at is not None else None,
                        "class_name": class_obj.name if class_obj else None,
                        "class_color": class_obj.color if class_obj else None
                    })
                return result
            
            elif tool_name == "update_assignment_status":
                # Use raw SQL for updates to avoid SQLAlchemy column issues
                # First check if assignment exists
                assignment = db.query(Assignment).filter(Assignment.id == arguments["assignment_id"]).first()
                if not assignment:
                    raise ValueError(f"Assignment {arguments['assignment_id']} not found")
                
                update_sql = text("UPDATE assignments SET status = :status, updated_at = CURRENT_TIMESTAMP WHERE id = :assignment_id")
                db.execute(update_sql, {"status": arguments["status"], "assignment_id": arguments["assignment_id"]})
                
                if arguments.get("actual_hours"):
                    hours_sql = text("UPDATE assignments SET actual_hours = :actual_hours WHERE id = :assignment_id")
                    db.execute(hours_sql, {"actual_hours": arguments["actual_hours"], "assignment_id": arguments["assignment_id"]})
                
                if arguments["status"] == "completed":
                    completed_sql = text("UPDATE assignments SET completed_at = :completed_at WHERE id = :assignment_id")
                    db.execute(completed_sql, {"completed_at": datetime.now(), "assignment_id": arguments["assignment_id"]})
                
                db.commit()
                return {"message": f"Updated assignment {arguments['assignment_id']} status to {arguments['status']}"}
            
            elif tool_name == "get_calendar_view":
                start_date = arguments.get("start_date", datetime.now().strftime("%Y-%m-%d"))
                end_date = arguments.get("end_date", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
                
                # Use raw SQL for calendar view to avoid column issues
                if arguments.get("include_completed", False):
                    calendar_sql = text("""
                        SELECT a.id, a.title, a.due_date, a.status, c.name as class_name, c.color as class_color
                        FROM assignments a
                        JOIN classes c ON a.class_id = c.id
                        WHERE a.due_date >= :start_date AND a.due_date <= :end_date
                        ORDER BY a.due_date
                    """)
                else:
                    calendar_sql = text("""
                        SELECT a.id, a.title, a.due_date, a.status, c.name as class_name, c.color as class_color
                        FROM assignments a
                        JOIN classes c ON a.class_id = c.id
                        WHERE a.due_date >= :start_date AND a.due_date <= :end_date AND a.status != 'completed'
                        ORDER BY a.due_date
                    """)
                
                result = db.execute(calendar_sql, {"start_date": start_date, "end_date": end_date})
                
                assignments = []
                for row in result:
                    assignments.append({
                        "id": row.id,
                        "title": row.title,
                        "due_date": row.due_date.isoformat() if row.due_date else None,
                        "class_name": row.class_name,
                        "class_color": row.class_color,
                        "status": row.status or "not_started"
                    })
                return assignments
            
            elif tool_name == "delete_assignment":
                assignment = db.query(Assignment).filter(Assignment.id == arguments["assignment_id"]).first()
                if not assignment:
                    raise ValueError(f"Assignment {arguments['assignment_id']} not found")
                
                db.delete(assignment)
                db.commit()
                return {"message": f"Deleted assignment {arguments['assignment_id']}"}
            
            elif tool_name == "delete_class":
                # Delete assignments first
                db.query(Assignment).filter(Assignment.class_id == arguments["class_id"]).delete()
                
                # Delete class
                class_obj = db.query(Class).filter(Class.id == arguments["class_id"]).first()
                if not class_obj:
                    raise ValueError(f"Class {arguments['class_id']} not found")
                
                db.delete(class_obj)
                db.commit()
                return {"message": f"Deleted class {arguments['class_id']} and all its assignments"}
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        
        finally:
            db.close()
    
    def get_tool_by_name(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tools_summary(self) -> str:
        """Get a summary of available tools for LLM prompts"""
        if not self.tools:
            return "No tools available"
        
        summary = "Available MCP Tools:\n"
        for tool in self.tools:
            summary += f"- {tool.name}: {tool.description}\n"
            if tool.input_schema.get("required"):
                summary += f"  Required: {', '.join(tool.input_schema['required'])}\n"
        
        return summary
