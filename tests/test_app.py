import pytest
from src.app import activities


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Verify GET /activities returns all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all 9 activities are present
        expected_activities = {
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club"
        }
        assert set(data.keys()) == expected_activities
        
        # Verify each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupSuccess:
    """Tests for successful POST /activities/{activity_name}/signup"""
    
    def test_signup_new_participant_success(self, client, reset_activities):
        """Verify new email can sign up for an available activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify participant was added to the activity
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    
    def test_signup_multiple_participants(self, client, reset_activities):
        """Verify multiple different participants can sign up for same activity"""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(f"/activities/Art Studio/signup?email={email1}")
        response2 = client.post(f"/activities/Art Studio/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert email1 in activities["Art Studio"]["participants"]
        assert email2 in activities["Art Studio"]["participants"]


class TestSignupErrors:
    """Tests for error cases in POST /activities/{activity_name}/signup"""
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Verify signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """Verify duplicate email signup returns 400"""
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_at_capacity(self, client, reset_activities):
        """Verify signup fails when activity is at max capacity"""
        activity_name = "Basketball Team"
        # Basketball Team has max_participants=15 and 1 current participant
        # Fill it up to capacity
        for i in range(14):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Next signup should fail
        response = client.post(
            f"/activities/{activity_name}/signup?email=overflow@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "capacity" in data["detail"].lower() or "full" in data["detail"].lower()


class TestDeleteSuccess:
    """Tests for successful DELETE /activities/{activity_name}/signup"""
    
    def test_delete_participant_success(self, client, reset_activities):
        """Verify existing participant can be removed from activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.delete(
            f"/activities/Chess Club/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        
        # Verify participant was removed
        assert email not in activities["Chess Club"]["participants"]
    
    def test_delete_then_verify_removal(self, client, reset_activities):
        """Verify participant is no longer in GET activities after deletion"""
        email = "sarah@mergington.edu"  # Already in Tennis Club
        
        # Delete participant
        response = client.delete(f"/activities/Tennis Club/signup?email={email}")
        assert response.status_code == 200
        
        # Fetch activities and verify
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert email not in data["Tennis Club"]["participants"]


class TestDeleteErrors:
    """Tests for error cases in DELETE /activities/{activity_name}/signup"""
    
    def test_delete_activity_not_found(self, client, reset_activities):
        """Verify delete from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_delete_email_not_signed_up(self, client, reset_activities):
        """Verify delete of non-participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/signup?email=notsigndup@mergington.edu"
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestIntegration:
    """Integration tests for multi-step workflows"""
    
    def test_signup_fetch_verify_flow(self, client, reset_activities):
        """Test signup → fetch activities → verify participant is present"""
        email = "newuser@mergington.edu"
        activity_name = "Science Club"
        
        # Signup
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Fetch activities
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify participant is in the activity
        assert email in data[activity_name]["participants"]
    
    def test_signup_delete_re_signup_flow(self, client, reset_activities):
        """Test signup → delete → re-signup workflow"""
        email = "testuser@mergington.edu"
        activity_name = "Drama Club"
        
        # Initial signup
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Delete
        response = client.delete(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        
        # Re-signup
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
