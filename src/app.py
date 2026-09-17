"""
High School Management System API

A simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import os
import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")
security = HTTPBasic()

USERS = {
    "student@mergington.edu": {"password": "student123", "role": "student"},
    "teacher@mergington.edu": {"password": "teacher123", "role": "staff"},
    "admin@mergington.edu": {"password": "admin123", "role": "admin"},
}

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


def authenticate_user(credentials: HTTPBasicCredentials):
    user_record = USERS.get(credentials.username)
    if user_record is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not secrets.compare_digest(user_record["password"], credentials.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return {"email": credentials.username, "role": user_record["role"]}


def require_role(*allowed_roles):
    def _dependency(credentials: HTTPBasicCredentials = Depends(security)):
        user = authenticate_user(credentials)
        if user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource",
            )
        return user

    return _dependency


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.post("/login")
def login(credentials: HTTPBasicCredentials = Depends(security)):
    user = authenticate_user(credentials)
    return user


@app.get("/admin/summary")
def admin_summary(current_user: dict = Depends(require_role("staff", "admin"))):
    activity_summaries = []
    total_participants = 0

    for activity_name, details in activities.items():
        participant_count = len(details["participants"])
        total_participants += participant_count
        activity_summaries.append(
            {
                "name": activity_name,
                "participants": participant_count,
                "capacity": details["max_participants"],
            }
        )

    return {
        "role": current_user["role"],
        "total_activities": len(activity_summaries),
        "total_participants": total_participants,
        "activities": activity_summaries,
    }


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str | None = None,
    current_user: dict = Depends(require_role("student", "staff", "admin")),
):
    """Sign up a student for an activity."""
    selected_email = email or current_user["email"]

    if current_user["role"] == "student" and selected_email != current_user["email"]:
        raise HTTPException(
            status_code=403,
            detail="Students can only sign up themselves",
        )

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if selected_email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up",
        )

    activity["participants"].append(selected_email)
    return {"message": f"Signed up {selected_email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str | None = None,
    current_user: dict = Depends(require_role("student", "staff", "admin")),
):
    """Unregister a student from an activity."""
    selected_email = email or current_user["email"]

    if current_user["role"] == "student" and selected_email != current_user["email"]:
        raise HTTPException(
            status_code=403,
            detail="Students can only unregister themselves",
        )

    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]

    if selected_email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity",
        )

    activity["participants"].remove(selected_email)
    return {"message": f"Unregistered {selected_email} from {activity_name}"}
