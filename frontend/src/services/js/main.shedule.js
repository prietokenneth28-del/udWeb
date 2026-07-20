// Horario — interactividad
//
// La tabla se construye a partir de lo que devuelve el backend
// (GET /api/horario), no de un archivo estático. Crear, editar y borrar
// clases/semestres se hace con los modales del HTML, que llaman a
// crearClaseHorario/actualizarClaseHorario/eliminarClaseHorario y
// crearSemestreHorario/eliminarSemestreHorario (api.js). Requiere sesión
// iniciada: la página entera es información personal, no un catálogo.

document.addEventListener('DOMContentLoaded', async function () {
    "use strict";

    if (!isLoggedIn()) {
        window.location.href = "/index.html";
        return;
    }

    const DIAS_TABLA = [1, 2, 3, 4, 5, 6]; // Lunes..Sábado, en el orden de las columnas
    const DIAS_SEMANA = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
    const HORA_INICIO_TABLA = 6;
    const HORA_FIN_TABLA = 22;

    let SCHEDULE = { semesters: {} };
    let claseSeleccionada = null; // id de la clase que se está editando, o null si es nueva

    const select = document.getElementById('semestreSelect');
    const table = document.querySelector('.table-horario');
    const tableContainer = document.getElementById('scheduleTableContainer');
    const noScheduleMessage = document.getElementById('noScheduleMessage');
    const contenedorHoy = document.getElementById('clasesHoyContainer');
    const tituloHoy = document.getElementById('tituloHoy');

    const claseModalEl = document.getElementById('claseModal');
    const claseModal = new bootstrap.Modal(claseModalEl);
    const semestreModal = new bootstrap.Modal(document.getElementById('semestreModal'));

    function pad2(n) {
        return String(n).padStart(2, "0");
    }

    // --- Carga de datos desde el backend ---------------------------------

    async function cargarHorario() {
        SCHEDULE = await getHorario();
    }

    // --- Construcción del <select> a partir de SCHEDULE.semesters -------

    function poblarSelectSemestres(mantenerSeleccion) {
        const previo = mantenerSeleccion ? select.value : null;
        select.innerHTML = "";
        const claves = Object.keys(SCHEDULE.semesters).sort((a, b) => Number(a) - Number(b));
        claves.forEach((clave) => {
            const opt = document.createElement("option");
            opt.value = clave;
            opt.textContent = SCHEDULE.semesters[clave].label || `Semestre ${clave}`;
            select.appendChild(opt);
        });
        if (previo && claves.includes(previo)) {
            select.value = previo;
        } else if (claves.length > 0) {
            select.value = claves[0];
        }
    }

    // --- Construcción de un <tbody> a partir de las clases de un semestre

    function construirTbody(semestreClave, semestreData) {
        const tbody = document.createElement('tbody');
        tbody.id = `horario-semestre-${semestreClave}`;
        tbody.className = 'horario-tbody';

        // grid[hora][dia] = null | 'ocupado' | claseObj
        const grid = {};
        for (let h = HORA_INICIO_TABLA; h < HORA_FIN_TABLA; h++) {
            grid[h] = {};
            DIAS_TABLA.forEach((d) => { grid[h][d] = null; });
        }

        (semestreData.classes || []).forEach((clase) => {
            for (let h = clase.horaInicio; h < clase.horaFin; h++) {
                if (grid[h] === undefined || !(clase.dia in grid[h])) continue;
                grid[h][clase.dia] = (h === clase.horaInicio) ? clase : 'ocupado';
            }
        });

        for (let h = HORA_INICIO_TABLA; h < HORA_FIN_TABLA; h++) {
            const tr = document.createElement('tr');

            const th = document.createElement('th');
            th.scope = 'row';
            th.textContent = `${h}:00 - ${h + 1}:00`;
            tr.appendChild(th);

            DIAS_TABLA.forEach((d) => {
                const celda = grid[h][d];
                if (celda === 'ocupado') return; // ya cubierta por un rowspan anterior

                const td = document.createElement('td');

                if (celda) {
                    const rowspan = celda.horaFin - celda.horaInicio;
                    if (rowspan > 1) td.rowSpan = rowspan;
                    td.className = 'align-middle';

                    const horaTexto = `${pad2(celda.horaInicio)}:00 - ${pad2(celda.horaFin)}:00`;
                    const aula = celda.aula || 'Aula Por Definir';

                    td.dataset.dia = String(d);
                    td.dataset.hora = horaTexto;
                    td.dataset.materia = celda.materia;
                    td.dataset.color = celda.color;
                    td.dataset.aula = aula;
                    td.dataset.claseId = celda.id;

                    td.innerHTML = `
                        <div class="materia-slot ${celda.color} text-white" data-clase-id="${celda.id}">
                            ${celda.materia}<br><small>${aula}</small>
                        </div>
                    `;
                } else {
                    td.className = 'celda-vacia';
                    td.dataset.dia = String(d);
                    td.dataset.horaInicio = String(h);
                    td.title = "Agregar clase en este horario";
                }
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        }

        return tbody;
    }

    function construirTabla() {
        table.querySelectorAll('tbody.horario-tbody').forEach((tb) => tb.remove());

        Object.keys(SCHEDULE.semesters).forEach((clave) => {
            const tbody = construirTbody(clave, SCHEDULE.semesters[clave]);
            table.appendChild(tbody);
        });
    }

    // --- Lógica de selección / "Clases de Hoy" ---------------------------

    function actualizarHorario() {
        const semestreSeleccionado = select.value;
        const tbodySeleccionado = document.getElementById(`horario-semestre-${semestreSeleccionado}`);

        document.querySelectorAll('.horario-tbody').forEach((tbody) => {
            tbody.classList.remove('active');
        });

        const semestreData = SCHEDULE.semesters[semestreSeleccionado];
        const tieneClases = tbodySeleccionado && semestreData && (semestreData.classes || []).length > 0;

        if (tbodySeleccionado) tbodySeleccionado.classList.add('active');

        if (tieneClases) {
            tableContainer.style.display = 'block';
            noScheduleMessage.style.display = 'none';
            generarHorarioHoy(tbodySeleccionado);
        } else if (tbodySeleccionado) {
            tableContainer.style.display = 'block';
            noScheduleMessage.style.display = 'none';
            contenedorHoy.innerHTML = '<p class="text-muted mb-0">No hay clases registradas para este semestre todavía. Usa "+ Clase" para agregar la primera.</p>';
        } else {
            tableContainer.style.display = 'none';
            noScheduleMessage.style.display = 'block';
            contenedorHoy.innerHTML = '';
        }
    }

    function generarHorarioHoy(tbody) {
        const hoy = new Date();
        const diaActualJS = hoy.getDay(); // 0 = Domingo, 1 = Lunes, etc.

        tituloHoy.innerHTML = `<i class="bi bi-calendar-event"></i> Clases de Hoy (${DIAS_SEMANA[diaActualJS]})`;
        contenedorHoy.innerHTML = '';

        if (diaActualJS === 0) {
            contenedorHoy.innerHTML = '<p class="text-success mb-0 fw-bold"><i class="bi bi-cup-hot"></i> Es domingo, no hay clases programadas. ¡A descansar!</p>';
            return;
        }

        const materiasHoy = tbody.querySelectorAll(`td[data-dia="${diaActualJS}"]`);

        if (materiasHoy.length === 0) {
            contenedorHoy.innerHTML = '<p class="text-muted mb-0">No tienes clases programadas para hoy en este semestre.</p>';
            return;
        }

        materiasHoy.forEach((celda) => {
            const hora = celda.getAttribute('data-hora');
            const materia = celda.getAttribute('data-materia');
            const color = celda.getAttribute('data-color');
            const aula = celda.getAttribute('data-aula') || 'Aula Por Definir';

            const div = document.createElement('div');
            div.className = `card mb-2 border-0 ${color} text-white`;
            div.innerHTML = `
                <div class="card-body p-2 d-flex justify-content-between align-items-center">
                    <div>
                        <strong class="text-uppercase">${materia}</strong><br>
                        <small>${aula}</small>
                    </div>
                    <span class="badge bg-dark bg-opacity-50 text-light fs-6">${hora}</span>
                </div>
            `;
            contenedorHoy.appendChild(div);
        });
    }

    // --- Modal de clase (crear / editar) ----------------------------------

    function abrirModalClaseNueva(dia, horaInicio) {
        claseSeleccionada = null;
        document.getElementById('claseModalLabel').textContent = 'Agregar clase';
        document.getElementById('claseMateria').value = '';
        document.getElementById('claseDia').value = String(dia || 1);
        document.getElementById('claseHoraInicio').value = horaInicio != null ? horaInicio : '';
        document.getElementById('claseHoraFin').value = horaInicio != null ? horaInicio + 1 : '';
        document.getElementById('claseColor').value = 'bg-primary';
        document.getElementById('claseAula').value = '';
        document.getElementById('claseError').classList.add('d-none');
        document.getElementById('claseDeleteBtn').classList.add('d-none');
        claseModal.show();
    }

    function abrirModalClaseExistente(claseId) {
        const semestreData = SCHEDULE.semesters[select.value];
        const clase = (semestreData.classes || []).find((c) => String(c.id) === String(claseId));
        if (!clase) return;

        claseSeleccionada = clase.id;
        document.getElementById('claseModalLabel').textContent = 'Editar clase';
        document.getElementById('claseMateria').value = clase.materia;
        document.getElementById('claseDia').value = String(clase.dia);
        document.getElementById('claseHoraInicio').value = clase.horaInicio;
        document.getElementById('claseHoraFin').value = clase.horaFin;
        document.getElementById('claseColor').value = clase.color;
        document.getElementById('claseAula').value = clase.aula || '';
        document.getElementById('claseError').classList.add('d-none');
        document.getElementById('claseDeleteBtn').classList.remove('d-none');
        claseModal.show();
    }

    async function guardarClase(event) {
        event.preventDefault();
        const errorBox = document.getElementById('claseError');
        errorBox.classList.add('d-none');

        const horaInicio = parseInt(document.getElementById('claseHoraInicio').value, 10);
        const horaFin = parseInt(document.getElementById('claseHoraFin').value, 10);

        if (horaFin <= horaInicio) {
            errorBox.textContent = "La hora de fin debe ser mayor que la hora de inicio.";
            errorBox.classList.remove('d-none');
            return;
        }

        const datos = {
            semestre_numero: Number(select.value),
            dia: Number(document.getElementById('claseDia').value),
            hora_inicio: horaInicio,
            hora_fin: horaFin,
            materia: document.getElementById('claseMateria').value.trim(),
            color: document.getElementById('claseColor').value,
            aula: document.getElementById('claseAula').value.trim() || null,
        };

        const saveBtn = document.getElementById('claseSaveBtn');
        saveBtn.disabled = true;
        try {
            if (claseSeleccionada) {
                await actualizarClaseHorario(claseSeleccionada, datos);
            } else {
                await crearClaseHorario(datos);
            }
            await cargarHorario();
            construirTabla();
            poblarSelectSemestres(true);
            actualizarHorario();
            claseModal.hide();
        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.classList.remove('d-none');
        } finally {
            saveBtn.disabled = false;
        }
    }

    async function eliminarClase() {
        if (!claseSeleccionada) return;
        if (!confirm("¿Eliminar esta clase del horario?")) return;

        try {
            await eliminarClaseHorario(claseSeleccionada);
            await cargarHorario();
            construirTabla();
            poblarSelectSemestres(true);
            actualizarHorario();
            claseModal.hide();
        } catch (err) {
            const errorBox = document.getElementById('claseError');
            errorBox.textContent = err.message;
            errorBox.classList.remove('d-none');
        }
    }

    // --- Modal de semestre (crear / eliminar) -----------------------------

    function abrirModalSemestre() {
        document.getElementById('semestreNumero').value = '';
        document.getElementById('semestreLabel').value = '';
        document.getElementById('semestreError').classList.add('d-none');
        semestreModal.show();
    }

    async function guardarSemestre(event) {
        event.preventDefault();
        const errorBox = document.getElementById('semestreError');
        errorBox.classList.add('d-none');

        const numero = parseInt(document.getElementById('semestreNumero').value, 10);
        const label = document.getElementById('semestreLabel').value.trim();

        try {
            await crearSemestreHorario(numero, label);
            await cargarHorario();
            poblarSelectSemestres(false);
            select.value = String(numero);
            construirTabla();
            actualizarHorario();
            semestreModal.hide();
        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.classList.remove('d-none');
        }
    }

    async function eliminarSemestreActual() {
        const numero = select.value;
        if (!numero) return;
        const label = SCHEDULE.semesters[numero] ? SCHEDULE.semesters[numero].label : `Semestre ${numero}`;
        if (!confirm(`¿Eliminar "${label}" y todas sus clases?`)) return;

        try {
            await eliminarSemestreHorario(numero);
            await cargarHorario();
            poblarSelectSemestres(false);
            construirTabla();
            actualizarHorario();
        } catch (err) {
            alert(err.message);
        }
    }

    // --- Inicio -------------------------------------------------------------

    try {
        await cargarHorario();
    } catch (err) {
        console.error("No se pudo cargar el horario desde el backend:", err);
        tableContainer.style.display = 'none';
        noScheduleMessage.style.display = 'block';
        noScheduleMessage.textContent = `No se pudo conectar con el backend (${err.message}).`;
        return;
    }

    poblarSelectSemestres(false);
    construirTabla();
    actualizarHorario();

    select.addEventListener('change', actualizarHorario);

    table.addEventListener('click', (event) => {
        const slot = event.target.closest('.materia-slot');
        if (slot) {
            abrirModalClaseExistente(slot.dataset.claseId);
            return;
        }
        const vacia = event.target.closest('.celda-vacia');
        if (vacia) {
            abrirModalClaseNueva(Number(vacia.dataset.dia), Number(vacia.dataset.horaInicio));
        }
    });

    document.getElementById('btnAgregarClase').addEventListener('click', () => abrirModalClaseNueva());
    document.getElementById('claseForm').addEventListener('submit', guardarClase);
    document.getElementById('claseDeleteBtn').addEventListener('click', eliminarClase);

    document.getElementById('btnAgregarSemestre').addEventListener('click', abrirModalSemestre);
    document.getElementById('semestreForm').addEventListener('submit', guardarSemestre);
    document.getElementById('btnEliminarSemestre').addEventListener('click', eliminarSemestreActual);
});
