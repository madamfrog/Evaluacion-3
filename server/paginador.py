from typing import Any

CANTIDAD_POR_PAGINA: int = 10

def paginador(datos: list[dict[Any, Any]], index_pagina: int) -> dict[Any, Any]:
    desde: int = CANTIDAD_POR_PAGINA * index_pagina
    hasta: int = CANTIDAD_POR_PAGINA + desde

    hay_anterior:  bool
    hay_siguiente: bool

    resultados: list[dict[Any, Any]]

    if hasta > len(datos):
        resultados = datos[desde: ]

    else:
        resultados = datos[desde: hasta]

    cantidad_total:  int = len(datos)
    cantidad_pagina: int = len(resultados)

    hay_anterior, hay_siguiente = verificar_paginador(datos, desde, hasta)

    return {
        'cantidad_total':  cantidad_total,
        'cantidad_pagina': cantidad_pagina,
        'pagina':          index_pagina,
        'hay_anterior':    hay_anterior,
        'hay_siguiente':   hay_siguiente,
        'resultados':      resultados,
    }


def verificar_paginador(datos: list[dict[Any, Any]], desde: int, hasta: int) -> tuple[bool, bool]:
    """
        datos: list[dict[Any, Any]]
        desde: int
        hasta: int

        retorna tuple[bool, bool]
        return hay_anterior: bool, hay_siguiente: bool
    """

    hay_anterior:  bool
    hay_siguiente: bool

    if desde == 0:
        hay_anterior = False
    else:
        hay_anterior = True

    try:
        datos[hasta + 1]
        hay_siguiente = True

    except IndexError:
        hay_siguiente = False

    return hay_anterior, hay_siguiente
