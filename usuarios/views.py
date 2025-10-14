from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import ExtractMonth  # si usas PostgreSQL/MySQL

import json

from .forms import LoginForm, UserRegistrationForm
from registros.models import RegistroContable, ArchivoCargado


#  Helpers 
def es_admin(user):
    return user.is_staff or user.is_superuser

def es_normal(user):
    return not user.is_staff


#  Redirección automática según rol
@login_required
def redireccion_dashboard(request):
    if es_admin(request.user):
        return redirect("usuarios:dashboard_superuser")
    return redirect("usuarios:dashboard_normal")


#  Login 
def home(request):
    form = LoginForm()
    return render(request, "registration/login.html", {"form": form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect("usuarios:redireccion_dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cd = form.cleaned_data
        user = authenticate(request, username=cd["username"], password=cd["password"])
        if user:
            login(request, user)
            return redirect("usuarios:redireccion_dashboard")
        messages.error(request, "Credenciales inválidas")
    return render(request, "registration/login.html", {"form": form})


class CustomLoginView(LoginView):
    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return reverse("usuarios:dashboard_superuser")
        return reverse("usuarios:dashboard_normal")


# Registro de usuario 
def registr(request):
    if request.method == "POST":
        user_form = UserRegistrationForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save()  # guarda encriptando la pass y vinculando registros
            messages.success(request, "Usuario creado exitosamente.")
            return render(request, "registration/register.html", {"new_user": new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, "registration/register.html", {"user_form": user_form})


# Dashboards 
@login_required
@user_passes_test(es_normal)
def user_dashboard(request):
    registros = RegistroContable.objects.filter(usuario=request.user)
    return render(
        request,
        "usuarios/dashboard_normal.html",
        {"tiene_registros": registros.exists()}
    )


@login_required
@user_passes_test(es_admin)
def admin_dashboard(request):
    """
    Panel de administración con métricas y datos para las gráficas.
    """
    User = get_user_model()

    total_usuarios = User.objects.count()
    total_archivos = ArchivoCargado.objects.count()
    total_registros = RegistroContable.objects.count()
    ultimos_archivos = ArchivoCargado.objects.order_by('-fecha_subida')[:5]

    #  Datos para las gráficas 
    # Archivos por mes (funciona en PostgreSQL/MySQL; para SQLite usa strftime)
    archivos_por_mes = (
        ArchivoCargado.objects
        .annotate(mes=ExtractMonth('fecha_subida'))
        .values('mes')
        .annotate(total=Count('id'))
        .order_by('mes')
    )

    # Usuarios activos vs inactivos
    usuarios_estado = (
        User.objects
        .values('is_active')
        .annotate(total=Count('id'))
    )

    # Top 5 usuarios por cantidad de archivos
    valores_por_usuario = (
        ArchivoCargado.objects
        .values('subido_por__username')
        .annotate(total=Count('id'))
        .order_by('-total')[:5]
    )

    context = {
        "total_usuarios": total_usuarios,
        "total_archivos": total_archivos,
        "total_registros": total_registros,
        "ultimos_archivos": ultimos_archivos,

        # 🔑 Datos serializados a JSON para Plotly
        "archivos_por_mes": json.dumps(list(archivos_por_mes)),
        "usuarios_estado": json.dumps(list(usuarios_estado)),
        "valores_por_usuario": json.dumps(list(valores_por_usuario)),
    }

    return render(request, "usuarios/dashboard_superuser.html", context)
