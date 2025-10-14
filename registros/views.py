from datetime import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.dateparse import parse_date
from .models import ArchivoCargado, RegistroContable
from .forms import SubirArchivoForm
from .utils import procesar_archivos
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django.http import HttpResponse, Http404
from .models import ArchivoCargado

# ==========================
# Helper: verificar si el usuario es admin
# ==========================
def es_admin(user):
    return user.is_staff or user.is_superuser


# ==========================
# Subir archivo Excel
# ==========================
@login_required
@user_passes_test(es_admin)
def subir_archivo(request):
    if request.method == "POST":
        form = SubirArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES["archivo"]
            contenido = archivo.read()

            archivo_model = ArchivoCargado.objects.create(
                nombre_original=archivo.name,
                datos=contenido,
                tamano=archivo.size,
                tipo_mime=archivo.content_type,
                subido_por=request.user,
            )

            try:
                registros_creados = procesar_archivos(archivo_model)
                messages.success(request, f"Archivo procesado con {registros_creados} registros creados.")
                return redirect("usuarios:dashboard_superuser")
            except Exception as e:
                messages.error(request, f"Error al procesar el archivo: {e}")
    else:
        form = SubirArchivoForm()

    return render(request, "registros/subir_archivos.html", {"form": form})


# ==========================
# Ver contenido de un archivo (con filtro y edición inline)
# ==========================
@login_required
def ver_archivo(request, pk):
    # Buscar el archivo o lanzar error 404 si no existe
    archivo = get_object_or_404(ArchivoCargado, pk=pk)

    # Filtrar los registros asociados a ese archivo
    registros = RegistroContable.objects.filter(archivo=archivo).order_by('-id')

    # --- Filtros por fecha ---
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        registros = registros.filter(fecha__gte=parse_date(fecha_inicio))
    if fecha_fin:
        registros = registros.filter(fecha__lte=parse_date(fecha_fin))

    # --- Edición directa (inline) ---
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        campo = request.POST.get('campo')
        nuevo_valor = request.POST.get('valor')

        if registro_id and campo:
            registro = get_object_or_404(RegistroContable, id=registro_id)

            # Verificar que el campo es editable
            if campo in [f.name for f in RegistroContable._meta.fields if f.name not in ['id', 'archivo']]:
                setattr(registro, campo, nuevo_valor)
                registro.save()
                messages.success(request, f"✅ Registro {registro_id} actualizado correctamente.")
            else:
                messages.warning(request, f"⚠️ El campo '{campo}' no puede modificarse directamente.")

            return redirect('registros:ver_archivo', pk=pk)

    # --- Columnas visibles en la tabla ---
    columnas = [f.name for f in RegistroContable._meta.fields if f.name not in ['id', 'archivo']]

    # --- Renderizar plantilla ---
    return render(request, 'registros/ver_archivo.html', {
        'archivo': archivo,
        'registros': registros,
        'columnas': columnas,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or ''
    })

# ==========================
# Lista de archivos subidos
# ==========================
@login_required
@user_passes_test(es_admin)
def lista_archivos(request):  # 👈 corregido el nombre (antes era lista_archivo)
    archivos = ArchivoCargado.objects.all().order_by('-fecha_subida')

    # Filtro por fechas
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if fecha_inicio and fecha_fin:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
            archivos = archivos.filter(fecha_subida__range=[fecha_inicio, fecha_fin])
        except ValueError:
            messages.warning(request, "Formato de fecha inválido. Use YYYY-MM-DD.")

    for a in archivos:
        a.tamano_kb = round(a.tamano / 1024, 2) if a.tamano else 0

    return render(request, 'registros/lista_archivos.html', {
        'archivos': archivos,
        'fecha_inicio': request.GET.get("fecha_inicio", ""),
        'fecha_fin': request.GET.get("fecha_fin", "")
    })


# ==========================
# Ver todos los registros contables
# ==========================
from datetime import datetime
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
import json

from .models import RegistroContable, ArchivoCargado


@login_required
def ver_registros(request, archivo_id=None):
    """
    Muestra los registros contables de un archivo en formato editable tipo Excel (Jspreadsheet).
    """
    registros = RegistroContable.objects.all().order_by('-id')
    archivo = None

    if archivo_id:
        archivo = get_object_or_404(ArchivoCargado, pk=archivo_id)
        registros = registros.filter(archivo=archivo)

    # Filtro por fechas
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if fecha_inicio:
        registros = registros.filter(fecha__gte=parse_date(fecha_inicio))
    if fecha_fin:
        registros = registros.filter(fecha__lte=parse_date(fecha_fin))

    # Columnas que se mostrarán y podrán editarse
    columnas = ["id", "fecha", "nombre", "identificacion", "valor", "descripcion", "usuario"]

    # Convertimos los registros a una lista de listas (para jspreadsheet)
    registros_json = json.dumps([
        [
            r.id,
            r.fecha.strftime("%Y-%m-%d") if r.fecha else "",
            r.nombre or "",
            r.identificacion or "",
            str(r.valor or ""),
            r.descripcion or "",
            str(r.usuario or ""),
        ]
        for r in registros
    ])

    return render(request, "registros/ver_registros.html", {
        "archivo": archivo,
        "columnas": columnas,
        "registros_json": registros_json,
        "fecha_inicio": fecha_inicio or "",
        "fecha_fin": fecha_fin or "",
    })


@csrf_exempt
@login_required
def guardar_registros(request, archivo_id):
    """
    Recibe los datos editados desde el frontend (jspreadsheet) y actualiza o crea registros.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        datos = json.loads(request.body)
        archivo = get_object_or_404(ArchivoCargado, pk=archivo_id)

        for fila in datos:
            # fila = [id, fecha, nombre, identificacion, valor, descripcion, usuario]
            registro_id = fila[0]
            fecha = fila[1]
            nombre = fila[2]
            identificacion = fila[3]
            valor = fila[4]
            descripcion = fila[5]

            if registro_id and str(registro_id).isdigit():
                # 🔄 Actualizar existente
                registro = RegistroContable.objects.filter(id=registro_id).first()
                if registro:
                    registro.fecha = datetime.strptime(fecha, "%Y-%m-%d") if fecha else None
                    registro.nombre = nombre
                    registro.identificacion = identificacion
                    registro.valor = float(valor or 0)
                    registro.descripcion = descripcion
                    registro.save()
            else:
                # 🆕 Crear nuevo
                RegistroContable.objects.create(
                    archivo=archivo,
                    fecha=datetime.strptime(fecha, "%Y-%m-%d") if fecha else None,
                    nombre=nombre,
                    identificacion=identificacion,
                    valor=float(valor or 0),
                    descripcion=descripcion,
                    usuario=request.user,
                )

        return JsonResponse({"mensaje": "✅ Cambios guardados correctamente."})

    except Exception as e:
        return JsonResponse({"error": f"❌ Error al guardar: {str(e)}"}, status=400)



# ==========================
# Detalle de un registro
# ==========================
@login_required
def detalle_registro(request, id):
    registro = get_object_or_404(RegistroContable, id=id)
    return render(request, "registros/detalle_registro.html", {"registro": registro})


def descargar_archivo(request, archivo_id):
    try:
        archivo = ArchivoCargado.objects.get(id=archivo_id)
    except ArchivoCargado.DoesNotExist:
        raise Http404("El archivo no existe")

    if not archivo.datos:
        raise Http404("El archivo no tiene datos asociados")

    response = HttpResponse(archivo.datos, content_type=archivo.tipo_mime or "application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{archivo.nombre_original}"'
    return response
