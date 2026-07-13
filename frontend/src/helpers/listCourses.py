# 1. Lista de diccionarios corregida
courses = [
    {'cd': 1, 'name': "Cálculo Diferencial", 'credits': 4, 'clasification': "Obligatorio Básico", 'semester': 1, 'color': "danger"},
    {'cd': 4, 'name': "Cátedra Francisco José de Caldas", 'credits': 1, 'clasification': "Obligatorio Complementario", 'semester': 1, 'color': "secondary"},
    {'cd': 9, 'name': "Álgebra Lineal", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 1, 'color': "danger"},
    {'cd': 1054, 'name': "Producción y Comprensión de Textos I", 'credits': 3, 'clasification': "Obligatorio Complementario", 'semester': 1, 'color': "secondary"},
    {'cd': 1075, 'name': "Ética y Sociedad", 'credits': 2, 'clasification': "Obligatorio Complementario", 'semester': 1, 'color': "secondary"},
    {'cd': 1411, 'name': "Dibujo Técnico", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 1, 'color': "warning"},
    {'cd': 19701, 'name': "Introducción a la Mecánica Industrial", 'credits': 1, 'clasification': "Obligatorio Básico", 'semester': 1, 'color': "warning"},
    {'cd': 9901, 'name': "Segunda Lengua I - Inglés", 'credits': 2, 'clasification': "Obligatorio Complementario", 'semester': 1, 'color': "secondary"},
    
    {'cd': 3, 'name': "Física I: Mecánica Newtoniana", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 2, 'color': "danger"},
    {'cd': 7, 'name': "Cálculo Integral", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 2, 'color': "danger"},
    {'cd': 12, 'name': "Cátedra Democracia y Ciudadanía", 'credits': 1, 'clasification': "Obligatorio Complementario", 'semester': 2, 'color': "secondary"},
    {'cd': 1056, 'name': "Producción y comprensión de Textos II", 'credits': 2, 'clasification': "Obligatorio Complementario", 'semester': 2, 'color': "secondary"},
    {'cd': 19702, 'name': "Materiales Metálicos", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 2, 'color': "warning"},
    {'cd': 19703, 'name': "Dibujo de Elementos de Máquinas", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 2, 'color': "warning"},
    {'cd': 19704, 'name': "Fundamentos de Programación", 'credits': 1, 'clasification': "Obligatorio Básico", 'semester': 2, 'color': "primary"},
    {'cd': 9903, 'name': "Segunda Lengua II - Inglés", 'credits': 2, 'clasification': "Obligatorio Complementario", 'semester': 2, 'color': "secondary"},
    
    {'cd': 13, 'name': "Física II: Electromagnetismo", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 3, 'color': "danger"},
    {'cd': 1060, 'name': "Ciencia Tecnología y Sociedad", 'credits': 2, 'clasification': "Obligatorio Complementario", 'semester': 3, 'color': "secondary"},
    {'cd': 1421, 'name': "Estatica", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 3, 'color': "primary"},
    {'cd': 19705, 'name': "Materiales Poliméricos y Compuestos", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 3, 'color': "warning"},
    {'cd': 19706, 'name': "Dibujo de Taller Industrial", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 3, 'color': "warning"},
    {'cd': 19707, 'name': "Metrología Dimensional", 'credits': 1, 'clasification': "Obligatorio Básico", 'semester': 3, 'color': "warning"},
    {'cd': 9903, 'name': "Segunda Lengua III - Inglés", 'credits': 2, 'clasification': "Obligatorio Complementario", 'semester': 3, 'color': "secondary"},
    {'cd': 19708, 'name': "Procesos de Mecanizado I", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 3, 'color': "warning"},
    
    {'cd': 16, 'name': "Cálculo Multivariado", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 4, 'color': "danger"},
    {'cd': 1433, 'name': "Mecanica de Fluidos", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 4, 'color': "success"},
    {'cd': 1436, 'name': "Resistencia de Materiales", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 4, 'color': "primary"},
    {'cd': 19709, 'name': "Procesos de Mecanizado II", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 4, 'color': "warning"},
    {'cd': 19710, 'name': "Dinámica de Mecanismos", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 4, 'color': "warning"},
    {'cd': 1428, 'name': "Física III: Ondas y Física Moderna", 'credits': 3, 'clasification': "Componente Propedéutico", 'semester': 4, 'color': "danger"},
    
    {'cd': 88, 'name': "Ecuaciones Diferenciales", 'credits': 3, 'clasification': "Componente Propedéutico", 'semester': 5, 'color': "danger"},
    {'cd': 1426, 'name': "Termodinámica", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 5, 'color': "success"},
    {'cd': 19711, 'name': "Mantenimiento de Máquinas", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 5, 'color': "danger"},
    {'cd': 19712, 'name': "Procesos de Conformado", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 5, 'color': "warning"},
    {'cd': 19713, 'name': "Elementos de Máquinas I", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 5, 'color': "primary"},
    {'cd': "-", 'name': "Electiva intriseca 1", 'credits': 2, 'clasification': "Electivo Intrinseco", 'semester': 5, 'color': "light"},
    {'cd': "-", 'name': "Electiva intriseca 2", 'credits': 2, 'clasification': "Electivo Intrinseco", 'semester': 5, 'color': "light"},
    
    {'cd': 1446, 'name': "Trabajo de Grado Tecnológico", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 6, 'color': "light"},
    {'cd': 19714, 'name': "Diseño de Procesos de Fabricación", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 6, 'color': "warning"},
    {'cd': 19715, 'name': "Elementos de Máquinas II", 'credits': 3, 'clasification': "Obligatorio Básico", 'semester': 6, 'color': "primary"},
    {'cd': 19716, 'name': "Máquinas Eléctricas", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 6, 'color': "success"},
    {'cd': 1824, 'name': "Máquinas Hidráulicas", 'credits': 3, 'clasification': "Componente Propedéutico", 'semester': 6, 'color': "success"},
    {'cd': "-", 'name': "Electiva intriseca 3", 'credits': 2, 'clasification': "Electivo Intrinseco", 'semester': 6, 'color': "light"},
    {'cd': "-", 'name': "Electiva extrinseca", 'credits': 2, 'clasification': "Obligatorio Básico", 'semester': 6, 'color': "light"}
]

