from fastapi import FastAPI
from fastapi import Request

from app.database import engine
from app.database import Base

from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment

from app.routes.user_routes import router as auth_router
from app.routes.post_routes import router as post_router
from app.routes.comment_routes import router as comment_router

from app import monitoring

import logging
import time


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


@app.middleware("http")
async def log_requests(

    request: Request,

    call_next
):

    start_time = time.time()

    monitoring.request_count += 1

    response = await call_next(request)

    process_time = time.time() - start_time

    monitoring.total_response_time += process_time

    if response.status_code >= 400:

        monitoring.error_count += 1

    logger.info(

        f"{request.method} "

        f"{request.url.path} "

        f"Status: {response.status_code} "

        f"Completed in: {process_time:.4f}s"
    )

    return response


# Include routes
app.include_router(auth_router)

app.include_router(post_router)

app.include_router(comment_router)


@app.get("/")
def home():

    return {

        "message": "Blog System Running Successfully"
    }


@app.get("/metrics")
def get_metrics():

    average_response_time = 0

    if monitoring.request_count > 0:

        average_response_time = (

            monitoring.total_response_time
            / monitoring.request_count
        )

    return {

        "request_count": monitoring.request_count,

        "error_count": monitoring.error_count,

        "average_response_time": average_response_time,

        "system_status": "healthy"
    }