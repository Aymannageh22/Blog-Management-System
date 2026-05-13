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


def get_token():

    email = f"{uuid.uuid4()}@example.com"

    client.post(

        "/register",

        json={

            "username": "testuser",

            "email": email,

            "password": "123456",

            "role": "author"
        }
    )

    login_response = client.post(

        "/login",

        data={

            "username": email,

            "password": "123456"
        }
    )

    return login_response.json()["access_token"]


def test_create_post():

    token = get_token()

    response = client.post(

        "/posts",

        json={

            "title": "Test Post",

            "content": "Test Content"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 201


def test_get_posts():

    response = client.get("/posts")

    assert response.status_code == 200


def test_get_single_post():

    response = client.get("/posts/1")

    assert response.status_code in [200, 404]


def test_update_post():

    token = get_token()

    client.post(

        "/posts",

        json={

            "title": "Old Title",

            "content": "Old Content"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    posts_response = client.get("/posts?limit=100")

    posts = posts_response.json()

    my_post = posts[-1]

    response = client.put(

        f"/posts/{my_post['id']}",

        json={

            "title": "New Title",

            "content": "New Content"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

def test_delete_post():

    token = get_token()

    client.post(

        "/posts",

        json={

            "title": "Delete Me",

            "content": "Delete Content"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    posts_response = client.get("/posts?limit=100")

    posts = posts_response.json()

    my_post = posts[-1]

    response = client.delete(

        f"/posts/{my_post['id']}",

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

def test_get_non_existing_post():

    response = client.get("/posts/999999")

    assert response.status_code == 404

def test_delete_post_without_token():

    token = get_token()

    client.post(

        "/posts",

        json={

            "title": "Protected Post",

            "content": "Protected Content"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    posts_response = client.get("/posts?limit=100")

    posts = posts_response.json()

    my_post = posts[-1]

    response = client.delete(

        f"/posts/{my_post['id']}"
    )

    assert response.status_code == 401