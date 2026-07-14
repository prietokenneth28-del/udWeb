// Plan de estudios — interactividad
//
// Estado: se guarda en memoria mientras la página está abierta (no usa
// localStorage). Si quieres que el avance se recuerde entre visitas,
// es fácil añadir localStorage.getItem/setItem en loadState/saveState.

(function () {
    "use strict";

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
            const isApproved = checkbox ? checkbox.checked : false;

            total += credits;
            if (isApproved) approved += credits;

            if (cycle === "tec") {
                totalTec += credits;
                if (isApproved) approvedTec += credits;
            } else if (cycle === "ing") {
                totalIng += credits;
                if (isApproved) approvedIng += credits;
            }

            card.classList.toggle("is-pending", !isApproved);
        });

        const percent = total > 0 ? Math.round((approved / total) * 100) : 0;
        const remaining = total - approved;

        setText("stat-total", total);
        setText("stat-approved", approved);
        setText("stat-percent", percent + "%");
        setText("stat-remaining", remaining);

        setText(
            "stat-total-breakdown",
            `Tec: ${totalTec} · Ing: ${totalIng}`
        );
        setText(
            "stat-approved-breakdown",
            `Tec: ${approvedTec} · Ing: ${approvedIng}`
        );

        const bar = document.getElementById("stat-progress-bar");
        if (bar) {
            bar.style.width = percent + "%";
            bar.parentElement.setAttribute("aria-valuenow", String(percent));
        }
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function attachCheckboxListeners() {
        document.querySelectorAll(".course-check").forEach((checkbox) => {
            checkbox.addEventListener("change", updateDashboard);
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
        attachCheckboxListeners();
        attachPdfButton();
        updateDashboard();
    });
})();