# Script de seed. Corre con: python seed_courses.py (dentro del venv, con
# el servidor de PostgreSQL disponible y la migración de Alembic aplicada).
#
# Es IDEMPOTENTE: si corres el script dos veces, no duplica ciclos,
# semestres, materias, ni el historial de materias ya aprobadas.

from sqlmodel import Session, select
from app.database import engine
from app.models import CicloAcademico, Semestre, Materia, HistorialAcademico

CICLOS = [
    ("tec", "Ciclo Tecnológico"),
    ("ing", "Ciclo de Ingeniería"),
]

# (id, nombre, codigo, creditos, cycle, semester, categoria, tipo, aprobada, prereq)
MATERIAS_RAW = [
    ('tec-1', 'CÁLCULO DIFERENCIAL', '1', 4.0, 'tec', 1, 'fisica-matematica', 'OB', True, []),
    ('tec-2', 'CÁTEDRA FRANCISCO JOSÉ DE CALDAS', '4', 1.0, 'tec', 1, 'lenguaje-sociales', 'OC', True, []),
    ('tec-3', 'ÁLGEBRA LINEAL', '9', 3.0, 'tec', 1, 'fisica-matematica', 'OB', True, []),
    ('tec-4', 'PRODUCCIÓN Y COMPRENSIÓN DE TEXTOS I', '1054', 3.0, 'tec', 1, 'lenguaje-sociales', 'OC', True, []),
    ('tec-5', 'ÉTICA Y SOCIEDAD', '1075', 2.0, 'tec', 1, 'lenguaje-sociales', 'OC', True, []),
    ('tec-6', 'DIBUJO TÉCNICO', '1411', 2.0, 'tec', 1, 'fabricacion', 'OB', True, []),
    ('tec-7', 'INTRODUCCIÓN A LA MECÁNICA INDUSTRIAL', '19701', 1.0, 'tec', 1, 'fabricacion', 'OB', True, []),
    ('tec-8', 'SEGUNDA LENGUA I - INGLÉS', '9901', 2.0, 'tec', 1, 'lenguaje-sociales', 'OC', True, []),
    ('tec-9', 'FÍSICA I: MECÁNICA NEWTONIANA', '3', 3.0, 'tec', 2, 'fisica-matematica', 'OB', True, []),
    ('tec-10', 'CÁLCULO INTEGRAL', '7', 3.0, 'tec', 2, 'fisica-matematica', 'OB', True, ['tec-1']),
    ('tec-11', 'CÁTEDRA DEMOCRACIA Y CIUDADANÍA', '12', 1.0, 'tec', 2, 'lenguaje-sociales', 'OC', True, []),
    ('tec-12', 'PRODUCCIÓN Y COMPRENSIÓN DE TEXTOS II', '1056', 2.0, 'tec', 2, 'lenguaje-sociales', 'OC', True, []),
    ('tec-13', 'MATERIALES METÁLICOS', '19702', 3.0, 'tec', 2, 'fabricacion', 'OB', True, []),
    ('tec-14', 'DIBUJO DE ELEMENTOS DE MÁQUINAS', '19703', 2.0, 'tec', 2, 'fabricacion', 'OB', True, []),
    ('tec-15', 'FUNDAMENTOS DE PROGRAMACIÓN', '19704', 1.0, 'tec', 2, 'diseno-programacion', 'OB', True, []),
    ('tec-16', 'SEGUNDA LENGUA II - INGLÉS', '9903', 2.0, 'tec', 2, 'lenguaje-sociales', 'OC', True, []),
    ('tec-17', 'FÍSICA II: ELECTROMAGNETISMO', '13', 3.0, 'tec', 3, 'fisica-matematica', 'OB', True, []),
    ('tec-18', 'CIENCIA TECNOLOGÍA Y SOCIEDAD', '1060', 2.0, 'tec', 3, 'lenguaje-sociales', 'OC', True, []),
    ('tec-19', 'ESTATICA', '1421', 3.0, 'tec', 3, 'diseno-programacion', 'OB', True, []),
    ('tec-20', 'MATERIALES POLIMÉRICOS Y COMPUESTOS', '19705', 2.0, 'tec', 3, 'fabricacion', 'OB', True, []),
    ('tec-21', 'DIBUJO DE TALLER INDUSTRIAL', '19706', 2.0, 'tec', 3, 'fabricacion', 'OB', True, []),
    ('tec-22', 'METROLOGÍA DIMENSIONAL', '19707', 1.0, 'tec', 3, 'fabricacion', 'OB', True, []),
    ('tec-23', 'SEGUNDA LENGUA III - INGLÉS', '9903', 2.0, 'tec', 3, 'lenguaje-sociales', 'OC', True, []),
    ('tec-24', 'PROCESOS DE MECANIZADO I', '19708', 3.0, 'tec', 3, 'fabricacion', 'OB', True, []),
    ('tec-25', 'CÁLCULO MULTIVARIADO', '16', 3.0, 'tec', 4, 'fisica-matematica', 'OB', True, []),
    ('tec-26', 'MECANICA DE FLUIDOS', '1433', 3.0, 'tec', 4, 'energias', 'OB', True, []),
    ('tec-27', 'RESISTENCIA DE MATERIALES', '1436', 3.0, 'tec', 4, 'diseno-programacion', 'OB', True, []),
    ('tec-28', 'PROCESOS DE MECANIZADO II', '19709', 3.0, 'tec', 4, 'fabricacion', 'OB', True, []),
    ('tec-29', 'DINÁMICA DE MECANISMOS', '19710', 3.0, 'tec', 4, 'fabricacion', 'OB', True, []),
    ('tec-30', 'FÍSICA III: ONDAS Y FÍSICA MODERNA', '1428', 3.0, 'tec', 4, 'fisica-matematica', 'CP', True, []),
    ('tec-31', 'ECUACIONES DIFERENCIALES', '88', 3.0, 'tec', 5, 'fisica-matematica', 'CP', True, []),
    ('tec-32', 'TERMODINÁMICA', '1426', 3.0, 'tec', 5, 'energias', 'OB', True, []),
    ('tec-33', 'MANTENIMIENTO DE MÁQUINAS', '19711', 2.0, 'tec', 5, 'fisica-matematica', 'OB', True, []),
    ('tec-34', 'PROCESOS DE CONFORMADO', '19712', 3.0, 'tec', 5, 'fabricacion', 'OB', True, []),
    ('tec-35', 'ELEMENTOS DE MÁQUINAS I', '19713', 3.0, 'tec', 5, 'diseno-programacion', 'OB', True, []),
    ('tec-36', 'ELECTIVA INTRISECA 1', '-', 2.0, 'tec', 5, 'electivas-grado', 'EI', True, []),
    ('tec-37', 'ELECTIVA INTRISECA 2', '-', 2.0, 'tec', 5, 'electivas-grado', 'EI', True, []),
    ('tec-38', 'TRABAJO DE GRADO TECNOLÓGICO', '1446', 2.0, 'tec', 6, 'electivas-grado', 'OB', True, []),
    ('tec-39', 'DISEÑO DE PROCESOS DE FABRICACIÓN', '19714', 3.0, 'tec', 6, 'fabricacion', 'OB', True, []),
    ('tec-40', 'ELEMENTOS DE MÁQUINAS II', '19715', 3.0, 'tec', 6, 'diseno-programacion', 'OB', True, []),
    ('tec-41', 'MÁQUINAS ELÉCTRICAS', '19716', 2.0, 'tec', 6, 'energias', 'OB', True, []),
    ('tec-42', 'MÁQUINAS HIDRÁULICAS', '1824', 3.0, 'tec', 6, 'energias', 'CP', True, []),
    ('tec-43', 'ELECTIVA INTRISECA 3', '-', 2.0, 'tec', 6, 'electivas-grado', 'EI', True, []),
    ('tec-44', 'ELECTIVA EXTRINSECA', '-', 2.0, 'tec', 6, 'electivas-grado', 'EE', True, []),
    ('ing-1', 'PROBABILIDAD Y ESTADÍSTICA', '19801', 2.0, 'ing', 7, 'fisica-matematica', 'OB', False, []),
    ('ing-2', 'TERMODINÁMICA APLICADA', '19804', 3.0, 'ing', 7, 'energias', 'OB', False, []),
    ('ing-3', 'DISEÑO POR ELEMENTOS FINITOS', '1817', 3.0, 'ing', 7, 'diseno-programacion', 'OB', False, []),
    ('ing-4', 'ASEGURAMIENTO METROLÓGICO', '19802', 2.0, 'ing', 7, 'fabricacion', 'OB', False, []),
    ('ing-5', 'CÁTEDRA DE CONTEXTO', '1082', 1.0, 'ing', 7, 'lenguaje-sociales', 'OC', False, []),
    ('ing-6', 'PRODUCCIÓN DE TEXTOS CIENTÍFICOS', '19803', 2.0, 'ing', 7, 'lenguaje-sociales', 'OC', False, []),
    ('ing-7', 'DISEÑO EXPERIMENTAL', '19806', 2.0, 'ing', 8, 'fisica-matematica', 'OB', False, []),
    ('ing-8', 'TRANSFERENCIA DE CALOR', '1818', 3.0, 'ing', 8, 'energias', 'OB', False, []),
    ('ing-9', 'MANTENIMIENTO DE EQUIPOS INDUSTRIALES', '19805', 3.0, 'ing', 8, 'fisica-matematica', 'OB', False, []),
    ('ing-10', 'DISEÑO DE MÁQUINAS', '1823', 3.0, 'ing', 8, 'diseno-programacion', 'OB', False, []),
    ('ing-11', 'ELECTIVA EXTRÍNSECA', '-', 2.0, 'ing', 8, 'electivas-grado', 'EE', False, []),
    ('ing-12', 'SISTEMAS DINÁMICOS Y CONTROL', '1805', 3.0, 'ing', 8, 'diseno-programacion', 'OB', False, []),
    ('ing-13', 'TRABAJO DE GRADO I', '1670', 2.0, 'ing', 9, 'electivas-grado', 'OB', False, []),
    ('ing-14', 'MÁQUINAS TÉRMICAS', '1838', 3.0, 'ing', 9, 'energias', 'OB', False, []),
    ('ing-15', 'INGENIERÍA ECONÓMICA', '1619', 3.0, 'ing', 9, 'lenguaje-sociales', 'OB', False, []),
    ('ing-16', 'ELECTIVA DE PROFUNDIZACIÓN I', '-', 2.0, 'ing', 9, 'electivas-grado', 'EI', False, []),
    ('ing-17', 'ELECTIVA DE PROFUNDIZACIÓN III', '-', 2.0, 'ing', 9, 'electivas-grado', 'EI', False, []),
    ('ing-18', 'INGENIERÍA DE MANUFACTURA', '19807', 3.0, 'ing', 9, 'fabricacion', 'OB', False, []),
    ('ing-19', 'ELECTIVA DE PROFUNDIZACIÓN II', '-', 2.0, 'ing', 9, 'electivas-grado', 'EI', False, []),
    ('ing-20', 'TRABAJO DE GRADO II', '1831', 2.0, 'ing', 10, 'electivas-grado', 'OB', False, []),
    ('ing-21', 'ELECTIVA DE PROFUNDIZACIÓN V', '-', 3.0, 'ing', 10, 'electivas-grado', 'EI', False, []),
    ('ing-22', 'FORMULACIÓN Y EVALUACIÓN DE PROYECTOS', '19808', 3.0, 'ing', 10, 'lenguaje-sociales', 'OB', False, []),
    ('ing-23', 'ELECTIVA DE PROFUNDIZACIÓN IV', '-', 2.0, 'ing', 10, 'electivas-grado', 'EI', False, []),
]


