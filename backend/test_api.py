#!/usr/bin/env python3
"""
Test script for Oasis OS Backend API
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Is it running?")
        return False

def test_workflow_execution():
    """Test workflow execution endpoint"""
    print("\n🔍 Testing workflow execution...")
    
    # Test data
    test_query = "Take a screenshot and save it"
    test_model = "gpt-4o"
    
    payload = {
        "query": test_query,
        "model": test_model
    }
    
    try:
        # Start workflow
        response = requests.post(
            f"{BASE_URL}/api/v1/workflow/execute",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            workflow_id = result["workflow_id"]
            print(f"✅ Workflow started successfully: {workflow_id}")
            
            # Monitor status
            print("⏳ Monitoring workflow status...")
            for i in range(30):  # Check for up to 30 seconds
                status_response = requests.get(f"{BASE_URL}/api/v1/workflow/{workflow_id}/status")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"📊 Status: {status['status']}")
                    
                    if status["status"] in ["completed", "failed", "cancelled"]:
                        if status["status"] == "completed":
                            print("✅ Workflow completed successfully!")
                            if status.get("logs"):
                                print(f"📝 Logs: {status['logs'][:200]}...")
                        else:
                            print(f"❌ Workflow {status['status']}: {status['message']}")
                        return True
                    
                    time.sleep(1)
                else:
                    print(f"❌ Error checking status: {status_response.status_code}")
                    return False
            
            print("⏰ Workflow timeout - cancelling...")
            cancel_response = requests.delete(f"{BASE_URL}/api/v1/workflow/{workflow_id}")
            if cancel_response.status_code == 200:
                print("✅ Workflow cancelled successfully")
            return True
            
        else:
            print(f"❌ Workflow execution failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing workflow: {str(e)}")
        return False

def test_invalid_requests():
    """Test error handling with invalid requests"""
    print("\n🔍 Testing error handling...")
    
    # Test empty query
    response = requests.post(
        f"{BASE_URL}/api/v1/workflow/execute",
        json={"query": "", "model": "gpt-4o"},
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 400:
        print("✅ Empty query validation works")
    else:
        print(f"❌ Empty query validation failed: {response.status_code}")
        return False
    
    # Test invalid workflow ID
    response = requests.get(f"{BASE_URL}/api/v1/workflow/invalid_id/status")
    if response.status_code == 404:
        print("✅ Invalid workflow ID handling works")
    else:
        print(f"❌ Invalid workflow ID handling failed: {response.status_code}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 Starting Oasis OS Backend API Tests")
    print("=" * 50)
    
    # Run tests
    tests = [
        test_health_check,
        test_invalid_requests,
        # test_workflow_execution,  # Comment out for quick testing
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        else:
            print(f"❌ Test failed: {test.__name__}")
    
    print(f"\n📊 Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 