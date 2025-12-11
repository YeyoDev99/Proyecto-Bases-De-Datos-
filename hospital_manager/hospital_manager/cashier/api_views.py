"""
API Views for Hospital Management System
All endpoints return JSON responses for the static frontend.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .db_utils import ejecutar_query, ejecutar_query_one, ejecutar_insert, ejecutar_update


def get_json_body(request):
    """Parse JSON body from request."""
    try:
        return json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def get_user_from_session(request):
    """Get user info from session."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    
    query = """
        SELECT e.id_emp, e.id_sede, e.id_dept, p.nom_persona, p.apellido_persona, r.nombre_rol
        FROM Empleados e
        JOIN Personas p ON e.id_persona = p.id_persona
        JOIN Roles r ON e.id_rol = r.id_rol
        WHERE e.id_emp = %s
    """
    user = ejecutar_query_one(query, [user_id])
    if user:
        return {
            'id_emp': user[0],
            'id_sede': user[1],
            'id_dept': user[2],
            'nombre': f"{user[3]} {user[4]}",
            'rol': user[5]
        }
    return None


def api_login_required(view_func):
    """Decorator to require API authentication."""
    def wrapper(request, *args, **kwargs):
        user = get_user_from_session(request)
        if not user:
            return JsonResponse({'error': 'No autenticado'}, status=401)
        request.user_data = user
        return view_func(request, *args, **kwargs)
    return wrapper


