
from datetime import datetime
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt

from .models import ArchivoCargado, RegistroContable
from .forms import SubirArchivoForm
from .utils import procesar_archivos



# verificar si el usuario es administrador

def es_admin(user):
    return user.is_staff or user.is_superuser



# Subir archivo Excel

@login_required
@user_passes_test(es_admin)
def subir_archivo(request):
    
    # 🔒 Restringimos el acceso: solo administradores o superusuarios
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "No tienes permiso para acceder a esta página.")
        return redirect("usuarios:user_dashboard")

    if request.method == "POST":
        form = SubirArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES["archivo"]
            contenido = archivo.read()

            try:
                # ✅ Crear el registro del archivo
                archivo_model = ArchivoCargado.objects.create(
                    nombre_original=archivo.name,
                    datos=contenido,
                    tamano=archivo.size,
                    tipo_mime=archivo.content_type,
                    subido_por=request.user,
                )

                # ✅ Procesar el archivo
                registros_creados = procesar_archivos(archivo_model)
                messages.success(request, f"✅ Archivo procesado con {registros_creados} registros creados.")

                # Redirigir según el tipo de usuario
                if request.user.is_superuser:
                    return redirect("usuarios:dashboard_superuser")
                else:
                    return redirect("usuarios:dashboard_admin")

            except Exception as e:
                messages.error(request, f"❌ Error al procesar el archivo: {e}")
    else:
        form = SubirArchivoForm()

    return render(request, "registros/subir_archivos.html", {"form": form})



#  Lista de archivos subidos

@login_required
@user_passes_test(es_admin)
def lista_archivos(request):
    """
    Muestra la lista de archivos subidos con opción de filtrar por fechas.
    """
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
            messages.warning(request, "⚠️ Formato de fecha inválido. Use YYYY-MM-DD.")

    # Conversión de tamaño a KB
    for a in archivos:
        a.tamano_kb = round(a.tamano / 1024, 2) if a.tamano else 0

    return render(request, 'registros/lista_archivos.html', {
        'archivos': archivos,
        'fecha_inicio': request.GET.get("fecha_inicio", ""),
        'fecha_fin': request.GET.get("fecha_fin", "")
    })



#  Ver contenido de un archivo

@login_required
def ver_archivo(request, pk):
    """
    Muestra los registros asociados a un archivo específico,
    con posibilidad de filtrarlos por fecha y editarlos en línea.
    """
    archivo = get_object_or_404(ArchivoCargado, pk=pk)
    registros = RegistroContable.objects.filter(archivo=archivo).order_by('-id')

    # Filtros por fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if fecha_inicio:
        registros = registros.filter(fecha__gte=parse_date(fecha_inicio))
    if fecha_fin:
        registros = registros.filter(fecha__lte=parse_date(fecha_fin))

    # Edición directa (inline)
    if request.method == 'POST':
        registro_id = request.POST.get('registro_id')
        campo = request.POST.get('campo')
        nuevo_valor = request.POST.get('valor')

        if registro_id and campo:
            registro = get_object_or_404(RegistroContable, id=registro_id)
            if campo in [f.name for f in RegistroContable._meta.fields if f.name not in ['id', 'archivo']]:
                setattr(registro, campo, nuevo_valor)
                registro.save()
                messages.success(request, f"✅ Registro {registro_id} actualizado correctamente.")
            else:
                messages.warning(request, f"⚠️ El campo '{campo}' no puede modificarse directamente.")

            return redirect('registros:ver_archivo', pk=pk)

    columnas = [f.name for f in RegistroContable._meta.fields if f.name not in ['id', 'archivo']]

    return render(request, 'registros/ver_archivo.html', {
        'archivo': archivo,
        'registros': registros,
        'columnas': columnas,
        'fecha_inicio': fecha_inicio or '',
        'fecha_fin': fecha_fin or ''
    })



#  Ver todos los registros contables (editable tipo Excel)

@user_passes_test(es_admin)
@login_required
def ver_registros(request, archivo_id=None):
    """
    Muestra los registros contables en formato tipo Excel (Jspreadsheet).
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

    # Columnas mostradas
    columnas = ["id", "fecha", "nombre", "identificacion", "valor", "descripcion", "usuario"]

    # Conversión a JSON
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
        "registros": registros,
        "fecha_inicio": fecha_inicio or "",
        "fecha_fin": fecha_fin or "",
    })



#  Guardar registros editados (Jspreadsheet)

@csrf_exempt
@login_required
def guardar_registros(request, archivo_id):
    """
    Guarda los cambios hechos en la vista editable tipo Excel.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        datos = json.loads(request.body)
        archivo = get_object_or_404(ArchivoCargado, pk=archivo_id)

        for fila in datos:
            registro_id = fila.get("id")
            fecha = fila.get("fecha")
            nombre = fila.get("nombre")
            identificacion = fila.get("identificacion")
            valor = fila.get("valor")
            descripcion = fila.get("descripcion")

            if registro_id and str(registro_id).isdigit():
                registro = RegistroContable.objects.filter(id=registro_id).first()
                if registro:
                    registro.fecha = datetime.strptime(fecha, "%Y-%m-%d") if fecha else None
                    registro.nombre = nombre
                    registro.identificacion = identificacion
                    registro.valor = float(valor or 0)
                    registro.descripcion = descripcion
                    registro.save()
            else:
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


#  Detalle de un registro contable

@login_required
def detalle_registro(request, id):
    registro = get_object_or_404(RegistroContable, id=id)
    return render(request, "registros/detalle_registro.html", {"registro": registro})



#  Descargar archivo binario

@login_required
def descargar_archivo(request, archivo_id):
    """
    Permite descargar el archivo binario almacenado en la base de datos.
    """
    try:
        archivo = ArchivoCargado.objects.get(id=archivo_id)
    except ArchivoCargado.DoesNotExist:
        raise Http404("El archivo no existe")

    if not archivo.datos:
        raise Http404("El archivo no tiene datos asociados")

    response = HttpResponse(
        archivo.datos,
        content_type=archivo.tipo_mime or "application/octet-stream"
    )
    response["Content-Disposition"] = f'attachment; filename="{archivo.nombre_original}"'
    return response
