from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from registros.models import ArchivoCargado
from django.contrib.auth.models import User

def archivos_por_mes(request):
    year = timezone.now().year
    qs = (
        ArchivoCargado.objects
        .filter(fecha_subida__year=year)
        .annotate(mes=ExtractMonth("fecha_subida"))
        .values("mes")
        .annotate(total=Count("id"))
        .order_by("mes")
    )

    return JsonResponse({
        "labels": [item["mes"] for item in qs],
        "data": [item["total"] for item in qs],
        "year": year
    })

def usuarios_activos(request):
    activos = User.objects.filter(is_active=True).count()
    inactivos = User.objects.filter(is_active=False).count()
    return JsonResponse({
        "labels": ["Activos", "Inactivos"],
        "data": [activos, inactivos]
    })
