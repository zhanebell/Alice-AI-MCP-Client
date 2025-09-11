#!/usr/bin/env python3
"""
Assignment Tracker MCP Server

This server provides tools for managing classes and assignments in an educational context.
It supports creating classes, adding assignments, updating assignment status, and parsing
syllabi using AI to automatically create assignments.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
import os
import sys

# Add the backend app to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from mcp.server import Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Database connection
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'assignments.db')

def get_db_connection():
    """Get a database connection and ensure tables exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    
    # Create tables if they don't exist
    conn.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            full_name TEXT,
            description TEXT,
            color TEXT DEFAULT '#3B82F6',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_date TIMESTAMP NOT NULL,
            status TEXT DEFAULT 'not_started',
            priority INTEGER DEFAULT 1,
            estimated_hours INTEGER,
            actual_hours INTEGER,
            class_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
    """)
    
    conn.commit()
    return conn

# Initialize the MCP server
server = Server("assignment-tracker")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for the assignment tracker."""
    return [
        Tool(
            name="create_class",
            description="Create a new class/subject for organizing assignments",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Class code (e.g., 'ICS 211')"},
                    "full_name": {"type": "string", "description": "Full class name (optional)"},
                    "description": {"type": "string", "description": "Class description (optional)"},
                    "color": {"type": "string", "description": "Hex color code for UI (optional, defaults to #3B82F6)"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="get_classes",
            description="Get all classes/subjects",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_assignment",
            description="Create a new assignment for a class",
            inputSchema={
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
        Tool(
            name="get_assignments",
            description="Get assignments with optional filtering",
            inputSchema={
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
        Tool(
            name="update_assignment_status",
            description="Update the status of an assignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "integer", "description": "ID of the assignment to update"},
                    "status": {"type": "string", "description": "New status: not_started, in_progress, completed"},
                    "actual_hours": {"type": "integer", "description": "Actual hours spent (optional, for completed assignments)"}
                },
                "required": ["assignment_id", "status"]
            }
        ),
        Tool(
            name="get_calendar_view",
            description="Get assignments organized by date for calendar view",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "Start date (ISO format, defaults to today)"},
                    "end_date": {"type": "string", "description": "End date (ISO format, defaults to 30 days from start)"},
                    "include_completed": {"type": "boolean", "description": "Include completed assignments (defaults to false)"}
                },
                "required": []
            }
        ),
        Tool(
            name="delete_assignment",
            description="Delete an assignment",
            inputSchema={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "integer", "description": "ID of the assignment to delete"}
                },
                "required": ["assignment_id"]
            }
        ),
        Tool(
            name="delete_class",
            description="Delete a class and all its assignments",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_id": {"type": "integer", "description": "ID of the class to delete"}
                },
                "required": ["class_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    
    if name == "create_class":
        conn = get_db_connection()
        try:
            now = datetime.now().isoformat()
            cursor = conn.execute(
                "INSERT INTO classes (name, full_name, description, color, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    arguments["name"],
                    arguments.get("full_name"),
                    arguments.get("description"),
                    arguments.get("color", "#3B82F6"),
                    now,
                    now
                )
            )
            conn.commit()
            class_id = cursor.lastrowid
            
            return [types.TextContent(
                type="text",
                text=f"Successfully created class '{arguments['name']}' with ID {class_id}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creating class: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "get_classes":
        conn = get_db_connection()
        try:
            cursor = conn.execute("SELECT * FROM classes ORDER BY name")
            classes = [dict(row) for row in cursor.fetchall()]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(classes, indent=2, default=str)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting classes: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "create_assignment":
        conn = get_db_connection()
        try:
            # Parse the due date
            due_date_str = arguments["due_date"]
            try:
                if "T" in due_date_str or " " in due_date_str:
                    due_date = datetime.fromisoformat(due_date_str.replace("T", " ").replace("Z", ""))
                else:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
            except ValueError:
                return [types.TextContent(
                    type="text",
                    text="Error: Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM:SS"
                )]
            
            now = datetime.now().isoformat()
            cursor = conn.execute(
                """INSERT INTO assignments 
                   (title, description, due_date, class_id, priority, estimated_hours, created_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    arguments["title"],
                    arguments.get("description"),
                    due_date,
                    arguments["class_id"],
                    arguments.get("priority", 1),
                    arguments.get("estimated_hours"),
                    now,
                    now
                )
            )
            conn.commit()
            assignment_id = cursor.lastrowid
            
            return [types.TextContent(
                type="text",
                text=f"Successfully created assignment '{arguments['title']}' with ID {assignment_id}"
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error creating assignment: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "get_assignments":
        conn = get_db_connection()
        try:
            query = """
                SELECT a.*, c.name as class_name, c.color as class_color
                FROM assignments a
                JOIN classes c ON a.class_id = c.id
                WHERE 1=1
            """
            params = []
            
            if arguments.get("class_id"):
                query += " AND a.class_id = ?"
                params.append(arguments["class_id"])
            
            if arguments.get("status"):
                query += " AND a.status = ?"
                params.append(arguments["status"])
            
            if not arguments.get("include_completed", False):
                query += " AND a.status != 'completed'"
            
            if arguments.get("start_date"):
                query += " AND a.due_date >= ?"
                params.append(arguments["start_date"])
            
            if arguments.get("end_date"):
                query += " AND a.due_date <= ?"
                params.append(arguments["end_date"])
            
            query += " ORDER BY a.due_date ASC"
            
            cursor = conn.execute(query, params)
            assignments = [dict(row) for row in cursor.fetchall()]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(assignments, indent=2, default=str)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting assignments: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "update_assignment_status":
        conn = get_db_connection()
        try:
            # Prepare update fields
            update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
            params = [arguments["status"]]
            
            # If marking as completed, set completed_at
            if arguments["status"] == "completed":
                update_fields.append("completed_at = CURRENT_TIMESTAMP")
                if arguments.get("actual_hours"):
                    update_fields.append("actual_hours = ?")
                    params.append(arguments["actual_hours"])
            else:
                # If not completed, clear completed_at
                update_fields.append("completed_at = NULL")
            
            params.append(arguments["assignment_id"])
            
            query = f"UPDATE assignments SET {', '.join(update_fields)} WHERE id = ?"
            
            cursor = conn.execute(query, params)
            conn.commit()
            
            if cursor.rowcount > 0:
                return [types.TextContent(
                    type="text",
                    text=f"Successfully updated assignment {arguments['assignment_id']} status to {arguments['status']}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"No assignment found with ID {arguments['assignment_id']}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error updating assignment status: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "get_calendar_view":
        conn = get_db_connection()
        try:
            # Set default dates
            start_date = arguments.get("start_date", datetime.now().strftime("%Y-%m-%d"))
            end_date = arguments.get("end_date", (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"))
            
            query = """
                SELECT a.*, c.name as class_name, c.color as class_color
                FROM assignments a
                JOIN classes c ON a.class_id = c.id
                WHERE a.due_date >= ? AND a.due_date <= ?
            """
            params = [start_date, end_date]
            
            if not arguments.get("include_completed", False):
                query += " AND a.status != 'completed'"
            
            query += " ORDER BY a.due_date ASC"
            
            cursor = conn.execute(query, params)
            assignments = [dict(row) for row in cursor.fetchall()]
            
            # Group by date
            calendar_data = {}
            for assignment in assignments:
                due_date = assignment["due_date"]
                if isinstance(due_date, str):
                    date_key = due_date.split()[0]  # Get just the date part
                else:
                    date_key = due_date.strftime("%Y-%m-%d")
                
                if date_key not in calendar_data:
                    calendar_data[date_key] = []
                calendar_data[date_key].append(assignment)
            
            return [types.TextContent(
                type="text",
                text=json.dumps(calendar_data, indent=2, default=str)
            )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error getting calendar view: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "delete_assignment":
        conn = get_db_connection()
        try:
            cursor = conn.execute("DELETE FROM assignments WHERE id = ?", (arguments["assignment_id"],))
            conn.commit()
            
            if cursor.rowcount > 0:
                return [types.TextContent(
                    type="text",
                    text=f"Successfully deleted assignment {arguments['assignment_id']}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"No assignment found with ID {arguments['assignment_id']}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error deleting assignment: {str(e)}"
            )]
        finally:
            conn.close()
    
    elif name == "delete_class":
        conn = get_db_connection()
        try:
            # Delete assignments first (foreign key constraint)
            conn.execute("DELETE FROM assignments WHERE class_id = ?", (arguments["class_id"],))
            cursor = conn.execute("DELETE FROM classes WHERE id = ?", (arguments["class_id"],))
            conn.commit()
            
            if cursor.rowcount > 0:
                return [types.TextContent(
                    type="text",
                    text=f"Successfully deleted class {arguments['class_id']} and all its assignments"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"No class found with ID {arguments['class_id']}"
                )]
        except Exception as e:
            return [types.TextContent(
                type="text",
                text=f"Error deleting class: {str(e)}"
            )]
        finally:
            conn.close()
    
    else:
        return [types.TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="assignment-tracker",
                server_version="1.0.0",
                capabilities=types.ServerCapabilities(
                    tools=types.ToolsCapability(listChanged=True),
                    resources=types.ResourcesCapability(subscribe=True, listChanged=True)
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
