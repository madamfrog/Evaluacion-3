import datetime
import logging
from typing import Any, Literal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from online.forms import PreguntasForm
from online.ia_utils import AsistenteIA
from online.models import Preguntas, Respuesta, Usuario

logger: logging.Logger = settings.LOGGER


@login_required
def IndexAdmin(request: HttpRequest) -> HttpResponse:
    """
    Vista principal de administración con insights de IA
    """
    usuario: object = request.user

    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin
    es_tecnico: int = usuario.tecnico

    if not es_admin and not es_tecnico:
        usuario_id: Any | None = usuario.pk
        return redirect(f"/Inicio/{usuario_id}")

    preguntas_ordenadas: QuerySet[Preguntas] = Preguntas.objects.all().order_by(
        "-Fecha_creacion"
    )

    # tendencias_ia = []
    # estadisticas_ia = {}
    # alertas_ia = []

    # FELIPE: NO ES NECESARIO, ESTOS DATOS SE MUESTRAN EN ANALITICS IA

    # try:
    #     asistente_ia = AsistenteIA()
    #     recomendador_ia = RecomendadorIA()
    #     preguntas_recientes = ListaPreguntas.filter(
    #         Fecha_creacion__gte=timezone.now() - timedelta(days=7)
    #     )[:10]
    #     preguntas_semana = ListaPreguntas.filter(
    #         Fecha_creacion__gte=timezone.now() - timedelta(days=7)
    #     ).count()

    #     for pregunta in preguntas_recientes:
    #         categoria = asistente_ia.clasificar_pregunta(pregunta.Pregunta)
    #         tendencias_ia.append({
    #             'id': pregunta.idPregunta,
    #             'titulo': pregunta.Titulo,
    #             'categoria': categoria,
    #             'usuario': pregunta.Usuario.usuario,
    #             'fecha': pregunta.Fecha_creacion
    #         })

    #     total_preguntas = ListaPreguntas.count()
    #     preguntas_sin_respuesta = ListaPreguntas.filter(
    #         respuesta__isnull=True
    #     ).count()
    #     if total_preguntas > 0:
    #         estadisticas_ia = {
    #             'total_preguntas': total_preguntas,
    #             'preguntas_sin_respuesta': preguntas_sin_respuesta,
    #             'porcentaje_resueltas': (
    #                 (total_preguntas - preguntas_sin_respuesta) / total_preguntas
    #             ) * 100,
    #             'tendencia_semanal': preguntas_semana
    #         }
    #         if preguntas_sin_respuesta > 5:
    #             alertas_ia.append({
    #                 'tipo': 'warning',
    #                 'mensaje': f'⚠️ Hay {preguntas_sin_respuesta} preguntas sin respuesta',
    #                 'prioridad': 'alta'
    #             })
    #         if preguntas_semana > 20:
    #             alertas_ia.append({
    #                 'tipo': 'info',
    #                 'mensaje': '📈 Alta actividad esta semana',
    #                 'prioridad': 'media'
    #             })
    # except Exception as e:
    #     print(f"Error en análisis de IA: {e}")
    #     estadisticas_ia = {
    #         'total_preguntas': ListaPreguntas.count(),
    #         'preguntas_sin_respuesta': ListaPreguntas.filter(
    #             respuesta__isnull=True
    #         ).count(),
    #         'error_ia': True
    #     }

    return render(
        request       = request,
        template_name = "indexAdmin.html",
        context       = {
            "preguntas": preguntas_ordenadas,
            # "tendencias_ia": tendencias_ia,
            # "estadisticas_ia": estadisticas_ia,
            # "alertas_ia": alertas_ia,
        },
    )


@login_required
@require_POST
def BorrarPregunta(request: HttpRequest, idPregunta: int) -> HttpResponse:
    """
    Vista para borrar preguntas con verificación de IA
    """

    usuario: object = request.user
    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin
    es_tecnico: int = usuario.tecnico

    if not es_admin and not es_tecnico:
        usuario_id: Any | None = usuario.pk
        return redirect(f"/Inicio/{usuario_id}")

    if es_tecnico:
        return redirect("/Administracion/")

    pregunta: Preguntas = get_object_or_404(Preguntas, idPregunta=idPregunta)

    pregunta.delete()

    return redirect("/Administracion/")


