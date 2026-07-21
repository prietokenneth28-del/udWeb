import os
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from sqlmodel import Session, select

from app.models import ClaseHorario, SemestreHorario

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_WEBHOOK_SECRET = os.getenv("TELEGRAM_WEBHOOK_SECRET")

ZONA_HORARIA = ZoneInfo("America/Bogota")

DIAS = {
    1: "Lunes",
    2: "Martes",
    3: "Miércoles",
    4: "Jueves",
    5: "Viernes",
    6: "Sábado",
}


def isoweekday_hoy() -> int:
    return datetime.now(ZONA_HORARIA).isoweekday()  # 1=Lunes .. 7=Domingo


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


def enviar_mensaje_telegram(texto: str, chat_id: str | None = None) -> None:
    destino = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not destino:
        raise RuntimeError("Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en el entorno")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    respuesta = httpx.post(
        url,
        json={"chat_id": destino, "text": texto},
        timeout=10,
    )
    respuesta.raise_for_status()


def responder_actualizacion_telegram(session: Session, update: dict) -> None:
    mensaje = update.get("message") or update.get("edited_message")
    if not mensaje:
        return

    chat_id = mensaje.get("chat", {}).get("id")
    if chat_id is None:
        return

    # Solo respondemos al chat configurado, para evitar que terceros usen el bot.
    if TELEGRAM_CHAT_ID and str(chat_id) != str(TELEGRAM_CHAT_ID):
        return

    texto_respuesta = construir_mensaje_horario_hoy(session, isoweekday_hoy())
    enviar_mensaje_telegram(texto_respuesta, chat_id=chat_id)
