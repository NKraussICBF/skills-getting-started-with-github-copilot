"""
Test suite for Mergington High School Activities API

This module contains comprehensive tests for all API endpoints
including signup, unregister, and activity listing functionality.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def backup_activities():
    """Create a backup of activities data and restore after test."""
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


class TestActivityEndpoints:
    """Test class for activity-related endpoints."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static index.html."""
        response = client.get("/", allow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]

    def test_get_activities(self, client):
        """Test getting all activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check if required fields exist for each activity
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_signup_for_activity_success(self, client, backup_activities):
        """Test successful signup for an activity."""
        email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        # Get initial participant count
        initial_response = client.get("/activities")
        initial_participants = len(initial_response.json()[activity_name]["participants"])
        
        # Sign up for activity
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was added
        updated_response = client.get("/activities")
        updated_participants = updated_response.json()[activity_name]["participants"]
        assert len(updated_participants) == initial_participants + 1
        assert email in updated_participants

    def test_signup_duplicate_registration(self, client, backup_activities):
        """Test that duplicate registration is prevented."""
        email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        # First signup should succeed
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity."""
        email = "test@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_from_activity_success(self, client, backup_activities):
        """Test successful unregistration from an activity."""
        email = "test@mergington.edu"
        activity_name = "Chess Club"
        
        # First sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Get participant count after signup
        activities_response = client.get("/activities")
        participants_after_signup = len(activities_response.json()[activity_name]["participants"])
        
        # Then unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        
        data = unregister_response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify participant was removed
        final_response = client.get("/activities")
        final_participants = final_response.json()[activity_name]["participants"]
        assert len(final_participants) == participants_after_signup - 1
        assert email not in final_participants

    def test_unregister_not_registered(self, client):
        """Test unregistering when not registered."""
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from non-existent activity."""
        email = "test@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_activity_data_structure(self, client):
        """Test that activity data has correct structure."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities_data = response.json()
        
        # Test specific activities that should exist
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in activities_data
            
            activity_data = activities_data[activity]
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            assert activity_data["max_participants"] > 0

    def test_email_encoding_in_urls(self, client, backup_activities):
        """Test that email addresses with special characters are handled correctly."""
        email = "test+user@mergington.edu"
        activity_name = "Chess Club"
        
        # Test signup with encoded email
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify the email was stored correctly
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants
        
        # Test unregister with encoded email
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200

    def test_activity_names_with_spaces(self, client, backup_activities):
        """Test handling activity names with spaces."""
        email = "test@mergington.edu"
        activity_name = "Programming Class"  # This has a space
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify signup worked
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert email in participants


class TestEdgeCases:
    """Test class for edge cases and error conditions."""

    def test_empty_email(self, client):
        """Test signup with empty email."""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email=")
        # The behavior might vary, but it should either succeed with empty string
        # or fail gracefully
        assert response.status_code in [200, 400, 422]

    def test_missing_email_parameter(self, client):
        """Test signup without email parameter."""
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup")
        assert response.status_code == 422  # Validation error

    def test_multiple_signups_different_activities(self, client, backup_activities):
        """Test that same email can sign up for different activities."""
        email = "test@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"
        
        # Sign up for first activity
        response1 = client.post(f"/activities/{activity1}/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(f"/activities/{activity2}/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email in activities_data[activity1]["participants"]
        assert email in activities_data[activity2]["participants"]


if __name__ == "__main__":
    pytest.main([__file__])