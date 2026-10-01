import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def register(client, name, email, password="Passw0rd!23"):
    return client.post("/register", data={
        "name": name, "email": email,
        "password": password, "confirm_password": password,
    }, follow_redirects=True)


def login(client, email, password="Passw0rd!23"):
    return client.post("/login", data={"email": email, "password": password},
                        follow_redirects=True)
