import datetime
import logging
from typing import Any
from uuid import UUID, uuid4

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMultiAlternatives
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, FormView

from online import recomendaciones_ia
from online.forms import LoginForm, PreguntasForm, RegisterForm, RespuestaForm
from online.ia_utils import AsistenteIA
from online.models import Preguntas, Respuesta, Usuario

logger: logging.Logger = settings.LOGGER

# Configuración del logger para la app online


def Index(request: HttpRequest) -> HttpResponse:
    """
    Página principal del sitio
    """
    return render(request, "index.html")


@require_POST
@login_required
def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Vista personalizada para logout
    """
    logout(request)
    return redirect("Login")



@login_required
def Inicio(request: HttpRequest) -> HttpResponse:
    """
    Vista del panel de usuario(inicio) - Optimizado
    """
    usuario: object = request.user

    assert isinstance(usuario, Usuario)

    usuario_pk: Any | None = usuario.pk

    usuario_logeado: Usuario = get_object_or_404(Usuario, id=request.user.pk)

    if usuario_pk != usuario.pk:
        return redirect("/Inicio/")


    # Optimización: Ordenar las preguntas por fecha de creación descendente
    preguntas = Preguntas.objects.filter(Usuario=usuario_logeado).order_by("-Fecha_creacion")
    hora_ahora = timezone.now()

    formulario_preguntas: PreguntasForm = PreguntasForm(initial={"Usuario": usuario.pk, "Fecha_creacion": hora_ahora})

    if request.method == "POST":
        response_post: dict[Any, Any] = request.POST.dict()
        formulario_preguntas = PreguntasForm(response_post)

        if formulario_preguntas.is_valid():
            # Clasificar con IA
            try:
                asistente = AsistenteIA()
                response_post["categoria"] = asistente.clasificar_pregunta(
                    response_post["Pregunta"]
                )

            except Exception as e:
                logger.error("Error al clasificar categoría: %s", e)
                response_post["categoria"] = "general"

            formulario_preguntas = PreguntasForm(response_post)
            formulario_preguntas.save()
            return redirect("/Inicio/")

    query_ia = request.GET.get("buscar_ayuda", "").strip()

    # Guarda la búsqueda del asistente virtual
    sugerencias_ia: dict[Any, Any] = {
        "consulta_original": query_ia,
        "respuesta_automatica": "Lo sentimos, el asistente virtual no se encuentra disponible en este momento. Inténtalo más tarde.",
        "recomendaciones": [],
    }

    if query_ia:
        logger.info("GENERANDO RESPUESTA AUTOMATICA")
        respuesta_automatica: str = obtener_respuesta_ia(query_ia)

        logger.info("GENERANDO RECOMENDACIONES")
        recomendaciones_ia: list[str] = obtener_recomendaciones_ia(query_ia)

        sugerencias_ia = {
            "consulta_original": query_ia,
            "respuesta_automatica": respuesta_automatica,
            "recomendaciones": recomendaciones_ia,
        }


    return render(
        request       = request,
        template_name = "inicio.html",
        context       = {
            "Preguntas": preguntas,
            "form": formulario_preguntas,
            "sugerencias_ia": sugerencias_ia,
        },
    )

def obtener_respuesta_ia(query_ia: str) -> str:
    asistente: AsistenteIA = AsistenteIA()
    return asistente.generar_respuesta_automatica(pregunta=query_ia)


def obtener_recomendaciones_ia(query_ia: str) -> list[str]:
    return recomendaciones_ia.obtener_recomendaciones_ia(nueva_pregunta=query_ia)

@login_required
def ViewRespuestas(request: HttpRequest, idUser: int, idPregunta: int):
    """
    Vista para ver y responder preguntas - Optimizado con select_related
    """

    usuario: object = request.user

    assert isinstance(usuario, Usuario)

    es_admin: int = usuario.admin
    es_tecnico: int = usuario.tecnico

    try:
        # Optimización: Traer la pregunta con su usuario relacionado en una sola consulta
        pregunta: Preguntas | None = Preguntas.objects.select_related("Usuario").get(
            idPregunta=idPregunta
        )

        if not (
            request.user.pk == pregunta.Usuario.pk
            or es_admin
            or es_tecnico
        ):
            return redirect("/Inicio/")

        now = timezone.now()

        # Optimización clave y trae los datos del usuario
        MostrarRespuestas = (
            Respuesta.objects.filter(id_Pregunta=pregunta)
            .select_related("Usuario")
            .order_by("FechaHora")
        )

        formRespuesta = RespuestaForm(
            initial={
                "id_Pregunta": idPregunta,
                "Usuario": request.user.pk,
                "FechaHora": now,
            }
        )

        if request.method == "POST":
            formRespuesta = RespuestaForm(request.POST)

            response_post: dict[str, Any] = request.POST.dict()

            if formRespuesta.is_valid():
                response_post["id_Pregunta"] = pregunta
                response_post["Usuario"] = request.user
                response_post["FechaHora"] = now
                formRespuesta.save()

                return redirect("/Respuesta/" + str(idUser) + "/" + str(idPregunta))

        return render(
            request,
            "Respuestas.html",
            {"Pregunta": pregunta, "form": formRespuesta, "Respuestas": MostrarRespuestas},
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
        return redirect("/Inicio/")


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
            logger.info("Usuario encontrado")

            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            if user.admin or user.tecnico:
                return redirect("/Administracion/")
            return redirect("/Inicio/")

        logger.info("Usuario No encontrado")
        form.add_error(None, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)





# FELIPE: CAMBIO DE CONTRASEÑA CON TOKEN Y FECHA VENCIMINETO
def CambioContrEmail(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        if not "correo" in request.POST:
            return render(
                request       = request,
                template_name = 'cambio_contr_correo.html',
            )

        correo: str = request.POST.get("correo", "")
        usuario: Usuario = get_object_or_404(Usuario, correo=correo)

        # FELIPE: AÑADIR TOKEN AL USUARIO Y FECHA DE VENCIMIENTO
        token_uuid: UUID = uuid4()

        usuario.token = str(token_uuid)
        usuario.token_hasta = timezone.now() + datetime.timedelta(minutes=30)
        usuario.save()

        logger.info("Token agregado y fecha de vencimiento")

        logger.info("Correo Confirmado")

        logger.info("Enviando Correo")
        contenido_HTML = render_to_string(
            template_name='email.html',
            context={"link": f"http://localhost:8000/cambio-contrasena/?token={token_uuid}"},
        )
        logger.info("HTML Creado")

        logger.info("Creando Mensaje")
        message_email = EmailMultiAlternatives(
            subject="Cambio de Contraseña",
            body="Sí usted cree que esto fue una equivocación, por favor ignore este mensaje.",
            from_email="fuentes.zuniga.felipe@gmail.com",
            to=[correo],
            headers={},
        )
        logger.info("Mensaje Creado")

        logger.info("Adjuntando Alternativas")
        message_email.attach_alternative(content=contenido_HTML, mimetype="text/html")
        logger.info("Tratando de enviar Correo")
        message_email.send()
        logger.info("Correo Enviado")

    return render(
        request       = request,
        template_name = 'cambio_contr_correo.html',
    )

def CambioContr(request: HttpRequest) -> HttpResponse:
    datos: dict[str, Any] = {}
    logger.info(request.POST)

    if request.method == "GET":
        token: str = request.GET.get("token", "")
        datos["token"] = token

    if request.method == "POST":
        token: str = request.POST.get("token", "")
        password: str = request.POST.get("password", "")
        confirmar_password: str = request.POST.get("confirmar_password", "")


        logger.info(f"TOKEN:                {token}")
        logger.info(f"PASSWORD:             {password}")
        logger.info(f"CONFIRMAR PASSWORD:   {confirmar_password}")

        if len(password) < 8 or len(confirmar_password) < 8:
            datos["contraseñaError"] = "Las contraseñas debe ser mayor que 8 digitos"
            datos["token"] = token

        elif password != confirmar_password:
            datos["contraseñaError"] = "Las contraseñas no son iguales"
            datos["token"] = token

        elif    (len(password) >= 8 
            and len(confirmar_password) >= 8 
            and password == confirmar_password):

            usuario_cambiar: Usuario = get_object_or_404(Usuario, token=token)

            usuario_query: QuerySet[Usuario] = Usuario.objects.filter(
                token=token,
                token_hasta__gt=timezone.now()
            )

            if usuario_query.exists():
                logger.info("usuario actualizado")

                usuario_cambiar.password    = make_password(password=password)
                usuario_cambiar.token_hasta = timezone.now()
                usuario_cambiar.save()
                return redirect("index")

            else:
                logger.info("token vencido")
                return redirect("index")

        datos["token"] = token
        logger.info("Cambio de contraseña Erroneo")

    return render(
        request       = request,
        template_name = 'cambio_contr.html',
        context       = datos,
    )
