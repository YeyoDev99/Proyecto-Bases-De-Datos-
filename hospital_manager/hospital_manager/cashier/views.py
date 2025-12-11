"""
Vistas del Sistema Hospitalario HIS+
Sistema SIN ORM - Consultas SQL directas
"""

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db import connection
from django.views.decorators.http import require_http_methods
from datetime import datetime, date
from functools import wraps
import json

from .forms import (
    LoginForm, CambiarPasswordForm, PersonaForm, PacienteForm,
    CitaForm, DiagnosticoForm, PrescripcionForm, ActualizarStockForm,
    EquipamientoForm, FiltroReportesForm, ejecutar_query, ejecutar_query_one
)

# ============================================================================
# FUNCIONES HELPER
# ============================================================================

def ejecutar_insert(query, params=None):
    """Ejecuta un INSERT y retorna el ID insertado"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.lastrowid

def ejecutar_update(query, params=None):
    """Ejecuta un UPDATE/DELETE y retorna filas afectadas"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.rowcount

def get_user_from_session(request):
    """Obtiene datos del usuario desde la sesión"""
    return {
        'id_emp': request.session.get('id_emp'),
        'email': request.session.get('email'),
        'nombre': request.session.get('nombre'),
        'rol': request.session.get('rol'),
        'id_sede': request.session.get('id_sede'),
        'id_dept': request.session.get('id_dept'),
    }

def login_required_custom(view_func):
    """Decorador para requerir login"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('id_emp'):
            return redirect('hospital:login')
        return view_func(request, *args, **kwargs)
    return wrapper

def role_required(*roles):
    """Decorador para requerir roles específicos"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_rol = request.session.get('rol')
            if user_rol not in roles:
                return redirect('hospital:sin_permisos')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def registrar_auditoria(id_emp, accion, tabla, id_registro, ip):
    """Registra evento de auditoría"""
    query = """
        INSERT INTO Auditoria_Accesos 
        (id_emp, accion, tabla_afectada, id_registro_afectado, ip_origen)
        VALUES (%s, %s, %s, %s, %s)
    """
    ejecutar_update(query, [id_emp, accion, tabla, str(id_registro), ip])

def get_client_ip(request):
    """Obtiene IP del cliente"""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')

# ============================================================================
# 1. AUTENTICACIÓN Y HOME
# ============================================================================

def index(request):
    """Página principal - Login"""
    if request.session.get('id_emp'):
        return redirect('hospital:dashboard')
    return render(request, 'cashier/index.html')

def login_view(request):
    """Procesar login"""
    error = None
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        
        if not email or not password:
            error = 'Por favor ingrese email y contraseña.'
        else:
            try:
                # Verificar credenciales con crypt de pgcrypto
                query = """
                    SELECT e.id_emp, p.nom_persona, p.apellido_persona, 
                           r.nombre_rol, e.id_sede, e.id_dept, e.activo
                    FROM Empleados e
                    INNER JOIN Personas p ON e.id_persona = p.id_persona
                    INNER JOIN Roles r ON e.id_rol = r.id_rol
                    WHERE p.email_persona = %s 
                    AND e.hash_contra = crypt(%s, e.hash_contra)
                """
                user = ejecutar_query_one(query, [email, password])
                
                if user:
                    if not user[6]:  # activo = False
                        error = 'Su cuenta está desactivada. Contacte al administrador.'
                    else:
                        # Login exitoso
                        request.session['id_emp'] = user[0]
                        request.session['email'] = email
                        request.session['nombre'] = f"{user[1]} {user[2]}"
                        request.session['rol'] = user[3]
                        request.session['id_sede'] = user[4]
                        request.session['id_dept'] = user[5]
                        try:
                            registrar_auditoria(user[0], 'LOGIN', 'Empleados', user[0], get_client_ip(request))
                        except:
                            pass  # No bloquear login si falla auditoría
                        messages.success(request, f'Bienvenido, {user[1]}!')
                        return redirect('hospital:dashboard')
                else:
                    error = 'Credenciales inválidas. Verifique su email y contraseña.'
            except Exception as e:
                error = f'Error de conexión a la base de datos: {str(e)}'
    
    return render(request, 'cashier/index.html', {'error': error})

def logout_user(request):
    """Cerrar sesión"""
    id_emp = request.session.get('id_emp')
    if id_emp:
        registrar_auditoria(id_emp, 'LOGOUT', 'Empleados', id_emp, get_client_ip(request))
    request.session.flush()
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('hospital:login')

@login_required_custom
def dashboard(request):
    """Dashboard principal"""
    user = get_user_from_session(request)
    id_sede = user['id_sede']
    
    # Estadísticas del día
    stats = {}
    
    # Citas del día
    query = "SELECT COUNT(*) FROM Citas WHERE id_sede = %s AND DATE(fecha_hora) = CURRENT_DATE"
    result = ejecutar_query_one(query, [id_sede])
    stats['citas_hoy'] = result[0] if result else 0
    
    # Pacientes atendidos
    query = """SELECT COUNT(*) FROM Citas WHERE id_sede = %s 
               AND DATE(fecha_hora) = CURRENT_DATE AND estado = 'COMPLETADA'"""
    result = ejecutar_query_one(query, [id_sede])
    stats['pacientes_atendidos'] = result[0] if result else 0
    
    # Citas pendientes
    query = """SELECT COUNT(*) FROM Citas WHERE id_sede = %s 
               AND estado = 'PROGRAMADA' AND fecha_hora >= NOW()"""
    result = ejecutar_query_one(query, [id_sede])
    stats['citas_pendientes'] = result[0] if result else 0
    
    # Alertas de inventario
    query = "SELECT COUNT(*) FROM Inventario_Farmacia WHERE id_sede = %s AND stock_actual < 50"
    result = ejecutar_query_one(query, [id_sede])
    stats['alertas_stock'] = result[0] if result else 0
    
    return render(request, 'cashier/menu.html', {'user': user, 'stats': stats})

# ============================================================================
# 2. GESTIÓN DE USUARIOS Y PERFILES
# ============================================================================

@login_required_custom
def perfil_usuario(request):
    """Ver/Editar perfil del usuario"""
    user = get_user_from_session(request)
    query = """
        SELECT p.*, e.id_sede, s.nom_sede, d.nom_dept, r.nombre_rol
        FROM Empleados e
        INNER JOIN Personas p ON e.id_persona = p.id_persona
        INNER JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        INNER JOIN Departamentos d ON e.id_dept = d.id_dept AND e.id_sede = d.id_sede
        INNER JOIN Roles r ON e.id_rol = r.id_rol
        WHERE e.id_emp = %s
    """
    perfil = ejecutar_query_one(query, [user['id_emp']])
    return render(request, 'cashier/perfil_empleado.html', {'user': user, 'perfil': perfil})

@login_required_custom
def cambiar_password(request):
    """Cambiar contraseña"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = CambiarPasswordForm(user['email'], request.POST)
        if form.is_valid():
            nueva = form.cleaned_data['password_nueva']
            query = """
                UPDATE Empleados SET hash_contra = crypt(%s, gen_salt('bf'))
                WHERE id_emp = %s
            """
            ejecutar_update(query, [nueva, user['id_emp']])
            messages.success(request, 'Contraseña actualizada correctamente.')
            return redirect('hospital:perfil')
    else:
        form = CambiarPasswordForm(user['email'])
    return render(request, 'cashier/perfil_empleado.html', {'user': user, 'form': form})

# ============================================================================
# 3. MÓDULO DE PACIENTES
# ============================================================================

@login_required_custom
def lista_pacientes(request):
    """Lista de pacientes"""
    user = get_user_from_session(request)
    busqueda = request.GET.get('q', '')
    
    # Administrador solo ve pacientes de su sede (que tienen citas en su sede)
    if user['rol'] == 'Administrador':
        query = """
            SELECT DISTINCT pac.cod_pac, p.nom_persona, p.apellido_persona, p.num_doc, 
                   p.fecha_nac, p.genero, p.tel_persona, p.email_persona
            FROM Pacientes pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
            LEFT JOIN Citas c ON c.cod_pac = pac.cod_pac
            WHERE (c.id_sede = %s OR c.id_cita IS NULL)
        """
        params = [user['id_sede']]
        if busqueda:
            query += " AND (p.num_doc LIKE %s OR p.nom_persona ILIKE %s OR p.apellido_persona ILIKE %s)"
            params.extend([f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%'])
    else:
        query = """
            SELECT pac.cod_pac, p.nom_persona, p.apellido_persona, p.num_doc, 
                   p.fecha_nac, p.genero, p.tel_persona, p.email_persona
            FROM Pacientes pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
        """
        params = []
        if busqueda:
            query += " WHERE p.num_doc LIKE %s OR p.nom_persona ILIKE %s OR p.apellido_persona ILIKE %s"
            params = [f'%{busqueda}%', f'%{busqueda}%', f'%{busqueda}%']
    query += " ORDER BY p.apellido_persona, p.nom_persona LIMIT 100"
    
    pacientes = ejecutar_query(query, params)
    return render(request, 'cashier/gestion_pacientes.html', {
        'user': user, 'pacientes': pacientes, 'busqueda': busqueda
    })

@login_required_custom
@role_required('Administrativo', 'Administrador')
def nuevo_paciente(request):
    """Registrar nuevo paciente"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Obtener siguiente ID
            result = ejecutar_query_one("SELECT COALESCE(MAX(id_persona), 0) + 1 FROM Personas")
            id_persona = result[0]
            
            # Insertar persona
            query = """
                INSERT INTO Personas (id_persona, nom_persona, apellido_persona, tipo_doc, 
                    num_doc, fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            ejecutar_update(query, [
                id_persona, data['nom_persona'], data['apellido_persona'], data['tipo_doc'],
                data['num_doc'], data['fecha_nac'], data['genero'], data['dir_persona'],
                data['tel_persona'], data['email_persona'], data['ciudad_residencia']
            ])
            
            # Insertar paciente
            result = ejecutar_query_one("SELECT COALESCE(MAX(cod_pac), 0) + 1 FROM Pacientes")
            cod_pac = result[0]
            ejecutar_update("INSERT INTO Pacientes (cod_pac, id_persona) VALUES (%s, %s)", 
                          [cod_pac, id_persona])
            
            registrar_auditoria(user['id_emp'], 'INSERT', 'Pacientes', cod_pac, get_client_ip(request))
            messages.success(request, 'Paciente registrado correctamente.')
            return redirect('hospital:lista_pacientes')
    else:
        form = PacienteForm()
    return render(request, 'cashier/gestion_pacientes.html', {'user': user, 'form': form, 'nuevo': True})

@login_required_custom
def detalle_paciente(request, pac_id):
    """Ver detalle de paciente"""
    user = get_user_from_session(request)
    query = """
        SELECT pac.cod_pac, p.*
        FROM Pacientes pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE pac.cod_pac = %s
    """
    paciente = ejecutar_query_one(query, [pac_id])
    
    # Historial de citas
    query_citas = """
        SELECT c.id_cita, c.fecha_hora, c.tipo_servicio, c.estado, c.motivo,
               pe.nom_persona || ' ' || pe.apellido_persona as medico
        FROM Citas c
        INNER JOIN Empleados e ON c.id_emp = e.id_emp
        INNER JOIN Personas pe ON e.id_persona = pe.id_persona
        WHERE c.cod_pac = %s ORDER BY c.fecha_hora DESC LIMIT 20
    """
    citas = ejecutar_query(query_citas, [pac_id])
    
    registrar_auditoria(user['id_emp'], 'SELECT', 'Pacientes', pac_id, get_client_ip(request))
    return render(request, 'cashier/gestion_pacientes.html', {
        'user': user, 'paciente': paciente, 'citas': citas, 'detalle': True
    })

@login_required_custom
@role_required('Administrativo', 'Administrador')
def editar_paciente(request, pac_id):
    """Editar paciente"""
    user = get_user_from_session(request)
    query = """
        SELECT p.* FROM Pacientes pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE pac.cod_pac = %s
    """
    paciente = ejecutar_query_one(query, [pac_id])
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, paciente_id=pac_id)
        if form.is_valid():
            data = form.cleaned_data
            query = """
                UPDATE Personas SET nom_persona=%s, apellido_persona=%s, tipo_doc=%s,
                    fecha_nac=%s, genero=%s, dir_persona=%s, tel_persona=%s, 
                    email_persona=%s, ciudad_residencia=%s
                WHERE id_persona = (SELECT id_persona FROM Pacientes WHERE cod_pac = %s)
            """
            ejecutar_update(query, [
                data['nom_persona'], data['apellido_persona'], data['tipo_doc'],
                data['fecha_nac'], data['genero'], data['dir_persona'],
                data['tel_persona'], data['email_persona'], data['ciudad_residencia'], pac_id
            ])
            registrar_auditoria(user['id_emp'], 'UPDATE', 'Pacientes', pac_id, get_client_ip(request))
            messages.success(request, 'Paciente actualizado correctamente.')
            return redirect('hospital:detalle_paciente', pac_id=pac_id)
    else:
        form = PacienteForm(initial={
            'nom_persona': paciente[1], 'apellido_persona': paciente[2],
            'tipo_doc': paciente[3], 'num_doc': paciente[4], 'fecha_nac': paciente[5],
            'genero': paciente[6], 'dir_persona': paciente[7], 'tel_persona': paciente[8],
            'email_persona': paciente[9], 'ciudad_residencia': paciente[10]
        }, paciente_id=pac_id)
    return render(request, 'cashier/gestion_pacientes.html', {
        'user': user, 'form': form, 'paciente': paciente, 'editar': True
    })

# ============================================================================
# 4. MÓDULO DE CITAS
# ============================================================================

@login_required_custom
def lista_citas(request):
    """Lista todas las citas"""
    user = get_user_from_session(request)
    query = """
        SELECT c.id_cita, c.fecha_hora, c.estado, c.tipo_servicio, c.motivo,
               p.nom_persona || ' ' || p.apellido_persona as paciente,
               pe.nom_persona || ' ' || pe.apellido_persona as medico, s.nom_sede
        FROM Citas c
        INNER JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        INNER JOIN Empleados e ON c.id_emp = e.id_emp
        INNER JOIN Personas pe ON e.id_persona = pe.id_persona
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        WHERE c.id_sede = %s ORDER BY c.fecha_hora DESC LIMIT 100
    """
    citas = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/citas_pendientes.html', {'user': user, 'citas': citas})

@login_required_custom
@role_required('Administrativo', 'Administrador')
def nueva_cita(request):
    """Programar nueva cita"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = CitaForm(user['id_sede'], request.POST)
        if form.is_valid():
            data = form.cleaned_data
            result = ejecutar_query_one("SELECT COALESCE(MAX(id_cita), 0) + 1 FROM Citas")
            id_cita = result[0]
            query = """
                INSERT INTO Citas (id_cita, id_sede, id_dept, id_emp, cod_pac, 
                    fecha_hora, fecha_hora_solicitada, tipo_servicio, estado, motivo)
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            """
            ejecutar_update(query, [
                id_cita, user['id_sede'], data['id_dept'], data['id_emp'],
                data['cod_pac'], data['fecha_hora'], data['tipo_servicio'],
                data['estado'], data['motivo']
            ])
            registrar_auditoria(user['id_emp'], 'INSERT', 'Citas', id_cita, get_client_ip(request))
            messages.success(request, 'Cita programada correctamente.')
            return redirect('hospital:lista_citas')
    else:
        form = CitaForm(user['id_sede'])
    return render(request, 'cashier/programar_cita.html', {'user': user, 'form': form})

