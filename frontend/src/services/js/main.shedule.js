document.addEventListener('DOMContentLoaded', function() {
            const select = document.getElementById('semestreSelect');
            const tableContainer = document.getElementById('scheduleTableContainer');
            const noScheduleMessage = document.getElementById('noScheduleMessage');

            // Elementos del "Horario de Hoy"
            const contenedorHoy = document.getElementById('clasesHoyContainer');
            const tituloHoy = document.getElementById('tituloHoy');

            function actualizarHorario() {
                const semestreSeleccionado = select.value;
                const tbodySeleccionado = document.getElementById(`horario-semestre-${semestreSeleccionado}`);

                // 1. Ocultar todos los tbodys
                document.querySelectorAll('.horario-tbody').forEach(tbody => {
                    tbody.classList.remove('active');
                });

                // 2. Gestionar la vista principal
                if (tbodySeleccionado && tbodySeleccionado.innerHTML.trim() !== '') {
                    tableContainer.style.display = 'block';
                    noScheduleMessage.style.display = 'none';
                    tbodySeleccionado.classList.add('active');

                    // 3. Generar el resumen de "Clases de Hoy"
                    generarHorarioHoy(tbodySeleccionado);
                } else {
                    tableContainer.style.display = 'none';
                    noScheduleMessage.style.display = 'block';
                    contenedorHoy.innerHTML = '<p class="text-muted mb-0">No hay datos para analizar el horario de hoy.</p>';
                }
            }

            function generarHorarioHoy(tbody) {
                const diasSemana = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"];
                const hoy = new Date();
                const diaActualJS = hoy.getDay(); // 0 = Domingo, 1 = Lunes, etc.

                // Actualizar título
                tituloHoy.innerHTML = `<i class="bi bi-calendar-event"></i> Clases de Hoy (${diasSemana[diaActualJS]})`;
                contenedorHoy.innerHTML = ''; // Limpiar contenedor

                if (diaActualJS === 0) {
                    contenedorHoy.innerHTML = '<p class="text-success mb-0 fw-bold"><i class="bi bi-cup-hot"></i> Es domingo, no hay clases programadas. ¡A descansar!</p>';
                    return;
                }

                // Buscar las materias del día actual gracias a los atributos 'data-dia' inyectados por Python
                const materiasHoy = tbody.querySelectorAll(`td[data-dia="${diaActualJS}"]`);

                if (materiasHoy.length === 0) {
                    contenedorHoy.innerHTML = '<p class="text-muted mb-0">No tienes clases programadas para hoy en este semestre.</p>';
                    return;
                }

                // Crear las mini-tarjetas para cada clase
                materiasHoy.forEach(celda => {
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

            // Ejecutar al cambiar el select
            select.addEventListener('change', actualizarHorario);

            // Ejecutar al cargar la página para verificar el estado inicial
            actualizarHorario();
        });