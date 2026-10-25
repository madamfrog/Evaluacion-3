from typing import Any

import chilean_rut
from django import forms

from online.models import Preguntas, Respuesta, Usuario


def validar_rut_chileno(rut_str: str) -> str | bool:
    """
    Valida el formato y el dígito verificador de un RUT chileno y
    Acepta todo tipo de formato 
    EJEMPLOS:
        -- BUEN CODIGO VERIFICADOR
        "17317684-8" -> 17.317.684-8

        -- MAL CODIGO VERIFICADOR
        "17317684-1" -> FALSE

        -- MAL RUT
        123.111.111-2 -> FALSE
    """
    try:
        es_valido_rut: bool = chilean_rut.is_valid(rut=rut_str)

        if not es_valido_rut:
            return False

        rut_formateado: str = chilean_rut.format_rut(rut=rut_str, validate_rut=es_valido_rut)

    except ValueError:
        return False

    return rut_formateado

class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Contraseña'})
    )
    password_2 = forms.CharField(
        label='',
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar contraseña'})
    )

    class Meta:
        model = Usuario
        fields = ['usuario', 'correo', 'rut']
        widgets = {
            'correo': forms.EmailInput(attrs={'placeholder': 'Ingrese su correo'}),
            'usuario': forms.TextInput(attrs={'placeholder': 'Ingrese su usuario'}),
            'rut': forms.TextInput(attrs={'placeholder': 'Ingrese su rut'})
        }

    def clean_correo(self):
        correo = self.cleaned_data.get('correo')
        if Usuario.objects.filter(correo=correo).exists():
            raise forms.ValidationError("El correo ya está en uso")
        return correo

    def clean_rut(self):
        rut: Any | None = self.cleaned_data.get('rut')

        if rut is None:
            raise forms.ValidationError("Por favor ingresar el Rut")

        rut_formateado: str | bool = validar_rut_chileno(rut_str=rut)

        if rut_formateado == False:
            raise forms.ValidationError("El RUT ingresado no es válido (verifique el dígito verificador).")
        
        if Usuario.objects.filter(rut=rut_formateado).exists():
            raise forms.ValidationError("Este RUT ya está registrado.") #Verificar si ya existe el rut
            
        return rut_formateado

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        usuario = cleaned_data.get("usuario")

        if usuario and len(usuario) > 20:
            self.add_error("usuario", "El nombre de usuario es demasiado largo!")
        if not usuario:
            self.add_error("usuario", "Debe ingresar un nombre de usuario!")
        if password and len(password) < 8:
            self.add_error("password", "La contraseña debe ser mayor a 8 dígitos")
        if password and password_2 and password != password_2:
            self.add_error("password_2", "Las contraseñas no coinciden")
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.set_password(self.cleaned_data["password"])
        if commit:
            usuario.save()
        return usuario

class LoginForm(forms.Form):
    Usuario = forms.CharField(
        label='',
        max_length=63,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese su usuario'})
    )
    password = forms.CharField(
        label='',
        max_length=63,
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingrese su contraseña'})
    )
    remember_me = forms.BooleanField(
        label='Recordar contraseña',
        required=False
    )

class PreguntasForm(forms.ModelForm):
    class Meta:
        model = Preguntas
        fields = ['Titulo', 'Pregunta', 'Usuario', 'Fecha_creacion']
        widgets = {
            'Titulo': forms.TextInput(attrs={'placeholder': 'Título de la pregunta'}),
            'Pregunta': forms.Textarea(attrs={'placeholder': 'Escriba su pregunta aquí...'}),
            'Usuario': forms.HiddenInput(),
            'Fecha_creacion': forms.HiddenInput(),
        }

class RespuestaForm(forms.ModelForm):
    class Meta:
        model = Respuesta
        fields = ['Respuesta', 'id_Pregunta', 'Usuario', 'FechaHora']
        widgets = {
            'Respuesta': forms.Textarea(
                attrs={'placeholder': 'Enviar mensaje...', 'maxlength': '200', 'rows': 3}),
            'id_Pregunta': forms.HiddenInput(),
            'Usuario': forms.HiddenInput(),
            'FechaHora': forms.HiddenInput(),
        }