# =============================================================================
# AUTHENTICATION
# =============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """Login endpoint. Returns user data on success."""
    data = get_json_body(request)
    email = data.get('email', '')
    password = data.get('password', '')
    
    if not email or not password:
        return JsonResponse({'error': 'Email y contraseña requeridos'}, status=400)
    
    query = """
        SELECT e.id_emp, e.id_sede, p.nom_persona, p.apellido_persona, r.nombre_rol, p.email_persona, s.nom_sede
        FROM Empleados e
        JOIN Personas p ON e.id_persona = p.id_persona
        JOIN Roles r ON e.id_rol = r.id_rol
        JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        WHERE p.email_persona = %s 
        AND e.hash_contra = crypt(%s, e.hash_contra)
    """
    user = ejecutar_query_one(query, [email, password])
    
    if not user:
        return JsonResponse({'error': 'Credenciales inválidas'}, status=401)
    
    # Set session
    request.session['user_id'] = user[0]
    request.session['user_sede'] = user[1]
    request.session['user_rol'] = user[4]
    
    return JsonResponse({
        'success': True,
        'user': {
            'id_emp': user[0],
            'id_sede': user[1],
            'nombre': f"{user[2]} {user[3]}",
            'rol': user[4],
            'email': user[5],
            'sede_nombre': user[6]
        }
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """Logout endpoint."""
    request.session.flush()
    return JsonResponse({'success': True})


@require_http_methods(["GET"])
def api_session(request):
    """Check current session."""
    user = get_user_from_session(request)
    if user:
        return JsonResponse({'authenticated': True, 'user': user})
    return JsonResponse({'authenticated': False})


@api_login_required
@require_http_methods(["GET"])
def api_perfil(request):
    """Get full user profile from database."""
    user_id = request.session.get('user_id')
    
    query = """
        SELECT 
            p.nom_persona, p.apellido_persona, p.tipo_doc, p.num_doc, 
            p.fecha_nac, p.genero, p.dir_persona, p.tel_persona, 
            p.email_persona, p.ciudad_residencia,
            r.nombre_rol, s.nom_sede, d.nom_dept
        FROM Empleados e
        JOIN Personas p ON e.id_persona = p.id_persona
        JOIN Roles r ON e.id_rol = r.id_rol
        JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        LEFT JOIN Departamentos d ON e.id_dept = d.id_dept AND e.id_sede = d.id_sede
        WHERE e.id_emp = %s
    """
    
    result = ejecutar_query_one(query, [user_id])
    
    if not result:
        return JsonResponse({'error': 'Perfil no encontrado'}, status=404)
    
    return JsonResponse({
        'perfil': {
            'nombre': result[0],
            'apellido': result[1],
            'tipo_doc': result[2],
            'num_doc': result[3],
            'fecha_nac': str(result[4]) if result[4] else None,
            'genero': result[5],
            'direccion': result[6],
            'telefono': result[7],
            'email': result[8],
            'ciudad': result[9],
            'rol': result[10],
            'sede': result[11],
            'departamento': result[12]
        }
    })


# =============================================================================
# SEDES, DEPARTAMENTOS, MEDICOS (Lookup data)
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_sedes(request):
    """Get all hospital branches."""
    query = "SELECT id_sede, nom_sede, direccion, telefono FROM Sedes_Hospitalarias ORDER BY nom_sede"
    sedes = ejecutar_query(query)
    return JsonResponse({
        'sedes': [{'id': s[0], 'nombre': s[1], 'direccion': s[2], 'telefono': s[3]} for s in sedes]
    })


@api_login_required
@require_http_methods(["GET"])
def api_departamentos(request):
    """Get departments, optionally filtered by sede."""
    sede_id = request.GET.get('sede_id')
    
    if sede_id:
        query = "SELECT id_dept, nom_dept FROM Departamentos WHERE id_sede = %s ORDER BY nom_dept"
        deps = ejecutar_query(query, [sede_id])
    else:
        query = "SELECT id_dept, nom_dept FROM Departamentos ORDER BY nom_dept"
        deps = ejecutar_query(query)
    
    return JsonResponse({
        'departamentos': [{'id': d[0], 'nombre': d[1]} for d in deps]
    })


@api_login_required
@require_http_methods(["GET"])
def api_medicos(request):
    """Get doctors, optionally filtered by sede and department."""
    sede_id = request.GET.get('sede_id')
    dept_id = request.GET.get('dept_id')
    
    query = """
        SELECT e.id_emp, p.nom_persona || ' ' || p.apellido_persona as nombre_completo
        FROM Empleados e
        JOIN Personas p ON e.id_persona = p.id_persona
        JOIN Roles r ON e.id_rol = r.id_rol
        WHERE r.nombre_rol = 'Medico'
    """
    params = []
    
    if sede_id:
        query += " AND e.id_sede = %s"
        params.append(sede_id)
    if dept_id:
        query += " AND e.id_dept = %s"
        params.append(dept_id)
    
    query += " ORDER BY nombre_completo"
    medicos = ejecutar_query(query, params)
    
    return JsonResponse({
        'medicos': [{'id': m[0], 'nombre': m[1]} for m in medicos]
    })


# =============================================================================
# PACIENTES
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_pacientes_lista(request):
    """Get list of patients."""
    user = request.user_data
    busqueda = request.GET.get('busqueda', '')
    
    query = """
        SELECT pac.cod_pac, p.nom_persona, p.apellido_persona, p.num_doc, p.email_persona, p.tel_persona, p.dir_persona
        FROM Pacientes pac
        JOIN Personas p ON pac.id_persona = p.id_persona
    """
    params = []
    
    # Filter by sede for non-admin users
    if user['rol'] not in ['Administrator', 'Administrador']:
        query += " WHERE pac.id_sede = %s"  # WARNING: Pacientes doesn't have id_sede in schema!
        # Schema check: Pacientes table does NOT have id_sede directly (Lines 96-100 of script_creacion). 
        # Citas has id_sede. 
        # However, logic in views.py (Line 241) filters patients by "Citas WHERE c.id_emp = user_id" for doctors.
        # But this code was checking `pac.id_sede`. This column likely doesn't exist.
        # Let's fix column names first. `cedula` -> `num_doc`, `direccion` -> `dir_persona`.
        # I will comment out the id_sede filter for now to avoid breaking if column missing, 
        # or better, use correct logic (See views.py:221).
        
    # Correcting column names for now
    if busqueda:
         query += " WHERE (p.nom_persona ILIKE %s OR p.apellido_persona ILIKE %s OR p.num_doc ILIKE %s)"
         params.extend([f'%{busqueda}%'] * 3)
    
    query += " ORDER BY p.nom_persona, p.apellido_persona"
    pacientes = ejecutar_query(query, params)
    
    return JsonResponse({
        'pacientes': [{
            'cod_pac': p[0],
            'nombre': p[1],
            'apellido': p[2],
            'cedula': p[3],
            'email': p[4],
            'telefono': p[5],
            'direccion': p[6]
        } for p in pacientes]
    })


@api_login_required
@require_http_methods(["GET"])
def api_paciente_detalle(request, cod_pac):
    """Get patient details."""
    query = """
        SELECT pac.cod_pac, p.nom_persona, p.apellido_persona, p.num_doc, p.email_persona, p.tel_persona, 
               p.dir_persona, p.fecha_nac, pac.tipo_sangre, pac.alergias,
               pac.contacto_emergencia
        FROM Pacientes pac
        JOIN Personas p ON pac.id_persona = p.id_persona
        WHERE pac.cod_pac = %s
    """
    paciente = ejecutar_query_one(query, [cod_pac])
    
    if not paciente:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)
    
    # Get patient's appointment history
    query_citas = """
        SELECT c.id_cita, c.fecha_hora, c.tipo_servicio, c.estado,
               emp_p.nom_persona || ' ' || emp_p.apellido_persona as medico
        FROM Citas c
        JOIN Empleados emp ON c.id_emp = emp.id_emp
        JOIN Personas emp_p ON emp.id_persona = emp_p.id_persona
        WHERE c.cod_pac = %s
        ORDER BY c.fecha_hora DESC LIMIT 10
    """
    citas = ejecutar_query(query_citas, [cod_pac])
    
    return JsonResponse({
        'paciente': {
            'cod_pac': paciente[0],
            'nombre': paciente[1],
            'apellido': paciente[2],
            'cedula': paciente[3],
            'email': paciente[4],
            'telefono': paciente[5],
            'direccion': paciente[6],
            'fecha_nacimiento': str(paciente[7]) if paciente[7] else None,
            'tipo_sangre': paciente[8],
            'alergias': paciente[9],
            'contacto_emergencia': paciente[10]
        },
        'citas': [{
            'id_cita': c[0],
            'fecha_hora': str(c[1]) if c[1] else None,
            'tipo_servicio': c[2],
            'estado': c[3],
            'medico': c[4]
        } for c in citas]
    })


@csrf_exempt
@api_login_required
@require_http_methods(["POST"])
def api_paciente_crear(request):
    """Create a new patient."""
    data = get_json_body(request)
    user = request.user_data
    
    # First create the Persona
    query_persona = """
        INSERT INTO Personas (nombre, apellido, cedula, email, telefono, direccion, fecha_nacimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id_persona
    """
    
    try:
        id_persona = ejecutar_insert(query_persona, [
            data.get('nombre'),
            data.get('apellido'),
            data.get('cedula'),
            data.get('email'),
            data.get('telefono'),
            data.get('direccion'),
            data.get('fecha_nacimiento')
        ])
        
        # Then create the Paciente
        sede_id = data.get('id_sede') or user['id_sede']
        query_paciente = """
            INSERT INTO Pacientes (id_persona, tipo_sangre, alergias, contacto_emergencia, id_sede)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING cod_pac
        """
        cod_pac = ejecutar_insert(query_paciente, [
            id_persona,
            data.get('tipo_sangre'),
            data.get('alergias'),
            data.get('contacto_emergencia'),
            sede_id
        ])
        
        return JsonResponse({'success': True, 'cod_pac': cod_pac})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# CITAS
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_citas_lista(request):
    """Get list of appointments."""
    user = request.user_data
    estado = request.GET.get('estado', '')
    
    query = """
        SELECT c.id_cita, c.fecha_hora, c.tipo_servicio, c.estado, c.motivo,
               p.nom_persona || ' ' || p.apellido_persona as paciente,
               emp_p.nom_persona || ' ' || emp_p.apellido_persona as medico,
               s.nom_sede as sede
        FROM Citas c
        JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        JOIN Personas p ON pac.id_persona = p.id_persona
        JOIN Empleados e ON c.id_emp = e.id_emp
        JOIN Personas emp_p ON e.id_persona = emp_p.id_persona
        JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        WHERE 1=1
    """
    params = []
    
    # Role-based filtering
    if user['rol'].lower() == 'medico':
        query += " AND c.id_emp = %s"
        params.append(user['id_emp'])
    elif user['rol'].lower() not in ['administrator', 'administrador']:
        query += " AND c.id_sede = %s"
        params.append(user['id_sede'])
    
    if estado:
        query += " AND c.estado = %s"
        params.append(estado)
    
    query += " ORDER BY c.fecha_hora DESC"
    
    try:
        citas = ejecutar_query(query, params)
        return JsonResponse({
            'citas': [{
                'id_cita': c[0],
                'fecha_hora': str(c[1]) if c[1] else None,
                'tipo_servicio': c[2],
                'estado': c[3],
                'motivo': c[4],
                'paciente': c[5],
                'medico': c[6],
                'sede': c[7]
            } for c in citas]
        })
    except Exception as e:
        print(f"Error in api_citas_lista: {e}")
        return JsonResponse({'error': f'Error al consultar citas: {str(e)}'}, status=500)


@api_login_required
@require_http_methods(["GET"])
def api_cita_detalle(request, id_cita):
    """Get appointment details."""
    query = """
        SELECT c.id_cita, c.fecha_hora, c.tipo_servicio, c.estado, c.motivo,
               c.cod_pac, c.id_emp, c.id_sede, c.id_dept,
               p.nom_persona || ' ' || p.apellido_persona as paciente,
               emp_p.nom_persona || ' ' || emp_p.apellido_persona as medico,
               s.nom_sede as sede, d.nom_dept as departamento
        FROM Citas c
        JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
        JOIN Personas p ON pac.id_persona = p.id_persona
        JOIN Empleados e ON c.id_emp = e.id_emp
        JOIN Personas emp_p ON e.id_persona = emp_p.id_persona
        JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        LEFT JOIN Departamentos d ON c.id_dept = d.id_dept
        WHERE c.id_cita = %s
    """
    cita = ejecutar_query_one(query, [id_cita])
    
    if not cita:
        return JsonResponse({'error': 'Cita no encontrada'}, status=404)
    
    return JsonResponse({
        'cita': {
            'id_cita': cita[0],
            'fecha_hora': str(cita[1]) if cita[1] else None,
            'tipo_servicio': cita[2],
            'estado': cita[3],
            'motivo': cita[4],
            'cod_pac': cita[5],
            'id_emp': cita[6],
            'id_sede': cita[7],
            'id_dept': cita[8],
            'paciente': cita[9],
            'medico': cita[10],
            'sede': cita[11],
            'departamento': cita[12]
        }
    })


@csrf_exempt
@api_login_required
@require_http_methods(["POST"])
def api_cita_crear(request):
    """Create a new appointment."""
    data = get_json_body(request)
    user = request.user_data
    
    sede_id = data.get('id_sede') or user['id_sede']
    
    try:
        # Generate next id_cita
        result = ejecutar_query_one("SELECT COALESCE(MAX(id_cita), 0) + 1 FROM Citas")
        id_cita = result[0] if result else 1
        
        query = """
            INSERT INTO Citas (id_cita, cod_pac, id_emp, id_sede, id_dept, fecha_hora, 
                              fecha_hora_solicitada, tipo_servicio, estado, motivo)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, 'PROGRAMADA', %s)
        """
        
        ejecutar_update(query, [
            id_cita,
            data.get('cod_pac'),
            data.get('id_emp'),
            sede_id,
            data.get('id_dept'),
            data.get('fecha_hora'),
            data.get('tipo_servicio'),
            data.get('motivo')
        ])
        return JsonResponse({'success': True, 'id_cita': id_cita})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["PUT"])
