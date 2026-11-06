import csv
from typing import Any

from fastapi import FastAPI

from paginador import paginador


# Show_Id Category Title Director Cast Country Release_Date Rating Duration Type Description

# JSON EJEMPLO 1 DATO:
#
#   {
#       show_id:       "",
#       categoria:     "",
#       titulo:        "",
#       director:      "",
#       reparto:       "",
#       pais:          "",
#       fecha_salida:  "",
#       calificacion:  "",
#       duracion:      "",
#       tipo:          "",
#       descripcion:   "",
#   }

# JSON EJEMPLO MUCHOS DATOS:
#
#   cantidad_total:         Int  4,
#   cantidad_pagina:        Int  2,
#   pagina:                 Int  11,
#   total_paginas:          Int  11,
#   hay_pagina_anterior:    Bool True,
#   hay_pagina_siguiente:   Bool False,
#
#   resultados: [
#       {
#           show_id:       "",
#           categoria:     "",
#           titulo:        "",
#           director:      "",
#           reparto:       "",
#           pais:          "",
#           fecha_salida:  "",
#           calificacion:  "",
#           duracion:      "",
#           tipo:          "",
#           descripcion:   "",
#       },
#
#       2: { ... }, 3: { ... }, 4: { ... }
#   ]


app = FastAPI()


datos:     list[dict[Any, Any]]
peliculas: list[dict[Any, Any]] = []
series:    list[dict[Any, Any]] = []


try:
    with open('database.csv') as csvFile:
        datos = list(csv.DictReader(f=csvFile))

        for item in datos:
            if item['Category'] == 'Movie':
                peliculas.append(item)

            elif item['Category'] == 'TV Show':
                series.append(item)


except FileNotFoundError as e:
    print("FileNotFoundError: ", e)
    exit()


@app.get('/')
def obtener_raiz():
    return {'test': 'datos'}


@app.get('/datos/{index_pagina}')
def obtener_datos(index_pagina: int) -> dict[Any, Any]:
    resultados: dict[Any, Any] = paginador(datos, index_pagina)
    return resultados


@app.get('/peliculas/{index_pagina}')
def obtener_peliculas(index_pagina: int) -> dict[Any, Any]:
    resultados: dict[Any, Any] = paginador(peliculas, index_pagina)
    return resultados


@app.get('/series/{index_pagina}')
def obtener_series(index_pagina: int) -> dict[Any, Any]:
    resultados: dict[Any, Any] = paginador(series, index_pagina)
    return resultados



# INICIAR SERVIDOR:
# LINUX:    PYTHON3 MAIN.PY
# WINDOWS:  PYTHON  MAIN.PY

import uvicorn

if __name__ == "__main__":
    config = uvicorn.Config("main:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    server.run()

