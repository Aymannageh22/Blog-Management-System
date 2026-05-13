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


def create_post(token):

    client.post(

        "/posts",

        json={

            "title": "Test Post",

            "content": "Test Content"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    posts_response = client.get("/posts?limit=100")

    posts = posts_response.json()

    return posts[-1]["id"]


def test_create_comment():

    token = get_token()

    post_id = create_post(token)

    response = client.post(

        f"/posts/{post_id}/comments",

        json={

            "content": "Test Comment"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200


def test_delete_comment():

    token = get_token()

    post_id = create_post(token)

    client.post(

        f"/posts/{post_id}/comments",

        json={

            "content": "Delete Comment"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    response = client.get(f"/posts/{post_id}")

    comments = response.json()["comments"]

    comment_id = comments[-1]["id"]

    delete_response = client.delete(

        f"/comments/{comment_id}",

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert delete_response.status_code == 200


def test_create_comment_without_token():

    token = get_token()

    post_id = create_post(token)

    response = client.post(

        f"/posts/{post_id}/comments",

        json={

            "content": "Unauthorized Comment"
        }
    )

    assert response.status_code == 401


def test_reply_to_comment():

    token = get_token()

    post_id = create_post(token)

    client.post(

        f"/posts/{post_id}/comments",

        json={

            "content": "Parent Comment"
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    response = client.get(f"/posts/{post_id}")

    comments = response.json()["comments"]

    parent_comment_id = comments[-1]["id"]

    reply_response = client.post(

        f"/posts/{post_id}/comments",

        json={

            "content": "Reply Comment",

            "parent_comment_id": parent_comment_id
        },

        headers={

            "Authorization": f"Bearer {token}"
        }
    )

    assert reply_response.status_code == 200