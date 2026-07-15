// Datos del horario de clases
//
// Igual que en courses-data.js: aquí van los datos, y main.shedule.js
// arma la tabla automáticamente. Para agregar, quitar o mover una clase,
// edita este archivo — no toques el HTML ni el JS de renderizado.
//
// meta.horaInicio / meta.horaFin: definen el rango de horas que se
// dibuja en la tabla (de 6 a 22 = filas de 6:00 a 21:00-22:00).
//
// Cada semestre tiene un "label" (texto que se muestra en el <select>)
// y un arreglo "classes" con las clases de esa semana típica.
//
// Cada clase:
//   dia         -> 1=Lunes, 2=Martes, 3=Miércoles, 4=Jueves, 5=Viernes, 6=Sábado
//                  (mismo criterio que Date.getDay(), 0 sería Domingo)
//   horaInicio  -> hora en que empieza (número entero, ej: 10)
//   horaFin     -> hora en que termina (número entero, ej: 12)
//   materia     -> nombre de la materia
//   color       -> clase de Bootstrap para el color (bg-primary, bg-success, etc.)
//   aula        -> (opcional) si no se define, se muestra "Aula Por Definir"
//
// No es necesario que las clases estén en orden ni agrupadas por día,
// el script las ubica solo. Si dos clases chocan en el mismo horario,
// gana la última que aparezca en el arreglo.

const SCHEDULE = {
    meta: {
        horaInicio: 6,
        horaFin: 22
    },
    semesters: {
        7: {
            label: "Semestre 7 (2026-2)",
            classes: [
                { dia: 6, horaInicio: 10, horaFin: 12, materia: "DISEÑO POR ELEMENTOS FINITOS", color: "bg-primary" },
                { dia: 6, horaInicio: 12, horaFin: 14, materia: "DISEÑO POR ELEMENTOS FINITOS", color: "bg-primary" },
                { dia: 6, horaInicio: 14, horaFin: 16, materia: "CÁTEDRA DE CONTEXTO", color: "bg-secondary" },
                { dia: 6, horaInicio: 16, horaFin: 18, materia: "CÁTEDRA DE CONTEXTO", color: "bg-secondary" },

                { dia: 1, horaInicio: 18, horaFin: 20, materia: "TERMODINÁMICA APLICADA", color: "bg-success" },
                { dia: 2, horaInicio: 18, horaFin: 20, materia: "PRODUCCIÓN DE TEXTOS CIENTÍFICOS", color: "bg-secondary" },
                { dia: 3, horaInicio: 18, horaFin: 20, materia: "TERMODINÁMICA APLICADA", color: "bg-success" },
                { dia: 4, horaInicio: 18, horaFin: 20, materia: "ASEGURAMIENTO METROLÓGICO", color: "bg-warning" },

                { dia: 1, horaInicio: 20, horaFin: 22, materia: "PRODUCCIÓN DE TEXTOS CIENTÍFICOS", color: "bg-secondary" },
                { dia: 2, horaInicio: 20, horaFin: 22, materia: "PROBABILIDAD Y ESTADÍSTICA", color: "bg-danger" },
                { dia: 3, horaInicio: 20, horaFin: 22, materia: "ASEGURAMIENTO METROLÓGICO", color: "bg-warning" },
                { dia: 5, horaInicio: 20, horaFin: 22, materia: "PROBABILIDAD Y ESTADÍSTICA", color: "bg-danger" }
            ]
        },
        8: {
            label: "Semestre 8",
            classes: []
        },
        9: {
            label: "Semestre 9",
            classes: []
        }
    }
};
