# matrixSolution.py
# Ensamblaje y resolución del sistema de ecuaciones lineales para la estática de la viga.
#
# Uso desde linea de comandos:
# N/A. Se importa como módulo: from matrixSolution import sumFY, sumM, singularityEq, solveEquation
#
# Flujo:
# 1. Construye el vector de variables para la sumatoria de fuerzas en Y.
# 2. Construye el vector de variables para la sumatoria de momentos.
# 3. Extrae ecuaciones adicionales de las condiciones de frontera (singularidad) si es hiperestática.
# 4. Resuelve el sistema matricial (Ax = B) utilizando numpy.linalg.solve.
# 5. Retorna las reacciones calculadas en los apoyos.

import numpy as np
from discontinousFunction import pointDiscontinuousFunctions

def sumFY(unknowns):
    """
    This function allows obtain the variables vector of the summatory of forces in y

    Args:
        r(dictionary): List supports's information.

    Returns:
        vector that contain ones with the number of variables
    """
    Ry = []
    for u in unknowns:
        if u['kind'] == 'force':
            Ry.append(1)
        else:
            Ry.append(0) # Los momentos de reacción no entran en sumatoria de fuerzas Y
            
    Ry.extend([0, 0]) # Constantes de integración C1 y C2
    return np.array(Ry)

def sumM(unknowns, moment, loadEq):
    """
    This function determinate the variable vector for the moment's equation

    Args:
        r(dictionary): List supports's information.
        moment(number): value of the moments provocated for the external loads

    Returns:
        vector that contain ones with the number of variables      
    
    """
    # To the moment's summatories in the first supports. The support that has 
    # the shortest distance from the origin is obtained:

    # Tomamos momento desde la ubicación del primer apoyo
    d = min(u['location'] for u in unknowns)

    if d != 0: 
        totalMoments = moment - (d * loadEq) 
    else: 
        totalMoments = moment

    momentMatrix = []
    for u in unknowns:
        if u['kind'] == 'force':
            momentMatrix.append(u['location'] - d)
        elif u['kind'] == 'moment':
            momentMatrix.append(1) # Un momento puro aporta 1 a la sumatoria
            
    momentMatrix.extend([0,0]) # Constantes de integración C1 y C2 
    return totalMoments, np.array(momentMatrix)

def singularityEq(unknowns, r, f, typesloads):
    matrix_eqs = []
    results = []

    for key, support in r.items():
        x = support['location']
        theta_ext, y_ext = pointDiscontinuousFunctions(f, x, typesloads)
        
        # --- Condición de frontera 1: Deflexión (y) = 0 ---
        row_y = []
        for u in unknowns:
            a = u['location']
            if x < a:
                row_y.append(0)
            else:
                if u['kind'] == 'force':
                    row_y.append((x - a)**3 / 6)
                elif u['kind'] == 'moment':
                    row_y.append((x - a)**2 / 2)
        row_y.extend([x, 1]) # C1*x + C2
        matrix_eqs.append(row_y)
        results.append(y_ext)

        # --- Condición de frontera 2: Pendiente (theta) = 0 (SOLO para Fixed) ---
        if support['dof'] == 2:
            row_theta = []
            for u in unknowns:
                a = u['location']
                if x < a:
                    row_theta.append(0)
                else:
                    if u['kind'] == 'force':
                        row_theta.append((x - a)**2 / 2)
                    elif u['kind'] == 'moment':
                        row_theta.append((x - a)**1) # (x-a)^1 / 1!
            row_theta.extend([1, 0]) # C1*(1) + C2*(0)
            matrix_eqs.append(row_theta)
            results.append(theta_ext)

    return np.array(matrix_eqs), np.array(results)

def solveEquation(sumForces, sumMoment, sumSingularity, loadEq, totalMoments, total_y, unknowns):
    if sumSingularity is not None:
        A = np.vstack([sumForces, sumMoment, sumSingularity], dtype=float)
        B = np.hstack([loadEq, totalMoments, total_y], dtype=float) * -1
    else:
        A = np.vstack([sumForces, sumMoment], dtype=float)
        B = np.hstack([loadEq, totalMoments], dtype=float) * -1
        
    X = np.linalg.solve(A, B)
    
    # Formatear el arreglo de vuelta usando la lista de incógnitas
    R_sol = {}
    for i, u in enumerate(unknowns):
        nombre = u['name']
        R_sol[nombre] = {
            'value': float(X[i]), 
            'a': u['location'], 
            'type': 'Point load' if u['kind'] == 'force' else 'Moment load'
        }
    
    return X, R_sol



        



        


    
