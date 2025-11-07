from django.contrib import admin
from .models import Backup

@admin.register(Backup)
class BackupAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha', 'ruta')
    ordering = ('-fecha',)