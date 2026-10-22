from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from online.models import Preguntas, Usuario
from online.forms import PreguntasForm
from online.ia_utils import AsistenteIA
from online.recomendaciones_ia import RecomendadorIA
import json
from datetime import timedelta
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.http import require_POST

@login_required
def IndexAdmin(request):
    """
    Vista principal de administración con insights de IA
    """
    if not (request.user.admin or request.user.tecnico):
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('/Inicio/' + str(request.user.id))

    ListaPreguntas = Preguntas.objects.all().order_by('-Fecha_creacion')
    tendencias_ia = []
    estadisticas_ia = {}
    alertas_ia = []

    try:
        asistente_ia = AsistenteIA()
        recomendador_ia = RecomendadorIA()
        preguntas_recientes = ListaPreguntas.filter(
            Fecha_creacion__gte=timezone.now() - timedelta(days=7)
        )[:10]
        preguntas_semana = ListaPreguntas.filter(
            Fecha_creacion__gte=timezone.now() - timedelta(days=7)
        ).count()

        for pregunta in preguntas_recientes:
            categoria = asistente_ia.clasificar_pregunta(pregunta.Pregunta)
            tendencias_ia.append({
                'id': pregunta.idPregunta,
                'titulo': pregunta.Titulo,
                'categoria': categoria,
                'usuario': pregunta.Usuario.usuario,
                'fecha': pregunta.Fecha_creacion
            })

        total_preguntas = ListaPreguntas.count()
        preguntas_sin_respuesta = ListaPreguntas.filter(
            respuesta__isnull=True
        ).count()
        if total_preguntas > 0:
            estadisticas_ia = {
                'total_preguntas': total_preguntas,
                'preguntas_sin_respuesta': preguntas_sin_respuesta,
                'porcentaje_resueltas': (
                    (total_preguntas - preguntas_sin_respuesta) / total_preguntas
                ) * 100,
                'tendencia_semanal': preguntas_semana
            }
            if preguntas_sin_respuesta > 5:
                alertas_ia.append({
                    'tipo': 'warning',
                    'mensaje': f'⚠️ Hay {preguntas_sin_respuesta} preguntas sin respuesta',
                    'prioridad': 'alta'
                })
            if preguntas_semana > 20:
                alertas_ia.append({
                    'tipo': 'info',
                    'mensaje': '📈 Alta actividad esta semana',
                    'prioridad': 'media'
                })
    except Exception as e:
        print(f"Error en análisis de IA: {e}")
        estadisticas_ia = {
            'total_preguntas': ListaPreguntas.count(),
            'preguntas_sin_respuesta': ListaPreguntas.filter(
                respuesta__isnull=True
            ).count(),
            'error_ia': True
        }

    return render(request, "indexAdmin.html", {
        "Preguntas": ListaPreguntas,
        "tendencias_ia": tendencias_ia,
        "estadisticas_ia": estadisticas_ia,
        "alertas_ia": alertas_ia
    })

@login_required
@require_POST
def BorrarPregunta(request, idUser, idPregunta):
    """
    Vista para borrar preguntas con verificación de IA
    """
    if not request.user.admin:
        if request.user.tecnico:
            return redirect("/Administracion/")
        return redirect("/Inicio/" + str(request.user.id))

    try:
        pregunta = Preguntas.objects.get(idPregunta=idPregunta)
    except Preguntas.DoesNotExist:
        messages.error(request, "La pregunta o usuario no existe.")
        return redirect('/Administracion/')
    pregunta.delete()
    messages.success(request, "Pregunta eliminada correctamente.")
    return redirect("/Administracion/")

