#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class HealthcareWellnessAPITester:
    def __init__(self, base_url="https://soignant-recharge.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.quest_ids = []
        self.session_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            
            success = response.status_code == expected_status
            response_data = {}
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return success, response.status_code, response_data
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
            return False, 0, {"error": str(e)}

    def test_api_root(self):
        """Test API root endpoint"""
        success, status, data = self.make_request('GET', 'api/', 200)
        return self.log_test(
            "API Root Endpoint", 
            success and "Énergie & Bien-être™" in str(data),
            f"Status: {status}, Response: {data}"
        )

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user = {
            "email": f"test_user_{timestamp}@example.com",
            "full_name": f"Dr. Test User {timestamp}",
            "profession": "infirmier",
            "password": "TestPassword123!"
        }
        
        success, status, data = self.make_request('POST', 'api/auth/register', test_user, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_data = data['user']
            return self.log_test(
                "User Registration", 
                True,
                f"User ID: {self.user_data.get('id')}, Email: {self.user_data.get('email')}"
            )
        else:
            return self.log_test(
                "User Registration", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_user_login(self):
        """Test user login with existing credentials"""
        if not self.user_data:
            return self.log_test("User Login", False, "No user data available for login test")
        
        login_data = {
            "email": self.user_data['email'],
            "password": "TestPassword123!"
        }
        
        success, status, data = self.make_request('POST', 'api/auth/login', login_data, 200)
        
        if success and 'access_token' in data:
            self.token = data['access_token']  # Update token
            return self.log_test(
                "User Login", 
                True,
                f"Token received, User: {data['user']['full_name']}"
            )
        else:
            return self.log_test(
                "User Login", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.token:
            return self.log_test("Get Current User", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/auth/me', None, 200)
        
        return self.log_test(
            "Get Current User", 
            success and 'email' in data,
            f"Status: {status}, User: {data.get('full_name', 'Unknown')}"
        )

    def test_get_quests_without_access(self):
        """Test getting available quests without paid access (should fail)"""
        if not self.token:
            return self.log_test("Get Quests (No Access)", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/quests', None, 403)
        
        return self.log_test(
            "Get Quests (No Access)", 
            success and "Paid access required" in str(data),
            f"Status: {status}, Response: {data}"
        )

    def test_get_today_quests_without_access(self):
        """Test getting today's user quests without paid access (should fail)"""
        if not self.token:
            return self.log_test("Get Today Quests (No Access)", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/user-quests/today', None, 403)
        
        return self.log_test(
            "Get Today Quests (No Access)", 
            success and "Paid access required" in str(data),
            f"Status: {status}, Response: {data}"
        )

    def test_complete_quest_without_access(self):
        """Test completing a quest without paid access (should fail)"""
        if not self.token:
            return self.log_test("Complete Quest (No Access)", False, "No authentication token")
        
        # Use a dummy quest ID since we can't get real ones without access
        dummy_quest_id = "dummy-quest-id"
        success, status, data = self.make_request('POST', f'api/user-quests/{dummy_quest_id}/complete', {}, 403)
        
        return self.log_test(
            "Complete Quest (No Access)", 
            success and "Paid access required" in str(data),
            f"Status: {status}, Response: {data}"
        )

    def test_dashboard_stats_without_access(self):
        """Test getting dashboard statistics without paid access (should fail)"""
        if not self.token:
            return self.log_test("Dashboard Stats (No Access)", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/dashboard/stats', None, 403)
        
        return self.log_test(
            "Dashboard Stats (No Access)", 
            success and "Paid access required" in str(data),
            f"Status: {status}, Response: {data}"
        )

    def test_duplicate_registration(self):
        """Test duplicate email registration (should fail)"""
        if not self.user_data:
            return self.log_test("Duplicate Registration", False, "No user data for duplicate test")
        
        duplicate_user = {
            "email": self.user_data['email'],  # Same email
            "full_name": "Another User",
            "profession": "medecin",
            "password": "AnotherPassword123!"
        }
        
        success, status, data = self.make_request('POST', 'api/auth/register', duplicate_user, 400)
        
        return self.log_test(
            "Duplicate Registration Prevention", 
            success and "already registered" in str(data).lower(),
            f"Status: {status}, Response: {data}"
        )

    def test_invalid_login(self):
        """Test login with invalid credentials"""
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        success, status, data = self.make_request('POST', 'api/auth/login', invalid_login, 401)
        
        return self.log_test(
            "Invalid Login Prevention", 
            success,
            f"Status: {status}, Response: {data}"
        )

    def test_create_checkout_session(self):
        """Test creating Stripe checkout session"""
        if not self.token:
            return self.log_test("Create Checkout Session", False, "No authentication token")
        
        checkout_data = {
            "origin_url": "https://soignant-recharge.preview.emergentagent.com"
        }
        
        success, status, data = self.make_request('POST', 'api/payments/checkout/session', checkout_data, 200)
        
        if success and 'url' in data and 'session_id' in data:
            self.session_id = data['session_id']
            return self.log_test(
                "Create Checkout Session", 
                True,
                f"Session ID: {self.session_id}, URL: {data['url'][:50]}..."
            )
        else:
            return self.log_test(
                "Create Checkout Session", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_checkout_status(self):
        """Test getting checkout session status"""
        if not self.token:
            return self.log_test("Checkout Status", False, "No authentication token")
        
        if not self.session_id:
            return self.log_test("Checkout Status", False, "No session ID available")
        
        success, status, data = self.make_request('GET', f'api/payments/checkout/status/{self.session_id}', None, 200)
        
        if success and 'status' in data and 'payment_status' in data:
            return self.log_test(
                "Checkout Status", 
                True,
                f"Status: {data['status']}, Payment: {data['payment_status']}, Amount: {data.get('amount_total', 'N/A')}"
            )
        else:
            return self.log_test(
                "Checkout Status", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_create_checkout_without_auth(self):
        """Test creating checkout session without authentication (should fail)"""
        original_token = self.token
        self.token = None  # Remove token temporarily
        
        checkout_data = {
            "origin_url": "https://soignant-recharge.preview.emergentagent.com"
        }
        
        success, status, data = self.make_request('POST', 'api/payments/checkout/session', checkout_data, 403)
        
        self.token = original_token  # Restore token
        
        return self.log_test(
            "Create Checkout (No Auth)", 
            success,
            f"Status: {status}, Response: {data}"
        )

    def test_checkout_status_without_auth(self):
        """Test getting checkout status without authentication (should fail)"""
        if not self.session_id:
            return self.log_test("Checkout Status (No Auth)", False, "No session ID available")
        
        original_token = self.token
        self.token = None  # Remove token temporarily
        
        success, status, data = self.make_request('GET', f'api/payments/checkout/status/{self.session_id}', None, 403)
        
        self.token = original_token  # Restore token
        
        return self.log_test(
            "Checkout Status (No Auth)", 
            success,
            f"Status: {status}, Response: {data}"
        )

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Énergie & Bien-être™ API Tests")
        print("=" * 60)
        
        # Basic API tests
        self.test_api_root()
        
        # Authentication flow tests
        self.test_user_registration()
        self.test_user_login()
        self.test_get_current_user()
        
        # Quest system tests (should fail without paid access)
        self.test_get_quests_without_access()
        self.test_get_today_quests_without_access()
        self.test_dashboard_stats_without_access()
        
        # Payment system tests
        self.test_create_checkout_session()
        self.test_checkout_status()
        
        # Error handling tests
        self.test_duplicate_registration()
        self.test_invalid_login()
        self.test_create_checkout_without_auth()
        self.test_checkout_status_without_auth()
        
        # Final results
        print("=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return 1

def main():
    tester = HealthcareWellnessAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())