from fastapi import FastAPI, HTTPException
from app.models import Course
from app.data import courses_db

app = FastAPI(title="Plan de Estudios API")

@app.get("/courses", response_model=list[Course])
def listar_cursos():
    return courses_db

@app.get("/courses/{course_id}", response_model=Course)
def obtener_curso(course_id: str):
    for course in courses_db:
        if course.id == course_id:
            return course
    raise HTTPException(status_code=404, detail="Curso no encontrado")

@app.post("/courses", response_model=Course, status_code=201)
def crear_curso(course: Course):
    for c in courses_db:
        if c.id == course.id:
            raise HTTPException(status_code=400, detail="Ya existe un curso con ese id")
    courses_db.append(course)
    return course

@app.put("/courses/{course_id}", response_model=Course)
def actualizar_curso(course_id: str, datos: Course):
    for i, c in enumerate(courses_db):
        if c.id == course_id:
            courses_db[i] = datos
            return datos
    raise HTTPException(status_code=404, detail="Curso no encontrado")

@app.delete("/courses/{course_id}", status_code=204)
def eliminar_curso(course_id: str):
    for i, c in enumerate(courses_db):
        if c.id == course_id:
            courses_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Curso no encontrado")