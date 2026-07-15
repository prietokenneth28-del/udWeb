// Plan de estudios — interactividad
//
// Las tarjetas de curso se generan a partir del plan de estudios y el
// historial de notas que expone el backend (ver /backend):
//   GET  /api/plan-estudios  -> ciclos > semestres > materias
//   GET  /api/historial      -> notas registradas por materia
//   GET  /api/estadisticas   -> créditos, % de avance y PAPA
//
// Marcar una materia como aprobada abre un formulario para capturar la
// nota real y el periodo (POST/PUT /api/historial). Desmarcarla borra
// ese registro de historial (DELETE /api/historial/{id}) — no hay
// almacenamiento local: todo vive en la base de datos del backend.

(function () {
    "use strict";

    const CATEGORY_TO_COLOR = {
        "fisica-matematica": "danger",
        "fabricacion": "warning",
        "energias": "success",
        "diseno-programacion": "primary",
        "lenguaje-sociales": "secondary",
        "electivas-grado": "light",
    };

    // Categoría por defecto para materias que el backend no clasificó
    // (columna opcional `categoria` en Materias).
    const DEFAULT_CATEGORY = "electivas-grado";

    // Estado en memoria, reconstruido en cada carga desde el backend.
    let historialByMateriaId = new Map();
    let pendingCourse = null; // curso que se está editando en el modal

    // --- Utilidades ------------------------------------------------------

    function cicloToCycleKey(nombreCiclo) {
        const n = nombreCiclo.toLowerCase();
        if (n.includes("tecnol")) return "tec";
        if (n.includes("ingenier")) return "ing";
        return "otro";
    }

    function cycleLabel(nombreCiclo, totalCredits) {
        return `${nombreCiclo} (${totalCredits} Créditos)`;
    }

    function currentPeriodo() {
        const now = new Date();
        const half = now.getMonth() + 1 <= 6 ? 1 : 2;
        return `${now.getFullYear()}-${half}`;
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function showApiError(message) {
        const banner = document.getElementById("api-error-banner");
        if (!banner) return;
        banner.textContent = message;
        banner.classList.remove("d-none");
    }

    function clearApiError() {
        const banner = document.getElementById("api-error-banner");
        if (banner) banner.classList.add("d-none");
    }

    // --- Carga de datos ----------------------------------------------------

    async function loadPlan() {
        const [ciclos, historial] = await Promise.all([
            Api.getPlanEstudios(),
            Api.getHistorial(),
        ]);

        historialByMateriaId = new Map();
        historial.forEach((registro) => {
            // El backend ya ordena por fecha_registro desc, así que el
            // primer registro que veamos por materia es el más reciente.
            if (!historialByMateriaId.has(registro.materia_id)) {
                historialByMateriaId.set(registro.materia_id, registro);
            }
        });

        return ciclos;
    }

    // --- Construcción de tarjetas -----------------------------------------

    function buildCourseCard(materia, cycleKey) {
        const category = materia.categoria || DEFAULT_CATEGORY;
        const color = CATEGORY_TO_COLOR[category] || "light";
        const registro = historialByMateriaId.get(materia.id);
        const approved = !!registro && registro.estado === "Aprobada";

        const card = document.createElement("div");
        card.className = `card course-card border-${color} text-${color} mb-3`;
        card.dataset.cycle = cycleKey;
        card.dataset.credits = materia.creditos;
        card.dataset.category = category;
        card.dataset.materiaId = String(materia.id);
        card.id = `materia-${materia.id}`;

        const codeLabel = materia.codigo && materia.codigo !== "-" ? materia.codigo : "-";

        card.innerHTML = `
            <div class="card-header border-${color}">
                <div class="row align-items-center">
                    <div class="col-auto form-check form-check-inline mb-0">
                        <input class="form-check-input course-check" type="checkbox"
                            ${approved ? "checked" : ""}
                            title="Marcar como aprobada"
                            aria-label="Aprobada: ${materia.nombre}">
                    </div>
                    <div class="col text-start ps-0">Cod: ${codeLabel}</div>
                    <div class="col-auto">${materia.tipo || ""}</div>
                </div>
            </div>
            <div class="card-body">
                <h5 class="card-title">${materia.nombre}</h5>
            </div>
            <div class="card-footer border-${color} text-${color}">
                Creditos: ${materia.creditos}${registroFooterExtra(registro)}
            </div>
        `;

        return card;
    }

    function registroFooterExtra(registro) {
        if (!registro || registro.nota_final === null || registro.nota_final === undefined) {
            return "";
        }
        return ` &middot; Nota: ${registro.nota_final} (${registro.estado})`;
    }

    function buildSemesterColumn(cycleKey, semesterNum, materias) {
        const col = document.createElement("div");
        col.className = "col-12 col-md-6 col-lg-2";

        const semCard = document.createElement("div");
        semCard.className = "card text-center mt-1";

        const header = document.createElement("div");
        header.className = "card-header";
        header.innerHTML = `<h4>Semestre ${semesterNum}</h4>`;
        semCard.appendChild(header);

        let semTotal = 0;
        materias.forEach((materia, idx) => {
            semTotal += materia.creditos;
            const cardEl = buildCourseCard(materia, cycleKey);
            if (idx === 0) cardEl.classList.add("mt-3");
            semCard.appendChild(cardEl);
        });

        const footer = document.createElement("div");
        footer.className = "card-footer border-secondary text-secondary";
        footer.innerHTML = `<h5>Total de creditos: ${semTotal}</h5>`;
        semCard.appendChild(footer);

        col.appendChild(semCard);
        return col;
    }

    function renderCycle(ciclo, containerId, headerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const cycleKey = cicloToCycleKey(ciclo.nombre);

        const semestres = [...ciclo.semestres].sort((a, b) => a.numero - b.numero);

        container.innerHTML = "";
        let totalCredits = 0;
        semestres.forEach((semestre) => {
            const materias = [...semestre.materias].sort((a, b) => a.id - b.id);
            totalCredits += materias.reduce((sum, m) => sum + m.creditos, 0);
            container.appendChild(buildSemesterColumn(cycleKey, semestre.numero, materias));
        });

        const headerEl = document.getElementById(headerId);
        if (headerEl) headerEl.textContent = cycleLabel(ciclo.nombre, totalCredits);
    }

    function renderPlan(ciclos) {
        const ciclosOrdenados = [...ciclos].sort((a, b) => a.id - b.id);
        const [cicloTec, cicloIng] = ciclosOrdenados;
        if (cicloTec) renderCycle(cicloTec, "tec-semesters", "tec-cycle-title");
        if (cicloIng) renderCycle(cicloIng, "ing-semesters", "ing-cycle-title");
    }

    // --- Dashboard (créditos, % de avance, PAPA) ---------------------------

    async function refreshDashboard() {
        try {
            const stats = await Api.getEstadisticas();

            setText("stat-total", stats.creditos_totales);
            setText("stat-approved", stats.creditos_aprobados);
            setText("stat-percent", `${stats.porcentaje_avance}%`);
            setText("stat-remaining", stats.creditos_pendientes);
            setText("stat-papa", stats.papa !== null ? stats.papa.toFixed(2) : "—");

            const desglose = stats.desglose_por_ciclo || {};
            const breakdown = Object.entries(desglose)
                .map(([nombre, d]) => `${nombre}: ${d.creditos_aprobados}/${d.creditos_totales}`)
                .join(" · ");
            setText("stat-total-breakdown", breakdown);
            setText("stat-approved-breakdown", breakdown);

            const bar = document.getElementById("stat-progress-bar");
            if (bar) {
                bar.style.width = `${stats.porcentaje_avance}%`;
                bar.parentElement.setAttribute("aria-valuenow", String(stats.porcentaje_avance));
            }
        } catch (err) {
            showApiError(err.message);
        }
    }

    // --- Modal: capturar nota real ------------------------------------------

    function getModalEls() {
        return {
            modalEl: document.getElementById("notaModal"),
            courseName: document.getElementById("notaModalCourseName"),
            notaInput: document.getElementById("notaInput"),
            periodoInput: document.getElementById("periodoInput"),
            errorEl: document.getElementById("notaModalError"),
            saveBtn: document.getElementById("notaModalSave"),
        };
    }

    function openNotaModal(materiaId, materiaNombre, checkbox) {
        const { modalEl, courseName, notaInput, periodoInput, errorEl } = getModalEls();
        const registro = historialByMateriaId.get(materiaId);

        courseName.textContent = materiaNombre;
        notaInput.value = registro && registro.nota_final !== null ? registro.nota_final : "";
        periodoInput.value = registro ? registro.periodo : currentPeriodo();
        errorEl.classList.add("d-none");

        pendingCourse = { materiaId, checkbox, saved: false };

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    async function saveNotaModal() {
        const { modalEl, notaInput, periodoInput, errorEl } = getModalEls();
        if (!pendingCourse) return;

        const nota = parseFloat(notaInput.value);
        const periodo = periodoInput.value.trim();

        if (Number.isNaN(nota) || nota < 0 || nota > 5) {
            errorEl.textContent = "Ingresa una nota válida entre 0.0 y 5.0.";
            errorEl.classList.remove("d-none");
            return;
        }
        if (!periodo) {
            errorEl.textContent = "Ingresa el periodo (ej. 2026-2).";
            errorEl.classList.remove("d-none");
            return;
        }

        try {
            const registroExistente = historialByMateriaId.get(pendingCourse.materiaId);
            if (registroExistente) {
                await Api.actualizarHistorial(registroExistente.id, { periodo, notaFinal: nota });
            } else {
                await Api.crearHistorial({ materiaId: pendingCourse.materiaId, periodo, notaFinal: nota });
            }

            pendingCourse.saved = true;
            clearApiError();
            bootstrap.Modal.getOrCreateInstance(modalEl).hide();
            await reloadAndRender();
        } catch (err) {
            errorEl.textContent = err.message;
            errorEl.classList.remove("d-none");
        }
    }

    function attachModalHandlers() {
        const { modalEl, saveBtn } = getModalEls();
        saveBtn.addEventListener("click", saveNotaModal);

        modalEl.addEventListener("hidden.bs.modal", () => {
            if (pendingCourse && !pendingCourse.saved) {
                // El usuario canceló: revertir la casilla a su estado anterior.
                pendingCourse.checkbox.checked = false;
            }
            pendingCourse = null;
        });
    }

    // --- Interacción con las casillas ---------------------------------------

    async function handleCheckboxChange(checkbox) {
        const card = checkbox.closest(".course-card");
        if (!card) return;

        const materiaId = Number(card.dataset.materiaId);
        const materiaNombre = card.querySelector(".card-title").textContent;
        const registro = historialByMateriaId.get(materiaId);

        if (checkbox.checked) {
            openNotaModal(materiaId, materiaNombre, checkbox);
            return;
        }

        // Se desmarcó: solo tiene sentido si había un registro aprobado.
        if (!registro) return;

        const confirmado = window.confirm(
            `¿Eliminar el registro de nota de "${materiaNombre}" (${registro.periodo}, nota ${registro.nota_final})? Esta acción no se puede deshacer.`
        );
        if (!confirmado) {
            checkbox.checked = true;
            return;
        }

        try {
            await Api.eliminarHistorial(registro.id);
            clearApiError();
            await reloadAndRender();
        } catch (err) {
            checkbox.checked = true;
            showApiError(err.message);
        }
    }

    function attachCheckboxListeners() {
        document.querySelectorAll(".course-check").forEach((checkbox) => {
            checkbox.addEventListener("change", () => handleCheckboxChange(checkbox));
        });
    }

    function attachPdfButton() {
        const btn = document.getElementById("btn-pdf");
        if (!btn || typeof html2pdf === "undefined") return;

        btn.addEventListener("click", () => {
            const target = document.querySelector("main");
            const opt = {
                margin: 6,
                filename: "plan-de-estudios.pdf",
                image: { type: "jpeg", quality: 0.98 },
                html2canvas: { scale: 2, backgroundColor: "#1a1d20" },
                jsPDF: { unit: "mm", format: "a3", orientation: "landscape" },
            };

            document.body.classList.add("pdf-export-mode");
            btn.disabled = true;
            const originalLabel = btn.innerHTML;
            btn.innerHTML = "Generando…";

            html2pdf()
                .set(opt)
                .from(target)
                .save()
                .finally(() => {
                    document.body.classList.remove("pdf-export-mode");
                    btn.disabled = false;
                    btn.innerHTML = originalLabel;
                });
        });
    }

    // --- Orquestación --------------------------------------------------------

    async function reloadAndRender() {
        try {
            const ciclos = await loadPlan();
            renderPlan(ciclos);
            attachCheckboxListeners();
            clearApiError();
        } catch (err) {
            showApiError(err.message);
        }
        await refreshDashboard();
    }

    document.addEventListener("DOMContentLoaded", () => {
        attachModalHandlers();
        attachPdfButton();
        reloadAndRender();
    });
})();
