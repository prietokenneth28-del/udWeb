// Plan de estudios — interactividad
//
// Las tarjetas de curso YA NO están escritas a mano en el HTML: se generan
// aquí a partir del arreglo COURSES definido en courses-data.js. Para
// agregar, quitar o editar un curso, modifica ese archivo — no este.
//
// Estado de aprobación: se guarda en localStorage (clave "planEstudios:v1"),
// así que el avance se recuerda entre visitas. El valor "approved" de cada
// curso en courses-data.js solo se usa la primera vez que abres la página
// en ese navegador (o si borras el almacenamiento local).

(function () {
    "use strict";

    const STORAGE_KEY = "planEstudios:v1";

    const CATEGORY_TO_COLOR = {
        "fisica-matematica": "danger",
        "fabricacion": "warning",
        "energias": "success",
        "diseno-programacion": "primary",
        "lenguaje-sociales": "secondary",
        "electivas-grado": "light",
    };

    const CYCLE_LABELS = {
        tec: "Ciclo Tecnológico",
        ing: "Ciclo de Ingeniería",
    };

    // --- Persistencia -------------------------------------------------

    function loadApprovedState() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : {};
        } catch (err) {
            console.warn("No se pudo leer el estado guardado:", err);
            return {};
        }
    }

    function saveApprovedState(state) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (err) {
            console.warn("No se pudo guardar el estado:", err);
        }
    }

    function isApproved(course, savedState) {
        // El estado guardado en el navegador tiene prioridad sobre el
        // valor por defecto que trae courses-data.js.
        if (Object.prototype.hasOwnProperty.call(savedState, course.id)) {
            return !!savedState[course.id];
        }
        return !!course.approved;
    }

    // --- Prerrequisitos --------------------------------------------------
    // Se leen del campo "prereq" (arreglo de ids) de cada curso en
    // courses-data.js. Para agregar uno: prereq: ["tec-1", "tec-9"]

    let courseById = null;

    function getCourseById(id) {
        if (!courseById) {
            courseById = new Map(COURSES.map((c) => [c.id, c]));
        }
        return courseById.get(id);
    }

    // true = todos cumplidos, false = falta alguno, null = no tiene prerrequisitos
    function prereqsCumplidos(course) {
        if (!course.prereq || course.prereq.length === 0) return null;
        return course.prereq.every((id) => {
            const card = document.getElementById(id);
            const checkbox = card ? card.querySelector(".course-check") : null;
            return checkbox ? checkbox.checked : false;
        });
    }

    function buildPrereqPopoverContent(course) {
        // Se evalúa cada vez que se abre el popover, así el check ✔/✘
        // siempre refleja el estado actual de las casillas.
        return function () {
            if (!course.prereq || course.prereq.length === 0) {
                return '<p class="mb-0 text-body-secondary small">Sin prerrequisitos.</p>';
            }
            const items = course.prereq
                .map((prereqId) => {
                    const prereqCourse = getCourseById(prereqId);
                    if (!prereqCourse) {
                        return `<li class="text-warning">${prereqId} (no encontrado en courses-data.js)</li>`;
                    }
                    const prereqCard = document.getElementById(prereqCourse.id);
                    const checkbox = prereqCard ? prereqCard.querySelector(".course-check") : null;
                    const cumplido = checkbox ? checkbox.checked : false;
                    const icon = cumplido
                        ? '<i class="bi bi-check-circle-fill text-success"></i>'
                        : '<i class="bi bi-x-circle text-danger"></i>';
                    return `<li>${icon} ${prereqCourse.name}</li>`;
                })
                .join("");
            return `<ul class="list-unstyled mb-0 text-start small">${items}</ul>`;
        };
    }

    function initPrereqPopovers() {
        document.querySelectorAll(".prereq-btn").forEach((btn) => {
            const existing = bootstrap.Popover.getInstance(btn);
            if (existing) existing.dispose();

            const course = getCourseById(btn.dataset.courseId);
            if (!course) return;

            new bootstrap.Popover(btn, {
                trigger: "focus",
                html: true,
                container: "body",
                placement: "auto",
                title: `Prerrequisitos — ${course.name}`,
                content: buildPrereqPopoverContent(course),
            });
        });
    }

    function updatePrereqIndicators() {
        document.querySelectorAll(".prereq-btn").forEach((btn) => {
            const course = getCourseById(btn.dataset.courseId);
            if (!course) return;
            const icon = btn.querySelector("i");
            if (!icon) return;

            const estado = prereqsCumplidos(course);
            icon.classList.remove("text-success", "text-danger", "text-body-secondary");
            if (estado === null) {
                icon.classList.add("text-body-secondary");
            } else if (estado) {
                icon.classList.add("text-success");
            } else {
                icon.classList.add("text-danger");
            }
        });
    }

    // --- Construcción de tarjetas --------------------------------------

    function buildCourseCard(course, savedState) {
        const color = CATEGORY_TO_COLOR[course.category] || "light";
        const approved = isApproved(course, savedState);

        const card = document.createElement("div");
        card.className = `card course-card border-${color} text-${color} mb-3`;
        card.dataset.cycle = course.cycle;
        card.dataset.credits = course.credits;
        card.dataset.category = course.category;
        card.id = course.id;

        const codeLabel = course.code && course.code !== "-" ? course.code : "-";

        const prereqBtn = `
            <button type="button" class="btn btn-sm btn-link p-0 lh-1 prereq-btn"
                data-course-id="${course.id}"
                data-bs-toggle="popover"
                aria-label="Ver prerrequisitos de ${course.name}">
                <i class="bi bi-info-circle"></i>
            </button>
        `;

        card.innerHTML = `
            <div class="card-header border-${color}">
                <div class="row align-items-center">
                    <div class="col-auto form-check form-check-inline mb-0">
                        <input class="form-check-input course-check" type="checkbox"
                            ${approved ? "checked" : ""}
                            title="Marcar como aprobada"
                            aria-label="Aprobada: ${course.name}">
                    </div>
                    <div class="col text-start ps-0">Cod: ${codeLabel}</div>
                    <div class="col-auto d-flex align-items-center gap-1">
                        <span>${course.type || ""}</span>
                        ${prereqBtn}
                    </div>
                </div>
            </div>
            <div class="card-body">
                <h5 class="card-title">${course.name}</h5>
            </div>
            <div class="card-footer border-${color} text-${color}">
                Creditos: ${course.credits}
            </div>
        `;

        return card;
    }

    function buildSemesterColumn(cycle, semesterNum, courses, savedState) {
        const col = document.createElement("div");
        col.className = "col-12 col-md-6 col-lg-2";

        const semCard = document.createElement("div");
        semCard.className = "card text-center mt-1";

        const header = document.createElement("div");
        header.className = "card-header";
        header.innerHTML = `<h4>Semestre ${semesterNum}</h4>`;
        semCard.appendChild(header);

        let semTotal = 0;
        courses.forEach((course, idx) => {
            semTotal += course.credits;
            const cardEl = buildCourseCard(course, savedState);
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

    function renderCycle(cycleKey, containerId, headerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const savedState = loadApprovedState();
        const courses = COURSES.filter((c) => c.cycle === cycleKey);

        const semesters = {};
        courses.forEach((c) => {
            if (!semesters[c.semester]) semesters[c.semester] = [];
            semesters[c.semester].push(c);
        });

        container.innerHTML = "";
        Object.keys(semesters)
            .map(Number)
            .sort((a, b) => a - b)
            .forEach((semNum) => {
                container.appendChild(
                    buildSemesterColumn(cycleKey, semNum, semesters[semNum], savedState)
                );
            });

        const totalCredits = courses.reduce((sum, c) => sum + c.credits, 0);
        const headerEl = document.getElementById(headerId);
        if (headerEl) {
            headerEl.textContent = `${CYCLE_LABELS[cycleKey]} (${totalCredits} Créditos)`;
        }
    }

    function renderPlan() {
        renderCycle("tec", "tec-semesters", "tec-cycle-title");
        renderCycle("ing", "ing-semesters", "ing-cycle-title");
    }

    // --- Dashboard -------------------------------------------------------

    function getCourseCards() {
        return Array.from(document.querySelectorAll(".course-card"));
    }

    function updateDashboard() {
        const cards = getCourseCards();

        let total = 0, approved = 0;
        let totalTec = 0, approvedTec = 0;
        let totalIng = 0, approvedIng = 0;

        cards.forEach((card) => {
            const credits = parseFloat(card.dataset.credits) || 0;
            const cycle = card.dataset.cycle;
            const checkbox = card.querySelector(".course-check");
            const isChecked = checkbox ? checkbox.checked : false;

            total += credits;
            if (isChecked) approved += credits;

            if (cycle === "tec") {
                totalTec += credits;
                if (isChecked) approvedTec += credits;
            } else if (cycle === "ing") {
                totalIng += credits;
                if (isChecked) approvedIng += credits;
            }

            card.classList.toggle("is-pending", !isChecked);
        });

        const percent = total > 0 ? Math.round((approved / total) * 100) : 0;
        const remaining = total - approved;

        setText("stat-total", total);
        setText("stat-approved", approved);
        setText("stat-percent", percent + "%");
        setText("stat-remaining", remaining);

        setText("stat-total-breakdown", `Tec: ${totalTec} · Ing: ${totalIng}`);
        setText("stat-approved-breakdown", `Tec: ${approvedTec} · Ing: ${approvedIng}`);

        const bar = document.getElementById("stat-progress-bar");
        if (bar) {
            bar.style.width = percent + "%";
            bar.parentElement.setAttribute("aria-valuenow", String(percent));
        }

        updatePrereqIndicators();
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function attachCheckboxListeners() {
        document.querySelectorAll(".course-check").forEach((checkbox) => {
            checkbox.addEventListener("change", () => {
                const card = checkbox.closest(".course-card");
                if (card) {
                    const state = loadApprovedState();
                    state[card.id] = checkbox.checked;
                    saveApprovedState(state);
                }
                updateDashboard();
            });
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

    document.addEventListener("DOMContentLoaded", () => {
        if (typeof COURSES === "undefined") {
            console.error("courses-data.js no se cargó antes que planEstudios.js");
            return;
        }
        renderPlan();
        attachCheckboxListeners();
        attachPdfButton();
        initPrereqPopovers();
        updateDashboard();
    });
})();