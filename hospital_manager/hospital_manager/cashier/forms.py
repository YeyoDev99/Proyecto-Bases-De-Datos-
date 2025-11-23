from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import (
    Persona, Empleados, Pacientes, Citas, Historias_Clinicas, Equipamiento,
    Inventario_Farmacia, Sedes_Hospitalarias, Departamentos
)

# ====================================================================
# 1. FORMULARIOS DE AUTENTICACIÓN Y REGISTRO (Basado en Persona)
# ====================================================================

class PersonaCreationForm(UserCreationForm):
    """
    Formulario personalizado para la creación de un nuevo usuario (Persona).
    Hereda de UserCreationForm, pero añade campos específicos de Persona.
    """
    class Meta(UserCreationForm.Meta):
        # Aseguramos que el modelo usado sea el correcto: Persona
        model = Persona 
        fields = UserCreationForm.Meta.fields + (
            'email', 'tipo_doc', 'num_doc', 'fecha_nac', 'genero',
            'direccion', 'celular', 'ciudad_residencia',
        )
        # Hacemos que 'username' no sea obligatorio en el formulario
        # ya que la autenticación es por email (USERNAME_FIELD='email')
        exclude = ('username',) 

class PersonaChangeForm(UserChangeForm):
    """
    Formulario personalizado para la edición de un usuario (Persona).
    """
    class Meta:
        # Aseguramos que el modelo usado sea el correcto: Persona
        model = Persona
        fields = ('first_name', 'last_name', 'email', 'tipo_doc', 'num_doc', 'fecha_nac', 
                  'genero', 'direccion', 'celular', 'ciudad_residencia', 'is_active')


# ====================================================================
# 2. FORMULARIOS DE MÓDULOS CLÍNICOS Y GESTIÓN
# ====================================================================

class GestionCitasForm(forms.ModelForm):
    """
    Formulario para la gestión de citas.
    """
    # Filtramos los empleados para que solo muestre Médicos para la asignación
    id_emp = forms.ModelChoiceField(
        queryset=Empleados.objects.filter(id_rol__nombre_rol='Médico'),
        label="Médico Asignado",
        required=True
    )
    # Mostramos los pacientes por su nombre y documento
    cod_pac = forms.ModelChoiceField(
        queryset=Pacientes.objects.all().select_related('persona'),
        label="Paciente",
        required=True,
        # Usamos una función lambda para mostrar el nombre completo y el documento
        to_field_name=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccione un Paciente"
    )

    class Meta:
        model = Citas
        fields = ['cod_pac', 'id_emp', 'id_dept', 'fecha_hora', 'tipo_servicio', 'estado']
        widgets = {
            'fecha_hora': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'tipo_servicio': forms.TextInput(attrs={'placeholder': 'Ej: Consulta General, Control'})
        }

class HistoriaClinicaForm(forms.ModelForm):
    """
    Formulario para el registro de una Historia Clínica después de una Cita.
    """
    class Meta:
        model = Historias_Clinicas
        # El campo id_cita debe ser autocompletado o filtrado
        fields = ['id_cita', 'motivo_consulta', 'diagnostico', 'observaciones']
        widgets = {
            'motivo_consulta': forms.Textarea(attrs={'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

# ====================================================================
# 3. FORMULARIOS DE RECURSOS Y LOGÍSTICA
# ====================================================================

class EquipamientoForm(forms.ModelForm):
    """
    Formulario para la gestión de equipos hospitalarios.
    """
    class Meta:
        model = Equipamiento
        fields = ['nom_eq', 'marca_modelo', 'id_dept', 'estado_equipo', 'fecha_ultimo_maint', 'responsable_id']
        widgets = {
            'fecha_ultimo_maint': forms.DateInput(attrs={'type': 'date'}),
        }

class InventarioFarmaciaForm(forms.ModelForm):
    """
    Formulario para la actualización del stock de inventario por sede.
    """
    class Meta:
        model = Inventario_Farmacia
        fields = ['id_sede', 'cod_med', 'stock_actual']
        # Los campos cod_med e id_sede juntos deben ser únicos, 
        # Django lo maneja automáticamente si no se cambia la queryset.

class SedeHospitalariaForm(forms.ModelForm):
    """
    Formulario para la gestión de Sedes Hospitalarias.
    """
    class Meta:
        model = Sedes_Hospitalarias
        fields = ['nom_sede', 'ciudad', 'direccion', 'telefono', 'es_nodo_central']
        widgets = {
            'es_nodo_central': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class DepartamentoForm(forms.ModelForm):
    """
    Formulario para la gestión de Departamentos.
    """
    class Meta:
        model = Departamentos
        fields = ['nom_dept', 'id_sede']
        widgets = {
            'id_sede': forms.Select(attrs={'class': 'form-select'}),
        }