// Gestión de actividades — interactividad
//
// Persistido en el backend (GET/POST/DELETE /api/actividades), no en
// localStorage. Requiere sesión iniciada, igual que historial y horario.
// El selector de "Materia" se llena con las clases del semestre más
// reciente registrado en el Horario (proxy razonable de "lo que estoy
// cursando ahora").

(function () {
    "use strict";

    let actividades = [];

    const formActividad = document.getElementById('form-actividad');
    const selectMateria = document.getElementById('act-materia');
    const contenedorActividades = document.getElementById('actividades-container');
    const mensajeVacio = document.getElementById('actividades-vacias');
    const errorBox = document.getElementById('actividad-error');
    const submitBtn = document.getElementById('actividad-submit');

    // 1. Cargar las materias del semestre más reciente del horario ---------

    async function cargarMateriasDelHorario() {
        let horario;
        try {
            horario = await getHorario();
        } catch (err) {
            console.error("No se pudo cargar el horario para llenar el selector de materias:", err);
            return;
        }

        // El semestre "actual" es el de número más alto que ya tenga clases
        // registradas — un semestre recién creado y todavía vacío (ej. el
        // siguiente periodo) no debe dejar el selector sin materias.
        const numerosConClases = Object.entries(horario.semesters || {})
            .filter(([, data]) => (data.classes || []).length > 0)
            .map(([numero]) => Number(numero));
        if (numerosConClases.length === 0) return;

        const semestreActual = String(Math.max(...numerosConClases));
        const clasesSemestre = horario.semesters[semestreActual].classes || [];
        const materiasUnicas = [...new Set(clasesSemestre.map((c) => c.materia))];

        materiasUnicas.forEach((materia) => {
            const option = document.createElement('option');
            option.value = materia;
            option.textContent = materia;
            selectMateria.appendChild(option);
        });
    }

    // 2. Renderizar las tarjetas de actividades -----------------------------

    function renderizarActividades() {
        contenedorActividades.innerHTML = '';

        if (actividades.length === 0) {
            mensajeVacio.classList.remove('d-none');
            return;
        }
        mensajeVacio.classList.add('d-none');

        const ordenadas = [...actividades].sort(
            (a, b) => new Date(a.fecha_limite) - new Date(b.fecha_limite)
        );

        ordenadas.forEach((act) => {
            const fechaObj = new Date(act.fecha_limite);
            const fechaFormateada = fechaObj.toLocaleDateString('es-ES', {
                weekday: 'short', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
            });

            const diasFaltantes = Math.ceil((fechaObj - new Date()) / (1000 * 60 * 60 * 24));
            let colorBorde = 'border-secondary';
            if (diasFaltantes < 0) colorBorde = 'border-danger opacity-75';
            else if (diasFaltantes <= 2) colorBorde = 'border-warning';

            const card = document.createElement('div');
            card.className = 'col-12 col-md-6';
            card.innerHTML = `
                <div class="card h-100 ${colorBorde} bg-dark">
                    <div class="card-header d-flex justify-content-between align-items-center py-2">
                        <small class="text-uppercase fw-bold text-info text-truncate me-2" title="${act.materia}">${act.materia}</small>
                        <button type="button" class="btn-close btn-close-white btn-sm" data-actividad-id="${act.id}" aria-label="Eliminar"></button>
                    </div>
                    <div class="card-body">
                        <p class="card-text mb-2">${act.descripcion}</p>
                        <div class="d-flex flex-column gap-1 small text-body-secondary mt-3">
                            <span><i class="bi bi-clock text-light me-1"></i> ${fechaFormateada}</span>
                            <span><i class="bi bi-box-seam text-light me-1"></i> ${act.modo_entrega}</span>
                        </div>
                    </div>
                    <div class="card-footer border-0 bg-transparent pt-0">
                        <a href="${act.link}" target="_blank" rel="noopener" class="btn btn-outline-light btn-sm w-100">
                            <i class="bi bi-cloud-arrow-up me-1"></i> Abrir link en la nube
                        </a>
                    </div>
                </div>
            `;
            contenedorActividades.appendChild(card);
        });
    }

    // 3. Cargar actividades desde el backend --------------------------------

    async function cargarActividades() {
        actividades = await getActividades();
        renderizarActividades();
    }

    // 4. Crear actividad ------------------------------------------------------

    formActividad.addEventListener('submit', async (event) => {
        event.preventDefault();
        errorBox.classList.add('d-none');

        const datos = {
            materia: selectMateria.value,
            fecha_limite: document.getElementById('act-fecha').value,
            modo_entrega: document.getElementById('act-entrega').value,
            link: document.getElementById('act-link').value,
            descripcion: document.getElementById('act-desc').value,
        };

        submitBtn.disabled = true;
        try {
            await crearActividad(datos);
            formActividad.reset();
            await cargarActividades();
        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.classList.remove('d-none');
        } finally {
            submitBtn.disabled = false;
        }
    });

    // 5. Eliminar actividad -----------------------------------------------

    contenedorActividades.addEventListener('click', async (event) => {
        const btn = event.target.closest('[data-actividad-id]');
        if (!btn) return;
        if (!confirm("¿Seguro que deseas eliminar esta actividad?")) return;

        try {
            await eliminarActividad(btn.dataset.actividadId);
            await cargarActividades();
        } catch (err) {
            alert(err.message);
        }
    });

    // Inicializar -------------------------------------------------------------

    document.addEventListener('DOMContentLoaded', async () => {
        if (!isLoggedIn()) {
            window.location.href = "/index.html";
            return;
        }

        await cargarMateriasDelHorario();
        try {
            await cargarActividades();
        } catch (err) {
            contenedorActividades.innerHTML = `<p class="text-danger">No se pudo conectar con el backend (${err.message}).</p>`;
        }
    });
})();
