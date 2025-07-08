#!/usr/bin/env python3

"""
Simple test to verify Ollama integration works correctly on Windows
"""

import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_ollama():
    """Test basic Ollama functionality"""
    try:
        # Use the exact same import pattern as working test_ollama.py
        from ollama import chat
        print("✅ Ollama library imported successfully")
        
        # Test basic chat using the exact same pattern
        response = chat(
            model='llama3.2-vision:latest',
            messages=[{
                'role': 'user',
                'content': 'Say "Hello from Ollama" and nothing else.'
            }]
        )
        
        print(f"✅ Basic Ollama chat works: {response['message']['content'][:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Ollama test failed: {e}")
        return False


def test_engine_integration():
    """Test our Ollama engine implementation"""
    try:
        from gui_agents.s1.mllm.MultimodalEngine import LMMEngineOllama
        
        # Initialize engine
        engine = LMMEngineOllama(model="llama3.2-vision:latest")
        print("✅ Ollama engine initialized")
        
        # Test message generation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in exactly 3 words."}
        ]
        
        response = engine.generate(messages, temperature=0.0)
        print(f"✅ Engine generate works: {response[:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Engine test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Ollama integration...")
    print("=" * 50)
    
    # Test 1: Basic Ollama
    print("1. Testing basic Ollama:")
    basic_works = test_basic_ollama()
    print()
    
    if basic_works:
        # Test 2: Engine integration
        print("2. Testing engine integration:")
        engine_works = test_engine_integration()
        print()
        
        if engine_works:
            print("🎉 All tests passed! Ollama integration is working.")
        else:
            print("⚠️  Basic Ollama works but engine integration failed.")
    else:
        print("❌ Basic Ollama failed. Please check:")
        print("   1. Is Ollama running? (ollama serve)")
        print("   2. Is the model available? (ollama pull llama3.2-vision:latest)")
        print("   3. Is the ollama Python package installed? (pip install ollama)") 