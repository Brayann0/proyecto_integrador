import os
import pandas as pd
from django.db import transaction
from registros.models import RegistroContable
from usuarios.models import Usuario, PersonaNoRegistrada
from io import BytesIO
import unidecode


def leer_archivo_binario(archivo_obj):
    """
    Lee un archivo Excel/CSV desde un campo binario en memoria.
    """
    contenido = BytesIO(archivo_obj.datos)  # Convertir bytes en flujo de datos
    nombre = archivo_obj.nombre_original.lower()

    try:
        if nombre.endswith(('.xlsx', '.xlsm', '.xltx', '.xltm')):
            df = pd.read_excel(contenido, engine='openpyxl')
        elif nombre.endswith('.xls'):
            df = pd.read_excel(contenido, engine='xlrd')
        elif nombre.endswith('.csv'):
            df = pd.read_csv(contenido)
        else:
            raise ValueError("Formato de archivo no soportado")

        df.columns = [
            unidecode.unidecode(str(c).strip().lower().replace(" ", "_"))
            for c in df.columns
        ]
        return df
    except Exception as e:
        raise ValueError(f"Error al leer el archivo: {e}")


@transaction.atomic
def procesar_archivos(archivo_obj):
    """
    Convierte un ArchivoCargado en registros contables sin importar el orden de columnas.
    """
    df = leer_archivo_binario(archivo_obj)

    # columnas requeridas
    required_cols = {"identificacion", "nombre", "valor", "fecha"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"El archivo debe contener al menos las columnas: {', '.join(required_cols)}")

    registros_creados = 0
    for _, row in df.iterrows():
        identificacion = str(row.get("identificacion")).strip() if row.get("identificacion") else None
        nombre = row.get("nombre", "")

        # Buscar usuario registrado
        usuario = Usuario.objects.filter(identificacion=identificacion).first() if identificacion else None

        # Si no hay usuario, crear o usar PersonaNoRegistrada
        persona = None
        if not usuario and identificacion:
            persona, _ = PersonaNoRegistrada.objects.get_or_create(
                cedula=identificacion,
                defaults={"nombre": nombre or "Desconocido"}
            )

        # Crear registro contable
        RegistroContable.objects.create(
            archivo=archivo_obj,
            usuario=usuario,
            persona_no_registrada=persona,  # asegúrate de que el campo en el modelo se llame así
            identificacion=identificacion,
            nombre=nombre,
            valor=row.get("valor", 0),
            descripcion=row.get("descripcion") if "descripcion" in df.columns else "",
            salario=row.get("salario") if "salario" in df.columns else None,
            fecha=row.get("fecha"),
            fecha_pago=row.get("fecha_pago") if "fecha_pago" in df.columns else None,
            email=row.get("email") if "email" in df.columns else None,
        )

        registros_creados += 1

    # Marcar archivo como procesado
    archivo_obj.procesado = True
    archivo_obj.registros_creados = registros_creados
    archivo_obj.save()

    return registros_creados

