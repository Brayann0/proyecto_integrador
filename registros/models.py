from django.db import models
from django.conf import settings

# Archivos subidos
class ArchivoCargado(models.Model):
    nombre_original = models.CharField(max_length=255)
    archivo = models.FileField(upload_to='archivos/')
    datos = models.BinaryField(null=True, blank=True) 
    tamano = models.PositiveIntegerField()
    tipo_mime = models.CharField(max_length=100, blank=True, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archivos_subidos"
    )

    procesado = models.BooleanField(default=False)
    registros_creados = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre_original} ({self.subido_por})"


# Registros internos de los archivos
class RegistroContable(models.Model):
    archivo = models.ForeignKey(
    'ArchivoCargado',
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='registros'
)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    persona_no_registrada= models.ForeignKey(
        'usuarios.PersonaNoRegistrada',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    fecha = models.DateField()
    nombre = models.CharField(max_length=100, null=True, blank=True)
    identificacion = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    valor = models.DecimalField(max_digits=12, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    salario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fecha_pago = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre or 'Sin nombre'} - {self.valor} ({self.fecha})"


