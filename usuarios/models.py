from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Usuario(AbstractUser):
    ROLES = [
        ('admin', 'Administrador'),
        ('usuario', 'Usuario'),
    ]

    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    identificacion = models.CharField(max_length=20, unique=True, null=True, blank=True)
    rol = models.CharField(max_length=20, choices=ROLES, default='usuario')  # 👈 nuevo campo

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'nombre', 'apellido']

    def __str__(self):
        return f"{self.email} ({self.rol})"
    

# Modelo para personas no registradas
class PersonaNoRegistrada(models.Model):
    nombre = models.CharField(max_length=255)
    cedula = models.CharField(max_length=20, unique=True)
    fecha_registro = models.DateField(auto_now_add=True)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.cedula})"
    


