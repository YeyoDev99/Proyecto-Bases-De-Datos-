"""
Formularios del Sistema Hospitalario HIS+
Sistema SIN ORM - Validación de datos con consultas SQL directas
"""

from django import forms
from django.core.exceptions import ValidationError
from django.db import connection
from datetime import datetime, date
import re

# ============================================================================
# FUNCIONES HELPER PARA CONSULTAS SQL
# ============================================================================

def ejecutar_query(query, params=None):
    """Ejecuta una query y retorna los resultados"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchall()


def ejecutar_query_one(query, params=None):
    """Ejecuta una query y retorna un solo resultado"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchone()


def obtener_choices_from_db(query, params=None):
    """
    Ejecuta una query y retorna choices para un campo Select.
    La query debe retornar (id, nombre)
    """
    results = ejecutar_query(query, params)
    return [(row[0], row[1]) for row in results]


# ============================================================================
# 1. FORMULARIOS DE AUTENTICACIÓN
# ============================================================================

class LoginForm(forms.Form):
    """Formulario de inicio de sesión"""
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=150,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'usuario@hospital.com',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            # Verificar credenciales en la BD
            query = """
                SELECT e.id_emp, e.activo
                FROM Empleados e
                INNER JOIN Personas p ON e.id_persona = p.id_persona
                WHERE p.email_persona = %s 
                AND e.hash_contra = crypt(%s, e.hash_contra)
            """
            result = ejecutar_query_one(query, [email, password])
            
            if not result:
                raise ValidationError('Credenciales inválidas.')
            
            if not result[1]:  # activo = False
                raise ValidationError('Su cuenta está desactivada. Contacte al administrador.')
        
        return cleaned_data


