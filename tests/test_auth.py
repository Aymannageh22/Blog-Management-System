import sys
import os
import uuid

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_register_user():

    random_email = f"{uuid.uuid4()}@example.com"

    response = client.post(

        "/register",

        json={

            "username": "testuser",

            "email": random_email,

            "password": "123456",

            "role": "author"
        }
    )

    assert response.status_code == 201


def test_login_user():

    random_email = f"{uuid.uuid4()}@example.com"

    client.post(

        "/register",

        json={

            "username": "testuser",

            "email": random_email,

            "password": "123456",

            "role": "author"
        }
    )

    response = client.post(

        "/login",

        data={

            "username": random_email,

            "password": "123456"
        }
    )

    assert response.status_code == 200

    assert "access_token" in response.json()


def test_protected_route_without_token():

    response = client.get(
        "/profile"
    )

    assert response.status_code == 401


def test_protected_route_with_token():

    random_email = f"{uuid.uuid4()}@example.com"

    client.post(

        "/register",

        json={

            "username": "testuser",

            "email": random_email,

            "password": "123456",

            "role": "author"
        }
    )

    login_response = client.post(

        "/login",

        data={

            "username": random_email,

            "password": "123456"
        }
    )

    token = login_response.json()["access_token"]

    response = client.get(

        "/profile",

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

def test_login_wrong_password():

    random_email = f"{uuid.uuid4()}@example.com"

    client.post(

        "/register",

        json={

            "username": "testuser",

            "email": random_email,

            "password": "123456",

            "role": "author"
        }
    )

    response = client.post(

        "/login",

        data={

            "username": random_email,

            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401