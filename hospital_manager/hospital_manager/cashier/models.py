from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

# ====================================================================
# 1. MODELO BASE (HERENCIA MULTI-TABLA: User actúa como Persona)
# ====================================================================

class Persona(AbstractUser):
    """
    Representa la tabla 'Personas' (Superclase). Contiene atributos comunes
    y es la base para la autenticación (Empleado) y el registro de Pacientes.
    """
    TIPO_DOCS = [
        ('CC', 'Cédula de Ciudadanía'),
        ('TI', 'Tarjeta de Identidad'),
        ('PA', 'Pasaporte'),
        ('RC', 'Registro Civil'),
        ('CE', 'Cédula de Extranjería'),
    ]

    # Campos de Autenticación de AbstractUser (ya incluidos: first_name, last_name, password, is_active, etc.)
    email = models.EmailField(_("email address"), max_length=255, unique=True)
    # Hacemos que username sea opcional a nivel de BD, ya que usamos el email para autenticar
    username = models.CharField(max_length=150, unique=False, null=True, blank=True) 
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'num_doc', 'tipo_doc']

    # Campos heredados de la tabla Personas del modelo relacional
    tipo_doc = models.CharField(max_length=2, choices=TIPO_DOCS, default='CC')
    num_doc = models.CharField(max_length=20, unique=True) # DNI/Cédula
    fecha_nac = models.DateField(null=True, blank=True)
    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Femenino'), ('O', 'Otro')], null=True, blank=True)
    direccion = models.CharField(max_length=200, default='No aplica', null=True, blank=True)
    celular = models.CharField(max_length=20, default='No aplica', null=True, blank=True)
    ciudad_residencia = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        verbose_name = _('Persona')
        verbose_name_plural = _('Personas')

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.num_doc})'

class Empleados(models.Model):
    """
    Tabla Empleados (Subclase). Hereda atributos de Persona (a través de la llave PK/FK).
    """
    # *** CORRECCIÓN CRÍTICA: Uso de 'cashier.Persona' para resolver el ValueError ***
    persona = models.OneToOneField(
        'cashier.Persona', 
        on_delete=models.CASCADE, 
        primary_key=True
    )
    
    # Campos específicos de Empleado (del modelo relacional)
    activo = models.BooleanField(default=True)
    
    # Llaves foráneas a tablas lookup y organizacionales
    id_dept = models.ForeignKey('Departamentos', on_delete=models.PROTECT, null=True, blank=True)
    id_rol = models.ForeignKey('Roles', on_delete=models.PROTECT)
    id_especialidad = models.ForeignKey('Especialidades', on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f'{self.id_rol.nombre_rol} - {self.persona.first_name} {self.persona.last_name}' 

class Pacientes(models.Model):
    """ 
    Tabla Pacientes (Subclase). Hereda atributos de Persona (a través de la llave PK/FK).
    """
    # *** CORRECCIÓN CRÍTICA: Uso de 'cashier.Persona' para resolver el ValueError ***
    persona = models.OneToOneField(
        'cashier.Persona', 
        on_delete=models.CASCADE, 
        primary_key=True
    )
    # cod_pac puede ser generado en el save() o ser la PK heredada, pero lo mantenemos como campo
    cod_pac = models.CharField(max_length=20, unique=True, editable=False, default='PAC_TEMP') 

    class Meta:
        verbose_name_plural = "Pacientes"

    def __str__(self):
        return f'Paciente: {self.persona.first_name} {self.persona.last_name}'
    
    # Aunque la lógica de save es opcional, la dejamos para ilustrar el cod_pac
    def save(self, *args, **kwargs):
        if self._state.adding and self.cod_pac == 'PAC_TEMP':
             # Esto es una simplificación. En producción se usaría una secuencia o lógica de negocio.
             self.cod_pac = f'PAC-{self.persona_id}' 
        super().save(*args, **kwargs)


# ====================================================================
# 2. MODELOS ORGANIZACIONALES Y DE LOOKUP (Resto del modelo, sin cambios)
# ====================================================================

class Roles(models.Model):
    """ Mapea la tabla Roles """
    id_rol = models.AutoField(primary_key=True)
    nombre_rol = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.nombre_rol

class Especialidades(models.Model):
    """ Mapea la tabla Especialidades """
    id_especialidad = models.AutoField(primary_key=True)
    nombre_esp = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_esp

class Sedes_Hospitalarias(models.Model):
    """ Mapea la tabla Sedes_Hospitalarias """
    id_sede = models.AutoField(primary_key=True)
    nom_sede = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=50)
    direccion = models.CharField(max_length=150)
    telefono = models.CharField(max_length=20)
    es_nodo_central = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.nom_sede} ({self.ciudad})'

class Departamentos(models.Model):
    """ Mapea la tabla Departamentos """
    id_dept = models.AutoField(primary_key=True)
    nom_dept = models.CharField(max_length=100)
    id_sede = models.ForeignKey(Sedes_Hospitalarias, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.nom_dept} en {self.id_sede.nom_sede}'

# ====================================================================
# 3. MÓDULO PACIENTES Y CLÍNICO 
# ====================================================================

