from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


ACTIVITY_NAME = "Test Activity"
ACTIVITY_PATH = f"/activities/{quote(ACTIVITY_NAME, safe='')}/signup"


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


@pytest.fixture
def test_activity(monkeypatch):
    activity = {
        "description": "Activity used by API tests",
        "schedule": "Fridays, 3:00 PM - 4:00 PM",
        "max_participants": 5,
        "participants": [],
    }
    monkeypatch.setitem(app_module.activities, ACTIVITY_NAME, activity)
    return activity


def test_root_redirects_to_static_index(client):
    # Arrange: no additional setup is needed.

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_includes_activity_details(client, test_activity):
    # Arrange: the fixture adds test_activity to the in-memory data.

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[ACTIVITY_NAME] == test_activity


def test_signup_adds_participant(client, test_activity):
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.post(ACTIVITY_PATH, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {ACTIVITY_NAME}"
    }
    assert test_activity["participants"] == [email]


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    unknown_activity_path = "/activities/Unknown%20Activity/signup"

    # Act
    response = client.post(unknown_activity_path, params={"email": "student@example.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client, test_activity):
    # Arrange
    email = "student@example.edu"
    test_activity["participants"].append(email)

    # Act
    response = client.post(ACTIVITY_PATH, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert test_activity["participants"] == [email]


def test_unregister_removes_participant(client, test_activity):
    # Arrange
    email = "student@example.edu"
    test_activity["participants"].append(email)

    # Act
    response = client.delete(ACTIVITY_PATH, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {ACTIVITY_NAME}"
    }
    assert test_activity["participants"] == []


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    unknown_activity_path = "/activities/Unknown%20Activity/signup"

    # Act
    response = client.delete(unknown_activity_path, params={"email": "student@example.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(client, test_activity):
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.delete(ACTIVITY_PATH, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
    assert test_activity["participants"] == []
