"""Basic API tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db

# Create test database
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_create_conversation():
    """Test creating a conversation."""
    response = client.post(
        "/api/v1/conversations",
        json={
            "title": "Test Conversation",
            "description": "Test description"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert "id" in data


def test_list_conversations():
    """Test listing conversations."""
    # Create a conversation first
    client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation"}
    )

    # List conversations
    response = client.get("/api/v1/conversations")
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_conversation():
    """Test getting a specific conversation."""
    # Create a conversation
    create_response = client.post(
        "/api/v1/conversations",
        json={"title": "Test Conversation"}
    )
    conversation_id = create_response.json()["id"]

    # Get the conversation
    response = client.get(f"/api/v1/conversations/{conversation_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation_id
    assert "messages" in data


def test_get_nonexistent_conversation():
    """Test getting a conversation that doesn't exist."""
    response = client.get("/api/v1/conversations/99999")
    assert response.status_code == 404
