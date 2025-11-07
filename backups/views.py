from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from django.conf import settings
from .models import Backup
import os
import subprocess
import datetime

BACKUP_DIR = os.path.join(settings.BASE_DIR, 'backups', 'archivos')
os.makedirs(BACKUP_DIR, exist_ok=True)

def lista_backups(request):
    backups = Backup.objects.all().order_by('-fecha')
    return render(request, 'backups/lista_backups.html', {'backups': backups})

def crear_backup(request):
    fecha = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_archivo = f'backup_{fecha}.json'
    ruta_backup = os.path.join(BACKUP_DIR, nombre_archivo)

    comando = f'python manage.py dumpdata > "{ruta_backup}"'
    subprocess.run(comando, shell=True)

    Backup.objects.create(nombre=nombre_archivo, ruta=ruta_backup)
    messages.success(request, '✅ Copia de seguridad creada correctamente.')
    return redirect('backups:lista_backups')

def descargar_backup(request, backup_id):
    backup = get_object_or_404(Backup, id=backup_id)
    if os.path.exists(backup.ruta):
        return FileResponse(open(backup.ruta, 'rb'), as_attachment=True, filename=backup.nombre)
    messages.error(request, '❌ El archivo no existe.')
    return redirect('backups:lista_backups')

def eliminar_backup(request, backup_id):
    backup = get_object_or_404(Backup, id=backup_id)
    if os.path.exists(backup.ruta):
        os.remove(backup.ruta)
    backup.delete()
    messages.success(request, '🗑️ Copia eliminada correctamente.')
    return redirect('backups:lista_backups')

def restaurar_backup(request, backup_id):
    backup = get_object_or_404(Backup, id=backup_id)
    if os.path.exists(backup.ruta):
        comando = f'python manage.py loaddata "{backup.ruta}"'
        subprocess.run(comando, shell=True)
        messages.success(request, '♻️ Copia restaurada exitosamente.')
    else:
        messages.error(request, '❌ No se encontró el archivo para restaurar.')
    return redirect('backups:lista_backups')
