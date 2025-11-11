import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original activities
    original = {k: v.copy() for k, v in activities.items()}
    original["Chess Club"]["participants"] = original["Chess Club"]["participants"].copy()
    
    yield
    
    # Restore original activities after test
    activities.clear()
    activities.update(original)


class TestActivitiesEndpoint:
    """Test the GET /activities endpoint"""
    
    def test_get_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Check that activities are returned
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        
        # Check activity structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_participants_list(self, client):
        """Test that participants are returned as a list"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_details["participants"], list)


class TestSignupEndpoint:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        email = "test@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
        
        # Verify participant was added
        assert email in activities[activity]["participants"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Test that duplicate signups are rejected"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Michael is already signed up for Chess Club
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signup for a non-existent activity"""
        email = "test@mergington.edu"
        activity = "NonExistent Activity"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test signing up for multiple activities"""
        email = "test@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups worked
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Basketball Club"]["participants"]


class TestUnregisterEndpoint:
    """Test the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, client, reset_activities):
        """Test successful unregister from an activity"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Verify participant is in the list
        assert email in activities[activity]["participants"]
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was removed
        assert email not in activities[activity]["participants"]
    
    def test_unregister_nonexistent_participant(self, client, reset_activities):
        """Test unregister for a participant not in the activity"""
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not registered" in data["detail"]
    
    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregister from a non-existent activity"""
        email = "test@mergington.edu"
        activity = "NonExistent Activity"
        
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static page"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
