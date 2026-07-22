# discontinousFunction.py
# Implementación de las funciones de singularidad (funciones de Macaulay) para el cálculo de la viga.
#
# Uso desde linea de comandos:
# N/A. Se importa como módulo: from discontinousFunction import numericalDiscontinousFuctions
#
# Flujo:
# 1. Recibe la posición, exponente y magnitud de una carga.
# 2. Evalúa la función discontinua para crear el vector a lo largo del dominio de la viga.
# 3. Suma las contribuciones individuales de cada carga (puntual, distribuida, momento).
# 4. Retorna los vectores numéricos de cortante (V), momento (M), pendiente (theta) y deflexión (y).

import numpy as np
from math import factorial


def discontinousfuction(a, n, A, longitud):
    """
    This function allows obtain the singularity vector of the discontinues functions 

    Args:
        a(number):  ubication of the load.
        n(number):  exponent
        A(number):  load value
        longitud(number): Beam length

    Returns:
        the singularity vector along the beam 
    """
    v = []
    size = round(longitud / 0.01 + 1)

    # Se utiliza linspace para forzar exactamente 'size' puntos entre 0 y longitud
    for x in np.linspace(0, longitud, size):
        if a > x:
            v.append(0)
        else:
            w = (A / factorial(n)) * (x - a)**n
            v.append(w)

    return np.array(v)
       
def numericalDiscontinousFuctions(f,l,typesloads):
    """
    This function allows the singularity numerical value calculation for the loads applied in the beam

    Args:
        f(number):  loads applies in the beam.
        typesloads(list): types of loads allows in the problem's solution
        l(number): Beam length

    Returns:
        the singularity value for every vector of the beam
    """
    size = round(l / 0.01 + 1)

    # Se inicializan como vectores estrictamente 1D
    v     = np.zeros(size)
    M     = np.zeros(size)
    theta = np.zeros(size)
    y     = np.zeros(size)
    loadEq    = 0
    MomentEq  = 0
    
    ## Numerical singularity calculation:
    for key, load in f.items():  
        l_type = load['type']
        val    = load['value']
        a      = load['a']
        a1 = load.get('a1', 0) 

        if l_type == typesloads[0]: # point load  
            v     += discontinousfuction(a, 0, val, l)
            M     += discontinousfuction(a, 1, val, l)  
            theta += discontinousfuction(a, 2, val, l)
            y     += discontinousfuction(a, 3, val, l)
            
            loadEq   += val
            MomentEq += a * val
        elif l_type == typesloads[1]: # Uniformly distributed 
            lengthLoad = a1 - a
            
            v     += discontinousfuction(a, 1, val, l) - discontinousfuction(a1, 1, val, l)
            M     += discontinousfuction(a, 2, val, l) - discontinousfuction(a1, 2, val, l)
            theta += discontinousfuction(a, 3, val, l) - discontinousfuction(a1, 3, val, l)
            y     += discontinousfuction(a, 4, val, l) - discontinousfuction(a1, 4, val, l)
            
            loadEq   += (val * lengthLoad)
            MomentEq += (a + (lengthLoad/2)) * (val * lengthLoad)

        elif l_type == typesloads[2]: # Triangular distributed 1
            lengthLoad = a1 - a
            val_L = val / lengthLoad 
            
            v     += discontinousfuction(a, 2, val, l) * val_L \
                   - discontinousfuction(a1, 2, val, l) * val_L \
                   - discontinousfuction(a1, 1, val, l)
            
            M     += discontinousfuction(a, 3, val, l) * val_L \
                   - discontinousfuction(a1, 3, val, l) * val_L \
                   - discontinousfuction(a1, 2, val, l)
            
            theta += discontinousfuction(a, 4, val, l) * val_L \
                   - discontinousfuction(a1, 4, val, l) * val_L \
                   - discontinousfuction(a1, 3, val, l)
            
            y     += discontinousfuction(a, 5, val, l) * val_L \
                   - discontinousfuction(a1, 5, val, l) * val_L \
                   - discontinousfuction(a1, 4, val, l)
                        
            loadEq   += (val * lengthLoad / 2)
            MomentEq += (a + (lengthLoad * (2/3))) * (val * lengthLoad / 2)
        elif l_type == typesloads[3]: # Triangular distributed 2
            lengthLoad = a - a1
            val_L = val / lengthLoad
            
            v     += discontinousfuction(a, 1, val, l) \
                   - discontinousfuction(a, 2, val, l) * val_L \
                   + discontinousfuction(a1, 2, val, l) * val_L
            
            M     += discontinousfuction(a, 2, val, l) \
                   - discontinousfuction(a, 3, val, l) * val_L \
                   + discontinousfuction(a1, 3, val, l) * val_L
            
            theta += discontinousfuction(a, 3, val, l) \
                   - discontinousfuction(a, 4, val, l) * val_L \
                   + discontinousfuction(a1, 4, val, l) * val_L
            
            y     += discontinousfuction(a, 4, val, l) \
                   - discontinousfuction(a, 5, val, l) * val_L \
                   + discontinousfuction(a1, 5, val, l) * val_L
                        
            loadEq   += (val * lengthLoad / 2)
            MomentEq += (a + (lengthLoad * (1/3))) * (val * lengthLoad / 2)
        elif l_type == typesloads[4]: # Moment
            M     += discontinousfuction(a, 0, val, l) 
            theta += discontinousfuction(a, 1, val, l)  
            y     += discontinousfuction(a, 2, val, l)
            
            MomentEq += val

    return v, M, theta, y, loadEq, MomentEq

