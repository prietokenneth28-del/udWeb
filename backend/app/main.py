from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from app.models import Course, User
from app.database import crear_tablas, get_session
from app.auth import router as auth_router, get_current_user

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Plan de Estudios API")

origenes_permitidos = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_permitidos,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
# ... el resto de tu código sigue igual
@app.on_event("startup")
def on_startup():
    crear_tablas()

@app.get("/courses", response_model=list[Course])
def listar_cursos(session: Session = Depends(get_session)):
    return session.exec(select(Course)).all()

@app.get("/courses/{course_id}", response_model=Course)
def obtener_curso(course_id: str, session: Session = Depends(get_session)):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    return course

@app.post("/courses", response_model=Course, status_code=201)
def crear_curso(
    course: Course,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    existente = session.get(Course, course.id)
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un curso con ese id")
    session.add(course)
    session.commit()
    session.refresh(course)
    return course

@app.put("/courses/{course_id}", response_model=Course)
def actualizar_curso(
    course_id: str,
    datos: Course,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    datos_dict = datos.model_dump(exclude={"id"})
    for clave, valor in datos_dict.items():
        setattr(course, clave, valor)
    session.add(course)
    session.commit()
    session.refresh(course)
    return course

@app.delete("/courses/{course_id}", status_code=204)
def eliminar_curso(
    course_id: str,
    session: Session = Depends(get_session),
    usuario_actual: User = Depends(get_current_user),
):
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    session.delete(course)
    session.commit()