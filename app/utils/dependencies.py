from fastapi import Depends
from fastapi import HTTPException

from fastapi.security import OAuth2PasswordBearer

from jose import jwt
from jose import JWTError

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User


SECRET_KEY = "mysecretkey"

ALGORITHM = "HS256"


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="login"
)


# Database dependency
def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# Get current logged in user
def get_current_user(

    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):

    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid token"
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_email = payload.get("sub")

        if user_email is None:

            raise credentials_exception

    except JWTError:

        raise credentials_exception


    user = db.query(User).filter(
        User.email == user_email
    ).first()


    if user is None:

        raise credentials_exception


    return user