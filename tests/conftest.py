import pytest
from starlette.testclient import TestClient
from src.app import app, activities
import copy


@pytest.fixture
def client():
    """Fixture for TestClient to make HTTP requests to the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Fixture to reset activities to original state after each test"""
    # Store original state before test
    original_activities = copy.deepcopy(activities)
    
    yield  # Run the test
    
    # Restore original state after test
    activities.clear()
    activities.update(original_activities)
