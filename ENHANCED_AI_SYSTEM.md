# Enhanced AI System Documentation

## Overview

The Alice AI system has been completely redesigned with a robust, multi-agent architecture that supports:

- **Configurable Language Models**: Switch between different AI providers (Groq, OpenAI, Anthropic, Ollama)
- **MCP Tool Discovery**: Automatically discover and use MCP (Model Context Protocol) tools
- **Multi-Step Reasoning**: Break down complex requests into logical steps
- **Tool Orchestration**: Execute multiple database operations in sequence
- **Robust Error Handling**: Fallback mechanisms and comprehensive error reporting

## Architecture Components

### 1. AI Configuration (`ai_config.py`)
- Centralized configuration for all supported AI models
- Environment-based API key management  
- Model availability checking

### 2. LLM Client (`llm_client.py`)
- Unified interface for multiple AI providers
- Automatic client initialization based on configuration
- Consistent response format across providers

### 3. MCP Tool Discovery (`mcp_discovery.py`)
- Dynamic discovery of available MCP tools
- Direct database execution (with MCP protocol support planned)
- Tool schema validation and parameter checking

### 4. Multi-Step Agent (`multi_step_agent.py`)
- Advanced AI agent that can reason about complex requests
- Workflow planning and execution
- Tool orchestration and result synthesis

### 5. Enhanced AI Service (`enhanced_ai_service.py`)
- Main service interface maintaining backward compatibility
- Async support for all operations
- Model switching capabilities

## Supported Models

### Groq (Default)
- `llama-70b`: Llama 3.3 70B Versatile (high quality, slower)
- `llama-8b`: Llama 3.1 8B Instant (faster, good quality)
- `mixtral`: Mixtral 8x7B (alternative option)

### OpenAI
- `gpt-4`: GPT-4 (requires OpenAI API key)
- `gpt-3.5-turbo`: GPT-3.5 Turbo (faster, cheaper)

### Anthropic
- `claude-3.5-sonnet`: Claude 3.5 Sonnet (requires Anthropic API key)

### Ollama (Local)
- `llama3-local`: Run Llama 3 locally (requires Ollama installation)

## Environment Configuration

Set these environment variables to configure AI providers:

```bash
# Groq (default)
GROQ_API_KEY=your_groq_api_key_here

# OpenAI (optional)
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic (optional) 
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Default model selection (optional)
ALICE_DEFAULT_MODEL=llama-70b
```

## Multi-Step Capabilities

The new system can handle complex, multi-step requests like:

### Example 1: Study Plan Creation
**Request**: "Read my assignments and create a study plan for this week"

**Execution**:
1. `get_assignments` - Retrieve current assignments
2. Analyze due dates, priorities, and estimated hours
3. `create_assignment` - Create study sessions for each subject
4. Generate comprehensive study schedule

### Example 2: Class Management  
**Request**: "Show me my CS class assignments and create 3 new programming projects"

**Execution**:
1. `get_classes` - Find computer science classes
2. `get_assignments` - Get existing CS assignments  
3. `create_assignment` (x3) - Create new programming projects
4. Present summary of existing and new assignments

### Example 3: Syllabus Processing
**Request**: "Parse this syllabus and set up my semester"

**Execution**:
1. Extract course information and assignment list
2. `create_class` - Create course entry
3. `create_assignment` (multiple) - Create all assignments from syllabus
4. Organize by priority and due dates

## API Endpoints

### Enhanced Chat Interface
```http
POST /api/ai/chat
{
    "message": "Your complex request here"
}
```

### Model Management
```http
# Get current model status and available models
GET /api/ai/status

# Switch to a different model
POST /api/ai/switch-model
{
    "model_key": "gpt-4"
}

# List all available models
GET /api/ai/models
```

### Backward Compatible Endpoints
```http
# Still supported for compatibility
POST /api/ai/parse-syllabus
POST /api/ai/generate-assignments
```

## Usage Examples

### Switching Models
```python
# Switch to GPT-4 for complex reasoning
await ai_service.switch_model("gpt-4")

# Switch back to faster model for simple tasks  
await ai_service.switch_model("llama-8b")
```

### Complex Requests
```python
# The AI can now handle multi-step workflows
response = await ai_service.chat(
    "Look at my assignments for this week, then create a detailed study schedule "
    "with 2-hour study blocks for each subject, prioritizing by due date and difficulty"
)
```

## Benefits Over Previous System

1. **Flexibility**: Not locked into a single AI provider or model
2. **Robustness**: Multi-step reasoning with error recovery
3. **Scalability**: Easy to add new models and capabilities
4. **User Experience**: More natural, conversational interaction
5. **Reliability**: Comprehensive fallback mechanisms
6. **Maintainability**: Modular, well-structured codebase

## Installation & Setup

1. **Install Dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Set Environment Variables**:
```bash
# Required - at least one AI provider
export GROQ_API_KEY=your_groq_key

# Optional - additional providers
export OPENAI_API_KEY=your_openai_key
export ANTHROPIC_API_KEY=your_anthropic_key

# Optional - model preference
export ALICE_DEFAULT_MODEL=llama-70b
```

3. **Start the Application**:
```bash
# The system will automatically initialize with the best available model
uvicorn main:app --reload
```

## Future Enhancements

- **Memory System**: Persistent conversation context
- **Custom Tools**: User-defined MCP tools and workflows
- **Learning**: Adapt to user preferences and patterns
- **Integration**: Connect with external calendar and task systems
- **Voice Interface**: Natural language voice interaction
- **Collaboration**: Multi-user assignment management

## Troubleshooting

### Model Not Available
- Check API key configuration
- Verify internet connection for cloud providers
- Ensure Ollama is running for local models

### Tool Execution Errors
- Check database connectivity
- Verify MCP server is accessible
- Review tool parameter validation

### Performance Issues
- Switch to faster models for simple tasks
- Check for large database queries
- Monitor API rate limits
