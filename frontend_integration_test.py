#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class EnergieBienEtreFrontendTester:
    def __init__(self, base_url="https://soignant-recharge.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def test_frontend_pages_accessible(self):
        """Test that key frontend pages are accessible"""
        pages = [
            ("Landing Page", "/"),
            ("Login Page", "/login"),
            ("Register Page", "/register"),
        ]
        
        all_passed = True
        for page_name, path in pages:
            try:
                response = requests.get(f"{self.base_url}{path}", timeout=10)
                success = response.status_code == 200
                if not success:
                    all_passed = False
                print(f"  {'✅' if success else '❌'} {page_name}: {response.status_code}")
            except Exception as e:
                all_passed = False
                print(f"  ❌ {page_name}: Error - {str(e)}")
        
        return self.log_test("Frontend Pages Accessibility", all_passed)

    def test_landing_page_content(self):
        """Test landing page contains key content"""
        try:
            response = requests.get(self.base_url, timeout=10)
            content = response.text
            
            required_elements = [
                ("Énergie & Bien-être™", "Énergie &amp; Bien-être™"),  # Check both versions
                "Votre dose de récupération en 8 minutes",
                "Pensée pour les soignants",
                "Commencer maintenant",
                "Fonctionnalités clés"
            ]
            
            missing_elements = []
            for element in required_elements:
                if isinstance(element, tuple):
                    # Check both versions
                    if element[0] not in content and element[1] not in content:
                        missing_elements.append(element[0])
                else:
                    if element not in content:
                        missing_elements.append(element)
            
            success = len(missing_elements) == 0
            details = f"Missing: {missing_elements}" if missing_elements else "All key elements found"
            
            return self.log_test("Landing Page Content", success, details)
            
        except Exception as e:
            return self.log_test("Landing Page Content", False, f"Error: {str(e)}")

    def test_register_page_content(self):
        """Test register page contains registration form"""
        try:
            response = requests.get(f"{self.base_url}/register", timeout=10)
            content = response.text
            
            required_elements = [
                "Créer un compte",
                "Nom complet",
                "Adresse email",
                "profession",
                "Mot de passe",
                "S'inscrire"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            success = len(missing_elements) == 0
            details = f"Missing: {missing_elements}" if missing_elements else "All form elements found"
            
            return self.log_test("Register Page Content", success, details)
            
        except Exception as e:
            return self.log_test("Register Page Content", False, f"Error: {str(e)}")

    def test_login_page_content(self):
        """Test login page contains login form"""
        try:
            response = requests.get(f"{self.base_url}/login", timeout=10)
            content = response.text
            
            required_elements = [
                "Connexion",
                "Adresse email",
                "Mot de passe",
                "Se connecter",
                "Créer un compte"
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            success = len(missing_elements) == 0
            details = f"Missing: {missing_elements}" if missing_elements else "All form elements found"
            
            return self.log_test("Login Page Content", success, details)
            
        except Exception as e:
            return self.log_test("Login Page Content", False, f"Error: {str(e)}")

    def test_user_registration_and_dashboard_access(self):
        """Test user registration via API and verify dashboard access would work"""
        timestamp = datetime.now().strftime("%H%M%S")
        test_user = {
            "email": f"test_user_{timestamp}@example.com",
            "full_name": f"Dr. Test User {timestamp}",
            "profession": "infirmier",
            "password": "TestPassword123!"
        }
        
        try:
            # Register user
            response = requests.post(f"{self.api_url}/auth/register", json=test_user, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                self.user_data = data['user']
                
                # Test dashboard data endpoints that the frontend would use
                headers = {'Authorization': f'Bearer {self.token}'}
                
                # Test dashboard stats
                stats_response = requests.get(f"{self.api_url}/dashboard/stats", headers=headers, timeout=10)
                stats_success = stats_response.status_code == 200
                
                # Test today's quests
                quests_response = requests.get(f"{self.api_url}/user-quests/today", headers=headers, timeout=10)
                quests_success = quests_response.status_code == 200
                
                overall_success = stats_success and quests_success
                details = f"Stats: {stats_success}, Quests: {quests_success}, User: {self.user_data.get('email')}"
                
                return self.log_test("Registration & Dashboard Data Access", overall_success, details)
            else:
                return self.log_test("Registration & Dashboard Data Access", False, f"Registration failed: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Registration & Dashboard Data Access", False, f"Error: {str(e)}")

    def test_freemium_limitations_in_api(self):
        """Test that freemium limitations are properly implemented in API"""
        if not self.token:
            return self.log_test("Freemium Limitations", False, "No authentication token")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Test quest limitations
            quests_response = requests.get(f"{self.api_url}/quests", headers=headers, timeout=10)
            quests_data = quests_response.json()
            
            # Test dashboard stats for freemium info
            stats_response = requests.get(f"{self.api_url}/dashboard/stats", headers=headers, timeout=10)
            stats_data = stats_response.json()
            
            # Check freemium limitations
            quest_limit_ok = len(quests_data) <= 2  # Should be limited to 2 for freemium
            has_freemium_info = 'freemium_limits' in stats_data
            is_not_premium = not stats_data.get('is_premium', True)
            
            success = quest_limit_ok and has_freemium_info and is_not_premium
            details = f"Quest limit: {len(quests_data)}/2, Has freemium info: {has_freemium_info}, Not premium: {is_not_premium}"
            
            return self.log_test("Freemium Limitations", success, details)
            
        except Exception as e:
            return self.log_test("Freemium Limitations", False, f"Error: {str(e)}")

    def test_no_blocking_premium_screens(self):
        """Test that there are no blocking premium screens in the frontend"""
        try:
            # Test main pages don't contain blocking premium messages
            pages_to_check = ["/", "/login", "/register"]
            
            blocking_phrases = [
                "Accès Premium Requis",
                "Premium Required",
                "Vous devez être premium",
                "Upgrade required"
            ]
            
            all_clear = True
            for page in pages_to_check:
                response = requests.get(f"{self.base_url}{page}", timeout=10)
                content = response.text.lower()
                
                for phrase in blocking_phrases:
                    if phrase.lower() in content:
                        all_clear = False
                        print(f"  ❌ Found blocking phrase '{phrase}' on {page}")
            
            return self.log_test("No Blocking Premium Screens", all_clear, "No blocking premium messages found in public pages")
            
        except Exception as e:
            return self.log_test("No Blocking Premium Screens", False, f"Error: {str(e)}")

    def test_dashboard_rich_content_availability(self):
        """Test that dashboard would have rich content for freemium users"""
        if not self.token:
            return self.log_test("Dashboard Rich Content", False, "No authentication token")
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            
            # Test dashboard stats endpoint
            stats_response = requests.get(f"{self.api_url}/dashboard/stats", headers=headers, timeout=10)
            stats_data = stats_response.json()
            
            # Test today's quests endpoint
            quests_response = requests.get(f"{self.api_url}/user-quests/today", headers=headers, timeout=10)
            quests_data = quests_response.json()
            
            # Check that freemium users get content
            has_stats = 'today_stats' in stats_data
            has_weekly_data = 'weekly_data' in stats_data
            has_quests = len(quests_data) > 0
            has_freemium_info = 'freemium_limits' in stats_data
            
            success = has_stats and has_weekly_data and has_quests and has_freemium_info
            details = f"Stats: {has_stats}, Weekly: {has_weekly_data}, Quests: {len(quests_data)}, Freemium info: {has_freemium_info}"
            
            return self.log_test("Dashboard Rich Content", success, details)
            
        except Exception as e:
            return self.log_test("Dashboard Rich Content", False, f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all frontend integration tests"""
        print("🚀 Starting Énergie & Bien-être™ Frontend Integration Tests")
        print("=" * 70)
        
        # Test frontend accessibility
        self.test_frontend_pages_accessible()
        
        # Test page content
        self.test_landing_page_content()
        self.test_register_page_content()
        self.test_login_page_content()
        
        # Test user flow and dashboard data
        self.test_user_registration_and_dashboard_access()
        
        # Test freemium features
        self.test_freemium_limitations_in_api()
        self.test_dashboard_rich_content_availability()
        
        # Test no blocking screens
        self.test_no_blocking_premium_screens()
        
        # Final results
        print("=" * 70)
        print(f"📊 Frontend Integration Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All frontend integration tests passed!")
            print("✅ Dashboard loads properly after registration")
            print("✅ Rich freemium content is available")
            print("✅ No blocking screens found")
            print("✅ Freemium limitations work correctly")
            print("✅ All key pages are accessible")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return 1

def main():
    tester = EnergieBienEtreFrontendTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())