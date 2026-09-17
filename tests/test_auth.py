import unittest

from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


class RoleAuthTests(unittest.TestCase):
    def test_login_success_for_student(self):
        response = client.post(
            "/login",
            json={"email": "student@mergington.edu", "password": "student123"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "student")
        self.assertEqual(response.json()["email"], "student@mergington.edu")

    def test_student_cannot_access_admin_summary(self):
        response = client.get(
            "/admin/summary",
            auth=("student@mergington.edu", "student123"),
        )

        self.assertEqual(response.status_code, 403)

    def test_staff_can_access_admin_summary(self):
        response = client.get(
            "/admin/summary",
            auth=("teacher@mergington.edu", "teacher123"),
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_signup_for_another_student(self):
        response = client.post(
            "/activities/Chess%20Club/signup?email=otherstudent@mergington.edu",
            auth=("student@mergington.edu", "student123"),
        )

        self.assertEqual(response.status_code, 403)

    def test_student_can_signup_for_themselves(self):
        response = client.post(
            "/activities/Chess%20Club/signup?email=student@mergington.edu",
            auth=("student@mergington.edu", "student123"),
        )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
