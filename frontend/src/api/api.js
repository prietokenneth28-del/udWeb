// api.js — toda la comunicación con el backend vive aquí.
// planEstudios.js llama a estas funciones, no hace fetch() directo.

const API_BASE_URL = "https://udweb-d5s8.onrender.com";

// El login vive en una página aparte (index.html) y el resto de páginas
// (pages/*.html) se navegan con recargas completas, así que el token no
// puede quedar solo en una variable en memoria: se persiste en
// sessionStorage (dura mientras la pestaña esté abierta, se borra al
// cerrarla) y cada página lo recupera al cargar api.js.
let authToken = sessionStorage.getItem("authToken");
let authUsername = sessionStorage.getItem("authUsername");

async function login(username, password) {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    const res = await fetch(`${API_BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body,
    });

    if (!res.ok) {
        throw new Error("Usuario o contraseña incorrectos");
    }

    const data = await res.json();
    authToken = data.access_token;
    authUsername = username;
    sessionStorage.setItem("authToken", authToken);
    sessionStorage.setItem("authUsername", authUsername);
    return authToken;
}

function logout() {
    authToken = null;
    authUsername = null;
    sessionStorage.removeItem("authToken");
    sessionStorage.removeItem("authUsername");
}

function isLoggedIn() {
    return authToken !== null;
}

function getUsername() {
    return authUsername;
}

function authHeaders() {
    return authToken ? { "Authorization": `Bearer ${authToken}` } : {};
}

async function getPlanEstudios() {
    const res = await fetch(`${API_BASE_URL}/api/plan-estudios`);
    if (!res.ok) throw new Error("No se pudo cargar el plan de estudios");
    return res.json();
}

async function getHistorial() {
    const res = await fetch(`${API_BASE_URL}/api/historial`, { headers: authHeaders() });
    if (!res.ok) throw new Error("No se pudo cargar el historial académico");
    return res.json();
}

async function getEstadisticas() {
    const res = await fetch(`${API_BASE_URL}/api/estadisticas`, { headers: authHeaders() });
    if (!res.ok) throw new Error("No se pudo cargar las estadísticas");
    return res.json();
}

async function crearHistorial(materiaId, datos) {
    const res = await fetch(`${API_BASE_URL}/api/historial`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ materia_id: materiaId, ...datos }),
    });
    if (!res.ok) throw new Error("No se pudo registrar el historial");
    return res.json();
}

async function actualizarHistorial(historialId, datos) {
    const res = await fetch(`${API_BASE_URL}/api/historial/${historialId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(datos),
    });
    if (!res.ok) throw new Error("No se pudo actualizar el historial");
    return res.json();
}

async function eliminarHistorial(historialId) {
    const res = await fetch(`${API_BASE_URL}/api/historial/${historialId}`, {
        method: "DELETE",
        headers: authHeaders(),
    });
    if (!res.ok) throw new Error("No se pudo eliminar el historial");
}