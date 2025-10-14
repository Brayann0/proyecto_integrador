from django.urls import path
from . import views

app_name = "registros"

urlpatterns = [
    path('subir/', views.subir_archivo, name='subir_archivo'),

    # Lista de archivos subidos
    path('archivos/', views.lista_archivos, name='lista_archivos'),

    # Ver contenido de un archivo específico (detalle)
    path('archivo/<int:pk>/', views.ver_archivo, name='ver_archivo'),

    # Ver todos los registros contables (global)
    path('ver/', views.ver_registros, name='ver_registros'),

    # Ver registros de un archivo en particular (nombre que usa la plantilla)
    path('ver/<int:archivo_id>/', views.ver_registros, name='ver_registros_por_archivo'),



    # Detalle de un registro específico
    path('detalle/<int:id>/', views.detalle_registro, name='detalle_registro'),
    
    path('archivo/<int:pk>/guardar/', views.guardar_registros, name='guardar_registros'),


    path('guardar/<int:archivo_id>/', views.guardar_registros, name='guardar_registros'),
    path("archivos/descargar/<int:archivo_id>/", views.descargar_archivo, name="descargar_archivo"),


]