# 2. Lógica para construir el HTML
html_output = ""

# Hay 6 semestres en total en tus datos
for semester_num in range(1, 7):
    # Filtrar cursos del semestre actual
    sem_courses = [c for c in courses if c['semester'] == semester_num]
    
    # Sumar los créditos del semestre
    total_credits = sum(c['credits'] for c in sem_courses)
    
    # Iniciar la columna y la tarjeta del semestre
    html_output += f"""
                            <!-- Columna {semester_num} -->
                            <div class="col">
                                <div class="card text-center mt-1">
                                    <div class="card-header">
                                        <h4>Semestre {semester_num}</h4>
                                    </div>"""
    
    # Crear cada tarjeta de materia dentro del semestre
    for index, course in enumerate(sem_courses):
        color = course['color']
        name = course['name'].upper() # Nombre en mayúsculas como en tu ejemplo
        credits = course['credits']
        cod = course['cd']
        clasification = course['clasification']
        # Agregar mt-3 a la primera tarjeta del semestre
        margin_top = " mt-3" if index == 0 else ""
        
        html_output += f"""
                                    <!-- Tarjeta {index + 1} -->
                                    <div class="card border-{color} text-{color} mb-3{margin_top}">
                                        <div class="card-header border-{color}">
                                            {cod}
                                        </div>
                                        <div class="card-body">
                                            <h5 class="card-title">{name}</h5>
                                        </div>
                                        <div class="card-footer border-{color} text-{color}">
                                            Creditos: {credits}
                                        </div>
                                    </div>"""
                                    
    # Cerrar la tarjeta del semestre y agregar el total de créditos
    html_output += f"""s
                                    <div class="card-footer border-secondary text-secondary">
                                            <h5>Total de creditos: {total_credits}</h5>
                                    </div>
                                </div>
                            </div>"""

# 3. Guardar el resultado en un archivo para que sea fácil de copiar
with open("coursesCards.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("HTML generado exitosamente. Revisa el archivo 'codigo_generado.html'")