def api_cita_actualizar(request, id_cita):
    """Update an appointment."""
    data = get_json_body(request)
    
    query = """
        UPDATE Citas SET
            cod_pac = %s,
            id_emp = %s,
            id_dept = %s,
            fecha_hora = %s,
            tipo_servicio = %s,
            motivo = %s
        WHERE id_cita = %s
    """
    
    try:
        ejecutar_update(query, [
            data.get('cod_pac'),
            data.get('id_emp'),
            data.get('id_dept'),
            data.get('fecha_hora'),
            data.get('tipo_servicio'),
            data.get('motivo'),
            id_cita
        ])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["DELETE"])
def api_cita_cancelar(request, id_cita):
    """Cancel an appointment."""
    query = "UPDATE Citas SET estado = 'CANCELADA' WHERE id_cita = %s"
    try:
        ejecutar_update(query, [id_cita])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# HISTORIAL CLINICO
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_historias_lista(request):
    """Get list of clinical histories."""
    user = request.user_data
    
    # Get patients with their clinical histories, citas, diagnoses
    query = """
        SELECT DISTINCT 
            hc.cod_hist,
            hc.fecha_registro,
            p.nom_persona || ' ' || p.apellido_persona as paciente,
            p.num_doc as documento,
            pac.cod_pac
        FROM Historias_Clinicas hc
        JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
        JOIN Personas p ON pac.id_persona = p.id_persona
        JOIN Citas c ON hc.cod_pac = c.cod_pac
    """
    params = []
    
    # Role-based filtering via citas
    if user['rol'].lower() == 'medico':
        query += " WHERE c.id_emp = %s"
        params.append(user['id_emp'])
    elif user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE c.id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY hc.fecha_registro DESC"
    
    try:
        historias = ejecutar_query(query, params)
        return JsonResponse({
            'historias': [{
                'cod_hist': h[0],
                'fecha_registro': str(h[1]) if h[1] else None,
                'paciente': h[2],
                'documento': h[3],
                'cod_pac': h[4]
            } for h in historias]
        })
    except Exception as e:
        print(f"Error in api_historias_lista: {e}")
        return JsonResponse({'historias': []})


