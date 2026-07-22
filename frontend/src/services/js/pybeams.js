// PyBeams — formulario dinámico de apoyos/cargas + cálculo de reacciones y diagramas
//
// No persiste nada en el backend: cada cálculo es una llamada stateless a
// POST /api/pybeams/calcular (requiere sesión, igual que el resto de la API).
// Los nombres de apoyos (A, B, C...) y cargas (F1, F2...) se renumeran
// automáticamente para que siempre coincidan con la posición de la fila.

(function () {
    "use strict";

    const DISTRIBUTED_TYPES = new Set([
        "Uniformly distributed",
        "Triangular distributed 1",
        "Triangular distributed 2",
    ]);

    const form = document.getElementById("form-pybeams");
    const submitBtn = document.getElementById("pb-submit");
    const errorBox = document.getElementById("pb-error");
    const pdfBtn = document.getElementById("pb-descargar-pdf");
    const pdfErrorBox = document.getElementById("pb-pdf-error");

    let ultimoPayload = null;

    const supportsContainer = document.getElementById("pb-supports-container");
    const loadsContainer = document.getElementById("pb-loads-container");
    const supportRowTemplate = document.getElementById("pb-support-row-template");
    const loadRowTemplate = document.getElementById("pb-load-row-template");

    const resultadosVacio = document.getElementById("pb-resultados-vacio");
    const resultados = document.getElementById("pb-resultados");
    const reaccionesBody = document.getElementById("pb-reacciones-body");
    const mmaxEl = document.getElementById("pb-mmax");
    const smodEl = document.getElementById("pb-smod");
    const imgDcl = document.getElementById("pb-img-dcl");
    const imgVm = document.getElementById("pb-img-vm");

    // --- Nombres automáticos ------------------------------------------------

    function letterFor(index) {
        // A, B, C... Z, AA, AB... (de sobra para cualquier viga razonable)
        let n = index;
        let name = "";
        do {
            name = String.fromCharCode(65 + (n % 26)) + name;
            n = Math.floor(n / 26) - 1;
        } while (n >= 0);
        return name;
    }

    function renumerarApoyos() {
        supportsContainer.querySelectorAll("[data-support-row]").forEach((row, index) => {
            row.querySelector('[data-field="name"]').value = letterFor(index);
        });
    }

    function renumerarCargas() {
        loadsContainer.querySelectorAll("[data-load-row]").forEach((row, index) => {
            row.querySelector('[data-field="name"]').value = `F${index + 1}`;
        });
    }

    // --- Filas de apoyos -----------------------------------------------------

    function agregarApoyo({ location = 0, type = "Pinned" } = {}) {
        const fragment = supportRowTemplate.content.cloneNode(true);
        const row = fragment.querySelector("[data-support-row]");
        row.querySelector('[data-field="location"]').value = location;
        row.querySelector('[data-field="type"]').value = type;
        row.querySelector("[data-remove-support]").addEventListener("click", () => {
            row.remove();
            renumerarApoyos();
        });
        supportsContainer.appendChild(row);
        renumerarApoyos();
    }

    // --- Filas de cargas -------------------------------------------------------

    function actualizarVisibilidadCarga(row) {
        const type = row.querySelector('[data-field="type"]').value;
        const distribuida = DISTRIBUTED_TYPES.has(type);
        const esMomento = type === "Moment load";

        const a1Wrapper = row.querySelector("[data-a1-wrapper]");
        const a1Input = row.querySelector('[data-field="a1"]');
        a1Wrapper.classList.toggle("d-none", !distribuida);
        a1Input.required = distribuida;
        if (!distribuida) a1Input.value = "";

        const valueLabel = row.querySelector("[data-value-label]");
        valueLabel.textContent = esMomento ? "Valor (kN·m)" : distribuida ? "Valor (kN/m)" : "Valor (kN)";

        const aLabel = row.querySelector("[data-a-label]");
        aLabel.textContent = distribuida ? "Desde a (m)" : "Posición a (m)";
    }

    function agregarCarga({ type = "Point load", value = -10, a = 0, a1 = null } = {}) {
        const fragment = loadRowTemplate.content.cloneNode(true);
        const row = fragment.querySelector("[data-load-row]");
        row.querySelector('[data-field="type"]').value = type;
        row.querySelector('[data-field="value"]').value = value;
        row.querySelector('[data-field="a"]').value = a;
        if (a1 !== null) row.querySelector('[data-field="a1"]').value = a1;

        row.querySelector('[data-field="type"]').addEventListener("change", (event) => {
            actualizarVisibilidadCarga(event.target.closest("[data-load-row]"));
        });
        row.querySelector("[data-remove-load]").addEventListener("click", () => {
            row.remove();
            renumerarCargas();
        });

        loadsContainer.appendChild(row);
        actualizarVisibilidadCarga(loadsContainer.lastElementChild);
        renumerarCargas();
    }

    document.getElementById("pb-add-support").addEventListener("click", () => agregarApoyo());
    document.getElementById("pb-add-load").addEventListener("click", () => agregarCarga());

    // --- Recolección de datos del formulario ------------------------------

    function recolectarPayload() {
        const l = Number(document.getElementById("pb-longitud").value);

        const supports = {};
        supportsContainer.querySelectorAll("[data-support-row]").forEach((row) => {
            const name = row.querySelector('[data-field="name"]').value;
            supports[name] = {
                location: Number(row.querySelector('[data-field="location"]').value),
                type: row.querySelector('[data-field="type"]').value,
            };
        });

        const loads = {};
        loadsContainer.querySelectorAll("[data-load-row]").forEach((row) => {
            const name = row.querySelector('[data-field="name"]').value;
            const type = row.querySelector('[data-field="type"]').value;
            const load = {
                value: Number(row.querySelector('[data-field="value"]').value),
                a: Number(row.querySelector('[data-field="a"]').value),
                type,
            };
            if (DISTRIBUTED_TYPES.has(type)) {
                load.a1 = Number(row.querySelector('[data-field="a1"]').value);
            }
            loads[name] = load;
        });

        return {
            l,
            Sy: Number(document.getElementById("pb-sy").value),
            FS: Number(document.getElementById("pb-fs").value),
            supports,
            loads,
        };
    }

    // --- Renderizado de resultados ------------------------------------------

    function unidadReaccion(tipo) {
        return tipo === "Moment load" ? "kN·m" : "kN";
    }

    function renderizarResultados(data) {
        reaccionesBody.innerHTML = "";
        Object.entries(data.reactions).forEach(([nombre, reaccion]) => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${nombre}</td>
                <td>${reaccion.value}</td>
                <td>${reaccion.location}</td>
                <td>${unidadReaccion(reaccion.type)}</td>
            `;
            reaccionesBody.appendChild(tr);
        });

        mmaxEl.textContent = `${data.Mmax} kN·m`;
        smodEl.textContent = `${data.required_section_modulus_cm3} cm³`;

        imgDcl.src = `data:image/png;base64,${data.diagrams.free_body}`;
        imgVm.src = `data:image/png;base64,${data.diagrams.shear_moment}`;

        resultadosVacio.classList.add("d-none");
        resultados.classList.remove("d-none");
    }

    // --- Envío del formulario ------------------------------------------------

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        errorBox.classList.add("d-none");

        submitBtn.disabled = true;
        const textoOriginal = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Calculando...';

        try {
            const payload = recolectarPayload();
            const data = await calcularViga(payload);
            ultimoPayload = payload;
            renderizarResultados(data);
        } catch (err) {
            errorBox.textContent = err.message;
            errorBox.classList.remove("d-none");
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = textoOriginal;
        }
    });

    // --- Descarga del reporte en PDF ------------------------------------

    pdfBtn.addEventListener("click", async () => {
        if (!ultimoPayload) return;
        pdfErrorBox.classList.add("d-none");

        pdfBtn.disabled = true;
        const textoOriginal = pdfBtn.innerHTML;
        pdfBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Generando...';

        try {
            const blob = await descargarReportePyBeams(ultimoPayload);
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "reporte_viga.pdf";
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            pdfErrorBox.textContent = err.message;
            pdfErrorBox.classList.remove("d-none");
        } finally {
            pdfBtn.disabled = false;
            pdfBtn.innerHTML = textoOriginal;
        }
    });

    // --- Inicializar -----------------------------------------------------------

    document.addEventListener("DOMContentLoaded", () => {
        if (!isLoggedIn()) {
            window.location.href = "/index.html";
            return;
        }

        agregarApoyo({ location: 0, type: "Pinned" });
        agregarApoyo({ location: 6, type: "Roller" });
        agregarCarga({ type: "Point load", value: -10, a: 3 });
    });
})();