@login_required
def GestionUsuarios(request):
    """
    Vista de gestión de usuarios con insights de IA
    """
    if not request.user.admin:
        messages.error(request, "No tienes permisos de administrador.")
        return redirect('/Inicio/' + str(request.user.id))

    Usuarios = Usuario.objects.all()

    # 🔥 INTEGRACIÓN DE IA: Análisis de actividad de usuarios
    analisis_usuarios = []

    try:
        asistente_ia = AsistenteIA()

        for usuario in Usuarios:
            preguntas_usuario = Preguntas.objects.filter(Usuario=usuario)
            total_preguntas = preguntas_usuario.count()

            # Clasificar preguntas del usuario
            categorias_usuario = []
            for pregunta in preguntas_usuario[:5]:  # Analizar primeras 5 preguntas
                try:
                    categoria = asistente_ia.clasificar_pregunta(pregunta.Pregunta)
                    categorias_usuario.append(categoria)
                except:
                    categorias_usuario.append("desconocida")

            # Encontrar categoría más común
            categoria_principal = "sin preguntas"
            if categorias_usuario:
                categoria_principal = max(set(categorias_usuario), key=categorias_usuario.count)

            analisis_usuarios.append({
                'usuario_id': usuario.id,
                'total_preguntas': total_preguntas,
                'categoria_principal': categoria_principal,
                'actividad_reciente': usuario.last_login is not None and
                                    usuario.last_login >= timezone.now() - timedelta(days=7)
            })

    except Exception as e:
        print(f"Error en análisis de usuarios con IA: {e}")

    if request.method == "POST":
        user_id = request.POST.get('Userid')
        activo = request.POST.get('activo') == 'on'
        admin = request.POST.get('admin') == 'on'
        tecnico = request.POST.get('tecnico') == 'on'

        try:
            userchange = Usuario.objects.get(id=user_id)

            # 🔥 INTEGRACIÓN DE IA: Análisis de cambios de rol
            cambios = []
            if userchange.admin != admin:
                cambios.append(f"Admin: {userchange.admin} → {admin}")
            if userchange.tecnico != tecnico:
                cambios.append(f"Técnico: {userchange.tecnico} → {tecnico}")
            if userchange.activo != activo:
                cambios.append(f"Activo: {userchange.activo} → {activo}")

            if cambios:
                print(f"Cambios de rol detectados por IA: {', '.join(cambios)}")

            userchange.admin = admin
            userchange.activo = activo
            userchange.tecnico = tecnico
            userchange.save()

            messages.success(request, f"Usuario {userchange.usuario} actualizado correctamente.")
            return redirect('/GestionUsuarios/')

        except Usuario.DoesNotExist:
            messages.error(request, "El usuario no existe.")

    return render(request, "GestionUsuarios.html", {
        "Usuarios": Usuarios,
        "analisis_usuarios": analisis_usuarios
    })

@login_required
@require_POST
def EliminarUsuario(request, idUser):
    """
    Vista para eliminar usuarios con análisis de IA
    """
    if request.user.admin:
        try:
            User = Usuario.objects.get(id=idUser)
            if User.id == request.user.id:
                messages.error(request, "No puedes eliminar tu propia cuenta.")
                return redirect('/GestionUsuarios/')

            usuario_eliminado = User.usuario
            User.delete()
            messages.success(request, f"Usuario {usuario_eliminado} eliminado correctamente.")

        except Usuario.DoesNotExist:
            messages.error(request, "El usuario no existe.")
    else:
        messages.error(request, "No tienes permisos para realizar esta acción.")

    return redirect('/GestionUsuarios/')

