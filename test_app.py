import pytest
from app import app, user_collection, chat_collection

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def cleanup_test_data():
    # Delete test users
    user_collection.delete_many({"email": {"$regex": "example.com"}})

    # Delete test chats
    chat_collection.delete_many({"chat_name": {"$regex": "Chat Room Name"}})

def test_post_query(client):
    query_data = {"query": "Your query goes here."}
    response = client.post('/query', json=query_data)
    assert response.status_code == 200
    assert response.json.get("msg").get("query") == query_data["query"]
    assert response.json.get("msg").get("response")
    

def test_post_query_invalid_request(client):
    response = client.post('/query', json={})
    assert response.status_code == 400

def test_post_user(client):
    user_data = {"email": "example@example.com", "password": "password", "name": "John Doe"}
    response = client.post('/register', json=user_data)
    assert response.status_code == 200
    assert response.json.get("msg") == "New User Registered!!"
    assert response.json.get("User").get("email") == user_data["email"]
    assert response.json.get("User").get("name") == user_data["name"]
    user_id = response.json.get("User").get("_id")
    yield user_id

def test_post_user_existing_user(client):
    existing_user_data = {"email": "existing@example.com", "password": "password", "name": "Jane Doe"}
    client.post('/register', json=existing_user_data)
    response = client.post('/register', json=existing_user_data)
    assert response.status_code == 400
    assert response.json.get("msg") == "User is already present!!"

def test_login_user(client):
    user_data = {"email": "example@example.com", "password": "password", "name": "John Doe"}
    client.post('/register', json=user_data)

    login_data = {"email": "example@example.com", "password": "password"}
    response = client.post('/login', json=login_data)
    assert response.status_code == 200
    assert response.json.get("msg") == "Login Successful!!"
    assert response.json.get("user").get("email") == login_data["email"]
    assert response.json.get("user").get("name") == user_data["name"]

def test_login_user_wrong_password(client):
    user_data = {"email": "example@example.com", "password": "password", "name": "John Doe"}
    client.post('/register', json=user_data)

    login_data = {"email": "example@example.com", "password": "wrong_password"}
    response = client.post('/login', json=login_data)
    assert response.status_code == 400
    assert response.json.get("msg") == "Password is Wrong!!"

def test_login_user_non_existing_user(client):
    login_data = {"email": "nonexisting@example.com", "password": "password"}
    response = client.post('/login', json=login_data)
    assert response.status_code == 400
    assert response.json.get("msg") == "User not found. Please register!!"

def test_get_chat(client):
    user_data = {"email": "example@example.com", "password": "password", "name": "John Doe"}
    response = client.post('/register', json=user_data)
    user_id = response.json.get("User").get("_id")

    response = client.get(f'/get_chat/{user_id}')
    assert response.status_code == 200
    assert len(response.json.get("chats")) == 0

def test_add_new_chat(client):
    user_data = {"email": "example@example.com", "password": "password", "name": "John Doe"}
    response = client.post('/register', json=user_data)
    user_id = response.json.get("User").get("_id")

    chat_data = {"name": "Chat Room Name", "_id": user_id}
    response = client.post('/add_chat', json=chat_data)
    assert response.status_code == 200

    chat_id = response.json.get("msg")["chatid"]

    response = client.get(f'/get_single_chat/{chat_id}')
    assert response.status_code == 200
    assert response.json.get("chat").get("chat_name") == chat_data["name"]
    assert response.json.get("chat").get("user_id") == user_id

def test_post_query_chat(client):
    user_data = {"email": "example@example.com", "password": "password", "name": "John Doe"}
    response = client.post('/register', json=user_data)
    user_id = response.json.get("User").get("_id")

    chat_data = {"name": "Chat Room Name", "_id": user_id}
    response = client.post('/add_chat', json=chat_data)
    chat_id = response.json.get("msg")["chatid"]

    query_data = {"query": "Your query for the chat goes here."}
    response = client.post(f'/query/{chat_id}', json=query_data)
    assert response.status_code == 200
    assert response.json.get("chat").get("chat_history")[-1].get("msg") == query_data["query"]
    assert response.json.get("chat").get("chat_history")[-2].get("msg")
    yield user_id, chat_id

@pytest.fixture(autouse=True)
def cleanup_test_users_and_chats(request):
    yield
    cleanup_test_data()