class CambiarPasswordForm(forms.Form):
    """Formulario para cambiar contraseña"""
    password_actual = forms.CharField(
        label='Contraseña Actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password_nueva = forms.CharField(
        label='Nueva Contraseña',
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Mínimo 8 caracteres'
    )
    password_confirmacion = forms.CharField(
        label='Confirmar Nueva Contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, user_email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_email = user_email
    
    def clean_password_actual(self):
        password = self.cleaned_data.get('password_actual')
        
        # Verificar que la contraseña actual sea correcta
        query = """
            SELECT e.id_emp
            FROM Empleados e
            INNER JOIN Personas p ON e.id_persona = p.id_persona
            WHERE p.email_persona = %s 
            AND e.hash_contra = crypt(%s, e.hash_contra)
        """
        result = ejecutar_query_one(query, [self.user_email, password])
        
        if not result:
            raise ValidationError('La contraseña actual es incorrecta.')
        
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        nueva = cleaned_data.get('password_nueva')
        confirmacion = cleaned_data.get('password_confirmacion')
        
        if nueva and confirmacion and nueva != confirmacion:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return cleaned_data


# ============================================================================
# 2. FORMULARIOS DE PERSONAS Y PACIENTES
# ============================================================================

class PersonaForm(forms.Form):
    """Formulario base para Personas (usado en Pacientes y Empleados)"""
    
    TIPO_DOC_CHOICES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('CE', 'Cédula de Extranjería'),
        ('PA', 'Pasaporte'),
    ]
    
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    
    nom_persona = forms.CharField(
        label='Nombre',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    apellido_persona = forms.CharField(
        label='Apellido',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tipo_doc = forms.ChoiceField(
        label='Tipo de Documento',
        choices=TIPO_DOC_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    num_doc = forms.CharField(
        label='Número de Documento',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_nac = forms.DateField(
        label='Fecha de Nacimiento',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    genero = forms.ChoiceField(
        label='Género',
        choices=GENERO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    dir_persona = forms.CharField(
        label='Dirección',
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tel_persona = forms.CharField(
        label='Teléfono',
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email_persona = forms.EmailField(
        label='Correo Electrónico',
        max_length=150,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    ciudad_residencia = forms.CharField(
        label='Ciudad de Residencia',
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    def clean_num_doc(self):
        num_doc = self.cleaned_data.get('num_doc')
        
        # Verificar si el documento ya existe (excepto si estamos editando)
        if not hasattr(self, 'persona_id'):  # Nuevo registro
            query = "SELECT COUNT(*) FROM Personas WHERE num_doc = %s"
            result = ejecutar_query_one(query, [num_doc])
            
            if result and result[0] > 0:
                raise ValidationError('Este número de documento ya está registrado.')
        
        return num_doc
    
    def clean_email_persona(self):
        email = self.cleaned_data.get('email_persona')
        
        # Verificar si el email ya existe
        if not hasattr(self, 'persona_id'):  # Nuevo registro
            query = "SELECT COUNT(*) FROM Personas WHERE email_persona = %s"
            result = ejecutar_query_one(query, [email])
            
            if result and result[0] > 0:
                raise ValidationError('Este correo electrónico ya está registrado.')
        
        return email
    
    def clean_fecha_nac(self):
        fecha = self.cleaned_data.get('fecha_nac')
        
        if fecha:
            # Calcular edad
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            
            if edad < 0:
                raise ValidationError('La fecha de nacimiento no puede ser futura.')
            
            if edad > 120:
                raise ValidationError('La fecha de nacimiento no es válida.')
        
        return fecha


class PacienteForm(PersonaForm):
    """Formulario para registrar/editar pacientes"""
    
    def __init__(self, *args, **kwargs):
        self.paciente_id = kwargs.pop('paciente_id', None)
        super().__init__(*args, **kwargs)


# ============================================================================
# 3. FORMULARIOS DE CITAS
# ============================================================================

class CitaForm(forms.Form):
    """Formulario para programar/editar citas"""
    
    cod_pac = forms.IntegerField(
        label='Paciente',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_emp = forms.IntegerField(
        label='Médico',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    id_dept = forms.IntegerField(
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_hora = forms.DateTimeField(
        label='Fecha y Hora de la Cita',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    tipo_servicio = forms.ChoiceField(
        label='Tipo de Servicio',
        choices=[
            ('Consulta', 'Consulta'),
            ('Urgencia', 'Urgencia'),
            ('Control', 'Control'),
            ('Especialidad', 'Especialidad'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    motivo = forms.CharField(
        label='Motivo de la Consulta',
        max_length=200,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    estado = forms.ChoiceField(
        label='Estado',
        choices=[
            ('PROGRAMADA', 'Programada'),
            ('COMPLETADA', 'Completada'),
            ('CANCELADA', 'Cancelada'),
        ],
        initial='PROGRAMADA',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, id_sede, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_sede = id_sede
        
        # Cargar opciones dinámicamente desde la BD
        self._cargar_pacientes()
        self._cargar_medicos(id_sede)
        self._cargar_departamentos(id_sede)
    
    def _cargar_pacientes(self):
        """Cargar lista de pacientes"""
        query = """
            SELECT pac.cod_pac, 
                   p.nom_persona || ' ' || p.apellido_persona || ' (' || p.num_doc || ')' as nombre_completo
            FROM Pacientes pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
            ORDER BY p.apellido_persona, p.nom_persona
        """
        choices = obtener_choices_from_db(query)
        self.fields['cod_pac'].widget.choices = [('', 'Seleccione un paciente')] + choices
    
    def _cargar_medicos(self, id_sede):
        """Cargar lista de médicos de la sede"""
        query = """
            SELECT e.id_emp, 
                   p.nom_persona || ' ' || p.apellido_persona as nombre_completo
            FROM Empleados e
            INNER JOIN Personas p ON e.id_persona = p.id_persona
            INNER JOIN Roles r ON e.id_rol = r.id_rol
            WHERE r.nombre_rol = 'Medico' 
            AND e.id_sede = %s 
            AND e.activo = TRUE
            ORDER BY p.apellido_persona, p.nom_persona
        """
        choices = obtener_choices_from_db(query, [id_sede])
        self.fields['id_emp'].widget.choices = [('', 'Seleccione un médico')] + choices
    
    def _cargar_departamentos(self, id_sede):
        """Cargar departamentos de la sede"""
        query = """
            SELECT id_dept, nom_dept
            FROM Departamentos
            WHERE id_sede = %s
            ORDER BY nom_dept
        """
        choices = obtener_choices_from_db(query, [id_sede])
        self.fields['id_dept'].widget.choices = [('', 'Seleccione un departamento')] + choices
    
    def clean_fecha_hora(self):
        fecha = self.cleaned_data.get('fecha_hora')
        
        if fecha:
            # No permitir citas en el pasado
            if fecha < datetime.now():
                raise ValidationError('No puede programar citas en el pasado.')
            
            # No permitir citas con más de 6 meses de anticipación
            if (fecha - datetime.now()).days > 180:
                raise ValidationError('No puede programar citas con más de 6 meses de anticipación.')
        
        return fecha


# ============================================================================
# 4. FORMULARIOS CLÍNICOS
# ============================================================================

class DiagnosticoForm(forms.Form):
    """Formulario para registrar diagnósticos"""
    
    id_enfermedad = forms.IntegerField(
        label='Enfermedad',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    observacion = forms.CharField(
        label='Observaciones',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        required=True
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cargar_enfermedades()
    
    def _cargar_enfermedades(self):
        """Cargar catálogo de enfermedades"""
        query = """
            SELECT id_enfermedad, nombre_enfermedad
            FROM Enfermedades
            ORDER BY nombre_enfermedad
        """
        choices = obtener_choices_from_db(query)
        self.fields['id_enfermedad'].widget.choices = [('', 'Seleccione una enfermedad')] + choices


class PrescripcionForm(forms.Form):
    """Formulario para prescribir medicamentos"""
    
    cod_med = forms.IntegerField(
        label='Medicamento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    dosis = forms.CharField(
        label='Dosis',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 500mg, 2 puff'
        })
    )
    frecuencia = forms.CharField(
        label='Frecuencia',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Cada 8 horas, Cada 12 horas'
        })
    )
    duracion_dias = forms.IntegerField(
        label='Duración (días)',
        min_value=1,
        max_value=365,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    cantidad_total = forms.IntegerField(
        label='Cantidad Total',
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Total de unidades a dispensar'
    )
    
    def __init__(self, id_sede, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_sede = id_sede
        self._cargar_medicamentos(id_sede)
    
    def _cargar_medicamentos(self, id_sede):
        """Cargar medicamentos disponibles en la sede"""
        query = """
            SELECT m.cod_med, 
                   m.nom_med || ' - ' || m.principio_activo || ' (Stock: ' || i.stock_actual || ')' as descripcion
            FROM Catalogo_Medicamentos m
            INNER JOIN Inventario_Farmacia i ON m.cod_med = i.cod_med
            WHERE i.id_sede = %s AND i.stock_actual > 0
            ORDER BY m.nom_med
        """
        choices = obtener_choices_from_db(query, [id_sede])
        self.fields['cod_med'].widget.choices = [('', 'Seleccione un medicamento')] + choices
    
    def clean(self):
        cleaned_data = super().clean()
        cod_med = cleaned_data.get('cod_med')
        cantidad = cleaned_data.get('cantidad_total')
        
        if cod_med and cantidad:
            # Verificar stock disponible
            query = """
                SELECT i.stock_actual
                FROM Inventario_Farmacia i
                WHERE i.cod_med = %s AND i.id_sede = %s
            """
            result = ejecutar_query_one(query, [cod_med, self.id_sede])
            
            if result and result[0] < cantidad:
                raise ValidationError(f'Stock insuficiente. Disponible: {result[0]} unidades.')
        
        return cleaned_data


# ============================================================================
# 5. FORMULARIOS DE INVENTARIO
# ============================================================================

class ActualizarStockForm(forms.Form):
    """Formulario para actualizar stock de medicamentos"""
    
    stock_actual = forms.IntegerField(
        label='Stock Actual',
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    motivo = forms.ChoiceField(
        label='Motivo del Cambio',
        choices=[
            ('COMPRA', 'Compra/Recepción'),
            ('AJUSTE', 'Ajuste de Inventario'),
            ('DEVOLUCION', 'Devolución'),
            ('PERDIDA', 'Pérdida/Daño'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    observaciones = forms.CharField(
        label='Observaciones',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


# ============================================================================
# 6. FORMULARIOS DE EQUIPAMIENTO
# ============================================================================

class EquipamientoForm(forms.Form):
    """Formulario para gestión de equipamiento"""
    
    nom_eq = forms.CharField(
        label='Nombre del Equipo',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    marca_modelo = forms.CharField(
        label='Marca y Modelo',
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    id_dept = forms.IntegerField(
        label='Departamento',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    estado_equipo = forms.ChoiceField(
        label='Estado',
        choices=[
            ('OPERATIVO', 'Operativo'),
            ('MANTENIMIENTO', 'En Mantenimiento'),
            ('FUERA_SERVICIO', 'Fuera de Servicio'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    fecha_ultimo_maint = forms.DateField(
        label='Fecha Último Mantenimiento',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    responsable_id = forms.IntegerField(
        label='Responsable',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, id_sede, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id_sede = id_sede
        self._cargar_departamentos(id_sede)
        self._cargar_empleados(id_sede)
    
    def _cargar_departamentos(self, id_sede):
        query = """
            SELECT id_dept, nom_dept
            FROM Departamentos
            WHERE id_sede = %s
            ORDER BY nom_dept
        """
        choices = obtener_choices_from_db(query, [id_sede])
        self.fields['id_dept'].widget.choices = [('', 'Seleccione un departamento')] + choices
    
    def _cargar_empleados(self, id_sede):
        query = """
            SELECT e.id_emp, p.nom_persona || ' ' || p.apellido_persona
            FROM Empleados e
            INNER JOIN Personas p ON e.id_persona = p.id_persona
            WHERE e.id_sede = %s AND e.activo = TRUE
            ORDER BY p.apellido_persona
        """
        choices = obtener_choices_from_db(query, [id_sede])
        self.fields['responsable_id'].widget.choices = [('', 'Sin asignar')] + choices


# ============================================================================
# 7. FORMULARIOS DE FILTROS Y BÚSQUEDA
# ============================================================================

class FiltroReportesForm(forms.Form):
    """Formulario para filtrar reportes"""
    
    fecha_inicio = forms.DateField(
        label='Fecha Inicio',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    fecha_fin = forms.DateField(
        label='Fecha Fin',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    id_sede = forms.IntegerField(
        label='Sede',
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cargar_sedes()
    
    def _cargar_sedes(self):
        query = "SELECT id_sede, nom_sede FROM Sedes_Hospitalarias ORDER BY nom_sede"
        choices = obtener_choices_from_db(query)
        self.fields['id_sede'].widget.choices = [('', 'Todas las sedes')] + choices