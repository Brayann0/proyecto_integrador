from django import forms
from .models import ArchivoCargado, RegistroContable


class SubirArchivoForm(forms.ModelForm):
    archivo = forms.FileField(
        label='Selecciona un archivo Excel o CSV',
        required=True,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ArchivoCargado
        fields = ['archivo']  # 👈 Importante: definimos el campo manualmente

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        archivo_subido = self.cleaned_data.get('archivo')

        if not archivo_subido:
            raise forms.ValidationError("Debes seleccionar un archivo válido.")

        # Creamos la instancia del modelo manualmente
        instance = ArchivoCargado(
            nombre_original=archivo_subido.name,
            tamano=archivo_subido.size,
            tipo_mime=archivo_subido.content_type,
            subido_por=self.user
        )

        # ✅ Guardamos los bytes binarios en el campo 'datos'
        instance.datos = archivo_subido.read()

        if commit:
            instance.save()

        return instance


class RegistroContableForm(forms.ModelForm):
    class Meta:
        model = RegistroContable
        fields = ['usuario', 'nombre', 'identificacion', 'salario', 'fecha_pago']


class BusquedaPorFechaForm(forms.Form):
    fecha_inicio = forms.DateField(
        label="Fecha inicio",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    fecha_fin = forms.DateField(
        label="Fecha fin",
        widget=forms.DateInput(attrs={'type': 'date'})
    )


class BusquedaPorFechaExactaForm(forms.Form):
    fecha_pago = forms.DateField(
        label="Fecha de pago",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