@login_required_custom
def detalle_cita(request, cita_id):
    """Ver detalle de cita"""
    user = get_user_from_session(request)
    query = """
        SELECT c.id_cita, c.id_sede, c.id_dept, c.id_emp, c.cod_pac,
               c.fecha_hora, c.fecha_hora_solicitada, c.estado, c.tipo_servicio, c.motivo,
               p.nom_persona || ' ' || p.apellido_persona as paciente,
               pe.nom_persona || ' ' || pe.apellido_persona as medico,
               s.nom_sede, d.nom_dept
        FROM Citas c
        INNER JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        INNER JOIN Empleados e ON c.id_emp = e.id_emp
        INNER JOIN Personas pe ON e.id_persona = pe.id_persona
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
        WHERE c.id_cita = %s
    """
    cita = ejecutar_query_one(query, [cita_id])
    return render(request, 'cashier/citas_pendientes.html', {'user': user, 'cita': cita, 'detalle': True})

@login_required_custom
@role_required('Administrativo', 'Administrador')
def editar_cita(request, cita_id):
    """Editar cita"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = CitaForm(user['id_sede'], request.POST)
        if form.is_valid():
            data = form.cleaned_data
            query = """
                UPDATE Citas SET id_dept=%s, id_emp=%s, cod_pac=%s, 
                    fecha_hora=%s, tipo_servicio=%s, estado=%s, motivo=%s
                WHERE id_cita = %s
            """
            ejecutar_update(query, [
                data['id_dept'], data['id_emp'], data['cod_pac'],
                data['fecha_hora'], data['tipo_servicio'], data['estado'],
                data['motivo'], cita_id
            ])
            registrar_auditoria(user['id_emp'], 'UPDATE', 'Citas', cita_id, get_client_ip(request))
            messages.success(request, 'Cita actualizada.')
            return redirect('hospital:detalle_cita', cita_id=cita_id)
    return redirect('hospital:lista_citas')

@login_required_custom
@role_required('Administrativo', 'Administrador')
def cancelar_cita(request, cita_id):
    """Cancelar cita"""
    user = get_user_from_session(request)
    query = "UPDATE Citas SET estado = 'CANCELADA' WHERE id_cita = %s"
    ejecutar_update(query, [cita_id])
    registrar_auditoria(user['id_emp'], 'UPDATE', 'Citas', cita_id, get_client_ip(request))
    messages.success(request, 'Cita cancelada.')
    return redirect('hospital:lista_citas')

@login_required_custom
def citas_pendientes(request):
    """Citas del día"""
    user = get_user_from_session(request)
    query = """
        SELECT c.id_cita, c.fecha_hora, c.estado, c.tipo_servicio, c.motivo,
               p.nom_persona || ' ' || p.apellido_persona as paciente
        FROM Citas c
        INNER JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE c.id_sede = %s AND DATE(c.fecha_hora) = CURRENT_DATE
        AND c.tipo_servicio = 'PROGRAMADA' ORDER BY c.fecha_hora
    """
    citas = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/citas_pendientes.html', {'user': user, 'citas': citas, 'hoy': True})

@login_required_custom
def citas_programadas(request):
    """Citas futuras"""
    user = get_user_from_session(request)
    query = """
        SELECT c.id_cita, c.fecha_hora, c.estado, c.tipo_servicio, c.motivo,
               p.nom_persona || ' ' || p.apellido_persona as paciente
        FROM Citas c
        INNER JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE c.id_sede = %s AND c.fecha_hora > NOW()
        AND c.tipo_servicio = 'PROGRAMADA' ORDER BY c.fecha_hora
    """
    citas = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/citas_pendientes.html', {'user': user, 'citas': citas, 'futuras': True})

@login_required_custom
def historial_citas(request):
    """Citas pasadas"""
    user = get_user_from_session(request)
    query = """
        SELECT c.id_cita, c.fecha_hora, c.estado, c.tipo_servicio, c.motivo,
               p.nom_persona || ' ' || p.apellido_persona as paciente
        FROM Citas c
        INNER JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE c.id_sede = %s AND c.fecha_hora < NOW()
        ORDER BY c.fecha_hora DESC LIMIT 100
    """
    citas = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/citas_pendientes.html', {'user': user, 'citas': citas, 'historial': True})

# ============================================================================
# 5. MÓDULO CLÍNICO - HISTORIAS Y DIAGNÓSTICOS
# ============================================================================

@login_required_custom
@role_required('Medico', 'Enfermero', 'Administrador', 'Administrativo')
def lista_historias(request):
    """Lista de historias clínicas"""
    user = get_user_from_session(request)
    
    # Médicos solo ven historias de sus propios pacientes
    if user['rol'] == 'Medico':
        query = """
            SELECT DISTINCT hc.cod_hist, hc.fecha_registro,
                   p.nom_persona || ' ' || p.apellido_persona as paciente, p.num_doc
            FROM Historias_Clinicas hc
            INNER JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
            INNER JOIN Citas c ON c.cod_pac = pac.cod_pac
            WHERE c.id_emp = %s
            ORDER BY hc.fecha_registro DESC LIMIT 100
        """
        historias = ejecutar_query(query, [user['id_emp']])
    else:
        query = """
            SELECT hc.cod_hist, hc.fecha_registro,
                   p.nom_persona || ' ' || p.apellido_persona as paciente, p.num_doc
            FROM Historias_Clinicas hc
            INNER JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
            ORDER BY hc.fecha_registro DESC LIMIT 100
        """
        historias = ejecutar_query(query)
    return render(request, 'cashier/ver_historial.html', {'user': user, 'historias': historias})

@login_required_custom
@role_required('Medico', 'Enfermero', 'Administrador', 'Administrativo')
def detalle_historia(request, hist_id):
    """Ver historia clínica"""
    user = get_user_from_session(request)
    
    # Médicos solo pueden ver historias de sus propios pacientes
    if user['rol'] == 'Medico':
        # Verificar que el médico ha atendido a este paciente
        check_query = """
            SELECT 1 FROM Historias_Clinicas hc
            INNER JOIN Citas c ON c.cod_pac = hc.cod_pac
            WHERE hc.cod_hist = %s AND c.id_emp = %s
        """
        tiene_acceso = ejecutar_query_one(check_query, [hist_id, user['id_emp']])
        if not tiene_acceso:
            messages.error(request, 'No tiene permisos para ver esta historia clínica.')
            return redirect('hospital:lista_historias')
    
    query = """SELECT * FROM vista_historias_consolidadas WHERE cod_hist = %s"""
    historia = ejecutar_query(query, [hist_id])
    
    # Obtener prescripciones asociadas a esta historia
    query_prescripciones = """
        SELECT pr.id_presc, m.nom_med, m.principio_activo, pr.dosis, pr.frecuencia, 
               pr.duracion_dias, pr.cantidad_total, pr.fecha_emision
        FROM Prescripciones pr
        INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
        WHERE pr.cod_hist = %s
        ORDER BY pr.fecha_emision DESC
    """
    prescripciones = ejecutar_query(query_prescripciones, [hist_id])
    
    registrar_auditoria(user['id_emp'], 'SELECT', 'Historias_Clinicas', hist_id, get_client_ip(request))
    return render(request, 'cashier/ver_historial.html', {
        'user': user, 'historia': historia, 'prescripciones': prescripciones, 'detalle': True
    })

@login_required_custom
@role_required('Medico', 'Enfermero', 'Administrador', 'Administrativo')
def historias_paciente(request, pac_id):
    """Historias de un paciente"""
    user = get_user_from_session(request)
    
    # Médicos solo pueden ver historias de pacientes que han atendido
    if user['rol'] == 'Medico':
        check_query = """SELECT 1 FROM Citas WHERE cod_pac = %s AND id_emp = %s"""
        tiene_acceso = ejecutar_query_one(check_query, [pac_id, user['id_emp']])
        if not tiene_acceso:
            messages.error(request, 'No tiene permisos para ver las historias de este paciente.')
            return redirect('hospital:lista_historias')
    
    query = """SELECT * FROM vista_historias_consolidadas WHERE cod_pac = %s ORDER BY fecha_registro DESC"""
    historias = ejecutar_query(query, [pac_id])
    return render(request, 'cashier/ver_historial.html', {'user': user, 'historias': historias, 'pac_id': pac_id})

@login_required_custom
@role_required('Medico')
def registrar_diagnostico(request, cita_id):
    """Registrar diagnóstico"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = DiagnosticoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Obtener o crear historia clínica
            cita = ejecutar_query_one("SELECT cod_pac FROM Citas WHERE id_cita = %s", [cita_id])
            cod_pac = cita[0]
            
            result = ejecutar_query_one("SELECT COALESCE(MAX(cod_hist), 0) + 1 FROM Historias_Clinicas")
            cod_hist = result[0]
            ejecutar_update(
                "INSERT INTO Historias_Clinicas (cod_hist, cod_pac) VALUES (%s, %s)",
                [cod_hist, cod_pac]
            )
            
            result = ejecutar_query_one("SELECT COALESCE(MAX(id_diagnostico), 0) + 1 FROM Diagnostico")
            id_diag = result[0]
            query = """
                INSERT INTO Diagnostico (id_diagnostico, id_enfermedad, id_cita, cod_hist, observacion)
                VALUES (%s, %s, %s, %s, %s)
            """
            ejecutar_update(query, [id_diag, data['id_enfermedad'], cita_id, cod_hist, data['observacion']])
            
            # Actualizar estado de cita
            ejecutar_update("UPDATE Citas SET estado = 'COMPLETADA' WHERE id_cita = %s", [cita_id])
            
            registrar_auditoria(user['id_emp'], 'INSERT', 'Historias_Clinicas', cod_hist, get_client_ip(request))
            messages.success(request, 'Diagnóstico registrado.')
            return redirect('hospital:detalle_cita', cita_id=cita_id)
    else:
        form = DiagnosticoForm()
    return render(request, 'cashier/registrar_diagnostico.html', {'user': user, 'form': form, 'cita_id': cita_id})

