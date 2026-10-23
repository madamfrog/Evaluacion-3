"""CallCenterGamer URL Configuration"""

"""CallCenterGamer URL Configuration"""

"""CallCenterGamer URL Configuration"""

from django.contrib import admin
from django.urls import path
from online.views import (
    Index,
    Inicio,
    RegisterView,
    LoginView,
    ViewRespuestas,
    logout_view,
)
from administracion.views import (
    IndexAdmin,
    BorrarPregunta,
    GestionUsuarios,
    EliminarUsuario,
    ModificarPregunta,
    AnalyticsIA,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", Index, name="index"),
    path("Administracion/", IndexAdmin, name="administracion"),
    path("AnalyticsIA/", AnalyticsIA, name="analytics_ia"),
    path("Login/", LoginView.as_view(), name="Login"),
    path("Register/", RegisterView.as_view(), name="Register"),
    path("Inicio/<int:id>/", Inicio, name="inicio"),
    # Usar vista personalizada para logout
    path("Logout/", logout_view, name="Logout"),
    path("Respuesta/<int:idUser>/<int:idPregunta>/", ViewRespuestas, name="respuestas"),
    path("GestionUsuarios/", GestionUsuarios, name="gestion_usuarios"),
    path("EliminarUsuario/<int:idUser>/", EliminarUsuario, name="eliminar_usuario"),
    # GESTION DE PREGUNTAS
    path("BorrarPregunta/<int:idPregunta>/", BorrarPregunta, name="borrar_pregunta"),
    path(
        "ModificarPregunta/<int:idPregunta>/",
        ModificarPregunta,
        name="modificar_pregunta",
    ),
]
