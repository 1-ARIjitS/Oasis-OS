#!/usr/bin/env python3
"""
Integration test script for Oasis OS Backend
Tests the complete workflow integration with CLI app
"""

import asyncio
import sys
import time
import requests
import json
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

API_BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except requests.ConnectionError:
        print("❌ Cannot connect to backend - ensure it's running on port 8000")
        return False

def test_workflow_execution():
    """Test complete workflow execution"""
    print("\n🧪 Testing workflow execution...")
    
    # Simple test query
    test_query = "Open calculator"
    
    # Start workflow
    try:
        response = requests.post(
            f"{API_BASE_URL}/workflow/execute",
            json={"query": test_query, "model": "gpt-4.1"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to start workflow: {response.status_code}")
            print(response.text)
            return False
            
        workflow_data = response.json()
        workflow_id = workflow_data["workflow_id"]
        print(f"✅ Workflow started: {workflow_id}")
        
    except Exception as e:
        print(f"❌ Error starting workflow: {e}")
        return False
    
    # Poll for status
    print("📊 Polling workflow status...")
    max_wait_time = 120  # 2 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait_time:
        try:
            response = requests.get(f"{API_BASE_URL}/workflow/{workflow_id}/status")
            
            if response.status_code != 200:
                print(f"❌ Error getting status: {response.status_code}")
                return False
                
            status_data = response.json()
            status = status_data["status"]
            message = status_data["message"]
            
            print(f"📈 Status: {status} - {message}")
            
            if status == "completed":
                print("✅ Workflow completed successfully!")
                print(f"⏱️ Duration: {status_data.get('duration', 'N/A')} seconds")
                return True
            elif status in ["failed", "cancelled"]:
                print(f"❌ Workflow {status}: {message}")
                return False
                
            time.sleep(2)  # Wait 2 seconds before next poll
            
        except Exception as e:
            print(f"❌ Error polling status: {e}")
            return False
    
    print("⏰ Workflow timeout - taking too long")
    return False

def test_api_endpoints():
    """Test all API endpoints"""
    print("\n🔌 Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
    
    # Test active workflows endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/workflow/active")
        if response.status_code == 200:
            active_workflows = response.json()
            print(f"✅ Active workflows endpoint working ({len(active_workflows)} active)")
        else:
            print(f"❌ Active workflows endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Active workflows endpoint error: {e}")

def test_invalid_requests():
    """Test error handling"""
    print("\n🚫 Testing error handling...")
    
    # Test empty query
    try:
        response = requests.post(
            f"{API_BASE_URL}/workflow/execute",
            json={"query": "", "model": "gpt-4.1"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 422:  # Validation error
            print("✅ Empty query validation working")
        else:
            print(f"❌ Empty query validation failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Empty query test error: {e}")
    
    # Test invalid workflow ID
    try:
        response = requests.get(f"{API_BASE_URL}/workflow/invalid-id/status")
        
        if response.status_code == 404:
            print("✅ Invalid workflow ID handling working")
        else:
            print(f"❌ Invalid workflow ID handling failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid workflow ID test error: {e}")

def main():
    """Run all integration tests"""
    print("🚀 Oasis OS Backend Integration Tests")
    print("=" * 50)
    
    # Check if backend is running
    if not test_health_check():
        print("\n💡 To start the backend, run:")
        print("   cd backend")
        print("   python start.py")
        return
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test error handling
    test_invalid_requests()
    
    # Ask user if they want to test workflow execution
    print("\n" + "=" * 50)
    test_execution = input("🤖 Test workflow execution? This will run CLI app (y/n): ").lower()
    
    if test_execution == 'y':
        success = test_workflow_execution()
        
        if success:
            print("\n🎉 All integration tests passed!")
            print("\n📋 Next steps:")
            print("1. Integrate with your frontend using the provided example")
            print("2. Update frontend to point to http://localhost:8000/api/v1")
            print("3. Use the WorkflowManager class for API communication")
        else:
            print("\n❌ Workflow execution test failed")
            print("Check the backend logs for more details")
    else:
        print("\n✅ Basic API tests completed")
        print("Run with workflow execution test when ready")

if __name__ == "__main__":
    main() 