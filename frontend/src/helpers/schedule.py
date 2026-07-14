materias = [
    {'cod': 19801, 'semester': 7, 'color': "bg-danger"   , 'name': "OB", 'type':"PROBABILIDAD Y ESTADÍSTICA"},
    {'cod': 19804, 'semester': 7, 'color': "bg-success"  , 'name': "OB", 'type':"TERMODINÁMICA APLICADA"},
    {'cod': 1817,  'semester': 7, 'color': "bg-primary"  , 'name': "OB", 'type':"DISEÑO POR ELEMENTOS FINITOS"},
    {'cod': 19802, 'semester': 7, 'color': "bg-warning"  , 'name': "OB", 'type':"ASEGURAMIENTO METROLÓGICO"},
    {'cod': 1082,  'semester': 7, 'color': "bg-secondary", 'name': "OC", 'type':"CÁTEDRA DE CONTEXTO"},
    {'cod': 19803, 'semester': 7, 'color': "bg-secondary", 'name': "OC", 'type':"PRODUCCIÓN DE TEXTOS CIENTÍFICOS"},
    
    {'cod': 19806, 'semester': 8, 'color': "bg-danger"   , 'name': "OB", 'type':"DISEÑO EXPERIMENTAL"} ,
    {'cod': 1818,  'semester': 8, 'color': "bg-success"  , 'name': "OB", 'type':"TRANSFERENCIA DE CALOR"} ,
    {'cod': 19805, 'semester': 8, 'color': "bg-danger"   , 'name': "OB", 'type':"MANTENIMIENTO DE EQUIPOS INDUSTRIALES"} ,
    {'cod': 1823,  'semester': 8, 'color': "bg-primary"  , 'name': "OB", 'type':"DISEÑO DE MÁQUINAS"} ,
    {'cod': "-",   'semester': 8, 'color': "bg-secondary", 'name': "EE", 'type':"ELECTIVA EXTRÍNSECA"} ,
    {'cod': 1805,  'semester': 8, 'color': "bg-primary"  , 'name': "OB", 'type':"SISTEMAS DINÁMICOS Y CONTROL"} ,
    #{'cod': , 'name': , 'type':} ;
]

# Filtrar materias del semestre 7
materias_7 = [materia for materia in materias if materia['semester'] == 7]

# Colores de Bootstrap para diferenciar las materias
#colores = ["bg-danger", "bg-primary", "bg-success", "bg-warning text-dark", "bg-secondary", "bg-info text-dark"]

# Matriz para organizar el horario: 6 días (Lunes a Sábado), 16 horas (6:00 a 21:00)
# Inicializamos todo en None    
horario = {dia: {hora: None for hora in range(6, 22)} for dia in range(6)}

# Asignaciones arbitrarias: Cada materia tiene 2 bloques de 2 horas. 
# Formato: (día_1, hora_inicio_1), (día_2, hora_inicio_2)
# Días: 0=Lunes, 1=Martes, 2=Miércoles, 3=Jueves, 4=Viernes, 5=Sábado
bloques_arbitrarios = [
    [(1, 20), (4, 20)],  #PROBABILIDAD Y ESTADÍSTICA 
    [(0, 18), (2, 18)],  #TERMODINÁMICA APLICADA
    [(5, 10), (5, 12)],  #DISEÑO POR ELEMENTOS FINITOS
    [(2, 20), (3, 18)],  #ASEGURAMIENTO METROLÓGICO
    [(5, 14), (5, 16)],  #CÁTEDRA DE CONTEXTO
    [(0, 20), (1, 18)]   #PRODUCCIÓN DE TEXTOS CIENTÍFICOS
]

# Llenar la matriz del horario
for i, materia in enumerate(materias_7):
    bloques = bloques_arbitrarios[i]
    #color = colores[i % len(colores)]
    
    for dia, hora_inicio in bloques:
        # Guardamos la info en la primera hora del bloque
        horario[dia][hora_inicio] = {
            'nombre': materia['type'],
            'color':  materia['color'],
            'es_inicio': True
        }
        # Marcamos la segunda hora para que el HTML sepa que debe saltarse esta celda (por el rowspan)
        horario[dia][hora_inicio + 1] = {
            'es_inicio': False
        }

# Generar el HTML
html_output = ""

for hora in range(6, 22):
    # Fila de almuerzo
    html_output += f"""
                                <tr>
                                    <th scope="row">{hora}:00 - {hora+1}:00</th>"""
    
    for dia in range(6):
        celda = horario[dia][hora]
        
        if celda is None:
            # Espacio vacío
            html_output += "\n                                    <td></td>"
        elif celda['es_inicio']:
            # Inicio de un bloque de 2 horas (usamos rowspan="2")
            html_output += f"""
                                    <td rowspan="2" class="align-middle">
                                        <div class="materia-slot {celda['color']} text-white">
                                            {celda['nombre']}<br><small>Aula Por Definir</small>
                                        </div>
                                    </td>"""
        # Si es_inicio es False, es la segunda hora del bloque. 
        # No agregamos <td> porque el rowspan="2" de la fila anterior ya ocupa este espacio.

    html_output += "\n                                </tr>"

# Guardar en archivo
with open("filas_horario.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("¡Listo! Copia el contenido de 'filas_horario.html' y pégalo dentro de tu <tbody>")