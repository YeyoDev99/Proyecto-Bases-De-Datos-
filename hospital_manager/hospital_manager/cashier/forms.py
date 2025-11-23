from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from .models import Persona, Empleados, Roles, Departamentos, Especialidades
from django import forms

class PersonaRegistrationForm(UserCreationForm):
    """
    Formulario de registro de PERSONA que también crea un registro en EMPLEADOS.
    Nota: En un HIS real, este formulario solo debería ser accesible por administradores.
    """
    # Campos heredados de AbstractUser que queremos personalizar en la UI
    password1 = forms.CharField(
        label= "Contraseña",
        widget=forms.PasswordInput(attrs={'class':'form-control', 'type':'password','placeholder':'Contraseña', 'id': 'password'}),
    )
    password2 = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class':'form-control', 'type':'password', 'placeholder':'Confirmar Contraseña'}),
    )

    # Campos específicos del modelo PERSONA
    first_name = forms.CharField(label="Nombres", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres del Empleado'}))
    last_name = forms.CharField(label="Apellidos", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos del Empleado'}))
    
    tipo_doc = forms.ChoiceField(label="Tipo de Documento", choices=Persona.TIPO_DOCS, widget=forms.Select(attrs={'class': 'form-select'}))
    num_doc = forms.CharField(label="Número de Documento", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 123456789'}))
    fecha_nac = forms.DateField(label="Fecha de Nacimiento", widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    genero = forms.ChoiceField(label="Género", choices=Persona.genero.field.choices, widget=forms.Select(attrs={'class': 'form-select'}))
    
    direccion = forms.CharField(label="Dirección", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Dirección de Residencia'}))
    celular = forms.CharField(label="Celular", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de contacto válido'}))
    ciudad_residencia = forms.CharField(label="Ciudad", required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ciudad de Residencia'}))

    # Campos específicos para crear la entidad EMPLEADOS (Foreign Keys)
    # Usamos ModelChoiceField para cargar las opciones de las tablas lookup
    id_rol = forms.ModelChoiceField(
        queryset=Roles.objects.all(),
        label="Rol / Cargo",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccione el Rol",
        help_text="Rol asignado al empleado (Médico, Admin, etc.)"
    )
    id_dept = forms.ModelChoiceField(
        queryset=Departamentos.objects.all(),
        label="Departamento / Área",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccione el Departamento",
        required=False
    )
    id_especialidad = forms.ModelChoiceField(
        queryset=Especialidades.objects.all(),
        label="Especialidad (Si es médico)",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="No aplica (Otro rol)",
        required=False
    )

    class Meta:
        model = Persona
        # Se listan todos los campos del modelo Persona + los de autenticación
        fields = (
            'email', 'first_name', 'last_name', 'tipo_doc', 'num_doc', 
            'fecha_nac', 'genero', 'direccion', 'celular', 'ciudad_residencia', 
            'id_rol', 'id_dept', 'id_especialidad', 'password1', 'password2'
        )
        widgets= {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico único'}),
        }
        
    def save(self, commit=True):
        """
        Guarda la Persona base y luego crea el objeto Empleado asociado.
        """
        # 1. Guarda la Persona (AbstractUser)
        persona = super().save(commit=False)
        
        # 2. Guarda la Persona en la BD
        if commit:
            persona.save()
            
        # 3. Crea el registro en la tabla Empleados, usando la Persona como llave PK/FK
        empleado = Empleados.objects.create(
            persona=persona,
            id_rol=self.cleaned_data['id_rol'],
            id_dept=self.cleaned_data['id_dept'],
            id_especialidad=self.cleaned_data['id_especialidad'],
            activo=True # Por defecto, activo al crearse
        )
        
        return empleado

# --- Formularios de Gestión Clínica ---

class GestionCitasForm(ModelForm):
    """
    Formulario base para la gestión de citas médicas.
    """
    # Usamos CharField con DateInput y TimeInput para mayor control en la UI
    fecha_hora = forms.DateTimeField(
        label="Fecha y Hora de la Cita",
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M']
    )
    
    # Solo cargar médicos (empleados con el rol "Médico")
    id_emp = forms.ModelChoiceField(
        queryset=Empleados.objects.filter(id_rol__nombre_rol='Médico'),
        label="Médico Asignado",
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Seleccione un Médico"
    )

    class Meta:
        from .models import Citas
        model = Citas
        fields = ['cod_pac', 'id_emp', 'id_dept', 'fecha_hora', 'tipo_servicio', 'estado']
        
        widgets = {
            'cod_pac': forms.Select(attrs={'class': 'form-select'}), # Se llenará con JavaScript si es necesario, o se deja como ModelSelect
            'id_dept': forms.Select(attrs={'class': 'form-select'}),
            'tipo_servicio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Consulta General, Control Post-operatorio'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class HistoriaClinicaForm(ModelForm):
    """
    Formulario para el registro o actualización de la historia clínica asociada a una cita.
    """
    class Meta:
        from .models import Historias_Clinicas
        model = Historias_Clinicas
        fields = ['motivo_consulta', 'diagnostico', 'observaciones']
        
        widgets = {
            'motivo_consulta': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'diagnostico': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }