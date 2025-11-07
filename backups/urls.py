from django.urls import path
from . import views

app_name = 'backups'

urlpatterns = [
    path('', views.lista_backups, name='lista_backups'),
    path('crear/', views.crear_backup, name='crear_backup'),
    path('descargar/<int:backup_id>/', views.descargar_backup, name='descargar_backup'),
    path('eliminar/<int:backup_id>/', views.eliminar_backup, name='eliminar_backup'),
    path('restaurar/<int:backup_id>/', views.restaurar_backup, name='restaurar_backup'),
]