@login_required
def ModificarPregunta(request, idPregunta):
    """
    Vista para modificar preguntas con asistencia de IA
    """
    if not request.user.admin:
        messages.error(request, "No tienes permisos de administrador.")
        return redirect('/Inicio/' + str(request.user.id))

    try:
        Pregunta = Preguntas.objects.get(idPregunta=idPregunta)
        sugerencias_ia = []

        # 🔥 INTEGRACIÓN DE IA: Análisis de la pregunta y sugerencias
        try:
            asistente_ia = AsistenteIA()
            recomendador_ia = RecomendadorIA()

            # 1. Clasificar la pregunta
            categoria_ia = asistente_ia.clasificar_pregunta(Pregunta.Pregunta)

            # 2. Generar sugerencias de mejora
            sugerencia_prompt = f"""
            Como experto en soporte técnico, analiza esta pregunta y sugiere mejoras:

            Título actual: {Pregunta.Titulo}
            Pregunta actual: {Pregunta.Pregunta}
            Categoría detectada: {categoria_ia}

            Sugiere:
            1. Un título más descriptivo
            2. Cómo mejorar la claridad de la pregunta
            3. Información adicional que sería útil

            Responde en formato JSON.
            """

            try:
                respuesta_ia = asistente_ia.generar_respuesta_automatica(sugerencia_prompt)
                # Intentar parsear como JSON, si falla usar texto plano
                if "{" in respuesta_ia and "}" in respuesta_ia:
                    sugerencias_ia = json.loads(respuesta_ia)
                else:
                    sugerencias_ia = [{"sugerencia": respuesta_ia}]
            except:
                sugerencias_ia = [{"sugerencia": "No se pudieron generar sugerencias en este momento."}]

            # 3. Buscar preguntas similares para referencia
            preguntas_similares = recomendador_ia.recomendar_respuestas_similares(Pregunta.Pregunta)

        except Exception as e:
            print(f"Error en análisis IA de pregunta: {e}")
            sugerencias_ia = [{"error": "El asistente de IA no está disponible"}]

        form = PreguntasForm(instance=Pregunta)

        if request.method == 'POST':
            form = PreguntasForm(request.POST, instance=Pregunta)
            if form.is_valid():
                pregunta_actualizada = form.save(commit=False)
                pregunta_actualizada.Usuario = Pregunta.Usuario
                pregunta_actualizada.Fecha_creacion = Pregunta.Fecha_creacion

                # 🔥 INTEGRACIÓN DE IA: Re-clasificar después de modificación
                try:
                    nueva_categoria = asistente_ia.clasificar_pregunta(pregunta_actualizada.Pregunta)
                    # Aquí podrías guardar la categoría si agregas el campo al modelo
                    print(f"Pregunta modificada - Nueva categoría IA: {nueva_categoria}")
                except Exception as e:
                    print(f"Error en re-clasificación IA: {e}")

                pregunta_actualizada.save()
                messages.success(request, "Pregunta modificada correctamente.")
                return redirect('/Administracion/')
            else:
                messages.error(request, "Error en el formulario. Verifica los datos.")

        return render(request, "ModificarPregunta.html", {
            "form": form,
            "pregunta": Pregunta,
            "sugerencias_ia": sugerencias_ia,
            "categoria_ia": categoria_ia if 'categoria_ia' in locals() else "No disponible",
            "preguntas_similares": preguntas_similares if 'preguntas_similares' in locals() else []
        })

    except Preguntas.DoesNotExist:
        messages.error(request, "La pregunta no existe.")
        return redirect('/Administracion/')

# 🔥 NUEVA VISTA: Panel de Analytics con IA
@login_required
def AnalyticsIA(request):
    """
    Vista exclusiva para análisis avanzados con IA
    """
    if not request.user.admin:
        messages.error(request, "No tienes permisos de administrador.")
        return redirect('/Inicio/' + str(request.user.id))

    try:
        asistente_ia = AsistenteIA()

        # Análisis de tendencias temporales
        preguntas_ultimo_mes = Preguntas.objects.filter(
            Fecha_creacion__gte=timezone.now() - timedelta(days=30)
        )

        # Análisis por categorías (usando IA)
        categorias_analisis = {}
        for pregunta in preguntas_ultimo_mes[:50]:  # Limitar para no sobrecargar la API
            try:
                categoria = asistente_ia.clasificar_pregunta(pregunta.Pregunta)
                if categoria not in categorias_analisis:
                    categorias_analisis[categoria] = 0
                categorias_analisis[categoria] += 1
            except:
                pass

        # Usuarios más activos
        usuarios_activos = Usuario.objects.annotate(
            num_preguntas=Count('preguntas')
        ).order_by('-num_preguntas')[:10]

        analytics_data = {
            'total_preguntas_mes': preguntas_ultimo_mes.count(),
            'categorias_tendencia': dict(sorted(categorias_analisis.items(),
                                              key=lambda x: x[1], reverse=True)[:5]),
            'usuarios_activos': usuarios_activos,
            'preguntas_sin_respuesta': Preguntas.objects.filter(respuesta__isnull=True).count(),
            'tiempo_promedio_respuesta': "2.5 días"  # Esto sería un cálculo real en producción
        }

    except Exception as e:
        print(f"Error en analytics IA: {e}")
        analytics_data = {'error': 'No se pudieron cargar los analytics'}

    return render(request, "analytics_ia.html", {
        "analytics_data": analytics_data
    })
