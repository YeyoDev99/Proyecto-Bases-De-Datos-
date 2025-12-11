"""
URLs del Sistema Hospitalario HIS+
Sistema Integral de Gestión Hospitalaria con Base de Datos Distribuida
"""

from django.urls import path
from . import views
from . import api_views

# Namespace de la aplicación
app_name = 'hospital'

urlpatterns = [
    # ============================================================================
    # 1. AUTENTICACIÓN Y HOME
    # ============================================================================
    path('', views.index, name='index'),                          # Login
    path('login/', views.login_view, name='login'),               # Login alternativo
    path('logout/', views.logout_user, name='logout'),            # Cerrar sesión
    path('dashboard/', views.dashboard, name='dashboard'),        # Dashboard principal
    
    # ============================================================================
    # 2. GESTIÓN DE USUARIOS Y PERFILES
    # ============================================================================
    path('perfil/', views.perfil_usuario, name='perfil'),                     # Ver/Editar perfil
    path('perfil/cambiar-password/', views.cambiar_password, name='cambiar_password'),
    
    # ============================================================================
    # 3. MÓDULO DE PACIENTES
    # ============================================================================
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),       # Lista de pacientes
    path('pacientes/nuevo/', views.nuevo_paciente, name='nuevo_paciente'),   # Registrar paciente
    path('pacientes/<int:pac_id>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:pac_id>/editar/', views.editar_paciente, name='editar_paciente'),
    
    # ============================================================================
    # 4. MÓDULO DE CITAS
    # ============================================================================
    path('citas/', views.lista_citas, name='lista_citas'),                   # Todas las citas
    path('citas/nueva/', views.nueva_cita, name='nueva_cita'),               # Programar cita
    path('citas/<int:cita_id>/', views.detalle_cita, name='detalle_cita'),   # Ver cita
    path('citas/<int:cita_id>/editar/', views.editar_cita, name='editar_cita'),
    path('citas/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('citas/pendientes/', views.citas_pendientes, name='citas_pendientes'),      # Citas del día
    path('citas/programadas/', views.citas_programadas, name='citas_programadas'),   # Futuras
    path('citas/historial/', views.historial_citas, name='historial_citas'),         # Pasadas
    
    # ============================================================================
    # 5. MÓDULO CLÍNICO - HISTORIAS CLÍNICAS Y DIAGNÓSTICOS
    # ============================================================================
    path('historias/', views.lista_historias, name='lista_historias'),
    path('historias/<int:hist_id>/', views.detalle_historia, name='detalle_historia'),
    path('historias/paciente/<int:pac_id>/', views.historias_paciente, name='historias_paciente'),
    
    # Diagnósticos
    path('citas/<int:cita_id>/diagnostico/', views.registrar_diagnostico, name='registrar_diagnostico'),
    path('diagnostico/<int:diag_id>/', views.detalle_diagnostico, name='detalle_diagnostico'),
    path('diagnostico/<int:diag_id>/editar/', views.editar_diagnostico, name='editar_diagnostico'),
    
    # ============================================================================
    # 6. MÓDULO DE PRESCRIPCIONES
    # ============================================================================
    path('prescripciones/', views.lista_prescripciones, name='lista_prescripciones'),
    path('prescripciones/nueva/', views.nueva_prescripcion, name='nueva_prescripcion'),
    path('historia/<int:hist_id>/prescribir/', views.prescribir_medicamento, name='prescribir_medicamento'),
    path('prescripciones/<int:presc_id>/', views.detalle_prescripcion, name='detalle_prescripcion'),
    
    # ============================================================================
    # 7. MÓDULO DE FARMACIA E INVENTARIO
    # ============================================================================
    path('farmacia/', views.gestion_farmacia, name='gestion_farmacia'),
    path('farmacia/inventario/', views.inventario_farmacia, name='inventario_farmacia'),
    path('farmacia/inventario/<int:inv_id>/actualizar/', views.actualizar_stock, name='actualizar_stock'),
    path('farmacia/medicamentos/', views.catalogo_medicamentos, name='catalogo_medicamentos'),
    path('farmacia/medicamentos/nuevo/', views.nuevo_medicamento, name='nuevo_medicamento'),
    path('farmacia/medicamentos/<int:med_id>/', views.detalle_medicamento, name='detalle_medicamento'),
    path('farmacia/alertas/', views.alertas_inventario, name='alertas_inventario'),
    
    # ============================================================================
    # 8. MÓDULO DE EQUIPAMIENTO
    # ============================================================================
    path('equipamiento/', views.lista_equipamiento, name='lista_equipamiento'),
    path('equipamiento/nuevo/', views.nuevo_equipamiento, name='nuevo_equipamiento'),
    path('equipamiento/<int:eq_id>/', views.detalle_equipamiento, name='detalle_equipamiento'),
    path('equipamiento/<int:eq_id>/editar/', views.editar_equipamiento, name='editar_equipamiento'),
    path('equipamiento/<int:eq_id>/mantenimiento/', views.registrar_mantenimiento, name='registrar_mantenimiento'),
    
    # ============================================================================
    # 9. MÓDULO DE REPORTES Y ANALÍTICA
    # ============================================================================
    path('reportes/', views.menu_reportes, name='menu_reportes'),
    
    # Reportes requeridos del proyecto
    path('reportes/medicamentos-recetados/', views.reporte_medicamentos_recetados, name='reporte_medicamentos_recetados'),
    path('reportes/medicos-consultas/', views.reporte_medicos_consultas, name='reporte_medicos_consultas'),
    path('reportes/tiempos-atencion/', views.reporte_tiempos_atencion, name='reporte_tiempos_atencion'),
    path('reportes/pacientes-enfermedad/', views.reporte_pacientes_enfermedad, name='reporte_pacientes_enfermedad'),
    path('reportes/equipamiento-compartido/', views.reporte_equipamiento_compartido, name='reporte_equipamiento_compartido'),
    
    # Reportes adicionales
    path('reportes/enfermedades-trimestre/', views.reporte_enfermedades_trimestre, name='reporte_enfermedades_trimestre'),
    path('reportes/consumo-medicamentos/', views.reporte_consumo_medicamentos, name='reporte_consumo_medicamentos'),
    path('reportes/utilizacion-recursos/', views.reporte_utilizacion_recursos, name='reporte_utilizacion_recursos'),
    path('reportes/indices-atencion/', views.reporte_indices_atencion, name='reporte_indices_atencion'),
    path('reportes/especialidades-demandadas/', views.reporte_especialidades_demandadas, name='reporte_especialidades_demandadas'),
    path('reportes/inventario-critico/', views.reporte_inventario_critico, name='reporte_inventario_critico'),
    path('reportes/productividad-medicos/', views.reporte_productividad_medicos, name='reporte_productividad_medicos'),
    path('reportes/tendencias-enfermedades/', views.reporte_tendencias_enfermedades, name='reporte_tendencias_enfermedades'),
    
    # Generación de reportes PDF/Excel
    path('reportes/generar/<str:tipo>/', views.generar_reporte, name='generar_reporte'),
    path('reportes/exportar/<str:tipo>/<str:formato>/', views.exportar_reporte, name='exportar_reporte'),
    
    # ============================================================================
    # 10. MÓDULO DE AUDITORÍA Y SEGURIDAD
    # ============================================================================
    path('auditoria/', views.auditoria_principal, name='auditoria_principal'),
    path('auditoria/accesos/', views.auditoria_accesos, name='auditoria_accesos'),
    path('auditoria/historias-clinicas/', views.auditoria_historias, name='auditoria_historias'),
    path('auditoria/filtrar/', views.filtrar_auditoria, name='filtrar_auditoria'),
    
    # ============================================================================
    # 11. MÓDULO DE VISTAS DISTRIBUIDAS (CONSULTAS CONSOLIDADAS)
    # ============================================================================
    path('vistas/historias-consolidadas/', views.vista_historias_consolidadas, name='vista_historias_consolidadas'),
    path('vistas/medicamentos-sede/', views.vista_medicamentos_sede, name='vista_medicamentos_sede'),
    path('vistas/medicos-consultas/', views.vista_medicos_consultas, name='vista_medicos_consultas'),
    path('vistas/enfermedades-sede/', views.vista_enfermedades_sede, name='vista_enfermedades_sede'),
    path('vistas/inventario-consolidado/', views.vista_inventario_consolidado, name='vista_inventario_consolidado'),
    
    # ============================================================================
    # 12. MÓDULO DE ADMINISTRACIÓN (Solo para Administradores)
    # ============================================================================
    path('admin-hospital/', views.admin_principal, name='admin_principal'),
    path('admin-hospital/empleados/', views.admin_empleados, name='admin_empleados'),
    path('admin-hospital/empleados/nuevo/', views.admin_nuevo_empleado, name='admin_nuevo_empleado'),
    path('admin-hospital/empleados/<int:emp_id>/', views.admin_detalle_empleado, name='admin_detalle_empleado'),
    path('admin-hospital/empleados/<int:emp_id>/editar/', views.admin_editar_empleado, name='admin_editar_empleado'),
    path('admin-hospital/empleados/<int:emp_id>/desactivar/', views.admin_desactivar_empleado, name='admin_desactivar_empleado'),
    
    path('admin-hospital/sedes/', views.admin_sedes, name='admin_sedes'),
    path('admin-hospital/departamentos/', views.admin_departamentos, name='admin_departamentos'),
    path('admin-hospital/roles/', views.admin_roles, name='admin_roles'),
    path('admin-hospital/especialidades/', views.admin_especialidades, name='admin_especialidades'),
    
    # ============================================================================
    # 13. API ENDPOINTS (Para AJAX y consultas dinámicas)
    # ============================================================================
    path('api/pacientes/buscar/', views.api_buscar_pacientes, name='api_buscar_pacientes'),
    path('api/medicos/disponibles/', views.api_medicos_disponibles, name='api_medicos_disponibles'),
    path('api/citas/disponibilidad/', views.api_disponibilidad_citas, name='api_disponibilidad_citas'),
    path('api/medicamentos/buscar/', views.api_buscar_medicamentos, name='api_buscar_medicamentos'),
    path('api/stock/verificar/<int:med_id>/', views.api_verificar_stock, name='api_verificar_stock'),
    path('api/enfermedades/buscar/', views.api_buscar_enfermedades, name='api_buscar_enfermedades'),
    path('api/departamentos/obtener/', views.api_obtener_departamentos, name='api_obtener_departamentos'),
    path('api/medicos/por-departamento/', views.api_obtener_medicos_por_dept, name='api_obtener_medicos_por_dept'),
    
    # ============================================================================
    # 15. NEW JSON API ENDPOINTS (Para Frontend Estático)
    # ============================================================================
    # Auth
    path('api/v2/login/', api_views.api_login, name='api_login'),
    path('api/v2/logout/', api_views.api_logout, name='api_logout'),
    path('api/v2/session/', api_views.api_session, name='api_session'),
    path('api/v2/perfil/', api_views.api_perfil, name='api_perfil'),
    path('api/v2/dashboard/stats/', api_views.api_dashboard_stats, name='api_dashboard_stats'),
    
    # Lookup data
    path('api/v2/sedes/', api_views.api_sedes, name='api_sedes'),
    path('api/v2/departamentos/', api_views.api_departamentos, name='api_departamentos'),
    path('api/v2/medicos/', api_views.api_medicos, name='api_medicos'),
    
    # Pacientes
    path('api/v2/pacientes/', api_views.api_pacientes_lista, name='api_pacientes'),
    path('api/v2/pacientes/crear/', api_views.api_paciente_crear, name='api_paciente_crear'),
    path('api/v2/pacientes/<int:cod_pac>/', api_views.api_paciente_detalle, name='api_paciente_detalle'),
    
    # Citas
    path('api/v2/citas/', api_views.api_citas_lista, name='api_citas'),
    path('api/v2/citas/crear/', api_views.api_cita_crear, name='api_cita_crear'),
    path('api/v2/citas/<int:id_cita>/', api_views.api_cita_detalle, name='api_cita_detalle'),
    path('api/v2/citas/<int:id_cita>/actualizar/', api_views.api_cita_actualizar, name='api_cita_actualizar'),
    path('api/v2/citas/<int:id_cita>/cancelar/', api_views.api_cita_cancelar, name='api_cita_cancelar'),
    
    # Historias Clínicas
    path('api/v2/historias/', api_views.api_historias_lista, name='api_historias'),
    path('api/v2/historias/<int:cod_hist>/', api_views.api_historia_detalle, name='api_historia_detalle'),
    
    # Inventario/Farmacia
    path('api/v2/inventario/', api_views.api_inventario_lista, name='api_inventario'),
    path('api/v2/inventario/<int:id_inv>/', api_views.api_inventario_actualizar, name='api_inventario_actualizar'),
    path('api/v2/medicamentos/', api_views.api_medicamentos_catalogo, name='api_medicamentos'),
    
    # Prescripciones
    path('api/v2/prescripciones/', api_views.api_prescripciones_lista, name='api_prescripciones'),
    path('api/v2/prescripciones/crear/', api_views.api_prescripcion_crear, name='api_prescripcion_crear'),
    
    # Equipamiento
    path('api/v2/equipamiento/', api_views.api_equipamiento_lista, name='api_equipamiento'),
    path('api/v2/equipamiento/crear/', api_views.api_equipo_crear, name='api_equipo_crear'),
    path('api/v2/equipamiento/<int:id_equipo>/', api_views.api_equipo_detalle, name='api_equipo_detalle'),
    
    # Reportes (old endpoint - keep for compatibility)

    
    # Reportes (new detailed endpoints)
    path('api/v2/reportes/medicamentos-recetados/', api_views.api_reportes_medicamentos_recetados, name='api_reportes_medicamentos_recetados'),
    path('api/v2/reportes/medicos-consultas/', api_views.api_reportes_medicos_consultas, name='api_reportes_medicos_consultas'),
    path('api/v2/reportes/enfermedades/', api_views.api_reportes_enfermedades, name='api_reportes_enfermedades'),
    
    # Auditoría
    path('api/v2/auditoria/accesos/', api_views.api_auditoria_accesos, name='api_auditoria_accesos'),
    
    # ============================================================================
    # 14. PÁGINAS DE ERROR Y AYUDA
    # ============================================================================
    path('sin-permisos/', views.sin_permisos, name='sin_permisos'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('sobre-sistema/', views.sobre_sistema, name='sobre_sistema'),
]