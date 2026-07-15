// Cliente HTTP para el backend FastAPI (ver /backend).
// Si corres el backend en otro host/puerto, cambia API_BASE_URL.
const API_BASE_URL = "http://127.0.0.1:8000";

const Api = {
    async getPlanEstudios() {
        return request("/api/plan-estudios");
    },

    async getHistorial() {
        return request("/api/historial");
    },

    async getEstadisticas() {
        return request("/api/estadisticas");
    },

    async crearHistorial({ materiaId, periodo, notaFinal }) {
        return request("/api/historial", {
            method: "POST",
            body: { materia_id: materiaId, periodo, nota_final: notaFinal },
        });
    },

    async actualizarHistorial(historialId, { periodo, notaFinal }) {
        return request(`/api/historial/${historialId}`, {
            method: "PUT",
            body: { periodo, nota_final: notaFinal },
        });
    },

    async eliminarHistorial(historialId) {
        return request(`/api/historial/${historialId}`, { method: "DELETE" });
    },
};

async function request(path, { method = "GET", body } = {}) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            method,
            headers: body ? { "Content-Type": "application/json" } : undefined,
            body: body ? JSON.stringify(body) : undefined,
        });
    } catch (err) {
        throw new Error(
            `No se pudo conectar con el backend en ${API_BASE_URL}. ` +
            `¿Está corriendo "uvicorn app.main:app --reload"? (${err.message})`
        );
    }

    if (!response.ok) {
        let detail = response.statusText;
        try {
            const data = await response.json();
            detail = data.detail || detail;
        } catch (_) {
            // el cuerpo no era JSON (p. ej. 204 No Content en errores raros)
        }
        throw new Error(`${response.status} ${detail}`);
    }

    if (response.status === 204) return null;
    return response.json();
}