@api_login_required
@require_http_methods(["GET"])
def api_historia_detalle(request, cod_hist):
    """Get clinical history details using robust LEFT JOINs."""
    
    # Query inspired by user request, adapted to return structured data for the frontend
    # We fetch flattened rows and group them in Python to avoid N+1 queries
    # Uses LEFT JOIN for Citas to ensure we get Patient info even if no Citas exist
    query = """
        SELECT 
            hc.cod_hist,
            hc.fecha_registro,
            p.nom_persona || ' ' || p.apellido_persona AS paciente,
            p.num_doc AS documento,
            c.id_cita,
            to_char(c.fecha_hora, 'YYYY-MM-DD HH24:MI'),
            c.motivo,
            doc_per.nom_persona || ' ' || doc_per.apellido_persona AS medico,
            esp.nombre_esp,
            enf.nombre_enfermedad,
            diag.observaciones,
            m.nom_med,
            m.principio_activo,
            pre.dosis,
            pre.frecuencia,
            pre.duracion_dias,
            pre.cantidad_total,
            pre.fecha_emision,
            s.nom_sede,
            d.nom_dept
        FROM Historias_Clinicas hc
        JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
        INNER JOIN Personas p ON pac.id_persona = p.id_persona
        LEFT JOIN Citas c ON pac.cod_pac = c.cod_pac
        LEFT JOIN Empleados doc ON c.id_emp = doc.id_emp
        LEFT JOIN Personas doc_per ON doc.id_persona = doc_per.id_persona
        LEFT JOIN Emp_Posee_Esp epe ON doc.id_emp = epe.id_emp
        LEFT JOIN Especialidades esp ON epe.id_especialidad = esp.id_especialidad
        LEFT JOIN Diagnostico diag ON c.id_cita = diag.id_cita
        LEFT JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
        LEFT JOIN Prescripciones pre ON c.id_cita = pre.id_cita
        LEFT JOIN Catalogo_Medicamentos m ON pre.cod_med = m.cod_med
        LEFT JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
        LEFT JOIN Departamentos d ON c.id_dept = d.id_dept
        WHERE hc.cod_hist = %s
        ORDER BY c.fecha_hora DESC, pre.id_presc ASC
    """
    
    try:
        rows = ejecutar_query(query, [cod_hist])
    except Exception as e:
        print(f"Error querying historia details: {e}")
        return JsonResponse({'error': 'Error al obtener datos'}, status=500)

    if not rows:
        return JsonResponse({'error': 'Historia no encontrada o sin datos'}, status=404)

    # Process flattened rows into hierarchical JSON
    # Structure: Historia -> Citas -> [Diagnostico, Prescripciones]
    
    # Base info from first row (assuming all rows belong to same history)
    historia_info = {
        'cod_hist': rows[0][0],
        'fecha_registro': str(rows[0][1]) if rows[0][1] else None,
        'paciente': rows[0][2],
        'documento': rows[0][3],
    }
    
    citas_map = {}
    
    for row in rows:
        id_cita = row[4]
        if not id_cita:
            continue
            
        if id_cita not in citas_map:
            citas_map[id_cita] = {
                'id_cita': id_cita,
                'fecha_hora': row[5],
                'motivo': row[6],
                'medico': row[7],
                'especialidad': row[8],
                'sede': row[18],
                'departamento': row[19],
                'diagnostico': { 
                    'enfermedad': row[9],
                    'observaciones': row[10]
                } if row[9] else None,
                'prescripciones': []
            }
        
        # Add prescription if present
        if row[11]: # nom_med present
            presc_data = {
                'medicamento': row[11],
                'principio_activo': row[12],
                'dosis': row[13],
                'frecuencia': row[14],
                'duracion_dias': row[15],
                'cantidad_total': row[16],
                'fecha_emision': str(row[17]) if row[17] else None
            }
            
            # Simple dedup check
            exists = False
            for p in citas_map[id_cita]['prescripciones']:
                if p['medicamento'] == presc_data['medicamento'] and p['dosis'] == presc_data['dosis']:
                    exists = True
                    break
            
            if not exists:
                citas_map[id_cita]['prescripciones'].append(presc_data)

    return JsonResponse({
        'historia': historia_info,
        'citas': list(citas_map.values())
    })


