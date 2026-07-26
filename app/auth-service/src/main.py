from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env", override=True)

from db.connection import get_db, User, Session as SessionModel, Base, engine
from models.user import UserCreate, UserLogin, TokenResponse, UserResponse

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRATION", "3600"))

app = FastAPI(title="Auth Service", version="1.0.0")
security = HTTPBearer()


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "sub": str(to_encode.get("sub", ""))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            print(f"[AUTH] Invalid token payload: user_id is None, token={token[:20]}...")
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError as e:
        print(f"[AUTH] JWT decode error: {e}, token={token[:20]}...")
        raise HTTPException(status_code=401, detail="Token inválido")

    session = db.query(SessionModel).filter(SessionModel.token == token).first()
    if session is None:
        print(f"[AUTH] Session not found for token={token[:20]}..., user_id={user_id}")
    elif session.expires_at < datetime.utcnow():
        print(f"[AUTH] Session expired: expires_at={session.expires_at}, now={datetime.utcnow()}")
    if session is None or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Token expirado")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        print(f"[AUTH] User not found or inactive: user_id={user_id}, user={user}")
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    return user


@app.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="El correo ya está en uso")

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"sub": new_user.id})
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    db_session = SessionModel(user_id=new_user.id, token=token, expires_at=expires_at)
    db.add(db_session)
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={"id": new_user.id, "username": new_user.username, "email": new_user.email},
    )


@app.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Usuario inactivo")

    token = create_access_token({"sub": user.id})
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    db_session = SessionModel(user_id=user.id, token=token, expires_at=expires_at)
    db.add(db_session)
    db.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user={"id": user.id, "username": user.username, "email": user.email},
    )


@app.get("/verify", response_model=UserResponse)
def verify_token(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
    )


@app.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    db_session = db.query(SessionModel).filter(SessionModel.token == token).first()
    if db_session:
        db.delete(db_session)
        db.commit()
    return {"message": "Sesión cerrada correctamente"}