@login_required_custom
def detalle_diagnostico(request, diag_id):
    """Ver diagnóstico"""
    user = get_user_from_session(request)
    query = """
        SELECT d.*, e.nombre_enfermedad
        FROM Diagnostico d
        INNER JOIN Enfermedades e ON d.id_enfermedad = e.id_enfermedad
        WHERE d.id_diagnostico = %s
    """
    diagnostico = ejecutar_query_one(query, [diag_id])
    return render(request, 'cashier/registrar_diagnostico.html', {'user': user, 'diagnostico': diagnostico})

@login_required_custom
@role_required('Medico')
def editar_diagnostico(request, diag_id):
    """Editar diagnóstico"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = DiagnosticoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            query = "UPDATE Diagnostico SET id_enfermedad=%s, observacion=%s WHERE id_diagnostico=%s"
            ejecutar_update(query, [data['id_enfermedad'], data['observacion'], diag_id])
            messages.success(request, 'Diagnóstico actualizado.')
    return redirect('hospital:detalle_diagnostico', diag_id=diag_id)

# ============================================================================
# 6. MÓDULO DE PRESCRIPCIONES
# ============================================================================

@login_required_custom
@role_required('Medico', 'Enfermero', 'Administrador', 'Administrativo')
def lista_prescripciones(request):
    """Lista de prescripciones"""
    user = get_user_from_session(request)
    
    # Médicos solo ven prescripciones de sus propios pacientes
    if user['rol'] == 'Medico':
        query = """
            SELECT pr.id_presc, pr.fecha_emision, m.nom_med, pr.dosis, pr.frecuencia,
                   p.nom_persona || ' ' || p.apellido_persona as paciente
            FROM Prescripciones pr
            INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
            INNER JOIN Historias_Clinicas hc ON pr.cod_hist = hc.cod_hist
            INNER JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
            INNER JOIN Citas c ON pr.id_cita = c.id_cita
            WHERE c.id_emp = %s
            ORDER BY pr.fecha_emision DESC LIMIT 100
        """
        prescripciones = ejecutar_query(query, [user['id_emp']])
    else:
        query = """
            SELECT pr.id_presc, pr.fecha_emision, m.nom_med, pr.dosis, pr.frecuencia,
                   p.nom_persona || ' ' || p.apellido_persona as paciente
            FROM Prescripciones pr
            INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
            INNER JOIN Historias_Clinicas hc ON pr.cod_hist = hc.cod_hist
            INNER JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
            INNER JOIN Personas p ON pac.id_persona = p.id_persona
            ORDER BY pr.fecha_emision DESC LIMIT 100
        """
        prescripciones = ejecutar_query(query)
    return render(request, 'cashier/prescribir_medicamento.html', {'user': user, 'prescripciones': prescripciones})

@login_required_custom
@role_required('Medico', 'Administrador')
def nueva_prescripcion(request):
    """Nueva prescripción"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = PrescripcionForm(user['id_sede'], request.POST)
        if form.is_valid():
            messages.success(request, 'Prescripción creada.')
            return redirect('hospital:lista_prescripciones')
    else:
        form = PrescripcionForm(user['id_sede'])
    return render(request, 'cashier/prescribir_medicamento.html', {'user': user, 'form': form})

