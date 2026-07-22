# main.py
# Archivo principal de ejecución (entry point) que coordina el análisis estructural de la viga.
#
# Uso desde linea de comandos:
# python main.py
#
# Flujo:
# 1. Definición de variables, apoyos y cargas.
# 2. Validación de los datos de entrada.
# 3. Cálculo de singularidad y resolución matricial del sistema (fuerzas y momentos).
# 4. Cálculo de propiedades geométricas (módulo de sección).
# 5. Generación de diagramas (DCL, Cortante, Momento).
# 6. Exportación de resultados a PDF y Excel.

import numpy as np
import pandas as pd
import os 
import sys

from discontinousFunction import numericalDiscontinousFuctions
from matrixSolution import  sumFY, sumM, singularityEq, solveEquation
from extraValidation import loadValidation
from grafication import plot_shear_moment, plot_free_body_diagram
# ── Ajuste de path para encontrar los módulos de PyBeams ─────────────────────

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR) 

## types of loads:
typesloads   = ["Point load",               #0
                "Uniformly distributed",    #1
                "Triangular distributed 1", #2
                "Triangular distributed 2", #3
                "Moment load"]              #4

typesSupport = {
    "Roller" : 1,
    "Pinned" : 1,  
    "Fixed"  : 2 
}

## I. Segment to define initial values and boundary conditions:  

#____________________________________________________________________________________
# Using this code section you can defined the boundary conditions of the beam problem:
#____________________________________________________________________________________

#---------------------------------------
# variables  | units |  Description    |
#---------------------------------------
l  = 12 #    | [m]   |  Beam length    |  
Sy = 344 #   | [MPa] |  Yield strength |  ASTM A 572
FS = 1.5 #   | [ - ] |  Safety Factor  |  
#---------------------------------------

## II. Supports beams:
#____________________________________________________________________________________
# Code Section to define the supports that ensure the sujection of the beam
#____________________________________________________________________________________
r = {
    'A' : {'location' : 0   , 'dof' : typesSupport['Fixed'], 'type' : "Fixed"},
    'B' : {'location' : l   , 'dof' : typesSupport['Fixed'], 'type' : "Fixed"}
}
#------------------------------------------------------------

## III. Loads applys:
#____________________________________________________________________________________
# Code Section to define the loads applies in the beam
# (You can define the number of loads of your preference as long as the nomenclature 
#  is respected.)
#____________________________________________________________________________________
f = {
    'Fa' : {'value' : -90, 'a' : 0 , 'a1' : l , 'type' : typesloads[1]},
}

## ------------------------------------------------------------
## EXTRA DATA VALIDATION
## ------------------------------------------------------------

loadValidation(f,typesloads,l)

#------------------------------------------------------------
##

def beamSolving(r, f, typesloads ,l):
    ## 2. Numerical calculation for the external loads applied in the beam:
    v, M, theta, y, loadEq, MomentEq = numericalDiscontinousFuctions(f, l, typesloads)
    
    ##3. Matrix solution:

    ##Creating a list with unknows variables:
    unknowns = []

    for key,support in r.items():

        unknowns.append(
            {
                'name':f'{key}y',
                'location':support['location'],
                'kind':'force'
            }
        )

        if support['dof'] == 2:

            unknowns.append(
                {
                    'name':f'M{key}',
                    'location':support['location'],
                    'kind':'moment'
                }
            )

    # 3.1 We obtain the equations to solve the problem in shape of a matrix:
    sumForces = sumFY(unknowns)                                 
    totalMoments, sumMoment = sumM(unknowns, MomentEq, loadEq)  

    # Las constantes de integración C1/C2 de la curva de deflexión siempre están
    # presentes como incógnitas, así que las ecuaciones de frontera siempre son
    # necesarias, sea la viga estáticamente determinada o indeterminada.
    sumSingularity, total_y = singularityEq(unknowns, r, f, typesloads)

    # 3.2 Equation solution and calculation of the singularity support reaction:
    # <-- Cambiar 'r' por 'unknowns' al final
    x, r_sol = solveEquation(sumForces, sumMoment, sumSingularity, loadEq, totalMoments, total_y, unknowns)

    # Unpack the reaction forces
    r_v, r_M, r_theta, r_y, r_loadEq, r_MomentEq = numericalDiscontinousFuctions(r_sol, l, typesloads)

    # Add them to the totals

    #At this point we obtained all the values needs to solves the beam static

    v        += r_v
    M        += r_M
    theta    += r_theta    
    y        += r_y
    loadEq   += r_loadEq
    MomentEq += r_MomentEq

    #We obtain the moment maximum value:
    Mmax = max([abs(np.min(M)), np.max(M)])

    #Printing the results
    #_____________________________________________________________________________

    print('-----------------LOAD RECTIONS VALUES:----------------------')

    data_list = []
    for name, data in r_sol.items():
        data_list.append({
            "Support": name,
            "Value": round(data.get('value', 0),3),
            "location": data.get('a', 'N/A'),
            "units": 'kN' if data.get('type') == typesloads[0] else 'kN.m'
    })

    result = pd.DataFrame(data_list)
    print(result.to_string(index=False)) 

    print("------------------------------------------------------------\n")

    print('-----------------BEAM PROPIETIES----------------------')
    print(f'Mmax = {round(Mmax,2)} kN.m')

    #_____________________________________________________________________________

    #3.3 Grafication:
    plot_shear_moment(v.flatten(), M.flatten(), l, xMax=None)
  
    return Mmax, r_sol, unknowns

def beamGeometry(Mmax, Sy, FS):

    sigmaAllow = Sy * 1000 / FS  #[kPa]Allowed Stress
    s = Mmax / sigmaAllow        #[m3] Section modulus required to withstand external forces
    s = s * 100**3               #[cm3]
    return s


Mmax, r_sol, unknowns = beamSolving(r,f,typesloads,l)
s = beamGeometry(Mmax, Sy, FS)

print(f'Required sectioning module (s): {round(s,2)} cm3' )
print("------------------------------------------------------------\n")

plot_free_body_diagram(r, f, typesloads, l, filename="diagrama_cuerpo_libre.png")

#---------------------------------------------------------
# 4. Generación del reporte en PDF
# generar_reporte_pdf(
#     filename_prefix="Reporte_Viga", 
#     l=l, 
#     Sy=Sy, 
#     FS=FS, 
#     r_sol=r_sol, 
#     r = r,
#     f=f, 
#     Mmax=Mmax, 
#     typesloads=typesloads, 
#     imagen_diagramas=os.path.abspath(os.path.join("report", "diagramas_viga.png")),
#     imagen_dcl=os.path.abspath(os.path.join("report", "diagrama_cuerpo_libre.png")),
#     output_dir="report"
# )

#--------------------------------------------------------------
#5. Generacion de reporte en Excel 
# if __name__ == "__main__":
#     path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(SCRIPT_DIR, "PyBeams.xlsx")

#     main(
#         path, 
#         r, 
#         f, 
#         l, 
#         Sy, 
#         FS, 
#         r_sol, 
#         Mmax, 
#         s,
#         img_dcl=os.path.abspath(os.path.join("report", "diagramas_viga.png")),
#         img_vm =os.path.abspath(os.path.join("report", "diagrama_cuerpo_libre.png")))

#-----------------------------------------------------------------




#-----------------------------------------------------------------
#6. Solucion del ejercicio en excel:

