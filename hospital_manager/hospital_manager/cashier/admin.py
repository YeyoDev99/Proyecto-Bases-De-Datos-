from django.contrib import admin

# Importa TODAS las clases de modelos definidas en models.py
from .models import (
    Persona, Empleados, Pacientes, Citas, Historias_Clinicas,
    Departamentos, Roles, Especialidades, Sedes_Hospitalarias,
    Catalogo_Medicamentos, Prescripciones, Equipamiento,
    Auditoria_Accesos, Inventario_Farmacia, Reportes_Generados
)

# ----------------------------------------------------
# PERSONALIZACIÓN DE VISTAS EN EL ADMIN (OPCIONAL)
# ----------------------------------------------------

class PersonaAdmin(admin.ModelAdmin):
    """
    Personalización de la vista del modelo Persona (Base de la autenticación).
    """
    list_display = ('id', 'first_name', 'last_name', 'num_doc', 'email')
    search_fields = ('first_name', 'last_name', 'num_doc', 'email')
    # Campos que se pueden editar directamente en la vista de lista
    list_editable = ('first_name', 'last_name', 'email')

class EmpleadoAdmin(admin.ModelAdmin):
    """
    Personalización de la vista de Empleados.
    """
    # Muestra campos de la tabla Empleados y del modelo relacionado (Persona)
    list_display = ('persona_id', 'get_full_name', 'id_rol', 'id_dept', 'activo', 'id_especialidad')
    list_filter = ('activo', 'id_rol', 'id_dept', 'id_especialidad')
    search_fields = ('persona__first_name', 'persona__last_name', 'persona__num_doc')
    raw_id_fields = ('persona',) # Útil para buscar Personas por ID en lugar de dropdown

    @admin.display(description='Nombre Completo')
    def get_full_name(self, obj):
        return f"{obj.persona.first_name} {obj.persona.last_name}"
    
class PacienteAdmin(admin.ModelAdmin):
    """
    Personalización de la vista de Pacientes.
    """
    list_display = ('persona_id', 'get_full_name', 'cod_pac')
    search_fields = ('persona__first_name', 'persona__last_name', 'cod_pac')
    raw_id_fields = ('persona',)

    @admin.display(description='Nombre Completo')
    def get_full_name(self, obj):
        return f"{obj.persona.first_name} {obj.persona.last_name}"

class CitaAdmin(admin.ModelAdmin):
    """
    Personalización de la vista de Citas.
    """
    list_display = ('id_cita', 'get_paciente_doc', 'get_medico_name', 'fecha_hora', 'estado', 'id_dept')
    list_filter = ('estado', 'tipo_servicio', 'id_dept')
    search_fields = ('cod_pac__persona__num_doc', 'id_emp__persona__last_name')
    date_hierarchy = 'fecha_hora' # Permite navegar por fechas

    @admin.display(description='Documento Paciente')
    def get_paciente_doc(self, obj):
        # Accede a Persona a través de Pacientes
        return obj.cod_pac.persona.num_doc
    
    @admin.display(description='Médico')
    def get_medico_name(self, obj):
        # Accede a Persona a través de Empleados
        return f"{obj.id_emp.persona.first_name} {obj.id_emp.persona.last_name}"


# ----------------------------------------------------
# REGISTRO DE MODELOS
# ----------------------------------------------------

# Modelos Base y de Herencia
admin.site.register(Persona, PersonaAdmin)
admin.site.register(Empleados, EmpleadoAdmin)
admin.site.register(Pacientes, PacienteAdmin)

# Modelos Clínicos y Transaccionales
admin.site.register(Citas, CitaAdmin)
admin.site.register(Historias_Clinicas)
admin.site.register(Prescripciones)

# Modelos Organizacionales y de Lookup
admin.site.register(Departamentos)
admin.site.register(Roles)
admin.site.register(Especialidades)
admin.site.register(Sedes_Hospitalarias)

# Modelos de Farmacia y Recursos
admin.site.register(Catalogo_Medicamentos)
admin.site.register(Inventario_Farmacia)
admin.site.register(Equipamiento)

# Modelos de Auditoría y Reportes
admin.site.register(Auditoria_Accesos)
admin.site.register(Reportes_Generados)