@login_required_custom
@role_required('Medico', 'Administrador')
def prescribir_medicamento(request, hist_id):
    """Prescribir medicamento a historia"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = PrescripcionForm(user['id_sede'], request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Obtener última cita del paciente
            cita = ejecutar_query_one(
                "SELECT c.id_cita FROM Citas c INNER JOIN Historias_Clinicas hc ON c.cod_pac = hc.cod_pac WHERE hc.cod_hist = %s ORDER BY c.fecha_hora DESC LIMIT 1",
                [hist_id]
            )
            result = ejecutar_query_one("SELECT COALESCE(MAX(id_presc), 0) + 1 FROM Prescripciones")
            id_presc = result[0]
            query = """
                INSERT INTO Prescripciones (id_presc, cod_med, cod_hist, id_cita, dosis, frecuencia, duracion_dias, cantidad_total, fecha_emision)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
            """
            ejecutar_update(query, [
                id_presc, data['cod_med'], hist_id, cita[0] if cita else None,
                data['dosis'], data['frecuencia'], data['duracion_dias'], data['cantidad_total']
            ])
            # Actualizar inventario
            ejecutar_update(
                "UPDATE Inventario_Farmacia SET stock_actual = stock_actual - %s WHERE cod_med = %s AND id_sede = %s",
                [data['cantidad_total'], data['cod_med'], user['id_sede']]
            )
            messages.success(request, 'Medicamento prescrito.')
            return redirect('hospital:detalle_historia', hist_id=hist_id)
    else:
        form = PrescripcionForm(user['id_sede'])
    return render(request, 'cashier/prescribir_medicamento.html', {'user': user, 'form': form, 'hist_id': hist_id})

@login_required_custom
@role_required('Medico', 'Enfermero', 'Administrador', 'Administrativo')
def detalle_prescripcion(request, presc_id):
    """Ver prescripción"""
    user = get_user_from_session(request)
    
    # Médicos solo pueden ver prescripciones de sus propios pacientes
    if user['rol'] == 'Medico':
        query = """
            SELECT pr.*, m.nom_med, m.principio_activo
            FROM Prescripciones pr
            INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
            INNER JOIN Citas c ON pr.id_cita = c.id_cita
            WHERE pr.id_presc = %s AND c.id_emp = %s
        """
        prescripcion = ejecutar_query_one(query, [presc_id, user['id_emp']])
    else:
        query = """
            SELECT pr.*, m.nom_med, m.principio_activo
            FROM Prescripciones pr
            INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
            WHERE pr.id_presc = %s
        """
        prescripcion = ejecutar_query_one(query, [presc_id])
    
    if not prescripcion:
        messages.error(request, 'No tiene permisos para ver esta prescripción.')
        return redirect('hospital:lista_prescripciones')
    return render(request, 'cashier/prescribir_medicamento.html', {'user': user, 'prescripcion': prescripcion})

# ============================================================================
# 7. MÓDULO DE FARMACIA E INVENTARIO
# ============================================================================

@login_required_custom
def gestion_farmacia(request):
    """Panel de farmacia"""
    user = get_user_from_session(request)
    return render(request, 'cashier/gestion_farmacia.html', {'user': user})

@login_required_custom
def inventario_farmacia(request):
    """Inventario de farmacia"""
    user = get_user_from_session(request)
    query = """
        SELECT i.id_inv, s.nom_sede, s.ciudad, m.cod_med, m.nom_med, m.principio_activo,
               i.stock_actual, i.fecha_actualizacion,
               CASE 
                   WHEN i.stock_actual < 10 THEN 'CRÍTICO'
                   WHEN i.stock_actual < 50 THEN 'BAJO'
                   WHEN i.stock_actual < 100 THEN 'MEDIO'
                   ELSE 'ÓPTIMO'
               END AS nivel_stock
        FROM Inventario_Farmacia i
        INNER JOIN Sedes_Hospitalarias s ON i.id_sede = s.id_sede
        INNER JOIN Catalogo_Medicamentos m ON i.cod_med = m.cod_med
        WHERE i.id_sede = %s ORDER BY m.nom_med
    """
    inventario = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/gestion_farmacia.html', {'user': user, 'inventario': inventario})

@login_required_custom
@role_required('Enfermero', 'Administrador')
def actualizar_stock(request, inv_id):
    """Actualizar stock"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = ActualizarStockForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            query = "UPDATE Inventario_Farmacia SET stock_actual = %s, fecha_actualizacion = NOW() WHERE id_inv = %s"
            ejecutar_update(query, [data['stock_actual'], inv_id])
            messages.success(request, 'Stock actualizado.')
            return redirect('hospital:inventario_farmacia')
    else:
        form = ActualizarStockForm()
    return render(request, 'cashier/actualizar_stock.html', {'user': user, 'form': form})

@login_required_custom
def catalogo_medicamentos(request):
    """Catálogo de medicamentos"""
    user = get_user_from_session(request)
    query = "SELECT * FROM Catalogo_Medicamentos ORDER BY nom_med"
    medicamentos = ejecutar_query(query)
    return render(request, 'cashier/gestion_farmacia.html', {'user': user, 'medicamentos': medicamentos})

@login_required_custom
@role_required('Administrador')
def nuevo_medicamento(request):
    """Nuevo medicamento"""
    user = get_user_from_session(request)
    messages.info(request, 'Función de crear medicamento.')
    return redirect('hospital:catalogo_medicamentos')

@login_required_custom
def detalle_medicamento(request, med_id):
    """Detalle medicamento"""
    user = get_user_from_session(request)
    query = "SELECT * FROM Catalogo_Medicamentos WHERE cod_med = %s"
    medicamento = ejecutar_query_one(query, [med_id])
    return render(request, 'cashier/gestion_farmacia.html', {'user': user, 'medicamento': medicamento})

@login_required_custom
def alertas_inventario(request):
    """Alertas de inventario bajo"""
    user = get_user_from_session(request)
    query = """
        SELECT i.id_inv, s.nom_sede, s.ciudad, m.cod_med, m.nom_med, m.principio_activo,
               i.stock_actual, i.fecha_actualizacion,
               CASE 
                   WHEN i.stock_actual < 10 THEN 'CRÍTICO'
                   WHEN i.stock_actual < 50 THEN 'BAJO'
                   WHEN i.stock_actual < 100 THEN 'MEDIO'
                   ELSE 'ÓPTIMO'
               END AS nivel_stock
        FROM Inventario_Farmacia i
        INNER JOIN Sedes_Hospitalarias s ON i.id_sede = s.id_sede
        INNER JOIN Catalogo_Medicamentos m ON i.cod_med = m.cod_med
        WHERE i.id_sede = %s AND i.stock_actual < 50
    """
    alertas = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/gestion_farmacia.html', {'user': user, 'alertas': alertas})

# ============================================================================
# 8. MÓDULO DE EQUIPAMIENTO
# ============================================================================

@login_required_custom
def lista_equipamiento(request):
    """Lista de equipamiento"""
    user = get_user_from_session(request)
    query = """
        SELECT eq.cod_eq, eq.nom_eq, eq.marca_modelo, s.id_sede, s.nom_sede, 
               d.id_dept, d.nom_dept, eq.estado_equipo, eq.fecha_ultimo_maint,
               pe.nom_persona || ' ' || pe.apellido_persona AS responsable
        FROM Equipamiento eq
        INNER JOIN Departamentos d ON eq.id_dept = d.id_dept AND eq.id_sede = d.id_sede
        INNER JOIN Sedes_Hospitalarias s ON d.id_sede = s.id_sede
        LEFT JOIN Empleados e ON eq.responsable_id = e.id_emp
        LEFT JOIN Personas pe ON e.id_persona = pe.id_persona
        WHERE eq.id_sede = %s
    """
    equipos = ejecutar_query(query, [user['id_sede']])
    return render(request, 'cashier/gestion_equipamiento.html', {'user': user, 'equipos': equipos})

@login_required_custom
@role_required('Administrador')
def nuevo_equipamiento(request):
    """Nuevo equipo"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = EquipamientoForm(user['id_sede'], request.POST)
        if form.is_valid():
            data = form.cleaned_data
            result = ejecutar_query_one("SELECT COALESCE(MAX(cod_eq), 0) + 1 FROM Equipamiento")
            cod_eq = result[0]
            query = """
                INSERT INTO Equipamiento (cod_eq, id_sede, id_dept, nom_eq, marca_modelo, estado_equipo, fecha_ultimo_maint, responsable_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            ejecutar_update(query, [
                cod_eq, user['id_sede'], data['id_dept'], data['nom_eq'],
                data['marca_modelo'], data['estado_equipo'], data['fecha_ultimo_maint'], data['responsable_id']
            ])
            messages.success(request, 'Equipo registrado.')
            return redirect('hospital:lista_equipamiento')
    else:
        form = EquipamientoForm(user['id_sede'])
    return render(request, 'cashier/gestion_equipamiento.html', {'user': user, 'form': form})

@login_required_custom
def detalle_equipamiento(request, eq_id):
    """Detalle equipo"""
    user = get_user_from_session(request)
    query = """
        SELECT eq.cod_eq, eq.nom_eq, eq.marca_modelo, s.id_sede, s.nom_sede, 
               d.id_dept, d.nom_dept, eq.estado_equipo, eq.fecha_ultimo_maint,
               pe.nom_persona || ' ' || pe.apellido_persona AS responsable
        FROM Equipamiento eq
        INNER JOIN Departamentos d ON eq.id_dept = d.id_dept AND eq.id_sede = d.id_sede
        INNER JOIN Sedes_Hospitalarias s ON d.id_sede = s.id_sede
        LEFT JOIN Empleados e ON eq.responsable_id = e.id_emp
        LEFT JOIN Personas pe ON e.id_persona = pe.id_persona
        WHERE eq.cod_eq = %s
    """
    equipo = ejecutar_query_one(query, [eq_id])
    return render(request, 'cashier/gestion_equipamiento.html', {'user': user, 'equipo': equipo})

@login_required_custom
@role_required('Administrador')
def editar_equipamiento(request, eq_id):
    """Editar equipo"""
    user = get_user_from_session(request)
    if request.method == 'POST':
        form = EquipamientoForm(user['id_sede'], request.POST)
        if form.is_valid():
            data = form.cleaned_data
            query = """UPDATE Equipamiento SET nom_eq=%s, marca_modelo=%s, estado_equipo=%s, 
                       fecha_ultimo_maint=%s, responsable_id=%s WHERE cod_eq=%s"""
            ejecutar_update(query, [
                data['nom_eq'], data['marca_modelo'], data['estado_equipo'],
                data['fecha_ultimo_maint'], data['responsable_id'], eq_id
            ])
            messages.success(request, 'Equipo actualizado.')
    return redirect('hospital:detalle_equipamiento', eq_id=eq_id)

@login_required_custom
@role_required('Administrador')
def registrar_mantenimiento(request, eq_id):
    """Registrar mantenimiento"""
    user = get_user_from_session(request)
    ejecutar_update("UPDATE Equipamiento SET fecha_ultimo_maint = CURRENT_DATE WHERE cod_eq = %s", [eq_id])
    messages.success(request, 'Mantenimiento registrado.')
    return redirect('hospital:detalle_equipamiento', eq_id=eq_id)

# ============================================================================
# 9. MÓDULO DE REPORTES Y ANALÍTICA
# ============================================================================

@login_required_custom
def menu_reportes(request):
    """Menú de reportes"""
    user = get_user_from_session(request)
    return render(request, 'cashier/reportes_analitica.html', {'user': user})

@login_required_custom
def reporte_medicamentos_recetados(request):
    """Medicamentos más recetados por sede"""
    user = get_user_from_session(request)
    query = """
        SELECT s.nom_sede, s.ciudad, m.nom_med, COUNT(pr.id_presc) AS total_prescripciones,
               SUM(pr.cantidad_total) AS cantidad_total_recetada
        FROM Prescripciones pr
        INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
        INNER JOIN Citas c ON pr.id_cita = c.id_cita
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        WHERE pr.fecha_emision >= CURRENT_DATE - INTERVAL '1 month'
        GROUP BY s.id_sede, s.nom_sede, s.ciudad, m.cod_med, m.nom_med
        ORDER BY s.nom_sede, total_prescripciones DESC
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'medicamentos'})

@login_required_custom
def reporte_medicos_consultas(request):
    """Médicos con más consultas atendidas"""
    user = get_user_from_session(request)
    query = """
        SELECT p.nom_persona || ' ' || p.apellido_persona AS nombre_medico,
               s.nom_sede, d.nom_dept, esp.nombre_esp AS especialidad,
               DATE_TRUNC('week', c.fecha_hora) AS semana, COUNT(c.id_cita) AS total_consultas
        FROM Citas c
        INNER JOIN Empleados e ON c.id_emp = e.id_emp
        INNER JOIN Personas p ON e.id_persona = p.id_persona
        INNER JOIN Roles r ON e.id_rol = r.id_rol
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
        LEFT JOIN Emp_Posee_Esp epe ON e.id_emp = epe.id_emp
        LEFT JOIN Especialidades esp ON epe.id_especialidad = esp.id_especialidad
        WHERE r.nombre_rol = 'Medico' AND c.estado = 'COMPLETADA'
        GROUP BY e.id_emp, p.nom_persona, p.apellido_persona, s.nom_sede, d.nom_dept, esp.nombre_esp, DATE_TRUNC('week', c.fecha_hora)
        ORDER BY semana DESC, total_consultas DESC LIMIT 20
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'medicos'})

@login_required_custom
def reporte_tiempos_atencion(request):
    """Tiempo promedio de espera entre solicitud y cita"""
    user = get_user_from_session(request)
    query = """
        SELECT s.nom_sede, d.nom_dept,
               ROUND(AVG(EXTRACT(EPOCH FROM (c.fecha_hora - c.fecha_hora_solicitada))/86400)::numeric, 2) AS dias_promedio,
               COUNT(*) AS total_casos
        FROM Citas c
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
        WHERE c.estado = 'COMPLETADA'
        GROUP BY s.id_sede, s.nom_sede, d.nom_dept ORDER BY dias_promedio
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'tiempos'})

@login_required_custom
def reporte_pacientes_enfermedad(request):
    """Total de pacientes por enfermedad y sede"""
    user = get_user_from_session(request)
    query = """
        SELECT s.nom_sede, enf.nombre_enfermedad, COUNT(DISTINCT hc.cod_pac) AS total_pacientes,
               COUNT(diag.id_diagnostico) AS total_diagnosticos
        FROM Diagnostico diag
        INNER JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
        INNER JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
        INNER JOIN Citas c ON diag.id_cita = c.id_cita
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        GROUP BY s.id_sede, s.nom_sede, enf.id_enfermedad, enf.nombre_enfermedad
        ORDER BY s.nom_sede, total_pacientes DESC
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'enfermedades'})

@login_required_custom
def reporte_equipamiento_compartido(request):
    """Departamentos que comparten equipamiento"""
    user = get_user_from_session(request)
    query = """
        WITH equipo_compartido AS (
            SELECT eq.nom_eq, eq.marca_modelo, COUNT(DISTINCT eq.id_sede) AS sedes_con_equipo
            FROM Equipamiento eq GROUP BY eq.nom_eq, eq.marca_modelo HAVING COUNT(DISTINCT eq.id_sede) > 1
        )
        SELECT ec.nom_eq, ec.marca_modelo, s.nom_sede, d.nom_dept, eq.estado_equipo
        FROM equipo_compartido ec
        INNER JOIN Equipamiento eq ON ec.nom_eq = eq.nom_eq AND ec.marca_modelo = eq.marca_modelo
        INNER JOIN Sedes_Hospitalarias s ON eq.id_sede = s.id_sede
        INNER JOIN Departamentos d ON eq.id_dept = d.id_dept AND eq.id_sede = d.id_sede
        ORDER BY ec.nom_eq, s.nom_sede
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'equipamiento'})

@login_required_custom
def reporte_enfermedades_trimestre(request):
    """Top enfermedades del trimestre"""
    user = get_user_from_session(request)
    query = """
        SELECT d.nom_dept, s.nom_sede, enf.nombre_enfermedad, COUNT(diag.id_diagnostico) AS total_casos
        FROM Diagnostico diag
        INNER JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
        INNER JOIN Citas c ON diag.id_cita = c.id_cita
        INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '3 months'
        GROUP BY d.nom_dept, s.nom_sede, enf.nombre_enfermedad ORDER BY total_casos DESC LIMIT 20
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'trimestre'})