def disfunctionScalar(a, n, A, x):
    """
    Calculates the value of the singularity function at a single point x.

    Args:
    a(number): Load location.
    n(number): Exponent.
    A(number): Load value.
    x(number): Point on the beam to be evaluated.

    Returns:
    float: The scalar value at point x.
    """
    if a > x:
        return 0.0
    else:
        return (A / factorial(n)) * (x - a)**n

def pointDiscontinuousFunctions(f, x, typesloads):
    """
    Calculates the scalar numerical value of the singularity (shear, moment, slope, and deflection) for the loads applied at a specific point x.

    Args:
    f(dict): Loads applied to the beam.
    typesloads(list): Load types allowed in the solution.
    x(number): Specific point along the beam.

    Returns:
    v_x, M_x, theta_x, y_x (float): The scalar values ​​at point x.

    """
    v_x = M_x = theta_x = y_x = 0.0

    ## Cálculo escalar de la singularidad en el punto x:
    for key, load in f.items():  
        l_type = load['type']
        val    = load['value']
        a      = load['a']
        a1     = load.get('a1', 0) 

        if l_type == typesloads[0]: # Carga puntual  
            v_x     += disfunctionScalar(a, 0, val, x)
            M_x     += disfunctionScalar(a, 1, val, x)  
            theta_x += disfunctionScalar(a, 2, val, x)
            y_x     += disfunctionScalar(a, 3, val, x)
            
        elif l_type == typesloads[1]: # Carga uniformemente distribuida 
            v_x     += disfunctionScalar(a, 1, val, x) - disfunctionScalar(a1, 1, val, x)
            M_x     += disfunctionScalar(a, 2, val, x) - disfunctionScalar(a1, 2, val, x)
            theta_x += disfunctionScalar(a, 3, val, x) - disfunctionScalar(a1, 3, val, x)
            y_x     += disfunctionScalar(a, 4, val, x) - disfunctionScalar(a1, 4, val, x)

        elif l_type == typesloads[2]: # Carga triangular distribuida 1
            lengthLoad = a1 - a
            val_L = val / lengthLoad 
            
            v_x     += disfunctionScalar(a, 2, val, x) * val_L \
                     - disfunctionScalar(a1, 2, val, x) * val_L \
                     - disfunctionScalar(a1, 1, val, x)
            M_x     += disfunctionScalar(a, 3, val, x) * val_L \
                     - disfunctionScalar(a1, 3, val, x) * val_L \
                     - disfunctionScalar(a1, 2, val, x)
            theta_x += disfunctionScalar(a, 4, val, x) * val_L \
                     - disfunctionScalar(a1, 4, val, x) * val_L \
                     - disfunctionScalar(a1, 3, val, x)
            y_x     += disfunctionScalar(a, 5, val, x) * val_L \
                     - disfunctionScalar(a1, 5, val, x) * val_L \
                     - disfunctionScalar(a1, 4, val, x)
                     
        elif l_type == typesloads[3]: # Carga triangular distribuida 2
            lengthLoad = a - a1
            val_L = val / lengthLoad
            
            v_x     += disfunctionScalar(a, 1, val, x) \
                     - disfunctionScalar(a, 2, val, x) * val_L \
                     + disfunctionScalar(a1, 2, val, x) * val_L
            M_x     += disfunctionScalar(a, 2, val, x) \
                     - disfunctionScalar(a, 3, val, x) * val_L \
                     + disfunctionScalar(a1, 3, val, x) * val_L
            theta_x += disfunctionScalar(a, 3, val, x) \
                     - disfunctionScalar(a, 4, val, x) * val_L \
                     + disfunctionScalar(a1, 4, val, x) * val_L
            y_x     += disfunctionScalar(a, 4, val, x) \
                     - disfunctionScalar(a, 5, val, x) * val_L \
                     + disfunctionScalar(a1, 5, val, x) * val_L
                     
        elif l_type == typesloads[4]: # Momento puntual
            M_x     += disfunctionScalar(a, 0, val, x) 
            theta_x += disfunctionScalar(a, 1, val, x)  
            y_x     += disfunctionScalar(a, 2, val, x)

    return theta_x, y_x