@login_required
def ModificarPregunta(request: HttpRequest, idPregunta: int) -> HttpResponse:
    """
    Vista para modificar preguntas con asistencia de IA
    """

    usuario: object = request.user
    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin

    if not es_admin:
        usuario_id: Any | None = usuario.pk
        return redirect(f"/Inicio/{usuario_id}")

    pregunta = get_object_or_404(Preguntas, idPregunta=idPregunta)
    sugerencias_ia: list[Any] = []

    asistente_ia: AsistenteIA = AsistenteIA()
    categoria_ia: str = ""
    preguntas_similares: list[Any] = []

    # FELIPE: NO ES NECESARIO, ESTOS DATOS SE MUESTRAN EN ANALITICS IA

    # 🔥 INTEGRACIÓN DE IA: Análisis de la pregunta y sugerencias
    # try:
    #     recomendador_ia = RecomendadorIA()

    #     # 1. Clasificar la pregunta
    #     categoria_ia = asistente_ia.clasificar_pregunta(Pregunta.Pregunta)

    #     # 2. Generar sugerencias de mejora
    #     sugerencia_prompt = f"""
    #     Como experto en soporte técnico, analiza esta pregunta y sugiere mejoras:

    #     Título actual: {Pregunta.Titulo}
    #     Pregunta actual: {Pregunta.Pregunta}
    #     Categoría detectada: {categoria_ia}

    #     Sugiere:
    #     1. Un título más descriptivo
    #     2. Cómo mejorar la claridad de la pregunta
    #     3. Información adicional que sería útil

    #     Responde en formato JSON.
    #     """

    #     try:
    #         respuesta_ia = asistente_ia.generar_respuesta_automatica(sugerencia_prompt)
    #         # Intentar parsear como JSON, si falla usar texto plano
    #         if "{" in respuesta_ia and "}" in respuesta_ia:
    #             sugerencias_ia = json.loads(respuesta_ia)
    #         else:
    #             sugerencias_ia = [{"sugerencia": respuesta_ia}]
    #     except:
    #         sugerencias_ia = [
    #             {"sugerencia": "No se pudieron generar sugerencias en este momento."}
    #         ]

    #     # 3. Buscar preguntas similares para referencia
    #     preguntas_similares = recomendador_ia.recomendar_respuestas_similares(
    #         Pregunta.Pregunta
    #     )

    # except Exception as e:
    #     print(f"Error en análisis IA de pregunta: {e}")
    #     sugerencias_ia = [{"error": "El asistente de IA no está disponible"}]

    form: PreguntasForm = PreguntasForm(instance=pregunta)

    if request.method == "POST":
        response_post: dict[Any, Any] = request.POST.dict()

        # FELIPE: CAMBIE LA LOGICA PARA AGREGAR USUARIO Y FECHA DE CREACION (POR DEFECTO EN EL POST ERA '' Y DABA INVALIDO EN IS_VALID)
        response_post.update(
            {"Usuario": pregunta.Usuario, "Fecha_creacion": pregunta.Fecha_creacion}
        )

        formulario_preguntas = PreguntasForm(response_post, instance=pregunta)

        if formulario_preguntas.is_valid():
            # 🔥 INTEGRACIÓN DE IA: Re-clasificar después de modificación

            nueva_categoria: str = asistente_ia.clasificar_pregunta(
                response_post["Pregunta"]
            )

            # Aquí podrías guardar la categoría si agregas el campo al modelo
            logger.info(
                f"Pregunta modificada - Nueva categoría IA: {nueva_categoria}"
            )

            formulario_preguntas = PreguntasForm(response_post, instance=pregunta)
            formulario_preguntas.save()

            messages.success(request, "Pregunta modificada correctamente.")
            return redirect("/Administracion/")
        else:
            messages.error(request, "Error en el formulario. Verifica los datos.")

    resultado_categoria_ia: str
    resultado_preguntas_similares: list[Any]

    if "categoria_ia" in locals():
        resultado_categoria_ia = categoria_ia
    else:
        resultado_categoria_ia = "No disponible"

    if "preguntas_similares" in locals():
        resultado_preguntas_similares = preguntas_similares
    else:
        resultado_preguntas_similares = []

    return render(
        request       = request,
        template_name = "ModificarPregunta.html",
        context       = {
            "form": form,
            "pregunta": pregunta,
            "sugerencias_ia": sugerencias_ia,
            "categoria_ia": resultado_categoria_ia,
            "preguntas_similares": resultado_preguntas_similares,
        },
    )