@login_required_custom
def reporte_consumo_medicamentos(request):
    """Consumo de medicamentos por departamento"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_consumo_medicamentos_dept ORDER BY cantidad_consumida DESC LIMIT 50"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'consumo'})

@login_required_custom
def reporte_utilizacion_recursos(request):
    """Utilización de recursos por sede"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_utilizacion_recursos ORDER BY total_citas DESC"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'recursos'})

@login_required_custom
def reporte_indices_atencion(request):
    """Índices de atención y tiempos de espera"""
    user = get_user_from_session(request)
    query = """
        SELECT s.nom_sede, COUNT(c.id_cita) AS total_citas,
               ROUND(AVG(EXTRACT(EPOCH FROM (c.fecha_hora - c.fecha_hora_solicitada))/86400)::numeric, 1) AS dias_espera
        FROM Citas c
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '1 month'
        GROUP BY s.id_sede, s.nom_sede ORDER BY dias_espera
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'indices'})

@login_required_custom
def reporte_especialidades_demandadas(request):
    """Especialidades más demandadas"""
    user = get_user_from_session(request)
    query = """
        SELECT esp.nombre_esp, s.nom_sede, COUNT(c.id_cita) AS total_consultas
        FROM Especialidades esp
        INNER JOIN Emp_Posee_Esp epe ON esp.id_especialidad = epe.id_especialidad
        INNER JOIN Empleados e ON epe.id_emp = e.id_emp
        INNER JOIN Citas c ON e.id_emp = c.id_emp
        INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '1 month'
        GROUP BY esp.nombre_esp, s.nom_sede ORDER BY total_consultas DESC
    """
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'especialidades'})

@login_required_custom
def reporte_inventario_critico(request):
    """Inventario crítico"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_inventario_consolidado WHERE stock_actual < 100 ORDER BY stock_actual"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'inventario'})

@login_required_custom
def reporte_productividad_medicos(request):
    """Productividad del personal médico"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_medicos_consultas ORDER BY total_consultas DESC"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'productividad'})

@login_required_custom
def reporte_tendencias_enfermedades(request):
    """Tendencias de enfermedades"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_enfermedades_por_sede ORDER BY total_diagnosticos DESC"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos, 'tipo': 'tendencias'})

@login_required_custom
def generar_reporte(request, tipo):
    """Generar reporte"""
    user = get_user_from_session(request)
    # Registrar generación de reporte
    result = ejecutar_query_one("SELECT COALESCE(MAX(id_reporte), 0) + 1 FROM Reportes_Generados")
    id_reporte = result[0]
    query = """INSERT INTO Reportes_Generados (id_reporte, id_sede, id_emp_generador, fecha_generacion, tipo_reporte)
               VALUES (%s, %s, %s, NOW(), %s)"""
    ejecutar_update(query, [id_reporte, user['id_sede'], user['id_emp'], tipo])
    messages.success(request, f'Reporte {tipo} generado.')
    return redirect('hospital:menu_reportes')

@login_required_custom
def exportar_reporte(request, tipo, formato):
    """Exportar reporte en formato específico"""
    user = get_user_from_session(request)
    messages.info(request, f'Exportando {tipo} en formato {formato}.')
    return redirect('hospital:menu_reportes')

# ============================================================================
# 10. MÓDULO DE AUDITORÍA
# ============================================================================

@login_required_custom
@role_required('Administrador', 'Auditor')
def auditoria_principal(request):
    """Panel de auditoría"""
    user = get_user_from_session(request)
    return render(request, 'cashier/auditoria_logs.html', {'user': user})

@login_required_custom
@role_required('Administrador', 'Auditor')
def auditoria_accesos(request):
    """Auditoría de accesos"""
    user = get_user_from_session(request)
    query = """
        SELECT aa.id_evento, aa.fecha_evento, p.nom_persona || ' ' || p.apellido_persona AS empleado,
               r.nombre_rol, s.nom_sede, aa.accion, aa.tabla_afectada, aa.id_registro_afectado, aa.ip_origen
        FROM Auditoria_Accesos aa
        LEFT JOIN Empleados e ON aa.id_emp = e.id_emp
        LEFT JOIN Personas p ON e.id_persona = p.id_persona
        LEFT JOIN Roles r ON e.id_rol = r.id_rol
        LEFT JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        ORDER BY aa.fecha_evento DESC LIMIT 100
    """
    logs = ejecutar_query(query)
    return render(request, 'cashier/auditoria_logs.html', {'user': user, 'logs': logs})

@login_required_custom
@role_required('Administrador', 'Auditor')
def auditoria_historias(request):
    """Auditoría de historias clínicas"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_auditoria_historias LIMIT 100"""
    logs = ejecutar_query(query)
    return render(request, 'cashier/auditoria_logs.html', {'user': user, 'logs': logs, 'historias': True})

@login_required_custom
@role_required('Administrador', 'Auditor')
def filtrar_auditoria(request):
    """Filtrar auditoría"""
    user = get_user_from_session(request)
    tabla = request.GET.get('tabla', '')
    query = """SELECT * FROM Auditoria_Accesos WHERE tabla_afectada = %s ORDER BY fecha_evento DESC LIMIT 100"""
    logs = ejecutar_query(query, [tabla]) if tabla else []
    return render(request, 'cashier/auditoria_logs.html', {'user': user, 'logs': logs})

# ============================================================================
# 11. VISTAS DISTRIBUIDAS
# ============================================================================

@login_required_custom
def vista_historias_consolidadas(request):
    """Historias clínicas consolidadas"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_historias_consolidadas ORDER BY fecha_registro DESC LIMIT 100"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/ver_historial.html', {'user': user, 'historias': datos, 'consolidado': True})

@login_required_custom
def vista_medicamentos_sede(request):
    """Medicamentos recetados por sede"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_medicamentos_recetados_sede ORDER BY total_prescripciones DESC"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/analitica_medicamentos.html', {'user': user, 'datos': datos})

@login_required_custom
def vista_medicos_consultas(request):
    """Médicos y consultas"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_medicos_consultas ORDER BY total_consultas DESC"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos})

@login_required_custom
def vista_enfermedades_sede(request):
    """Enfermedades por sede"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_enfermedades_por_sede ORDER BY total_diagnosticos DESC"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/reportes_analitica.html', {'user': user, 'datos': datos})

@login_required_custom
def vista_inventario_consolidado(request):
    """Inventario consolidado"""
    user = get_user_from_session(request)
    query = """SELECT * FROM vista_inventario_consolidado ORDER BY nom_sede, nom_med"""
    datos = ejecutar_query(query)
    return render(request, 'cashier/gestion_farmacia.html', {'user': user, 'inventario': datos, 'consolidado': True})

# ============================================================================
# 12. ADMINISTRACIÓN
# ============================================================================

@login_required_custom
@role_required('Administrador')
def admin_principal(request):
    """Panel de administración"""
    user = get_user_from_session(request)
    return render(request, 'cashier/menu.html', {'user': user, 'admin': True})

