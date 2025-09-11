"""
Enhanced AI System Usage Examples
This demonstrates the new capabilities of the Alice AI system
"""

# Example complex requests that the new AI system can handle:

EXAMPLE_REQUESTS = [
    # Multi-step workflow examples
    {
        "request": "Read my assignments and create a study plan for this week. Add these tasks into my assignments for my CS class.",
        "description": "Complex workflow: reads existing data, analyzes it, creates new assignments",
        "steps": [
            "1. get_assignments - Retrieve all current assignments", 
            "2. Analyze due dates, priorities, estimated hours",
            "3. get_classes - Find CS class ID",
            "4. create_assignment - Create study sessions/tasks",
            "5. Generate comprehensive study schedule"
        ]
    },
    
    {
        "request": "Show me my programming assignments due this week and create 2 additional practice projects",
        "description": "Filtered query + content creation",
        "steps": [
            "1. get_assignments - Filter by date range and keywords",
            "2. Present current programming assignments",
            "3. create_assignment (x2) - Generate practice projects",
            "4. Organize by difficulty and timeline"
        ]
    },
    
    {
        "request": "Parse this syllabus: 'CS 101 - Intro to Programming. Assignment 1 due Sept 15, Midterm Oct 20, Final Project Dec 10'",
        "description": "Syllabus parsing with automatic class/assignment creation",
        "steps": [
            "1. Extract course info and assignment list",
            "2. create_class - Create 'CS 101' course",
            "3. create_assignment (x3) - Create Assignment 1, Midterm, Final Project",
            "4. Set appropriate priorities and due dates"
        ]
    },
    
    {
        "request": "What's my workload like next week? Create a balanced schedule if it's too heavy.",
        "description": "Analysis + conditional action",
        "steps": [
            "1. get_calendar_view - Get next week's assignments",
            "2. Calculate total estimated hours",
            "3. If > threshold, create_assignment for buffer/break times",
            "4. Suggest schedule optimization"
        ]
    },
    
    {
        "request": "I need to prepare for my database final exam. Create a 2-week study plan with daily tasks.",
        "description": "Targeted preparation with detailed planning",
        "steps": [
            "1. get_classes - Find database course",
            "2. get_assignments - Review existing DB assignments",
            "3. create_assignment (x14) - Daily study tasks",
            "4. Progressive difficulty and topic coverage"
        ]
    }
]

# Model switching examples
MODEL_USAGE_SCENARIOS = {
    "llama-70b": {
        "best_for": "Complex reasoning, multi-step planning, creative tasks",
        "example": "Creating comprehensive study plans, analyzing complex syllabi"
    },
    
    "llama-8b": {
        "best_for": "Quick responses, simple queries, routine tasks", 
        "example": "Listing assignments, basic Q&A, status updates"
    },
    
    "gpt-4": {
        "best_for": "Highest quality reasoning, complex analysis",
        "example": "Academic planning, detailed course analysis"
    },
    
    "claude-3.5-sonnet": {
        "best_for": "Structured analysis, detailed explanations",
        "example": "Breaking down complex projects, study strategies"
    }
}

# API usage patterns
API_EXAMPLES = {
    "chat_endpoint": {
        "url": "POST /api/ai/chat",
        "payload": {
            "message": "Show me my assignments for next week and create a study schedule"
        },
        "response_fields": [
            "response: The AI's comprehensive response",
            "agent_used: 'multi-step' (new agent system)",
            "action_taken: true/false (whether database changes were made)",
            "data: { tools_used: [...], workflow_steps: 3, success: true }"
        ]
    },
    
    "model_switching": {
        "check_models": "GET /api/ai/models",
        "switch_model": {
            "url": "POST /api/ai/switch-model", 
            "payload": {"model_key": "gpt-4"}
        },
        "use_case": "Switch to higher quality model for complex tasks"
    }
}

# Environment setup examples
ENVIRONMENT_SETUP = """
# Basic setup (Groq only)
GROQ_API_KEY=your_groq_api_key_here
ALICE_DEFAULT_MODEL=llama-70b

# Multi-provider setup
GROQ_API_KEY=your_groq_api_key
OPENAI_API_KEY=your_openai_api_key  
ANTHROPIC_API_KEY=your_anthropic_api_key

# Performance optimization
ALICE_DEFAULT_MODEL=llama-8b  # Faster for most tasks
"""

# Frontend integration examples  
FRONTEND_INTEGRATION = """
// New enhanced chat with model switching
const chatWithAI = async (message, preferredModel = null) => {
    // Switch model if specified
    if (preferredModel) {
        await fetch('/api/ai/switch-model', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({model_key: preferredModel})
        });
    }
    
    // Send complex request
    const response = await fetch('/api/ai/chat', {
        method: 'POST', 
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message})
    });
    
    const result = await response.json();
    
    // Handle multi-step results
    if (result.action_taken && result.data.tools_used) {
        console.log('AI executed:', result.data.tools_used);
        // Refresh UI components that might have changed
        refreshAssignments();
        refreshCalendar();
    }
    
    return result.response;
};

// Example usage
await chatWithAI(
    "Read my assignments and create a study plan for finals week",
    "gpt-4"  // Use best model for complex planning
);

await chatWithAI(
    "What assignments do I have today?", 
    "llama-8b"  // Use fast model for simple queries
);
"""

if __name__ == "__main__":
    print("Enhanced AI System - Usage Examples")
    print("=" * 50)
    
    print("\n🚀 Complex Requests the AI Can Now Handle:")
    for i, example in enumerate(EXAMPLE_REQUESTS, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   Request: \"{example['request']}\"")
        print("   Execution Steps:")
        for step in example['steps']:
            print(f"      {step}")
    
    print(f"\n🧠 Model Selection Guide:")
    for model, info in MODEL_USAGE_SCENARIOS.items():
        print(f"\n   {model}:")
        print(f"      Best for: {info['best_for']}")
        print(f"      Example: {info['example']}")
    
    print(f"\n📝 Environment Setup:")
    print(ENVIRONMENT_SETUP)
    
    print(f"\n💻 Frontend Integration:")
    print(FRONTEND_INTEGRATION)
    
    print("\n🎯 Key Benefits:")
    print("   • No more single-tool limitations")
    print("   • Multi-step reasoning and planning")
    print("   • Configurable AI models for different needs")
    print("   • Robust error handling and fallbacks")
    print("   • Natural conversation interface")
    print("   • Database operations via AI reasoning")
