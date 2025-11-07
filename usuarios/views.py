from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.db.models.functions import ExtractMonth
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


# ====================================================
# LOGIN PERSONALIZADO (correo o usuario)
# ====================================================
from django.views import View

class CustomLoginView(View):
    template_name = 'usuarios/login.html'

    def get(self, request):
        form = LoginForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        print(">>> Se recibió POST en login con datos:", request.POST)  # 🔍 Depuración

        form = LoginForm(request, data=request.POST)

        if form.is_valid():
            username_or_email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            # 🔍 Autenticación: puede ser username o email
            user = authenticate(request, username=username_or_email, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, "Inicio de sesión exitoso.")
                    print(f">>> Login exitoso para: {user.username} ({user.rol})")

                    # 🔁 Redirección según rol
                    if user.is_superuser or getattr(user, "rol", "") == "admin":
                        print(">>> Redirigiendo a dashboard de ADMIN.")
                        return redirect('usuarios:dashboard_superuser')
                    else:
                        print(">>> Redirigiendo a dashboard de USUARIO NORMAL.")
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
    print(">>> Entrando a la vista register...")  # 🔍 Ver si la vista se ejecuta

    if request.method == 'POST':
        print(">>> Se recibió POST con datos:", request.POST)  # 🔍 Ver lo que llega del formulario

        user_form = UserRegistrationForm(request.POST)

        if user_form.is_valid():
            print(">>> Formulario válido. Datos limpios:", user_form.cleaned_data)

            # Guardar sin hacer commit para modificar antes de guardar definitivamente
            user = user_form.save(commit=False)

            # Verificar si tiene la clave de administrador
            admin_key = user_form.cleaned_data.get('admin_key', '').strip()
            if admin_key == 'ADMINSUPER2025':
                user.rol = 'admin'
                user.is_staff = True
                user.is_superuser = False  # si quieres que sea admin pero no superusuario
                print(">>> Usuario creado como ADMINISTRADOR.")
            else:
                user.rol = 'usuario'
                user.is_staff = False
                user.is_superuser = False
                print(">>> Usuario creado como NORMAL.")

            # Guardar el usuario definitivamente
            user.save()
            print(">>> Usuario guardado correctamente:", user)

            messages.success(request, 'Tu cuenta ha sido creada exitosamente.')
            return redirect('usuarios:login')
        else:
            print(">>> Formulario inválido. Errores:", user_form.errors)
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        print(">>> Método GET — Mostrando formulario vacío.")
        user_form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'user_form': user_form})



# ====================================================
# DASHBOARD USUARIO NORMAL
# ====================================================
@login_required
@user_passes_test(es_normal)
def user_dashboard(request):
    registros = RegistroContable.objects.filter(usuario=request.user)
    return render(request, "usuarios/dashboard_normal.html", {
        "tiene_registros": registros.exists()
    })


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

    # Si es superusuario, ve todo; si es admin, solo sus archivos
    if request.user.is_superuser:
        archivos = ArchivoCargado.objects.all()
    else:
        archivos = ArchivoCargado.objects.filter(subido_por=request.user)

    total_usuarios = User.objects.count()
    total_archivos = archivos.count()
    total_registros = RegistroContable.objects.count()
    ultimos_archivos = archivos.order_by('-fecha_subida')[:5]

    # Datos para gráficas
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
