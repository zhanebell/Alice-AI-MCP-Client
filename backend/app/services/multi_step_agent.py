"""
Multi-Step AI Agent System
Orchestrates complex workflows using LLM reasoning and MCP tools
"""

import json
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .llm_client import LLMClient, ChatMessage, ChatResponse
from .mcp_discovery import MCPToolDiscovery, MCPTool, MCPToolResult
from .ai_config import AIConfig

@dataclass
class AgentStep:
    """Represents a single step in an agent workflow"""
    step_number: int
    description: str
    tool_name: Optional[str] = None
    tool_arguments: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    completed: bool = False

@dataclass
class AgentWorkflow:
    """Represents a complete agent workflow"""
    user_request: str
    steps: List[AgentStep]
    current_step: int = 0
    completed: bool = False
    final_response: Optional[str] = None

class MultiStepAIAgent:
    """
    Advanced AI agent that can:
    1. Break down complex requests into steps
    2. Use MCP tools to execute those steps
    3. Reason about the results and adapt the workflow
    4. Provide comprehensive responses
    """
    
    def __init__(self, model_key: Optional[str] = None):
        self.llm_client = LLMClient(model_key)
        self.mcp_discovery = MCPToolDiscovery()
        self.available_tools: List[MCPTool] = []
        self._tools_initialized = False
    
    async def initialize(self):
        """Initialize the agent by discovering available tools"""
        if not self._tools_initialized:
            self.available_tools = await self.mcp_discovery.discover_tools()
            self._tools_initialized = True
            print(f"Initialized agent with {len(self.available_tools)} MCP tools")
    
    async def process_request(self, user_request: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process a complex user request by breaking it down into steps and executing them
        Returns (final_response, metadata)
        """
        await self.initialize()
        
        if not self.llm_client.is_available():
            return self._fallback_response(user_request)
        
        try:
            # Step 1: Analyze the request and create a workflow plan
            workflow = await self._create_workflow_plan(user_request)
            
            # Step 2: Execute the workflow steps
            await self._execute_workflow(workflow)
            
            # Step 3: Generate final response based on results
            final_response = await self._generate_final_response(workflow)
            
            metadata = {
                "workflow_steps": len(workflow.steps),
                "tools_used": [step.tool_name for step in workflow.steps if step.tool_name],
                "execution_time": sum(getattr(step.result, 'execution_time', 0) for step in workflow.steps if hasattr(step.result, 'execution_time')),
                "success": workflow.completed and not any(step.error for step in workflow.steps)
            }
            
            return final_response, metadata
        
        except Exception as e:
            print(f"Error in multi-step agent: {e}")
            return f"I encountered an error processing your request: {str(e)}", {"error": True}
    
    async def _create_workflow_plan(self, user_request: str) -> AgentWorkflow:
        """Analyze the request and create a step-by-step workflow plan"""
        
        # Create a prompt that helps the LLM understand available tools and plan steps
        tools_description = self._format_tools_for_prompt()
        
        planning_prompt = f"""You are Alice, an intelligent AI assistant for academic task management. 

Your task is to analyze the user's request and create a step-by-step execution plan using the available tools.

User Request: "{user_request}"

Available Tools:
{tools_description}

Create a detailed execution plan. For each step, determine:
1. What needs to be done (description)
2. Which tool to use (if any)
3. What arguments to pass to the tool

Respond with a JSON object in this exact format:
{{
    "steps": [
        {{
            "step_number": 1,
            "description": "Brief description of what this step does",
            "tool_name": "tool_name_or_null",
            "tool_arguments": {{"key": "value"}} or null
        }}
    ],
    "reasoning": "Brief explanation of the overall approach"
}}

Important guidelines:
- Break complex requests into logical steps
- Use get_assignments or get_classes to gather information first
- Always provide specific, realistic dates when creating assignments
- If creating assignments, first check if classes exist and get their IDs
- For study plans, read existing assignments first, then create new ones
- Make sure tool arguments match the exact schema requirements
- If no tools are needed for a step, set tool_name and tool_arguments to null

Examples of complex workflows:
- "Read my assignments and create a study plan" → 1) get_assignments, 2) analyze & plan, 3) create_assignment (for study sessions)
- "Show me my CS class assignments" → 1) get_classes (filter for CS), 2) get_assignments (for that class)
- "Create 3 programming assignments for my Python class" → 1) get_classes, 2) create_assignment (x3)
"""
        
        messages = [
            ChatMessage(role="system", content="You are a planning agent that creates structured execution plans."),
            ChatMessage(role="user", content=planning_prompt)
        ]
        
        response = await asyncio.to_thread(self.llm_client.chat, messages, temperature=0.1, max_tokens=1500)
        
        try:
            # Parse the JSON response
            plan_data = self._extract_json_from_response(response.content)
            
            steps = []
            for step_data in plan_data.get("steps", []):
                steps.append(AgentStep(
                    step_number=step_data["step_number"],
                    description=step_data["description"],
                    tool_name=step_data.get("tool_name"),
                    tool_arguments=step_data.get("tool_arguments")
                ))
            
            workflow = AgentWorkflow(
                user_request=user_request,
                steps=steps
            )
            
            print(f"Created workflow plan with {len(steps)} steps:")
            for step in steps:
                print(f"  {step.step_number}: {step.description} (tool: {step.tool_name})")
            
            return workflow
        
        except Exception as e:
            print(f"Error creating workflow plan: {e}")
            print(f"LLM Response: {response.content}")
            
            # Create a simple fallback workflow
            fallback_step = AgentStep(
                step_number=1,
                description="Process user request with available information",
                tool_name=None,
                tool_arguments=None
            )
            
            return AgentWorkflow(
                user_request=user_request,
                steps=[fallback_step]
            )
    
    async def _execute_workflow(self, workflow: AgentWorkflow):
        """Execute all steps in the workflow"""
        
        for step in workflow.steps:
            print(f"Executing step {step.step_number}: {step.description}")
            
            try:
                if step.tool_name:
                    # Execute the MCP tool
                    result = await self.mcp_discovery.execute_tool(step.tool_name, step.tool_arguments or {})
                    step.result = result
                    
                    if not result.success:
                        step.error = result.error
                        print(f"Step {step.step_number} failed: {result.error}")
                    else:
                        print(f"Step {step.step_number} completed successfully")
                else:
                    # This is a reasoning/analysis step
                    step.result = {"type": "reasoning", "description": step.description}
                
                step.completed = True
                workflow.current_step = step.step_number
                
            except Exception as e:
                step.error = str(e)
                print(f"Error executing step {step.step_number}: {e}")
        
        # Check if workflow completed successfully
        workflow.completed = all(step.completed for step in workflow.steps)
    
    async def _generate_final_response(self, workflow: AgentWorkflow) -> str:
        """Generate a comprehensive final response based on workflow results"""
        
        # Prepare context about what was executed
        execution_summary = self._summarize_workflow_execution(workflow)
        
        response_prompt = f"""Based on the executed workflow, provide a comprehensive and helpful response to the user.

