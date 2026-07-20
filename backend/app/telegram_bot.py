import os

import httpx
from sqlmodel import Session, select

from app.models import ClaseHorario, SemestreHorario

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DIAS = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
}


def _semestre_activo(session: Session) -> int | None:
    override = os.getenv("HORARIO_SEMESTRE_ACTIVO")
    if override:
        return int(override)

    numero = session.exec(
        select(SemestreHorario.numero).order_by(SemestreHorario.numero.desc())
    ).first()
    return numero


def _formatear_hora(valor: int) -> str:
    return f"{valor:02d}:00"


def construir_mensaje_horario_hoy(session: Session, dia: int) -> str:
    nombre_dia = DIAS.get(dia)
    if nombre_dia is None:
        return "Hoy es domingo, no tienes clases 🎉"

    semestre_numero = _semestre_activo(session)
    if semestre_numero is None:
        return "No hay ningún semestre configurado en el horario todavía."

    clases = session.exec(
        select(ClaseHorario)
        .where(ClaseHorario.semestre_numero == semestre_numero)
        .where(ClaseHorario.dia == dia)
        .order_by(ClaseHorario.hora_inicio)
    ).all()

    if not clases:
        return f"📅 {nombre_dia}: no tienes clases hoy 🎉"

    lineas = [f"📅 Clases de hoy ({nombre_dia}):", ""]
    for clase in clases:
        rango = f"{_formatear_hora(clase.hora_inicio)}–{_formatear_hora(clase.hora_fin)}"
        linea = f"• {rango}  {clase.materia}"
        if clase.aula:
            linea += f" (aula {clase.aula})"
        lineas.append(linea)

    return "\n".join(lineas)


def enviar_mensaje_telegram(texto: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en el entorno")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    respuesta = httpx.post(
        url,
        json={"chat_id": TELEGRAM_CHAT_ID, "text": texto},
        timeout=10,
    )
    respuesta.raise_for_status()
