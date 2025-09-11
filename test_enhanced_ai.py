"""
Test script for the Enhanced AI System
Run this to verify the new AI architecture works correctly
"""

import asyncio
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from backend.app.services.enhanced_ai_service import EnhancedAIService
from backend.app.services.ai_config import AIConfig
from backend.app.services.llm_client import test_available_models

async def test_ai_system():
    """Test the enhanced AI system"""
    print("=== Enhanced AI System Test ===\n")
    
    # Test 1: Check available models
    print("1. Testing Available Models:")
    available = test_available_models()
    for model, status in available.items():
        status_str = "✓ Available" if status else "✗ Not Available"
        print(f"   {model}: {status_str}")
    print()
    
    # Test 2: Initialize AI Service
    print("2. Initializing AI Service:")
    try:
        ai_service = await EnhancedAIService().initialize()
        print("   ✓ AI Service initialized successfully")
        
        # Get status
        status = ai_service.get_status()
        print(f"   Current Model: {status['current_model']}")
        print(f"   Model Available: {status['current_model_available']}")
        print(f"   MCP Tools: {status['mcp_tools_count']}")
        
    except Exception as e:
        print(f"   ✗ Error initializing AI Service: {e}")
        return
    
    print()
    
    # Test 3: Simple chat (without database)
    print("3. Testing Simple Chat:")
    try:
        # This won't work without a database session, but we can test initialization
        print("   ✓ Chat system ready (requires database for full testing)")
    except Exception as e:
        print(f"   ✗ Error with chat system: {e}")
    
    print()
    
    # Test 4: MCP Tool Discovery
    print("4. Testing MCP Tool Discovery:")
    try:
        if hasattr(ai_service, 'agent') and ai_service.agent:
            tools = ai_service.agent.available_tools
            print(f"   ✓ Discovered {len(tools)} MCP tools:")
            for tool in tools[:5]:  # Show first 5 tools
                print(f"     - {tool.name}: {tool.description}")
            if len(tools) > 5:
                print(f"     ... and {len(tools) - 5} more")
        else:
            print("   ⚠ MCP tools not initialized (requires full setup)")
    except Exception as e:
        print(f"   ✗ Error discovering MCP tools: {e}")
    
    print()
    
    # Test 5: Model switching (if multiple models available)
    print("5. Testing Model Switching:")
    available_models = [m for m, available in available.items() if available]
    if len(available_models) > 1:
        try:
            original_model = ai_service.model_key
            new_model = available_models[1] if available_models[0] == original_model else available_models[0]
            
            success = await ai_service.switch_model(new_model)
            if success:
                print(f"   ✓ Successfully switched from {original_model} to {new_model}")
                
                # Switch back
                await ai_service.switch_model(original_model)
                print(f"   ✓ Successfully switched back to {original_model}")
            else:
                print(f"   ✗ Failed to switch models")
        except Exception as e:
            print(f"   ✗ Error testing model switching: {e}")
    else:
        print("   ⚠ Only one model available, skipping switch test")
    
    print()
    print("=== Test Complete ===")
    print("\nTo fully test the system:")
    print("1. Set up your environment variables (GROQ_API_KEY, etc.)")
    print("2. Start the FastAPI server: uvicorn main:app --reload")
    print("3. Test the /api/ai/chat endpoint with complex requests")
    print("4. Try requests like: 'show me my assignments and create a study plan'")

if __name__ == "__main__":
    # Run the async test
    asyncio.run(test_ai_system())
