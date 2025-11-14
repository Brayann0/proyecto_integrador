from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import Usuario
from registros.models import RegistroContable
import os


# ===========================================
# FORMULARIO DE LOGIN
# ===========================================
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput
    )


# ===========================================
# FORMULARIO DE REGISTRO DE USUARIOS
# ===========================================
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput,
        help_text="Debe tener al menos 6 caracteres."
    )
    password2 = forms.CharField(
        label='Confirmar Contraseña',
        widget=forms.PasswordInput,
        help_text="Repite la contraseña para verificarla."
    )
    admin_key = forms.CharField(
        label='Clave de administrador (opcional)',
        required=False,
        widget=forms.PasswordInput,
        help_text="Déjalo vacío si quieres ser usuario normal."
    )

    class Meta:
        model = Usuario
        fields = ['nombre', 'apellido', 'email', 'identificacion']

    # --- Validar correo ---
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not email or "@" not in email:
            raise forms.ValidationError("Debes ingresar un correo electrónico válido.")
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está en uso.")
        return email

    # --- Validar contraseñas ---
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password2 = cleaned_data.get('password2')

        if password and len(password) < 6:
            self.add_error('password', "La contraseña debe tener al menos 6 caracteres.")
        if password and password2 and password != password2:
            self.add_error('password2', "Las contraseñas no coinciden.")
        return cleaned_data

    # --- Guardar usuario ---
    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get('password')

        # 🔒 Encriptar contraseña
        user.set_password(raw_password)

        # ⚙️ Rellenar el username con el mismo valor del email
        user.username = user.email

        # --- Asignar rol según clave de administrador ---
        CLAVE_ADMIN = os.getenv("ADMIN_KEY", "ADMINSUPER2025")
        user.is_staff = (self.cleaned_data.get("admin_key") == CLAVE_ADMIN)
        user.rol = 'admin' if user.is_staff else 'usuario'

        if commit:
            user.save()

            # Vincular registros contables previos con la misma identificación
            RegistroContable.objects.filter(
                identificacion=user.identificacion,
                usuario__isnull=True
            ).update(usuario=user)

        return user
