from django.db import models
import os

class Backup(models.Model):
    nombre = models.CharField(max_length=200)
    fecha = models.DateTimeField(auto_now_add=True)
    ruta = models.TextField() 

    def __str__(self):
        return self.nombre

    def nombre_archivo(self):
        return os.path.basename(self.ruta)
