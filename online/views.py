import logging
from online.recomendaciones_ia import obtener_recomendaciones_ia
from online.ia_utils import AsistenteIA
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.utils import timezone
from django.views.decorators.http import require_POST
from online.forms import RegisterForm, LoginForm, PreguntasForm, RespuestaForm
from django.views.generic import CreateView, FormView
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from online.models import Preguntas, Usuario, Respuesta

from django.conf import settings

logger: logging.Logger = settings.LOGGER

# Configuración del logger para la app online


def Index(request):
    """
    Página principal del sitio
    """
    return render(request, "index.html")


@require_POST
def logout_view(request):
    """
    Vista personalizada para logout
    """
    logout(request)
    return redirect("Login")


@login_required
def Inicio(request, id):
    """
    Vista del panel de usuario(inicio) - Optimizado
    """
    try:
        User = Usuario.objects.get(id=id)
        if request.user.id != User.id:
            return redirect("/Inicio/" + str(request.user.id))

        # Optimización: Ordenar las preguntas por fecha de creación descendente
        preguntas = Preguntas.objects.filter(Usuario=User).order_by("-Fecha_creacion")
        now = timezone.now()
        form = PreguntasForm(initial={"Usuario": id, "Fecha_creacion": now})

        # Guarda la búsqueda del asistente virtual
        sugerencias_ia = None
        query_ia = request.GET.get("buscar_ayuda", "").strip()
        if query_ia:
            try:
                sugerencias_ia = obtener_recomendaciones_ia(query_ia)
            except Exception as e:
                logger.error("Error al obtener sugerencias de IA: %s", e)
                sugerencias_ia = {
                    "consulta_original": query_ia,
                    "respuesta_automatica": "Lo sentimos, el asistente virtual no se encuentra disponible en este momento. Inténtalo más tarde.",
                    "recomendaciones": [],
                }

        if request.method == "POST":
            form = PreguntasForm(request.POST)
            if form.is_valid():
                pregunta = form.save(commit=False)
                pregunta.Usuario = User
                pregunta.Fecha_creacion = now

                # Clasificar con IA
                try:
                    asistente = AsistenteIA()
                    pregunta.categoria = asistente.clasificar_pregunta(
                        pregunta.Pregunta
                    )
                except Exception as e:
                    logger.error("Error al clasificar categoría: %s", e)
                    pregunta.categoria = "general"

                pregunta.save()
                return redirect("/Inicio/" + str(id))

        return render(
            request,
            "inicio.html",
            {
                "Preguntas": preguntas,
                "form": form,
                "id": id,
                "sugerencias_ia": sugerencias_ia,
            },
        )
    except Usuario.DoesNotExist:
        return redirect("/")


@login_required
def ViewRespuestas(request, idUser, idPregunta):
    """
    Vista para ver y responder preguntas - Optimizado con select_related
    """
    try:
        # Optimización: Traer la pregunta con su usuario relacionado en una sola consulta
        pregunta = Preguntas.objects.select_related("Usuario").get(
            idPregunta=idPregunta
        )

        if not (
            request.user.id == pregunta.Usuario_id
            or request.user.admin
            or request.user.tecnico
        ):
            return redirect("/Inicio/" + str(request.user.id))

        now = timezone.now()

        # Optimización clave y trae los datos del usuario
        MostrarRespuestas = (
            Respuesta.objects.filter(id_Pregunta=pregunta)
            .select_related("Usuario")
            .order_by("FechaHora")
        )

        form = RespuestaForm(
            initial={
                "id_Pregunta": idPregunta,
                "Usuario": request.user.id,
                "FechaHora": now,
            }
        )

        if request.method == "POST":
            form = RespuestaForm(request.POST)
            if form.is_valid():
                respuesta = form.save(commit=False)
                respuesta.id_Pregunta = pregunta
                respuesta.Usuario = request.user
                respuesta.FechaHora = now
                respuesta.save()
                return redirect("/Respuesta/" + str(idUser) + "/" + str(idPregunta))

        return render(
            request,
            "Respuestas.html",
            {"Pregunta": pregunta, "form": form, "Respuestas": MostrarRespuestas},
        )
    except Preguntas.DoesNotExist:
        return redirect("/")


# Vistas basadas en clases
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "register.html"
    success_url = "/"

    def form_valid(self, form):
        request = self.request
        user = form.save()
        login(request, user)
        if user.admin:
            return redirect("/Administracion/")
        return redirect("/Inicio/" + str(user.id))


class LoginView(FormView):
    form_class = LoginForm
    template_name = "login.html"
    success_url = "/"

    def form_valid(self, form):
        request = self.request
        usuario = form.cleaned_data.get("Usuario")
        password = form.cleaned_data.get("password")
        remember_me = form.cleaned_data["remember_me"]

        user = authenticate(request, username=usuario, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            if user.admin or user.tecnico:
                return redirect("/Administracion/")
            return redirect("/Inicio/" + str(user.id))
        form.add_error(None, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)
