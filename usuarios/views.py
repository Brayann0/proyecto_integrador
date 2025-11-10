from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.db import models
import json

from .forms import LoginForm, UserRegistrationForm
from registros.models import RegistroContable, ArchivoCargado


# ====================================================
# Helpers para roles
# ====================================================
def es_admin(user):
    return user.is_superuser or getattr(user, "rol", "") == "admin"

def es_normal(user):
    return getattr(user, "rol", "") == "usuario"


# ====================================================
# Redirección automática según tipo de usuario
# ====================================================
@login_required
def redireccion_dashboard(request):
    if request.user.is_superuser or getattr(request.user, "rol", "") == "admin":
        return redirect("usuarios:dashboard_superuser")
    return redirect("usuarios:dashboard_normal")



def asociar_registros_a_usuario(user):
    """
    Busca registros contables que coincidan con el email o la cédula del usuario
    y los asocia automáticamente.
    """
    try:
        coincidencias = RegistroContable.objects.filter(
            models.Q(email__iexact=user.email) | models.Q(identificacion=str(user.identificacion)),
            usuario__isnull=True
        )

        total = coincidencias.count()

        if total > 0:
            for registro in coincidencias:
                registro.usuario = user
                registro.save()
            print(f"✅ {total} registros asociados automáticamente a {user.username} ({user.email})")

    except Exception as e:
        print(f"⚠️ Error asociando registros a {user.username}: {e}")


# ====================================================
# LOGIN PERSONALIZADO
# ====================================================
from django.views import View

class CustomLoginView(View):
    template_name = 'usuarios/login.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        print(">>> Se recibió POST en login con datos:", request.POST)

        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, "Inicio de sesión exitoso.")
                    print(f">>> Login exitoso para: {user.username} ({user.rol})")
                    
                    asociar_registros_a_usuario(user)

                    # Redirección por rol
                    if user.is_superuser or getattr(user, "rol", "") == "admin":
                        return redirect('usuarios:dashboard_superuser')
                    else:
                        return redirect('usuarios:dashboard_normal')
                else:
                    messages.error(request, "Tu cuenta está inactiva. Contacta al administrador.")
            else:
                messages.error(request, "Correo/usuario o contraseña incorrectos.")
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")

        return render(request, self.template_name, {'form': form})


# ====================================================
# REGISTRO DE USUARIOS
# ====================================================
def register(request):
    print(">>> Entrando a la vista register...")

    if request.method == 'POST':
        print(">>> Se recibió POST con datos:", request.POST)

        user_form = UserRegistrationForm(request.POST)

        if user_form.is_valid():
            user = user_form.save(commit=False)

            admin_key = user_form.cleaned_data.get('admin_key', '').strip()
            if admin_key == 'ADMINSUPER2025':
                user.rol = 'admin'
                user.is_staff = True
                user.is_superuser = False
            else:
                user.rol = 'usuario'
                user.is_staff = False
                user.is_superuser = False

            user.save()
            messages.success(request, 'Tu cuenta ha sido creada exitosamente.')
            return redirect('usuarios:login')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        user_form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'user_form': user_form})


# ====================================================
# DASHBOARD USUARIO NORMAL
# ====================================================
@login_required
@user_passes_test(es_normal)
def user_dashboard(request):
    """
    Muestra los registros contables solo del usuario logueado.
    Incluye resumen rápido.
    """
    registros = RegistroContable.objects.filter(usuario=request.user).order_by('-fecha')

    # Estadísticas básicas
    total_registros = registros.count()
    total_valor = sum(r.valor for r in registros)
    ultimo_registro = registros.first()

    context = {
        "registros": registros,
        "total_registros": total_registros,
        "total_valor": total_valor,
        "ultimo_registro": ultimo_registro,
    }

    return render(request, "usuarios/dashboard_normal.html", context)


# ====================================================
# DASHBOARD ADMINISTRADOR / SUPERUSUARIO
# ====================================================
@login_required
@user_passes_test(es_admin)
def admin_dashboard(request):
    """
    Vista para administradores y superusuarios.
    Los superusuarios ven todo; los administradores solo lo que suben ellos.
    """
    User = get_user_model()

    if request.user.is_superuser:
        archivos = ArchivoCargado.objects.all()
    else:
        archivos = ArchivoCargado.objects.filter(subido_por=request.user)

    total_usuarios = User.objects.count()
    total_archivos = archivos.count()
    total_registros = RegistroContable.objects.count()
    ultimos_archivos = archivos.order_by('-fecha_subida')[:5]

    archivos_por_mes = (
        archivos.annotate(mes=ExtractMonth('fecha_subida'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    usuarios_estado = (
        User.objects.values('is_active')
        .annotate(total=Count('id'))
    )

    valores_por_usuario = (
        ArchivoCargado.objects.values('subido_por__username')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    context = {
        "total_usuarios": total_usuarios,
        "total_archivos": total_archivos,
        "total_registros": total_registros,
        "ultimos_archivos": ultimos_archivos,
        "archivos_por_mes": json.dumps(list(archivos_por_mes)),
        "usuarios_estado": json.dumps(list(usuarios_estado)),
        "valores_por_usuario": json.dumps(list(valores_por_usuario)),
    }

    return render(request, "usuarios/dashboard_superuser.html", context)
