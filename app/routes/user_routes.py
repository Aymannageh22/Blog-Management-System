from fastapi import APIRouter
from fastapi import Depends
from fastapi import File, UploadFile
import os
import shutil
import uuid

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user_schema import UserCreate
from app.auth.hashing import hash_password

from fastapi.security import OAuth2PasswordBearer
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.jwt_handler import verify_token
from fastapi import HTTPException
from fastapi import status
import logging

from app.auth.hashing import verify_password
from app.auth.jwt_handler import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(

    tags=["Users"]
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)

print("AUTH ROUTES LOADED")


# Database session dependency
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# Register new user
@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register_user(

    user: UserCreate,

    db: Session = Depends(get_db)
):

    if user.role not in ["reader", "author"]:

        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )


    # Create new user object
    new_user = User(

        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )

    # Add user to database
    db.add(new_user)

    # Save changes
    db.commit()

    logger.info(
        f"New user registered: {new_user.username}"
    )

    # Refresh object
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }


@router.post("/login")
def login(

    request: OAuth2PasswordRequestForm = Depends(),

    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == request.username
    ).first()


    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email"
        )


    if not verify_password(
        request.password,
        user.password
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid password"
        )


    access_token = create_access_token(
        data={
            "sub": user.email
        }
    )

    logger.info(
        f"User logged in: {user.username}"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/profile")
def get_profile(

    token: str = Depends(oauth2_scheme),

    db: Session = Depends(get_db)
):

    payload = verify_token(token)

    if payload is None:

        raise HTTPException(

            status_code=401,

            detail="Invalid token"
        )

    user = db.query(User).filter(

        User.email == payload.get("sub")

    ).first()


    if not user:

        raise HTTPException(

            status_code=404,

            detail="User not found"
        )


    return {

        "message": "Protected route accessed",

        "user_data": payload,

        "username": user.username if user else None,

        "role": user.role if user else None,
        
        "profile_image": user.profile_image if user else None
    }

UPLOAD_DIR = "static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-profile-image")
async def upload_profile_image(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG and PNG are allowed.")

    # Validate file size (approximate using content length if available, but usually done via reading)
    # We'll read the first 5MB. If there's more, it's too big.
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB.")

    # Generate unique filename
    ext = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # Save the file
    with open(file_path, "wb") as f:
        f.write(contents)

    # Update user in DB
    image_url = f"/static/uploads/{unique_filename}"
    user.profile_image = image_url
    db.commit()

    logger.info(f"User {user.username} uploaded a new profile image: {unique_filename}")

    return {"message": "Profile image updated successfully", "profile_image": image_url}