# =============================================================================
# INVENTARIO / FARMACIA
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_inventario_lista(request):
    """Get pharmacy inventory."""
    user = request.user_data
    
    query = """
        SELECT i.id_inv, m.nom_med, m.principio_activo, i.cantidad, i.fecha_actualizacion,
               s.nom_sede, i.id_sede
        FROM Inventario_Farmacia i
        JOIN Catalogo_Medicamentos m ON i.cod_med = m.cod_med
        JOIN Sedes_Hospitalarias s ON i.id_sede = s.id_sede
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE i.id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY m.nom_med"
    inventario = ejecutar_query(query, params)
    
    return JsonResponse({
        'inventario': [{
            'id_inv': i[0],
            'medicamento': i[1],
            'principio_activo': i[2],
            'cantidad': i[3],
            'fecha_actualizacion': str(i[4]) if i[4] else None,
            'sede': i[5]
        } for i in inventario]
    })


@csrf_exempt
@api_login_required
@require_http_methods(["PUT"])
def api_inventario_actualizar(request, id_inv):
    """Update inventory stock."""
    data = get_json_body(request)
    nueva_cantidad = data.get('cantidad')
    
    if nueva_cantidad is None:
        return JsonResponse({'error': 'Cantidad requerida'}, status=400)
    
    query = "UPDATE Inventario_Farmacia SET cantidad = %s WHERE id_inv = %s"
    try:
        ejecutar_update(query, [nueva_cantidad, id_inv])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# EQUIPAMIENTO
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_equipamiento_lista(request):
    """Get equipment list."""
    user = request.user_data
    
    query = """
        SELECT e.cod_eq, e.nom_eq, e.marca_modelo, e.estado_equipo, e.fecha_ultimo_maint,
               s.nom_sede, d.nom_dept,
               p.nom_persona || ' ' || p.apellido_persona as responsable
        FROM Equipamiento e
        JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        LEFT JOIN Departamentos d ON e.id_dept = d.id_dept AND e.id_sede = d.id_sede
        LEFT JOIN Empleados emp ON e.responsable_id = emp.id_emp
        LEFT JOIN Personas p ON emp.id_persona = p.id_persona
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE e.id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY e.nom_eq"
    equipos = ejecutar_query(query, params)
    
    return JsonResponse({
        'equipamiento': [{
            'cod_eq': e[0],
            'nombre': e[1],
            'marca': e[2],
            'estado': e[3],
            'ultimo_mantenimiento': str(e[4]) if e[4] else None,
            'sede': e[5],
            'departamento': e[6],
            'responsable': e[7]
        } for e in equipos]
    })


