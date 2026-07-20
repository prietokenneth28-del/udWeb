import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.database import get_session
from app.models import User
from app.security import hash_password, verify_password, crear_access_token, decodificar_access_token
from app.models import User, UserCreate

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


REGISTER_SECRET = os.getenv("REGISTER_SECRET")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(datos: UserCreate, session: Session = Depends(get_session)):
    if not REGISTER_SECRET or datos.register_secret != REGISTER_SECRET:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Clave de registro incorrecta")

    existente = session.exec(select(User).where(User.username == datos.username)).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ese username ya está registrado")

    nuevo_usuario = User(username=datos.username, hashed_password=hash_password(datos.password))
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return {"id": nuevo_usuario.id, "username": nuevo_usuario.username}


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    usuario = session.exec(select(User).where(User.username == form_data.username)).first()

    if not usuario or not verify_password(form_data.password, usuario.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = crear_access_token(data={"sub": usuario.username})
    return {"access_token": access_token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_access_token(token)
    if payload is None:
        raise credenciales_invalidas

    username = payload.get("sub")
    if username is None:
        raise credenciales_invalidas

    usuario = session.exec(select(User).where(User.username == username)).first()
    if usuario is None:
        raise credenciales_invalidas

    return usuario

