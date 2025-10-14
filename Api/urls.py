from django.urls import path
from . import views

urlpatterns = [
    path("archivos/por-mes/", views.archivos_por_mes, name="archivos_por_mes"),
    path("usuarios/activos/", views.usuarios_activos, name="usuarios_activos"),
]