@login_required
def GestionUsuarios(request: HttpRequest) -> HttpResponse:
    """
    Vista de gestión de usuarios con insights de IA
    """

    usuario: object = request.user
    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin
    es_tecnico: int = usuario.tecnico

    if not es_admin and not es_tecnico:
        return redirect(f"/Inicio/")

    Usuarios: QuerySet[Usuario] = Usuario.objects.all()

    # FELIPE: NO ES NECESARIO, ESTOS DATOS SE MUESTRAN EN ANALITICS IA

    # 🔥 INTEGRACIÓN DE IA: Análisis de actividad de usuarios
    # analisis_usuarios: list[Any] = []
    # try:
    #     asistente_ia = AsistenteIA()
    #     for usuario in Usuarios:
    #         preguntas_usuario = Preguntas.objects.filter(Usuario=usuario)
    #         total_preguntas = preguntas_usuario.count()

    #         # Clasificar preguntas del usuario
    #         categorias_usuario = []
    #         for pregunta in preguntas_usuario[:5]:  # Analizar primeras 5 preguntas
    #             try:
    #                 categoria = asistente_ia.clasificar_pregunta(pregunta.Pregunta)
    #                 categorias_usuario.append(categoria)
    #             except:
    #                 categorias_usuario.append("desconocida")

    #         # Encontrar categoría más común
    #         categoria_principal = "sin preguntas"
    #         if categorias_usuario:
    #             categoria_principal = max(
    #                 set(categorias_usuario), key=categorias_usuario.count
    #             )

    #         analisis_usuarios.append(
    #             {
    #                 "usuario_id": usuario.id,
    #                 "total_preguntas": total_preguntas,
    #                 "categoria_principal": categoria_principal,
    #                 "actividad_reciente": usuario.last_login is not None
    #                 and usuario.last_login >= timezone.now() - timedelta(days=7),
    #             }
    #         )

    # except Exception as e:
    #     print(f"Error en análisis de usuarios con IA: {e}")

    if request.method == "POST":
        user_id: str | None = request.POST.get("Userid")
        activo: bool = request.POST.get("activo") == "on"
        admin: bool = request.POST.get("admin") == "on"
        tecnico: bool = request.POST.get("tecnico") == "on"

        userchange: Usuario = get_object_or_404(Usuario, id=user_id)

        # 🔥 INTEGRACIÓN DE IA: Análisis de cambios de rol
        cambios: list[str] = []

        if userchange.admin != admin:
            cambios.append(f"Admin: {userchange.admin} → {admin}")
        if userchange.tecnico != tecnico:
            cambios.append(f"Técnico: {userchange.tecnico} → {tecnico}")
        if userchange.activo != activo:
            cambios.append(f"Activo: {userchange.activo} → {activo}")

        if cambios:
            logger.info(msg=f"Cambios de rol detectados por IA: {', '.join(cambios)}")

        userchange.admin = admin
        userchange.activo = activo
        userchange.tecnico = tecnico
        userchange.save()

        messages.success(
            request, f"Usuario {userchange.usuario} actualizado correctamente."
        )

        return redirect("/GestionUsuarios/")

    return render(
        request       = request,
        template_name = "GestionUsuarios.html",
        context       = {"Usuarios": Usuarios},
    )


@login_required
@require_POST
def EliminarUsuario(request: HttpRequest, idUser: int) -> HttpResponse:
    """
    Vista para eliminar usuarios con análisis de IA
    """

    usuario: object = request.user
    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin
    es_tecnico: int = usuario.tecnico

    if not es_admin and not es_tecnico:
        usuario_id: Any | None = usuario.pk
        return redirect(f"/Inicio/{usuario_id}")

    if es_admin:
        usuario_a_eliminar: Usuario = get_object_or_404(Usuario, id=idUser)
        usuario_id: Any | None = usuario.pk

        if usuario_a_eliminar.pk == usuario_id:
            messages.error(request, "No puedes eliminar tu propia cuenta.")
            return redirect("/GestionUsuarios/")

        usuario_eliminado = usuario_a_eliminar.usuario
        usuario_a_eliminar.delete()

        messages.success(
            request, f"Usuario {usuario_eliminado} eliminado correctamente."
        )

    else:
        messages.error(request, "No tienes permisos para realizar esta acción.")

    return redirect("/GestionUsuarios/")


