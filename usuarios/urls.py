from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = "usuarios"

urlpatterns = [
    path("login/", views.CustomLoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(next_page="usuarios:login"), name="logout"),
    path("register/", views.register, name="register"),
     path('cambiar_contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),

    # Redirección automática (admin o usuario normal)
    path("dashboard/", views.redireccion_dashboard, name="dashboard"),

    # Dashboards 
    path("dashboard/admin/", views.admin_dashboard, name="dashboard_superuser"),
    path("dashboard/user/", views.user_dashboard, name="dashboard_normal"),
]

