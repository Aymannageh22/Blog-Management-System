from fastapi import APIRouter
from fastapi import Depends

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

router = APIRouter()

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

    token: str = Depends(oauth2_scheme)
):

    payload = verify_token(token)

    if payload is None:

        return {
            "error": "Invalid token"
        }

    return {
        "message": "Protected route accessed",
        "user_data": payload
    }