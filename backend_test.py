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
            "email": f"test_user_{timestamp}@healthcare.test",
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

    def test_get_quests(self):
        """Test getting available quests"""
        if not self.token:
            return self.log_test("Get Quests", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/quests', None, 200)
        
        if success and isinstance(data, list) and len(data) > 0:
            quest_types = [q.get('type') for q in data]
            expected_types = ['respiration', 'etirement', 'hydratation', 'meditation']
            has_expected_types = all(qt in quest_types for qt in expected_types)
            
            return self.log_test(
                "Get Quests", 
                has_expected_types,
                f"Found {len(data)} quests with types: {quest_types}"
            )
        else:
            return self.log_test(
                "Get Quests", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_get_today_quests(self):
        """Test getting today's user quests"""
        if not self.token:
            return self.log_test("Get Today Quests", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/user-quests/today', None, 200)
        
        if success and isinstance(data, list):
            self.quest_ids = [q.get('id') for q in data if q.get('status') == 'pending']
            return self.log_test(
                "Get Today Quests", 
                len(data) > 0,
                f"Found {len(data)} quests, {len(self.quest_ids)} pending"
            )
        else:
            return self.log_test(
                "Get Today Quests", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_complete_quest(self):
        """Test completing a quest"""
        if not self.token:
            return self.log_test("Complete Quest", False, "No authentication token")
        
        if not self.quest_ids:
            return self.log_test("Complete Quest", False, "No pending quests available")
        
        quest_id = self.quest_ids[0]  # Complete first pending quest
        success, status, data = self.make_request('POST', f'api/user-quests/{quest_id}/complete', {}, 200)
        
        if success and 'points_earned' in data:
            return self.log_test(
                "Complete Quest", 
                True,
                f"Quest completed, earned {data['points_earned']} points"
            )
        else:
            return self.log_test(
                "Complete Quest", 
                False,
                f"Status: {status}, Response: {data}"
            )

    def test_dashboard_stats(self):
        """Test getting dashboard statistics"""
        if not self.token:
            return self.log_test("Dashboard Stats", False, "No authentication token")
        
        success, status, data = self.make_request('GET', 'api/dashboard/stats', None, 200)
        
        if success and 'weekly_data' in data and 'today_stats' in data:
            weekly_data = data['weekly_data']
            today_stats = data['today_stats']
            
            has_weekly_structure = (
                isinstance(weekly_data, list) and 
                len(weekly_data) == 7 and
                all('day' in item and 'valeur' in item for item in weekly_data)
            )
            
            has_today_structure = (
                'quests_completed' in today_stats and
                'total_quests' in today_stats and
                'total_points' in today_stats and
                'completion_percentage' in today_stats
            )
            
            return self.log_test(
                "Dashboard Stats", 
                has_weekly_structure and has_today_structure,
                f"Weekly data: {len(weekly_data)} days, Today: {today_stats['quests_completed']}/{today_stats['total_quests']} quests"
            )
        else:
            return self.log_test(
                "Dashboard Stats", 
                False,
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
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        }
        
        success, status, data = self.make_request('POST', 'api/auth/login', invalid_login, 401)
        
        return self.log_test(
            "Invalid Login Prevention", 
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
        
        # Quest system tests
        self.test_get_quests()
        self.test_get_today_quests()
        self.test_complete_quest()
        self.test_dashboard_stats()
        
        # Error handling tests
        self.test_duplicate_registration()
        self.test_invalid_login()
        
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