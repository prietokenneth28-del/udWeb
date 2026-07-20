// Plan de estudios — interactividad
//
// Las tarjetas de curso se generan a partir de lo que devuelve el backend
// (GET /api/plan-estudios + GET /api/historial), no de un archivo estático.
// El estado de "aprobada" vive en la tabla Historial_Academico: togglear el
// checkbox crea/actualiza/borra un registro de historial vía la API
// (requiere haber iniciado sesión).

(function () {
    "use strict";

    let COURSES = [];
    // materia_id -> registro de historial (el más reciente por materia)
    let historialPorMateria = new Map();

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

    // --- Datos desde el backend -----------------------------------------

    async function loadPlanFromBackend() {
        // El historial requiere sesión iniciada; para visitantes anónimos
        // ("ver el plan sin iniciar sesión") simplemente se omite y todas
        // las materias se muestran como pendientes.
        const [ciclos, historial] = await Promise.all([
            getPlanEstudios(),
            isLoggedIn() ? getHistorial() : Promise.resolve([]),
        ]);

        historialPorMateria = new Map();
        historial.forEach((registro) => {
            // Si hay varios registros para la misma materia (reintentos),
            // nos quedamos con el más reciente.
            const actual = historialPorMateria.get(registro.materia_id);
            if (!actual || new Date(registro.fecha_registro) > new Date(actual.fecha_registro)) {
                historialPorMateria.set(registro.materia_id, registro);
            }
        });

        const courses = [];
        ciclos.forEach((ciclo) => {
            ciclo.semestres.forEach((semestre) => {
                semestre.materias.forEach((materia) => {
                    courses.push({
                        id: materia.id,
                        name: materia.nombre,
                        code: materia.codigo,
                        credits: materia.creditos,
                        cycle: ciclo.id,
                        semester: semestre.numero,
                        category: materia.categoria,
                        type: materia.tipo,
                        prereq: materia.prereq,
                    });
                });
            });
        });
        return courses;
    }

    function isApproved(course) {
        const registro = historialPorMateria.get(course.id);
        return !!registro && registro.estado === "Aprobada";
    }

    async function setApproved(course, approved) {
        const registro = historialPorMateria.get(course.id);

        if (approved) {
            if (registro) {
                const actualizado = await actualizarHistorial(registro.id, {
                    materia_id: course.id,
                    periodo: registro.periodo,
                    nota_final: registro.nota_final,
                    estado: "Aprobada",
                });
                historialPorMateria.set(course.id, actualizado);
            } else {
                const creado = await crearHistorial(course.id, {
                    periodo: null,
                    nota_final: null,
                    estado: "Aprobada",
                });
                historialPorMateria.set(course.id, creado);
            }
            return;
        }

        // Desmarcar: solo se puede si el registro no tiene una nota real
        // asociada (fue creado únicamente por el checkbox).
        if (registro && registro.nota_final === null) {
            await eliminarHistorial(registro.id);
            historialPorMateria.delete(course.id);
        } else if (registro) {
            throw new Error("Esta materia tiene una nota registrada; no se puede desmarcar desde aquí.");
        }
    }

    // --- Prerrequisitos --------------------------------------------------
    // Se leen del campo "prereq" (arreglo de ids) de cada materia, que viene
    // del prereq_json de la tabla Materia en el backend.

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
                        return `<li class="text-warning">${prereqId} (no encontrado en el plan de estudios)</li>`;
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

    function buildCourseCard(course) {
        const color = CATEGORY_TO_COLOR[course.category] || "light";
        const approved = isApproved(course);

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

    function buildSemesterColumn(cycle, semesterNum, courses) {
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
            const cardEl = buildCourseCard(course);
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
                    buildSemesterColumn(cycleKey, semNum, semesters[semNum])
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
            checkbox.addEventListener("change", async () => {
                const card = checkbox.closest(".course-card");
                const course = card ? getCourseById(card.id) : null;
                if (!course) return;

                if (!isLoggedIn()) {
                    checkbox.checked = !checkbox.checked;
                    alert("Debes iniciar sesión para guardar cambios en el plan de estudios.");
                    window.location.href = "/index.html";
                    return;
                }

                const nuevoEstado = checkbox.checked;
                checkbox.disabled = true;
                try {
                    await setApproved(course, nuevoEstado);
                } catch (err) {
                    checkbox.checked = !nuevoEstado;
                    alert(err.message);
                } finally {
                    checkbox.disabled = false;
                    updateDashboard();
                }
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

    document.addEventListener("DOMContentLoaded", async () => {
        try {
            COURSES = await loadPlanFromBackend();
            courseById = null; // se reconstruye con los datos frescos
        } catch (err) {
            console.error("No se pudo cargar el plan de estudios desde el backend:", err);
            const container = document.getElementById("tec-semesters");
            if (container) {
                container.innerHTML = `<p class="text-danger">No se pudo conectar con el backend (${err.message}). Verifica que el servidor esté corriendo.</p>`;
            }
            return;
        }

        renderPlan();
        attachCheckboxListeners();
        attachPdfButton();
        initPrereqPopovers();
        updateDashboard();
    });
})();