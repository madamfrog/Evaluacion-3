from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import logout
from django.utils import timezone
from django.views.decorators.http import require_POST
from online.forms import RegisterForm, LoginForm, PreguntasForm, RespuestaForm
from django.views.generic import CreateView, FormView
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from online.models import Preguntas, Usuario, Respuesta

# Vista para la página principal
def Index(request):
    """
    Página principal del sitio
    """
    return render(request, "index.html")

# Vista para logout personalizada
@require_POST
def logout_view(request):
    """
    Vista personalizada para logout
    """
    logout(request)
    return redirect('Login')

# Vista de inicio de usuario
@login_required
def Inicio(request, id):
    """
    Vista del panel de usuario
    """
    try:
        User = Usuario.objects.get(id=id)
        if request.user.id != User.id:
            return redirect('/Inicio/' + str(request.user.id))
        preguntas = Preguntas.objects.filter(Usuario=User)
        now = timezone.now()
        form = PreguntasForm(initial={'Usuario': id, 'Fecha_creacion': now})

        if request.method == "POST":
            form = PreguntasForm(request.POST)
            if form.is_valid():
                pregunta = form.save(commit=False)
                pregunta.Usuario = User
                pregunta.Fecha_creacion = now
                pregunta.save()
                return redirect('/Inicio/' + str(id))

        return render(request, "inicio.html", {
            "Preguntas": preguntas,
            "form": form,
            "id": id
        })
    except Usuario.DoesNotExist:
        return redirect('/')

# Vista de respuestas
@login_required
def ViewRespuestas(request, idUser, idPregunta):
    """
    Vista para ver y responder preguntas
    """
    try:
        pregunta = Preguntas.objects.get(idPregunta=idPregunta)
        if not (
            request.user.id == pregunta.Usuario_id
            or request.user.admin
            or request.user.tecnico
        ):
            return redirect('/Inicio/' + str(request.user.id))

        now = timezone.now()
        MostrarRespuestas = Respuesta.objects.filter(id_Pregunta=pregunta)

        form = RespuestaForm(initial={
            'id_Pregunta': idPregunta,
            'Usuario': request.user.id,
            'FechaHora': now
        })

        if request.method == "POST":
            form = RespuestaForm(request.POST)
            if form.is_valid():
                respuesta = form.save(commit=False)
                respuesta.id_Pregunta = pregunta
                respuesta.Usuario = request.user
                respuesta.FechaHora = now
                respuesta.save()
                return redirect('/Respuesta/' + str(idUser) + "/" + str(idPregunta))

        return render(request, "Respuestas.html", {
            "Pregunta": pregunta,
            "form": form,
            "Respuestas": MostrarRespuestas
        })
    except Preguntas.DoesNotExist:
        return redirect('/')

# Vistas basadas en clases
class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'register.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        user = form.save()
        login(request, user)
        if user.admin:
            return redirect('/Administracion/')
        return redirect('/Inicio/' + str(user.id))

class LoginView(FormView):
    form_class = LoginForm
    template_name = 'login.html'
    success_url = '/'

    def form_valid(self, form):
        request = self.request
        usuario = form.cleaned_data.get("Usuario")
        password = form.cleaned_data.get("password")
        remember_me = form.cleaned_data['remember_me']

        user = authenticate(request, username=usuario, password=password)
        if user is not None:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            if user.admin or user.tecnico:
                return redirect('/Administracion/')
            return redirect('/Inicio/' + str(user.id))
        form.add_error(None, "Usuario o contraseña incorrectos.")
        return super().form_invalid(form)