@login_required_custom
@role_required('Administrador')
def admin_empleados(request):
    """Lista de empleados"""
    user = get_user_from_session(request)
    query = """
        SELECT e.id_emp, p.nom_persona, p.apellido_persona, r.nombre_rol, 
               s.nom_sede, d.nom_dept, e.activo
        FROM Empleados e
        INNER JOIN Personas p ON e.id_persona = p.id_persona
        INNER JOIN Roles r ON e.id_rol = r.id_rol
        INNER JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        INNER JOIN Departamentos d ON e.id_dept = d.id_dept AND e.id_sede = d.id_sede
        ORDER BY p.apellido_persona
    """
    empleados = ejecutar_query(query)
    return render(request, 'cashier/perfil_empleado.html', {'user': user, 'empleados': empleados, 'admin': True})

@login_required_custom
@role_required('Administrador')
def admin_nuevo_empleado(request):
    """Nuevo empleado"""
    user = get_user_from_session(request)
    messages.info(request, 'Función de crear empleado.')
    return redirect('hospital:admin_empleados')

@login_required_custom
@role_required('Administrador')
def admin_detalle_empleado(request, emp_id):
    """Detalle de empleado"""
    user = get_user_from_session(request)
    query = """
        SELECT e.*, p.*, r.nombre_rol, s.nom_sede, d.nom_dept
        FROM Empleados e
        INNER JOIN Personas p ON e.id_persona = p.id_persona
        INNER JOIN Roles r ON e.id_rol = r.id_rol
        INNER JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        INNER JOIN Departamentos d ON e.id_dept = d.id_dept AND e.id_sede = d.id_sede
        WHERE e.id_emp = %s
    """
    empleado = ejecutar_query_one(query, [emp_id])
    return render(request, 'cashier/perfil_empleado.html', {'user': user, 'empleado': empleado, 'admin': True})

@login_required_custom
@role_required('Administrador')
def admin_editar_empleado(request, emp_id):
    """Editar empleado"""
    user = get_user_from_session(request)
    messages.info(request, 'Función de editar empleado.')
    return redirect('hospital:admin_detalle_empleado', emp_id=emp_id)

@login_required_custom
@role_required('Administrador')
def admin_desactivar_empleado(request, emp_id):
    """Desactivar empleado"""
    user = get_user_from_session(request)
    ejecutar_update("UPDATE Empleados SET activo = FALSE WHERE id_emp = %s", [emp_id])
    messages.success(request, 'Empleado desactivado.')
    return redirect('hospital:admin_empleados')

@login_required_custom
@role_required('Administrador')
def admin_sedes(request):
    """Gestión de sedes"""
    user = get_user_from_session(request)
    query = "SELECT * FROM Sedes_Hospitalarias ORDER BY nom_sede"
    sedes = ejecutar_query(query)
    return render(request, 'cashier/menu.html', {'user': user, 'sedes': sedes})

@login_required_custom
@role_required('Administrador')
def admin_departamentos(request):
    """Gestión de departamentos"""
    user = get_user_from_session(request)
    query = """
        SELECT d.*, s.nom_sede FROM Departamentos d
        INNER JOIN Sedes_Hospitalarias s ON d.id_sede = s.id_sede ORDER BY s.nom_sede, d.nom_dept
    """
    departamentos = ejecutar_query(query)
    return render(request, 'cashier/menu.html', {'user': user, 'departamentos': departamentos})

@login_required_custom
@role_required('Administrador')
def admin_roles(request):
    """Gestión de roles"""
    user = get_user_from_session(request)
    query = "SELECT * FROM Roles ORDER BY id_rol"
    roles = ejecutar_query(query)
    return render(request, 'cashier/menu.html', {'user': user, 'roles': roles})

@login_required_custom
@role_required('Administrador')
def admin_especialidades(request):
    """Gestión de especialidades"""
    user = get_user_from_session(request)
    query = "SELECT * FROM Especialidades ORDER BY nombre_esp"
    especialidades = ejecutar_query(query)
    return render(request, 'cashier/menu.html', {'user': user, 'especialidades': especialidades})

# ============================================================================
# 13. API ENDPOINTS
# ============================================================================

@login_required_custom
def api_buscar_pacientes(request):
    """API: Buscar pacientes"""
    q = request.GET.get('q', '')
    query = """
        SELECT pac.cod_pac, p.nom_persona || ' ' || p.apellido_persona as nombre, p.num_doc
        FROM Pacientes pac INNER JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE p.num_doc LIKE %s OR p.nom_persona ILIKE %s LIMIT 10
    """
    results = ejecutar_query(query, [f'%{q}%', f'%{q}%'])
    return JsonResponse({'pacientes': [{'id': r[0], 'nombre': r[1], 'doc': r[2]} for r in results]})

@login_required_custom
def api_medicos_disponibles(request):
    """API: Médicos disponibles"""
    user = get_user_from_session(request)
    query = """
        SELECT e.id_emp, p.nom_persona || ' ' || p.apellido_persona as nombre
        FROM Empleados e INNER JOIN Personas p ON e.id_persona = p.id_persona
        INNER JOIN Roles r ON e.id_rol = r.id_rol
        WHERE r.nombre_rol = 'Medico' AND e.id_sede = %s AND e.activo = TRUE
    """
    results = ejecutar_query(query, [user['id_sede']])
    return JsonResponse({'medicos': [{'id': r[0], 'nombre': r[1]} for r in results]})

@login_required_custom
def api_disponibilidad_citas(request):
    """API: Disponibilidad de citas"""
    fecha = request.GET.get('fecha', '')
    medico_id = request.GET.get('medico_id', '')
    query = """
        SELECT fecha_hora FROM Citas WHERE id_emp = %s AND DATE(fecha_hora) = %s AND estado = 'PROGRAMADA'
    """
    results = ejecutar_query(query, [medico_id, fecha]) if fecha and medico_id else []
    return JsonResponse({'ocupados': [str(r[0]) for r in results]})

@login_required_custom
def api_buscar_medicamentos(request):
    """API: Buscar medicamentos"""
    q = request.GET.get('q', '')
    query = "SELECT cod_med, nom_med, principio_activo FROM Catalogo_Medicamentos WHERE nom_med ILIKE %s LIMIT 10"
    results = ejecutar_query(query, [f'%{q}%'])
    return JsonResponse({'medicamentos': [{'id': r[0], 'nombre': r[1], 'principio': r[2]} for r in results]})

@login_required_custom
def api_verificar_stock(request, med_id):
    """API: Verificar stock"""
    user = get_user_from_session(request)
    query = "SELECT stock_actual FROM Inventario_Farmacia WHERE cod_med = %s AND id_sede = %s"
    result = ejecutar_query_one(query, [med_id, user['id_sede']])
    return JsonResponse({'stock': result[0] if result else 0})

@login_required_custom
def api_buscar_enfermedades(request):
    """API: Buscar enfermedades"""
    q = request.GET.get('q', '')
    query = "SELECT id_enfermedad, nombre_enfermedad FROM Enfermedades WHERE nombre_enfermedad ILIKE %s LIMIT 10"
    results = ejecutar_query(query, [f'%{q}%'])
    return JsonResponse({'enfermedades': [{'id': r[0], 'nombre': r[1]} for r in results]})

# ============================================================================
# 14. PÁGINAS AUXILIARES
# ============================================================================

def sin_permisos(request):
    """Página de sin permisos"""
    return render(request, 'cashier/index.html', {'error': 'No tiene permisos para acceder a esta página.'})

def ayuda(request):
    """Página de ayuda"""
    user = get_user_from_session(request)
    return render(request, 'cashier/menu.html', {'user': user, 'ayuda': True})

def sobre_sistema(request):
    """Información del sistema"""
    user = get_user_from_session(request)
    return render(request, 'cashier/menu.html', {'user': user, 'sobre': True})
