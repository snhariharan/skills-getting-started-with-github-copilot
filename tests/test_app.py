import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to a known state before each test."""
    original = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


# --- GET /activities ---

def test_get_activities_returns_all_activities():
    # Arrange: activities are loaded from the app

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Soccer Team" in data
    assert "Art Workshop" in data
    assert "Math Olympiad" in data


def test_get_activities_includes_expected_fields():
    # Arrange: no additional setup needed

    # Act
    response = client.get("/activities")

    # Assert
    data = response.json()
    chess = data["Chess Club"]
    assert "description" in chess
    assert "schedule" in chess
    assert "max_participants" in chess
    assert "participants" in chess


# --- POST /activities/{activity_name}/signup ---

def test_signup_adds_participant():
    # Arrange
    email = "newstudent@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities[activity]["participants"]


def test_signup_returns_404_for_unknown_activity():
    # Arrange
    email = "student@mergington.edu"
    activity = "Nonexistent Club"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_prevents_duplicate_registration():
    # Arrange: michael is already in Chess Club
    email = "michael@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.post(f"/activities/{activity}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Already registered for this activity"


def test_signup_returns_400_when_activity_is_full():
    # Arrange: fill Soccer Team to its max capacity
    activity = "Soccer Team"
    max_participants = activities[activity]["max_participants"]
    for i in range(max_participants):
        activities[activity]["participants"].append(f"filler{i}@mergington.edu")

    # Act
    response = client.post(f"/activities/{activity}/signup?email=overflow@mergington.edu")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


# --- DELETE /activities/{activity_name}/unregister ---

def test_unregister_removes_participant():
    # Arrange: michael is already in Chess Club
    email = "michael@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in activities[activity]["participants"]


def test_unregister_returns_404_for_unknown_activity():
    # Arrange
    email = "student@mergington.edu"
    activity = "Nonexistent Club"

    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_non_participant():
    # Arrange
    email = "notregistered@mergington.edu"
    activity = "Chess Club"

    # Act
    response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_signup_then_unregister_roundtrip():
    # Arrange
    email = "roundtrip@mergington.edu"
    activity = "Drama Club"

    # Act: sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    # Act: unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")

    # Assert
    assert signup_response.status_code == 200
    assert unregister_response.status_code == 200
    assert email not in activities[activity]["participants"]
