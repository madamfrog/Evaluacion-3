from django import forms
from online.models import Usuario
from django.contrib.auth.forms import ReadOnlyPasswordHashField
class UserAdminCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)

    class Meta:
        model = Usuario
        fields = ['usuario','correo']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_2 = cleaned_data.get("password_2")
        if password is not None and password != password_2:
            self.add_error("password_2", "Your passwords must match")
        return cleaned_data

    def save(self, commit=True):
        Usuario = super().save(commit=False)
        Usuario.set_password(self.cleaned_data["password"])
        if commit:
            Usuario.save()
        return Usuario                                                                                                                                                                              
class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = Usuario
        fields = ['usuario','correo', 'password', 'activo', 'admin','tecnico']

    def clean_password(self):
        return self.initial["password"]

