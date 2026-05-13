from fastapi import FastAPI

from app.database import engine
from app.database import Base

from app.models.user import User
from app.routes.user_routes import router as auth_router
from app.routes.post_routes import router as post_router
from app.models.post import Post

from app.models.comment import Comment
from app.routes.comment_routes import router as comment_router
import logging

logging.basicConfig(

    level=logging.INFO,

    format="%(asctime)s - %(levelname)s - %(message)s",

    handlers=[

        logging.FileHandler("app.log"),

        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


app = FastAPI()


# Include routes
app.include_router(auth_router)

app.include_router(post_router)
app.include_router(comment_router)


@app.get("/")
def home():

    return {
        "message": "Blog System Running Successfully"
    }