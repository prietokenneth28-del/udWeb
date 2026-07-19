// components.js — inyecta el header y el footer compartidos (components/*.html)
// y deja lista la sesión (usuario/logout) en el header. Debe cargarse
// DESPUÉS de api.js (usa login/logout/isLoggedIn/getUsername) y las páginas
// pueden esperar a `window.appLayoutReady` antes de tocar el header/footer.

(function () {
    "use strict";

    function loadInclude(url, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return Promise.resolve();

        return fetch(url)
            .then((res) => {
                if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
                return res.text();
            })
            .then((html) => {
                container.innerHTML = html;
            })
            .catch((err) => {
                console.error(`No se pudo cargar ${url}:`, err);
            });
    }

    function markActiveNavLink() {
        const currentPath = window.location.pathname;
        document.querySelectorAll("#main-nav .nav-link").forEach((link) => {
            const linkPath = new URL(link.getAttribute("href"), window.location.origin).pathname;
            link.classList.toggle("active", linkPath === currentPath);
        });
    }

    function initSessionUI() {
        const info = document.getElementById("session-info");
        const loginLink = document.getElementById("login-link");
        const logoutBtn = document.getElementById("logout-btn");
        if (!info || !loginLink || !logoutBtn) return;

        function render() {
            const logged = typeof isLoggedIn === "function" && isLoggedIn();
            if (logged) {
                const username = typeof getUsername === "function" ? getUsername() : null;
                info.textContent = `Sesión: ${username || "usuario"}`;
                loginLink.classList.add("d-none");
                logoutBtn.classList.remove("d-none");
            } else {
                info.textContent = "";
                loginLink.classList.remove("d-none");
                logoutBtn.classList.add("d-none");
            }
        }

        logoutBtn.addEventListener("click", () => {
            if (typeof logout === "function") logout();
            render();
            document.dispatchEvent(new CustomEvent("session:changed"));
        });

        render();
    }

    window.appLayoutReady = Promise.all([
        loadInclude("/components/header.html", "header-container"),
        loadInclude("/components/footer.html", "footer-container"),
    ]).then(() => {
        const footerYear = document.getElementById("footer-year");
        if (footerYear) footerYear.textContent = new Date().getFullYear();

        markActiveNavLink();
        initSessionUI();
        document.dispatchEvent(new CustomEvent("layout:ready"));
    });
})();
