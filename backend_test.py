import requests
import sys
import json
from datetime import datetime, timedelta
import uuid

class TimetableAPITester:
    def __init__(self, base_url="https://timely-teach.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.staff_token = None
        self.admin_user = None
        self.staff_user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if files:
            # Remove Content-Type for file uploads
            test_headers.pop('Content-Type', None)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            details = f"Status: {response.status_code}"
            
            if not success:
                details += f", Expected: {expected_status}"
                try:
                    error_data = response.json()
                    details += f", Error: {error_data.get('detail', 'Unknown error')}"
                except:
                    details += f", Response: {response.text[:100]}"

            self.log_test(name, success, details)
            
            if success:
                try:
                    return response.json()
                except:
                    return {"success": True}
            return None

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return None

    def test_health_check(self):
        """Test health check endpoint"""
        print("\n🔍 Testing Health Check...")
        result = self.run_test("Health Check", "GET", "health", 200)
        return result is not None

    def test_user_registration(self):
        """Test user registration for both admin and staff"""
        print("\n🔍 Testing User Registration...")
        
        # Generate unique emails
        timestamp = datetime.now().strftime('%H%M%S')
        admin_email = f"admin_{timestamp}@test.com"
        staff_email = f"staff_{timestamp}@test.com"
        
        # Register admin user
        admin_data = {
            "name": "Test Admin",
            "email": admin_email,
            "password": "TestPass123!",
            "phone": "+1234567890",
            "role": "admin"
        }
        
        admin_result = self.run_test("Register Admin User", "POST", "auth/register", 200, admin_data)
        if admin_result:
            self.admin_token = admin_result.get('token')
            self.admin_user = admin_result.get('user')
        
        # Register staff user
        staff_data = {
            "name": "Test Staff",
            "email": staff_email,
            "password": "TestPass123!",
            "phone": "+1234567891",
            "role": "staff"
        }
        
        staff_result = self.run_test("Register Staff User", "POST", "auth/register", 200, staff_data)
        if staff_result:
            self.staff_token = staff_result.get('token')
            self.staff_user = staff_result.get('user')
        
        return admin_result is not None and staff_result is not None

    def test_user_login(self):
        """Test user login"""
        print("\n🔍 Testing User Login...")
        
        if not self.admin_user or not self.staff_user:
            self.log_test("Login Test", False, "Users not registered")
            return False
        
        # Test admin login
        admin_login_data = {
            "email": self.admin_user['email'],
            "password": "TestPass123!"
        }
        
        admin_login_result = self.run_test("Admin Login", "POST", "auth/login", 200, admin_login_data)
        
        # Test staff login
        staff_login_data = {
            "email": self.staff_user['email'],
            "password": "TestPass123!"
        }
        
        staff_login_result = self.run_test("Staff Login", "POST", "auth/login", 200, staff_login_data)
        
        return admin_login_result is not None and staff_login_result is not None

    def test_auth_me(self):
        """Test get current user endpoint"""
        print("\n🔍 Testing Auth Me Endpoint...")
        
        if not self.admin_token:
            self.log_test("Auth Me Test", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        result = self.run_test("Get Current User", "GET", "auth/me", 200, headers=headers)
        
        return result is not None

    def test_admin_create_class(self):
        """Test admin class creation"""
        print("\n🔍 Testing Admin Class Creation...")
        
        if not self.admin_token or not self.staff_user:
            self.log_test("Create Class Test", False, "Missing admin token or staff user")
            return False
        
        # Create a class for the staff user
        future_time = datetime.now() + timedelta(hours=2)
        class_data = {
            "title": "Test Mathematics Class",
            "room": "Room 101",
            "teacher_email": self.staff_user['email'],
            "start_datetime": future_time.isoformat(),
            "end_datetime": (future_time + timedelta(hours=1)).isoformat(),
            "recurrence": "ONCE"
        }
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        result = self.run_test("Create Class", "POST", "admin/classes", 200, class_data, headers)
        
        return result is not None

    def test_admin_upcoming_classes(self):
        """Test admin view upcoming classes"""
        print("\n🔍 Testing Admin Upcoming Classes...")
        
        if not self.admin_token:
            self.log_test("Upcoming Classes Test", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        result = self.run_test("Get Upcoming Classes", "GET", "admin/upcoming?hours=48", 200, headers=headers)
        
        return result is not None

    def test_admin_users(self):
        """Test admin view all users"""
        print("\n🔍 Testing Admin View Users...")
        
        if not self.admin_token:
            self.log_test("View Users Test", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        result = self.run_test("Get All Users", "GET", "admin/users", 200, headers=headers)
        
        return result is not None

    def test_admin_logs(self):
        """Test admin view logs"""
        print("\n🔍 Testing Admin View Logs...")
        
        if not self.admin_token:
            self.log_test("View Logs Test", False, "No admin token")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        result = self.run_test("Get Logs", "GET", "admin/logs?limit=50", 200, headers=headers)
        
        return result is not None

    def test_admin_test_reminder(self):
        """Test admin send test reminder"""
        print("\n🔍 Testing Admin Test Reminder...")
        
        if not self.admin_token or not self.admin_user:
            self.log_test("Test Reminder", False, "Missing admin token or user")
            return False
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        endpoint = f"admin/test-reminder?user_email={self.admin_user['email']}"
        result = self.run_test("Send Test Reminder", "POST", endpoint, 200, headers=headers)
        
        return result is not None

    def test_staff_my_classes(self):
        """Test staff view my classes"""
        print("\n🔍 Testing Staff My Classes...")
        
        if not self.staff_token:
            self.log_test("Staff My Classes", False, "No staff token")
            return False
        
        headers = {"Authorization": f"Bearer {self.staff_token}"}
        result = self.run_test("Get My Classes", "GET", "users/me/classes?days=7", 200, headers=headers)
        
        return result is not None

    def test_staff_update_preferences(self):
        """Test staff update preferences"""
        print("\n🔍 Testing Staff Update Preferences...")
        
        if not self.staff_token:
            self.log_test("Update Preferences", False, "No staff token")
            return False
        
        prefs_data = {
            "lead_time_minutes": 30,
            "channels": {"email": True, "sms": False, "push": False},
            "quiet_hours": {"enabled": True, "start": "22:00", "end": "07:00"}
        }
        
        headers = {"Authorization": f"Bearer {self.staff_token}"}
        result = self.run_test("Update Preferences", "PUT", "users/me/preferences", 200, prefs_data, headers)
        
        return result is not None

    def test_staff_my_timetable(self):
        """Test staff view my timetable"""
        print("\n🔍 Testing Staff My Timetable...")
        
        if not self.staff_token:
            self.log_test("Staff My Timetable", False, "No staff token")
            return False
        
        headers = {"Authorization": f"Bearer {self.staff_token}"}
        result = self.run_test("Get My Timetable", "GET", "users/me/timetable", 200, headers=headers)
        
        return result is not None

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        print("\n🔍 Testing Unauthorized Access...")
        
        # Test admin endpoint without token
        self.run_test("Unauthorized Admin Access", "GET", "admin/users", 401)
        
        # Test staff endpoint without token
        self.run_test("Unauthorized Staff Access", "GET", "users/me/classes", 401)
        
        # Test staff accessing admin endpoint
        if self.staff_token:
            headers = {"Authorization": f"Bearer {self.staff_token}"}
            self.run_test("Staff Access Admin Endpoint", "GET", "admin/users", 403, headers=headers)

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Timetable API Tests...")
        print(f"Testing against: {self.base_url}")
        
        # Basic tests
        self.test_health_check()
        
        # Authentication tests
        if self.test_user_registration():
            self.test_user_login()
            self.test_auth_me()
        
        # Admin functionality tests
        self.test_admin_create_class()
        self.test_admin_upcoming_classes()
        self.test_admin_users()
        self.test_admin_logs()
        self.test_admin_test_reminder()
        
        # Staff functionality tests
        self.test_staff_my_classes()
        self.test_staff_update_preferences()
        self.test_staff_my_timetable()
        
        # Security tests
        self.test_unauthorized_access()
        
        # Print summary
        print(f"\n📊 Test Summary:")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        return self.tests_passed, self.tests_run, self.test_results

def main():
    tester = TimetableAPITester()
    passed, total, results = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "summary": {
                "tests_run": total,
                "tests_passed": passed,
                "success_rate": f"{(passed/total)*100:.1f}%"
            },
            "results": results
        }, f, indent=2)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())