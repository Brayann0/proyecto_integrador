from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario
from registros.models import RegistroContable


# Formulario de login
class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Correo electrónico o usuario')
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)


# Formulario de registro de usuarios
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña', 
        widget=forms.PasswordInput,
        help_text="Debe tener al menos 6 caracteres."
    )
    password2 = forms.CharField(
        label='Repetir Contraseña', 
        widget=forms.PasswordInput
    )

    class Meta:
        model = Usuario
        fields = ['username', 'nombre', 'apellido', 'email', 'identificacion']

    # Validación de email
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email or "@" not in email:
            raise forms.ValidationError("Debes ingresar un correo electrónico válido.")
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        return email

    # Validación de contraseñas
    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password') != cd.get('password2'):
            raise forms.ValidationError('Las contraseñas no coinciden')
        return cd['password2']

    # Guardado del usuario
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])  # Encriptar contraseña
        if commit:
            user.save()

            # Vincular registros contables existentes por identificación
            RegistroContable.objects.filter(
                identificacion=user.identificacion,
                usuario__isnull=True
            ).update(usuario=user)

        return user
