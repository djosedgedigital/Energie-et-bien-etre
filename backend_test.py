import requests
import sys
import json
from datetime import datetime
import time

class WellnessAppTester:
    def __init__(self, base_url="https://energie-wellbeing.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_id = None
        self.test_session_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if success and response.content:
                try:
                    response_data = response.json()
                    details += f" | Response keys: {list(response_data.keys()) if isinstance(response_data, dict) else 'Non-dict response'}"
                except:
                    details += " | Non-JSON response"
            
            if not success:
                details += f" | Expected: {expected_status}"
                if response.content:
                    try:
                        error_data = response.json()
                        details += f" | Error: {error_data.get('detail', 'Unknown error')}"
                    except:
                        details += f" | Raw error: {response.text[:100]}"

            return self.log_test(name, success, details), response.json() if success and response.content else {}

        except Exception as e:
            return self.log_test(name, False, f"Exception: {str(e)}"), {}

    def test_health_check(self):
        """Test basic health endpoint"""
        return self.run_test("Health Check", "GET", f"{self.base_url}/health", 200)

    def test_landing_page(self):
        """Test landing page loads"""
        try:
            response = requests.get(self.base_url, timeout=10)
            success = response.status_code == 200 and "Énergie & Bien-être" in response.text
            return self.log_test("Landing Page", success, f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Landing Page", False, f"Exception: {str(e)}")

    def test_create_user(self):
        """Test user creation"""
        test_email = f"test_{int(time.time())}@example.com"
        success, response = self.run_test(
            "Create User",
            "POST",
            "users",
            200,  # Server returns 200 for both create and existing user
            data={"email": test_email, "name": "Test User"}
        )
        if success and response.get('id'):
            self.test_user_id = response['id']
            return True
        return False

    def test_get_user_by_email(self):
        """Test getting user by email"""
        if not self.test_user_id:
            return self.log_test("Get User by Email", False, "No test user created")
        
        # Use demo email that should exist
        success, response = self.run_test(
            "Get User by Email",
            "GET",
            "users/email/demo@example.com",
            200
        )
        return success

    def test_get_user_by_id(self):
        """Test getting user by ID"""
        if not self.test_user_id:
            return self.log_test("Get User by ID", False, "No test user ID available")
        
        success, response = self.run_test(
            "Get User by ID",
            "GET",
            f"users/{self.test_user_id}",
            200
        )
        return success

    def test_dashboard_data(self):
        """Test dashboard data retrieval"""
        if not self.test_user_id:
            return self.log_test("Dashboard Data", False, "No test user ID available")
        
        success, response = self.run_test(
            "Dashboard Data",
            "GET",
            f"dashboard/{self.test_user_id}",
            200
        )
        
        if success:
            required_keys = ['user', 'energy_percentage', 'habit_log', 'quote', 'level', 'xp_total']
            missing_keys = [key for key in required_keys if key not in response]
            if missing_keys:
                return self.log_test("Dashboard Data Structure", False, f"Missing keys: {missing_keys}")
            else:
                self.log_test("Dashboard Data Structure", True, "All required keys present")
        
        return success

    def test_update_habits(self):
        """Test habit updates"""
        if not self.test_user_id:
            return self.log_test("Update Habits", False, "No test user ID available")
        
        habit_data = {
            "water_ml": 1500,
            "sleep_h": 7.0,
            "nutrition_score_0_100": 80,
            "activity_min": 25,
            "serenity_min": 10,
            "mood_1_10": 8,
            "stress_0_10": 3
        }
        
        success, response = self.run_test(
            "Update Habits",
            "PUT",
            f"habits/{self.test_user_id}",
            200,
            data=habit_data
        )
        return success

    def test_get_quests(self):
        """Test quest retrieval"""
        if not self.test_user_id:
            return self.log_test("Get Quests", False, "No test user ID available")
        
        success, response = self.run_test(
            "Get User Quests",
            "GET",
            f"quests/{self.test_user_id}",
            200
        )
        return success

    def test_random_quote(self):
        """Test random quote endpoint"""
        success, response = self.run_test(
            "Random Quote",
            "GET",
            "quotes/random",
            200
        )
        
        if success and response:
            has_text = 'text' in response
            return self.log_test("Quote Structure", has_text, f"Has text field: {has_text}")
        return success

    def test_checkout_session_creation(self):
        """Test Stripe checkout session creation"""
        success, response = self.run_test(
            "Create Checkout Session",
            "POST",
            "checkout/session",
            200,
            data={"origin_url": self.base_url}
        )
        
        if success and response.get('session_id'):
            self.test_session_id = response['session_id']
            has_url = 'url' in response and response['url'].startswith('https://checkout.stripe.com')
            return self.log_test("Checkout Session Structure", has_url, f"Valid Stripe URL: {has_url}")
        return success

    def test_checkout_status(self):
        """Test checkout status check"""
        if not self.test_session_id:
            return self.log_test("Checkout Status", False, "No test session ID available")
        
        success, response = self.run_test(
            "Checkout Status",
            "GET",
            f"checkout/status/{self.test_session_id}",
            200
        )
        return success

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Wellness App Backend Tests")
        print("=" * 50)
        
        # Basic connectivity tests
        print("\n📡 Basic Connectivity Tests:")
        self.test_health_check()
        self.test_landing_page()
        
        # User management tests
        print("\n👤 User Management Tests:")
        self.test_create_user()
        self.test_get_user_by_email()
        self.test_get_user_by_id()
        
        # Core functionality tests
        print("\n🎯 Core Functionality Tests:")
        self.test_dashboard_data()
        self.test_update_habits()
        self.test_get_quests()
        self.test_random_quote()
        
        # Payment system tests
        print("\n💳 Payment System Tests:")
        self.test_checkout_session_creation()
        self.test_checkout_status()
        
        # Final results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend is working correctly.")
            return 0
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} test(s) failed. Check the issues above.")
            return 1

def main():
    tester = WellnessAppTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())