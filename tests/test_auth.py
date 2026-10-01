from tests.conftest import register, login


def test_register_creates_account(client):
    resp = register(client, "Abhinav Kumar", "abhinav@example.com")
    assert "Account created" in resp.get_data(as_text=True)


def test_duplicate_email_rejected(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    resp = client.post("/register", data={
        "name": "Someone Else", "email": "abhinav@example.com",
        "password": "Passw0rd!23", "confirm_password": "Passw0rd!23",
    })
    assert b"already exists" in resp.data


def test_login_success_redirects_to_dashboard(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    resp = login(client, "abhinav@example.com")
    assert "Your documents" in resp.get_data(as_text=True)


def test_login_wrong_password_fails(client):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    resp = login(client, "abhinav@example.com", password="wrongpassword")
    assert "Invalid email or password" in resp.get_data(as_text=True)


def test_account_locks_after_repeated_failures(client, app):
    register(client, "Abhinav Kumar", "abhinav@example.com")
    max_attempts = app.config["MAX_FAILED_LOGIN_ATTEMPTS"]
    for _ in range(max_attempts):
        login(client, "abhinav@example.com", password="wrongpassword")
    resp = login(client, "abhinav@example.com", password="Passw0rd!23")
    assert "locked" in resp.get_data(as_text=True).lower()


def test_logout_requires_login(client):
    resp = client.get("/logout", follow_redirects=True)
    assert "Please log in" in resp.get_data(as_text=True)


def test_dashboard_requires_login(client):
    resp = client.get("/dashboard", follow_redirects=True)
    assert "Please log in" in resp.get_data(as_text=True)