Original User Request: "{workflow.user_request}"

Workflow Execution Summary:
{execution_summary}

Your response should:
1. Directly address what the user asked for
2. Summarize what was accomplished
3. Present any data or results in a clear, organized way
4. Be conversational and helpful
5. Include specific details like names, dates, counts, etc.
6. If any steps failed, explain what went wrong and suggest alternatives

Provide a natural, helpful response as Alice, the AI assistant."""
        
        messages = [
            ChatMessage(role="system", content="You are Alice, a helpful AI assistant. Provide clear, detailed responses based on executed actions."),
            ChatMessage(role="user", content=response_prompt)
        ]
        
        try:
            response = await asyncio.to_thread(self.llm_client.chat, messages, temperature=0.3, max_tokens=1000)
            return response.content
        
        except Exception as e:
            print(f"Error generating final response: {e}")
            return self._create_fallback_final_response(workflow)
    
    def _format_tools_for_prompt(self) -> str:
        """Format available tools for inclusion in prompts"""
        if not self.available_tools:
            return "No tools available"
        
        formatted_tools = []
        for tool in self.available_tools:
            tool_desc = f"• {tool.name}: {tool.description}"
            
            # Add parameter info
            properties = tool.input_schema.get("properties", {})
            required = tool.input_schema.get("required", [])
            
            if properties:
                params = []
                for param, info in properties.items():
                    param_str = param
                    if param in required:
                        param_str += " (required)"
                    if "description" in info:
                        param_str += f" - {info['description']}"
                    params.append(param_str)
                
                tool_desc += f"\n  Parameters: {', '.join(params)}"
            
            formatted_tools.append(tool_desc)
        
        return "\n".join(formatted_tools)
    
    def _extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """Extract JSON from LLM response, handling markdown code blocks"""
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith('```json'):
            response = response[7:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        response = response.strip()
        
        # Find JSON object
        json_start = response.find('{')
        json_end = response.rfind('}')
        
        if json_start == -1 or json_end == -1:
            raise ValueError("No JSON object found in response")
        
        json_str = response[json_start:json_end + 1]
        return json.loads(json_str)
    
    def _summarize_workflow_execution(self, workflow: AgentWorkflow) -> str:
        """Create a summary of workflow execution for the final response generation"""
        summary_parts = []
        
        for step in workflow.steps:
            if step.error:
                summary_parts.append(f"Step {step.step_number}: FAILED - {step.error}")
            elif step.tool_name and step.result:
                if hasattr(step.result, 'success') and step.result.success:
                    summary_parts.append(f"Step {step.step_number}: Used {step.tool_name} successfully")
                    if hasattr(step.result, 'result') and step.result.result:
                        # Include relevant data from the result
                        result_data = step.result.result
                        if isinstance(result_data, dict):
                            if "message" in result_data:
                                summary_parts.append(f"  Result: {result_data['message']}")
                            elif isinstance(result_data, list):
                                summary_parts.append(f"  Found {len(result_data)} items")
                        elif isinstance(result_data, list):
                            summary_parts.append(f"  Found {len(result_data)} items")
                else:
                    summary_parts.append(f"Step {step.step_number}: {step.tool_name} failed")
            else:
                summary_parts.append(f"Step {step.step_number}: {step.description}")
        
        return "\n".join(summary_parts)
    
    def _create_fallback_final_response(self, workflow: AgentWorkflow) -> str:
        """Create a fallback response when final response generation fails"""
        completed_steps = sum(1 for step in workflow.steps if step.completed)
        total_steps = len(workflow.steps)
        
        if workflow.completed:
            return f"I've completed your request by executing {completed_steps} steps. The workflow finished successfully!"
        else:
            return f"I processed your request and completed {completed_steps} out of {total_steps} steps. Some steps may have encountered issues."
    
    def _fallback_response(self, user_request: str) -> Tuple[str, Dict[str, Any]]:
        """Fallback response when LLM is not available"""
        return (
            "I'm having trouble with my AI capabilities right now, but I can still help with basic operations. "
            "Could you try a more specific request like 'show my assignments' or 'create a new class'?",
            {"fallback": True, "llm_available": False}
        )

# Convenience function
async def create_agent(model_key: Optional[str] = None) -> MultiStepAIAgent:
    """Create and initialize a multi-step AI agent"""
    agent = MultiStepAIAgent(model_key)
    await agent.initialize()
    return agent
