// api.js — toda la comunicación con el backend vive aquí.
// planEstudios.js llama a estas funciones, no hace fetch() directo.

const API_BASE_URL = "http://127.0.0.1:8000";

let authToken = null; // se guarda en memoria mientras la pestaña esté abierta

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
    return authToken;
}

function isLoggedIn() {
    return authToken !== null;
}

function authHeaders() {
    return authToken ? { "Authorization": `Bearer ${authToken}` } : {};
}