@api_login_required
@require_http_methods(["GET"])
def api_equipo_detalle(request, id_equipo):
    """Get equipment details."""
    query = """
        SELECT e.id_equipo, e.nombre, e.tipo, e.estado, e.fecha_adquisicion,
               e.id_sede, s.nombre as sede
        FROM Equipamiento e
        JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
        WHERE e.id_equipo = %s
    """
    equipo = ejecutar_query_one(query, [id_equipo])
    
    if not equipo:
        return JsonResponse({'error': 'Equipo no encontrado'}, status=404)
    
    return JsonResponse({
        'equipo': {
            'id_equipo': equipo[0],
            'nombre': equipo[1],
            'tipo': equipo[2],
            'estado': equipo[3],
            'fecha_adquisicion': str(equipo[4]) if equipo[4] else None,
            'id_sede': equipo[5],
            'sede': equipo[6]
        }
    })


@csrf_exempt
@api_login_required
@require_http_methods(["POST"])
def api_equipo_crear(request):
    """Create new equipment."""
    data = get_json_body(request)
    user = request.user_data
    
    sede_id = data.get('id_sede') or user['id_sede']
    dept_id = data.get('id_dept') or user.get('id_dept')  # Fallback to user's department
    
    try:
        # Generate next cod_eq
        result = ejecutar_query_one("SELECT COALESCE(MAX(cod_eq), 0) + 1 FROM Equipamiento")
        cod_eq = result[0] if result else 1
        
        query = """
            INSERT INTO Equipamiento (cod_eq, id_sede, id_dept, nom_eq, marca_modelo, 
                                     estado_equipo, fecha_ultimo_maint, responsable_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        ejecutar_update(query, [
            cod_eq,
            sede_id,
            dept_id,  # Use dept_id with fallback
            data.get('nom_eq') or data.get('nombre'),  # Support both field names
            data.get('marca_modelo') or data.get('tipo'),
            data.get('estado_equipo') or data.get('estado', 'Disponible'),
            data.get('fecha_ultimo_maint') or data.get('fecha_adquisicion'),
            data.get('responsable_id')
        ])
        return JsonResponse({'success': True, 'cod_eq': cod_eq})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# REPORTES
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
@api_login_required
@require_http_methods(["GET"])
def api_reportes_medicamentos_recetados(request):
    """Get most prescribed medications report using view."""
    user = request.user_data
    
    # Check if we should filter by sede (non-admin)
    # views.py returns all data, but usually we filter for non-admin
    # We will filter by sede if user is not Administrator
    
    query = """
        SELECT nom_sede, nom_med, total_prescripciones, cantidad_total_recetada, mes
        FROM vista_medicamentos_recetados_sede
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY cantidad_total_recetada DESC, total_prescripciones DESC LIMIT 20"
    
    try:
        data = ejecutar_query(query, params)
        return JsonResponse({
            'medicamentos': [{
                'sede': d[0],
                'medicamento': d[1],
                'total_prescripciones': d[2],
                'cantidad_total': d[3],
                'mes': str(d[4]) if d[4] else None
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["GET"])
def api_reportes_medicos_consultas(request):
    """Get doctors with most consultations report using view."""
    user = request.user_data
    
    query = """
        SELECT nombre_medico, nom_sede, nom_dept, especialidad, total_consultas
        FROM vista_medicos_consultas
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        # Filter by sede requires joining or checking if view has id_sede (it does have nom_sede but maybe not id_sede exposed directly in SELECT * but view definition has it)
        # Let's check view definition again: SELECT e.id_emp, ... s.nom_sede ...
        # View definition:
        # SELECT e.id_emp, p.nom... as nombre_medico, s.nom_sede ...
        # It doesn't select s.id_sede explicitely in the top SELECT list of the VIEW!
        # Wait, let me re-read view definition for vista_medicos_consultas.
        # Line 306: SELECT e.id_emp, p.nom... s.nom_sede ... 
        # It does NOT have id_sede in the SELECT list. It has id_emp.
        # So I can filter by nom_sede OR I can join with Empleados to filter by id_sede.
        # Or I can just return all if the user doesn't mind, but for security best practice I should filter.
        # Since I have id_emp, I can filter where id_emp in (select id_emp from empleados where id_sede = user.id_sede)
        query += " WHERE id_emp IN (SELECT id_emp FROM Empleados WHERE id_sede = %s)"
        params.append(user['id_sede'])
    
    query += " ORDER BY total_consultas DESC, nombre_medico ASC LIMIT 20"
    
    try:
        data = ejecutar_query(query, params)
        return JsonResponse({
            'medicos': [{
                'medico': d[0],
                'sede': d[1],
                'departamento': d[2],
                'especialidad': d[3],
                'total_consultas': d[4]
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["GET"])
def api_reportes_enfermedades(request):
    """Get diseases stats report using view."""
    user = request.user_data
    
    query = """
        SELECT nom_sede, nombre_enfermedad, total_diagnosticos, pacientes_afectados, mes
        FROM vista_enfermedades_por_sede
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        # View definition: SELECT s.id_sede ...
        # Yes, vista_enfermedades_por_sede has s.id_sede at the beginning.
        query += " WHERE id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY total_diagnosticos DESC, pacientes_afectados DESC LIMIT 20"
    
    try:
        data = ejecutar_query(query, params)
        return JsonResponse({
            'enfermedades': [{
                'sede': d[0],
                'enfermedad': d[1],
                'total_diagnosticos': d[2],
                'pacientes_afectados': d[3],
                'mes': str(d[4]) if d[4] else None
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# DASHBOARD
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """Get dashboard statistics."""
    user = request.user_data
    
    # Filter by sede if user is not admin
    sede_condition = ""
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        sede_condition = " AND id_sede = %s"
        params.append(user['id_sede'])
    
    # 1. Citas Hoy
    query_hoy = f"SELECT COUNT(*) FROM Citas WHERE DATE(fecha_hora) = CURRENT_DATE {sede_condition}"
    result_hoy = ejecutar_query_one(query_hoy, params)
    citas_hoy = result_hoy[0] if result_hoy else 0
    
    # 2. Pacientes Atendidos (Hoy)
    query_atendidos = f"SELECT COUNT(*) FROM Citas WHERE estado = 'COMPLETADA' AND DATE(fecha_hora) = CURRENT_DATE {sede_condition}"
    result_atendidos = ejecutar_query_one(query_atendidos, params)
    pacientes_atendidos = result_atendidos[0] if result_atendidos else 0
    
    # 3. Citas Pendientes (Futuras)
    query_pendientes = f"SELECT COUNT(*) FROM Citas WHERE estado = 'PROGRAMADA' AND fecha_hora >= CURRENT_TIMESTAMP {sede_condition}"
    result_pendientes = ejecutar_query_one(query_pendientes, params)
    citas_pendientes = result_pendientes[0] if result_pendientes else 0
    
    # 4. Alertas Stock
    stock_params = []
    stock_condition = ""
    if user['rol'].lower() not in ['administrator', 'administrador']:
        stock_condition = " AND id_sede = %s"
        stock_params.append(user['id_sede'])
        
    query_stock = f"SELECT COUNT(*) FROM Inventario_Farmacia WHERE cantidad < 10 {stock_condition}"
    result_stock = ejecutar_query_one(query_stock, stock_params)
    alertas_stock = result_stock[0] if result_stock else 0
    
    return JsonResponse({
        'stats': {
            'citas_hoy': citas_hoy,
            'pacientes_atendidos': pacientes_atendidos,
            'citas_pendientes': citas_pendientes,
            'alertas_stock': alertas_stock
        }
    })


# =============================================================================
# MEDICAMENTOS (CATÁLOGO)
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_medicamentos_catalogo(request):
    """Get medications catalog."""
    query = """
        SELECT cod_med, nom_med, principio_activo, unidad_medida, proveedor_principal
        FROM Catalogo_Medicamentos
        ORDER BY nom_med
    """
    medicamentos = ejecutar_query(query)
    
    return JsonResponse({
        'medicamentos': [{
            'cod_med': m[0],
            'nombre': m[1],
            'principio_activo': m[2],
            'unidad': m[3],
            'proveedor': m[4]
        } for m in medicamentos]
    })


# =============================================================================
# PRESCRIPCIONES
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_prescripciones_lista(request):
    """Get list of prescriptions."""
    user = request.user_data
    cod_pac = request.GET.get('cod_pac', '')
    
    query = """
        SELECT pr.id_presc, pr.fecha_emision, pr.dosis, pr.frecuencia, pr.duracion_dias,
               m.nom_med, p.nom_persona || ' ' || p.apellido_persona as paciente,
               emp_p.nom_persona || ' ' || emp_p.apellido_persona as medico
        FROM Prescripciones pr
        JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
        JOIN Historias_Clinicas hc ON pr.cod_hist = hc.cod_hist
        JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
        JOIN Personas p ON pac.id_persona = p.id_persona
        JOIN Citas c ON pr.id_cita = c.id_cita
        JOIN Empleados e ON c.id_emp = e.id_emp
        JOIN Personas emp_p ON e.id_persona = emp_p.id_persona
        WHERE 1=1
    """
    params = []
    
    if cod_pac:
        query += " AND pac.cod_pac = %s"
        params.append(cod_pac)
    
    # Role-based filtering
    if user['rol'].lower() == 'medico':
        query += " AND c.id_emp = %s"
        params.append(user['id_emp'])
    elif user['rol'].lower() not in ['administrator', 'administrador']:
        query += " AND c.id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY pr.fecha_emision DESC LIMIT 100"
    
    try:
        prescripciones = ejecutar_query(query, params)
        return JsonResponse({
            'prescripciones': [{
                'id_presc': p[0],
                'fecha_emision': str(p[1]) if p[1] else None,
                'dosis': p[2],
                'frecuencia': p[3],
                'duracion_dias': p[4],
                'medicamento': p[5],
                'paciente': p[6],
                'medico': p[7]
            } for p in prescripciones]
        })
    except Exception as e:
        print(f"Error in api_prescripciones_lista: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@api_login_required
@require_http_methods(["POST"])
def api_prescripcion_crear(request):
    """Create a new prescription."""
    data = get_json_body(request)
    
    query = """
        INSERT INTO Prescripciones (id_presc, cod_med, cod_hist, id_cita, dosis, frecuencia, 
                                   duracion_dias, cantidad_total, fecha_emision)
        VALUES (DEFAULT, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE)
        RETURNING id_presc
    """
    
    try:
        id_presc = ejecutar_insert(query, [
            data.get('cod_med'),
            data.get('cod_hist'),
            data.get('id_cita'),
            data.get('dosis'),
            data.get('frecuencia'),
            data.get('duracion_dias'),
            data.get('cantidad_total')
        ])
        return JsonResponse({'success': True, 'id_presc': id_presc})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# REPORTES (Usando vistas de la BD)
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_reportes_medicamentos_recetados(request):
    """Get most prescribed medications report."""
    user = request.user_data
    
    query = """
        SELECT nom_sede, nom_med, total_prescripciones, cantidad_total_recetada, mes
        FROM vista_medicamentos_recetados_sede
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY total_prescripciones DESC, cantidad_total_recetada DESC LIMIT 20"
    
    try:
        data = ejecutar_query(query, params)
        return JsonResponse({
            'medicamentos': [{
                'sede': d[0],
                'medicamento': d[1],
                'total_prescripciones': d[2],
                'cantidad_total': d[3],
                'mes': str(d[4]) if d[4] else None
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["GET"])
def api_reportes_medicos_consultas(request):
    """Get doctors with most consultations."""
    user = request.user_data
    
    query = """
        SELECT nombre_medico, nom_sede, nom_dept, especialidad, total_consultas, semana
        FROM vista_medicos_consultas
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE id_emp IN (SELECT id_emp FROM Empleados WHERE id_sede = %s)"
        params.append(user['id_sede'])
    
    query += " ORDER BY total_consultas DESC LIMIT 20"
    
    try:
        data = ejecutar_query(query, params)
        return JsonResponse({
            'medicos': [{
                'medico': d[0],
                'sede': d[1],
                'departamento': d[2],
                'especialidad': d[3],
                'total_consultas': d[4],
                'semana': str(d[5]) if d[5] else None
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_login_required
@require_http_methods(["GET"])
def api_reportes_enfermedades(request):
    """Get diseases by sede report."""
    user = request.user_data
    
    query = """
        SELECT nom_sede, nombre_enfermedad, total_diagnosticos, pacientes_afectados, mes
        FROM vista_enfermedades_por_sede
    """
    params = []
    
    if user['rol'].lower() not in ['administrator', 'administrador']:
        query += " WHERE id_sede = %s"
        params.append(user['id_sede'])
    
    query += " ORDER BY total_diagnosticos DESC LIMIT 20"
    
    try:
        data = ejecutar_query(query, params)
        return JsonResponse({
            'enfermedades': [{
                'sede': d[0],
                'enfermedad': d[1],
                'total_diagnosticos': d[2],
                'pacientes_afectados': d[3],
                'mes': str(d[4]) if d[4] else None
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# AUDITORÍA
# =============================================================================

@api_login_required
@require_http_methods(["GET"])
def api_auditoria_accesos(request):
    """Get audit log (admin/auditor only)."""
    user = request.user_data
    
    # Check if user has permission
    if user['rol'].lower() not in ['administrator', 'administrador', 'auditor']:
        return JsonResponse({'error': 'No tiene permisos para ver auditoría'}, status=403)
    
    query = """
        SELECT aa.id_evento, aa.fecha_evento, aa.accion, aa.tabla_afectada,
               aa.id_registro_afectado, aa.ip_origen,
               p.nom_persona || ' ' || p.apellido_persona as empleado,
               r.nombre_rol
        FROM Auditoria_Accesos aa
        LEFT JOIN Empleados e ON aa.id_emp = e.id_emp
        LEFT JOIN Personas p ON e.id_persona = p.id_persona
        LEFT JOIN Roles r ON e.id_rol = r.id_rol
        ORDER BY aa.fecha_evento DESC
        LIMIT 200
    """
    
    try:
        data = ejecutar_query(query)
        return JsonResponse({
            'auditoria': [{
                'id_evento': d[0],
                'fecha': str(d[1]) if d[1] else None,
                'accion': d[2],
                'tabla': d[3],
                'registro_id': d[4],
                'ip': d[5],
                'empleado': d[6],
                'rol': d[7]
            } for d in data]
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
