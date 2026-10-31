import os
import sys
import unittest
from pathlib import Path

BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__))).parent
sys.path.insert(0, str(BASE_DIR / "TheQuest_Customer_MobileApp"))

from app import app

class TestAllCustomerMobileViews(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_anonymous_views(self):
        views = ["/", "/rooms", "/login", "/about", "/rewards", "/services", "/ask"]
        for v in views:
            res = self.app.get(v)
            self.assertEqual(res.status_code, 200, f"View {v} failed with {res.status_code}")

    def test_authenticated_checked_in_views(self):
        # Login with Amelia Watson (Room 102 Checked In)
        login_res = self.app.post("/api/login", json={
            "identifier": "amelia.watson@gmail.com",
            "password": "Password123!"
        })
        self.assertEqual(login_res.status_code, 200)

        views = ["/", "/rooms", "/key", "/services", "/ask", "/rewards", "/profile", "/about"]
        for v in views:
            res = self.app.get(v)
            self.assertEqual(res.status_code, 200, f"Authenticated view {v} failed with {res.status_code}")

        # Test Digital Keycard View specifics
        key_res = self.app.get("/key")
        self.assertIn(b"Suite 102", key_res.data)
        self.assertIn(b"ACTIVE KEYCARD", key_res.data)
        self.assertIn(b"Quest_Room_102", key_res.data)
        self.assertIn(b"Tap Phone to Door Lock", key_res.data)

    def test_company_mobile_doors_view(self):
        # Also test that Company Mobile doors.html renders cleanly
        sys.path.insert(0, str(BASE_DIR / "TheQuest_Company_MobileApp"))
        from TheQuest_Company_MobileApp.app import app as comp_app
        comp_client = comp_app.test_client()
        comp_client.testing = True

        # Login as Admin
        res_login = comp_client.post("/", data={"username": "admin", "password": "admin123"}, follow_redirects=True)
        # Check /keys page
        res_keys = comp_client.get("/keys")
        self.assertEqual(res_keys.status_code, 200)
        self.assertIn(b"Master Key & Door Access Console", res_keys.data)
        self.assertIn(b"Active Daily Staff Master Key", res_keys.data)


if __name__ == "__main__":
    unittest.main()