def promedio_respuestas_admin() -> datetime.timedelta | Literal[0]:
    # PROMEDIO DE RESPUESTAS ENTRE LA CRECION DE LA PREGUNTA HASTA LA PRIMERA RESPUESTA DE UN ADMIN O TECNICO
    lista_preguntas: QuerySet[Preguntas] = Preguntas.objects.all()

    lista_tiempo_duracion: list[datetime.timedelta] = []

    for pregunta in lista_preguntas:
        lista_respuestas = Respuesta.objects.filter(
            id_Pregunta=pregunta.idPregunta
        ).order_by("FechaHora")

        fecha_creacion: datetime.datetime = pregunta.Fecha_creacion

        for respuesta in lista_respuestas:
            if respuesta.Usuario.admin | respuesta.Usuario.tecnico:
                lista_tiempo_duracion.append(respuesta.FechaHora - fecha_creacion)
                break
        else:
            lista_tiempo_duracion.append(timezone.now() - fecha_creacion)

    if len(lista_tiempo_duracion) == 0:
        return 0

    return sum(lista_tiempo_duracion, datetime.timedelta(0)) / len(
        lista_tiempo_duracion
    )


def timedelta_string(delta: datetime.timedelta) -> str:
    total_segundos: int = int(delta.total_seconds())

    dias: int = total_segundos // 86400
    segundos_restantes: int = total_segundos - (dias * 86400)

    horas: int = total_segundos // 3600
    segundos_restantes = total_segundos - (horas * 3600)

    minutos = segundos_restantes // 60
    # segundos = segundos_restantes - (minutos * 60)

    # total time
    return f"{dias} días y {horas:02}:{minutos:02} horas"


# 🔥 NUEVA VISTA: Panel de Analytics con IA
@login_required
def AnalyticsIA(request: HttpRequest) -> HttpResponse:
    """
    Vista exclusiva para análisis avanzados con IA
    """

    usuario: object = request.user
    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin

    if not es_admin:
        usuario_id: Any | None = usuario.pk
        return redirect(f"/Inicio/{usuario_id}")

    total_promedio_respuestas: datetime.timedelta | Literal[0] = promedio_respuestas_admin()

    if total_promedio_respuestas == 0:
        promedio_respuestas = "No hay preguntas"
    else:
        promedio_respuestas: Any = timedelta_string(total_promedio_respuestas)

    try:
        asistente_ia = AsistenteIA()

        # Análisis de tendencias temporales
        preguntas_ultimo_mes = Preguntas.objects.filter(
            Fecha_creacion__gte=timezone.now() - datetime.timedelta(days=30)
        )

        # Análisis por categorías (usando IA)
        categorias_analisis = {}
        for pregunta in preguntas_ultimo_mes[:50]:  # Limitar para no sobrecargar la API
            categoria: Any | str = asistente_ia.clasificar_pregunta(pregunta.Pregunta)
            if categoria not in categorias_analisis:
                categorias_analisis[categoria] = 0
            categorias_analisis[categoria] += 1

        # Usuarios más activos
        usuarios_activos = Usuario.objects.annotate(
            num_preguntas=Count("preguntas")
        ).order_by("-num_preguntas")[:10]

        analytics_data: dict[Any, Any] = {
            "total_preguntas_mes": preguntas_ultimo_mes.count(),
            "categorias_tendencia": dict(
                sorted(categorias_analisis.items(), key=lambda x: x[1], reverse=True)[:5]
            ),
            "usuarios_activos": usuarios_activos,
            "preguntas_sin_respuesta": Preguntas.objects.filter(
                respuesta__isnull=True
            ).count(),
            "tiempo_promedio_respuesta": promedio_respuestas,
        }

    except Exception as e:
        logger.info(msg=f"Error en analytics IA: {e}")
        analytics_data = {"error": "No se pudieron cargar los analytics"}

    logger.info(analytics_data)
    return render(
        request       = request, 
        template_name = "analytics_ia.html", 
        context       = {"analytics_data": analytics_data})
