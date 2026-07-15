// Horario — interactividad
//
// La tabla YA NO está escrita a mano en el HTML: se construye aquí a
// partir del objeto SCHEDULE definido en schedule-data.js. Para agregar
// un semestre nuevo o mover una clase, edita ese archivo — no este.

document.addEventListener('DOMContentLoaded', function () {
    "use strict";

    if (typeof SCHEDULE === "undefined") {
        console.error("schedule-data.js no se cargó antes que main.shedule.js");
        return;
    }

    const DIAS_TABLA = [1, 2, 3, 4, 5, 6]; // Lunes..Sábado, en el orden de las columnas
    const DIAS_SEMANA = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];

    const select = document.getElementById('semestreSelect');
    const table = document.querySelector('.table-horario');
    const tableContainer = document.getElementById('scheduleTableContainer');
    const noScheduleMessage = document.getElementById('noScheduleMessage');
    const contenedorHoy = document.getElementById('clasesHoyContainer');
    const tituloHoy = document.getElementById('tituloHoy');

    function pad2(n) {
        return String(n).padStart(2, "0");
    }

    // --- Construcción del <select> a partir de SCHEDULE.semesters -------

    function poblarSelectSemestres() {
        select.innerHTML = "";
        const claves = Object.keys(SCHEDULE.semesters).sort((a, b) => Number(a) - Number(b));
        claves.forEach((clave) => {
            const opt = document.createElement("option");
            opt.value = clave;
            opt.textContent = SCHEDULE.semesters[clave].label || `Semestre ${clave}`;
            select.appendChild(opt);
        });
        if (claves.length > 0) select.value = claves[0];
    }

    // --- Construcción de un <tbody> a partir de las clases de un semestre

    function construirTbody(semestreClave, semestreData) {
        const tbody = document.createElement('tbody');
        tbody.id = `horario-semestre-${semestreClave}`;
        tbody.className = 'horario-tbody';

        const { horaInicio, horaFin } = SCHEDULE.meta;

        // grid[hora][dia] = null | 'ocupado' | claseObj
        const grid = {};
        for (let h = horaInicio; h < horaFin; h++) {
            grid[h] = {};
            DIAS_TABLA.forEach((d) => { grid[h][d] = null; });
        }

        (semestreData.classes || []).forEach((clase) => {
            for (let h = clase.horaInicio; h < clase.horaFin; h++) {
                if (grid[h] === undefined || !(clase.dia in grid[h])) continue;
                grid[h][clase.dia] = (h === clase.horaInicio) ? clase : 'ocupado';
            }
        });

        for (let h = horaInicio; h < horaFin; h++) {
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

                    td.innerHTML = `
                        <div class="materia-slot ${celda.color} text-white">
                            ${celda.materia}<br><small>${aula}</small>
                        </div>
                    `;
                }
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        }

        return tbody;
    }

    function construirTabla() {
        // Elimina los tbody generados en una render previa (deja el thead intacto)
        table.querySelectorAll('tbody.horario-tbody').forEach((tb) => tb.remove());

        Object.keys(SCHEDULE.semesters).forEach((clave) => {
            const tbody = construirTbody(clave, SCHEDULE.semesters[clave]);
            table.appendChild(tbody);
        });
    }

    // --- Lógica de selección / "Clases de Hoy" (igual que antes) --------

    function actualizarHorario() {
        const semestreSeleccionado = select.value;
        const tbodySeleccionado = document.getElementById(`horario-semestre-${semestreSeleccionado}`);

        document.querySelectorAll('.horario-tbody').forEach((tbody) => {
            tbody.classList.remove('active');
        });

        const tieneClases = tbodySeleccionado &&
            (SCHEDULE.semesters[semestreSeleccionado].classes || []).length > 0;

        if (tieneClases) {
            tableContainer.style.display = 'block';
            noScheduleMessage.style.display = 'none';
            tbodySeleccionado.classList.add('active');
            generarHorarioHoy(tbodySeleccionado);
        } else {
            tableContainer.style.display = 'none';
            noScheduleMessage.style.display = 'block';
            contenedorHoy.innerHTML = '<p class="text-muted mb-0">No hay datos para analizar el horario de hoy.</p>';
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

            const div = document.createElement('div');
            div.className = `card mb-2 border-0 ${color} text-white`;
            div.innerHTML = `
                <div class="card-body p-2 d-flex justify-content-between align-items-center">
                    <div>
                        <strong class="text-uppercase">${materia}</strong><br>
                        <small>Aula Por Definir</small>
                    </div>
                    <span class="badge bg-dark bg-opacity-50 text-light fs-6">${hora}</span>
                </div>
            `;
            contenedorHoy.appendChild(div);
        });
    }

    // --- Inicio -----------------------------------------------------------

    poblarSelectSemestres();
    construirTabla();
    select.addEventListener('change', actualizarHorario);
    actualizarHorario();
});