def seed():
    with Session(engine) as session:
        ciclos_insertados = 0
        for ciclo_id, nombre in CICLOS:
            if not session.get(CicloAcademico, ciclo_id):
                session.add(CicloAcademico(id=ciclo_id, nombre=nombre))
                ciclos_insertados += 1
        session.commit()

        # id de semestre por (ciclo, numero)
        semestre_id_por_clave: dict[tuple[str, int], int] = {}
        existentes = session.exec(select(Semestre)).all()
        for s in existentes:
            semestre_id_por_clave[(s.ciclo_id, s.numero)] = s.id

        semestres_insertados = 0
        claves_necesarias = sorted({(cycle, semester) for (_, _, _, _, cycle, semester, *_ ) in MATERIAS_RAW})
        for ciclo_id, numero in claves_necesarias:
            if (ciclo_id, numero) not in semestre_id_por_clave:
                nuevo = Semestre(numero=numero, ciclo_id=ciclo_id)
                session.add(nuevo)
                session.commit()
                session.refresh(nuevo)
                semestre_id_por_clave[(ciclo_id, numero)] = nuevo.id
                semestres_insertados += 1

        materias_insertadas = 0
        materias_saltadas = 0
        historial_insertado = 0
        for materia_id, nombre, codigo, creditos, ciclo_id, numero, categoria, tipo, aprobada, prereq in MATERIAS_RAW:
            existente = session.get(Materia, materia_id)
            if existente:
                materias_saltadas += 1
            else:
                nueva_materia = Materia(
                    id=materia_id,
                    nombre=nombre,
                    codigo=codigo,
                    creditos=creditos,
                    tipo=tipo,
                    categoria=categoria,
                    semestre_id=semestre_id_por_clave[(ciclo_id, numero)],
                )
                nueva_materia.prereq = prereq
                session.add(nueva_materia)
                materias_insertadas += 1

            if aprobada:
                ya_tiene_historial = session.exec(
                    select(HistorialAcademico).where(HistorialAcademico.materia_id == materia_id)
                ).first()
                if not ya_tiene_historial:
                    session.add(HistorialAcademico(
                        materia_id=materia_id,
                        periodo=None,
                        nota_final=None,
                        estado="Aprobada",
                    ))
                    historial_insertado += 1

        session.commit()

    print(f"Ciclos insertados: {ciclos_insertados}")
    print(f"Semestres insertados: {semestres_insertados}")
    print(f"Materias insertadas: {materias_insertadas} | Ya existían (saltadas): {materias_saltadas}")
    print(f"Registros de historial insertados: {historial_insertado}")


if __name__ == "__main__":
    seed()
