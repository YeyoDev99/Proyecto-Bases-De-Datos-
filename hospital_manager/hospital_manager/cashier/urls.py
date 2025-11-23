from django.urls import path, include
from . import views

app_name = 'cashier'

urlpatterns = [
    # Rutas de Autenticación y Home
    path("", views.index, name='index'), # Login (adaptado de 'index')
    path("sign_up/", views.sign_up, name='sign_up'), # Registro de Empleados (solo por Admin)
    path('menu/', views.menu, name='menu'), # Menú principal del HIS+
    path('logout/', views.logout_user, name='logout'),

    # NOTA: Se elimina 'card_activation' y 'card_validation' ya que no aplican en HIS+.
    # Si 'card_validation' se usa como un validador de acceso, se renombrará a algo más relevante.
    # Por ahora, se elimina para simplificar el flujo.

    # ==========================================================
    # RUTAS DE GESTIÓN HOSPITALARIA (HIS+)
    # ==========================================================

    # 1. Módulo Pacientes / Historias Clínicas (Adaptado de 'check_balance')
    path('gestion_pacientes/', views.gestion_pacientes, name='gestion_pacientes'),
    path('ver_historia/<int:paciente_pk>/', views.ver_historia, name='ver_historia'),
    
    # 2. Módulo Citas (Adaptado de 'purchase_tickets')
    path('programar_citas/', views.programar_citas, name='programar_citas'),
    path('citas_pendientes/', views.citas_pendientes, name='citas_pendientes'),
    
    # 3. Módulo Clínico / Diagnóstico (Adaptado de 'deposit')
    path('registrar_diagnostico/<int:cita_pk>/', views.registrar_diagnostico, name='registrar_diagnostico'),
    path('prescribir_medicamento/<int:historia_pk>/', views.prescribir_medicamento, name='prescribir_medicamento'),
    
    # 4. Módulo Farmacia / Inventario (Adaptado de 'withdraw_money')
    path('gestion_farmacia/', views.gestion_farmacia, name='gestion_farmacia'),
    path('actualizar_stock/<int:inv_pk>/', views.actualizar_stock, name='actualizar_stock'),

    # 5. Módulo Reportes y Analítica (Requisito del PDF)
    path('reportes_analitica/', views.reportes_analitica, name='reportes_analitica'),
    path('analitica_medicamentos/', views.analitica_medicamentos, name='analitica_medicamentos'),
    
    # 6. Módulo Auditoría y Recursos (Requisito del PDF)
    path('auditoria_logs/', views.auditoria_logs, name='auditoria_logs'),
    path('gestion_equipamiento/', views.gestion_equipamiento, name='gestion_equipamiento'),

]