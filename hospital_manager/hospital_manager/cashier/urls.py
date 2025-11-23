from django.urls import path, include
from . import views

# Define el nombre de la aplicación para el namespace de Django
app_name = 'cashier'

urlpatterns = [
    # ----------------------------------------------------------
    # 1. RUTAS DE AUTENTICACIÓN Y HOME
    # ----------------------------------------------------------
    path("", views.index, name='index'),                     # Login
    path("sign_up/", views.sign_up, name='sign_up'),         # Registro de Empleados
    path('menu/', views.menu, name='menu'),                 # Menú principal (Dashboard)
    path('logout/', views.logout_user, name='logout'),      # Cierre de sesión

    # ----------------------------------------------------------
    # 2. RUTAS DE PERFIL Y CONFIGURACIÓN
    # ----------------------------------------------------------
    # Esta ruta es nueva y necesaria para editar el perfil del empleado logueado
    path('perfil/', views.perfil_empleado, name='perfil_empleado'),

    # ----------------------------------------------------------
    # 3. MÓDULO PACIENTES / HISTORIAS CLÍNICAS
    # ----------------------------------------------------------
    path('gestion_pacientes/', views.gestion_pacientes, name='gestion_pacientes'),
    # Usamos <int:pk> para referenciar el ID del Paciente para la vista de su historial
    path('ver_historia/<int:paciente_pk>/', views.ver_historia, name='ver_historia'),
    
    # ----------------------------------------------------------
    # 4. MÓDULO CITAS
    # ----------------------------------------------------------
    path('programar_citas/', views.programar_citas, name='programar_citas'),
    path('citas_pendientes/', views.citas_pendientes, name='citas_pendientes'),
    
    # ----------------------------------------------------------
    # 5. MÓDULO CLÍNICO / DIAGNÓSTICO
    # ----------------------------------------------------------
    # ID de la Cita para registrar el Diagnóstico
    path('registrar_diagnostico/<int:cita_pk>/', views.registrar_diagnostico, name='registrar_diagnostico'),
    # ID de la Historia Clínica para añadir Prescripciones
    path('prescribir_medicamento/<int:historia_pk>/', views.prescribir_medicamento, name='prescribir_medicamento'),
    
    # ----------------------------------------------------------
    # 6. MÓDULO FARMACIA / INVENTARIO
    # ----------------------------------------------------------
    path('gestion_farmacia/', views.gestion_farmacia, name='gestion_farmacia'),
    # ID del Medicamento (Inventario) para actualizar su stock
    path('actualizar_stock/<int:inv_pk>/', views.actualizar_stock, name='actualizar_stock'),

    # ----------------------------------------------------------
    # 7. MÓDULO REPORTES Y ANALÍTICA
    # ----------------------------------------------------------
    path('reportes_analitica/', views.reportes_analitica, name='reportes_analitica'),
    path('analitica_medicamentos/', views.analitica_medicamentos, name='analitica_medicamentos'),
    
    # ----------------------------------------------------------
    # 8. MÓDULO AUDITORÍA Y RECURSOS
    # ----------------------------------------------------------
    path('auditoria_logs/', views.auditoria_logs, name='auditoria_logs'),
    # Usa un PK opcional para permitir la edición o el registro nuevo del equipamiento
    path('gestion_equipamiento/', views.gestion_equipamiento, name='gestion_equipamiento'),
    path('gestion_equipamiento/<int:eq_pk>/', views.gestion_equipamiento, name='gestion_equipamiento_editar'),

]