class Citas(models.Model):
    """ Mapea la tabla Citas """
    ESTADOS = [
        ('PROGRAMADA', 'Programada'),
        ('REALIZADA', 'Realizada'),
        ('CANCELADA', 'Cancelada'),
        ('PENDIENTE', 'Pendiente')
    ]
    
    id_cita = models.BigAutoField(primary_key=True)
    cod_pac = models.ForeignKey(Pacientes, on_delete=models.PROTECT) 
    # Filtro para que solo se pueda asignar un Empleado con rol 'Médico'
    id_emp = models.ForeignKey(Empleados, on_delete=models.PROTECT, limit_choices_to={'id_rol__nombre_rol': 'Médico'}) 
    id_dept = models.ForeignKey(Departamentos, on_delete=models.PROTECT)
    fecha_hora = models.DateTimeField()
    tipo_servicio = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PROGRAMADA')

    class Meta:
        verbose_name_plural = "Citas"
        # Restricción para evitar que un médico tenga dos citas a la misma hora
        unique_together = ('id_emp', 'fecha_hora') 
    
    def __str__(self):
        return f'Cita {self.id_cita} ({self.estado}) - {self.cod_pac}'

class Historias_Clinicas(models.Model):
    """ Mapea la tabla Historias_Clinicas """
    cod_hist = models.BigAutoField(primary_key=True)
    id_cita = models.OneToOneField(Citas, on_delete=models.PROTECT, unique=True) # Relación 1:1 con Citas
    fecha_registro = models.DateTimeField(auto_now_add=True)
    motivo_consulta = models.TextField()
    diagnostico = models.TextField()
    observaciones = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Historias Clínicas"

    def __str__(self):
        return f'Historia {self.cod_hist} | Cita: {self.id_cita.id_cita}'

# ====================================================================
# 4. MÓDULO FARMACIA Y PRESCRIPCIONES
# ====================================================================

class Catalogo_Medicamentos(models.Model):
    """ Mapea la tabla Catalogo_Medicamentos (Información replicada globalmente) """
    cod_med = models.AutoField(primary_key=True)
    nom_med = models.CharField(max_length=150, unique=True)
    principio_activo = models.CharField(max_length=150, null=True, blank=True)
    descripcion = models.TextField(null=True, blank=True)
    unidad_medida = models.CharField(max_length=20)
    proveedor_principal = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Catálogo de Medicamentos"

    def __str__(self):
        return self.nom_med

class Inventario_Farmacia(models.Model):
    """ Mapea la tabla Inventario_Farmacia (Stock local por sede) """
    id_inv = models.BigAutoField(primary_key=True)
    id_sede = models.ForeignKey(Sedes_Hospitalarias, on_delete=models.PROTECT)
    cod_med = models.ForeignKey(Catalogo_Medicamentos, on_delete=models.PROTECT)
    stock_actual = models.IntegerField(default=0)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Inventario de Farmacia"
        unique_together = ('id_sede', 'cod_med') # Un medicamento solo tiene un stock por sede
    
    def __str__(self):
        return f'{self.cod_med.nom_med} - Stock en {self.id_sede.nom_sede}: {self.stock_actual}'


class Prescripciones(models.Model):
    """ Mapea la tabla Prescripciones """
    id_presc = models.BigAutoField(primary_key=True)
    cod_hist = models.ForeignKey(Historias_Clinicas, on_delete=models.CASCADE)
    cod_med = models.ForeignKey(Catalogo_Medicamentos, on_delete=models.PROTECT)
    dosis = models.CharField(max_length=50)
    frecuencia = models.CharField(max_length=100)
    duracion_dias = models.IntegerField()
    cantidad_total = models.IntegerField(null=True, blank=True)
    fecha_emision = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Prescripciones"

    def __str__(self):
        return f'Rx: {self.cod_med.nom_med} ({self.cod_hist.id_cita})'

# ====================================================================
# 5. MÓDULO INFRAESTRUCTURA Y LOGS
# ====================================================================

class Equipamiento(models.Model):
    """ Mapea la tabla Equipamiento """
    ESTADOS = [
        ('OPERATIVO', 'Operativo'),
        ('MANTENIMIENTO', 'En Mantenimiento'),
        ('BAJA', 'Dado de Baja')
    ]

    cod_eq = models.AutoField(primary_key=True)
    nom_eq = models.CharField(max_length=100)
    marca_modelo = models.CharField(max_length=100, null=True, blank=True)
    id_dept = models.ForeignKey(Departamentos, on_delete=models.PROTECT)
    estado_equipo = models.CharField(max_length=20, choices=ESTADOS)
    fecha_ultimo_maint = models.DateField(null=True, blank=True)
    responsable_id = models.ForeignKey(
        Empleados, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='equipos_a_cargo'
    )
    
    def __str__(self):
        return f'{self.nom_eq} ({self.estado_equipo}) - Depto: {self.id_dept.nom_dept}'

class Auditoria_Accesos(models.Model):
    """ Mapea la tabla Auditoria_Accesos """
    id_evento = models.BigAutoField(primary_key=True)
    id_emp = models.ForeignKey(Empleados, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=50)
    tabla_afectada = models.CharField(max_length=50, null=True, blank=True)
    id_registro_afectado = models.CharField(max_length=50, null=True, blank=True)
    fecha_evento = models.DateTimeField(auto_now_add=True)
    ip_origen = models.CharField(max_length=45, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Auditoría de Accesos"
        ordering = ['-fecha_evento'] # Los logs más nuevos primero

    def __str__(self):
        return f'[{self.fecha_evento}] {self.accion} por {self.id_emp}'
    

class Reportes_Generados(models.Model):
    """ Mapea la tabla Reportes_Generados """
    id_reporte = models.AutoField(primary_key=True)
    id_sede = models.ForeignKey(Sedes_Hospitalarias, on_delete=models.PROTECT)
    id_emp_generador = models.ForeignKey(Empleados, on_delete=models.PROTECT)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    tipo_reporte = models.CharField(max_length=50)
    parametros_json = models.TextField(null=True, blank=True) # Para guardar los filtros usados

    class Meta:
        verbose_name_plural = "Reportes Generados"

    def __str__(self):
        return f'Reporte {self.tipo_reporte} ({self.id_sede.nom_sede})'