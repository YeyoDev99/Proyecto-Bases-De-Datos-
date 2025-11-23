from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Count, Avg, F # Para analítica
from django.utils import timezone
from datetime import timedelta

from .models import *
from .forms import PersonaRegistrationForm, GestionCitasForm, HistoriaClinicaForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

# ==========================================================
# FUNCIONES AUXILIARES DE TESTEO DE ROLES
# ==========================================================

def es_medico(user):
    """ Verifica si el usuario autenticado tiene el rol de Médico """
    try:
        # Accede a la entidad Empleados a través de la relación OneToOneField 'persona'
        return user.empleados.id_rol.nombre_rol == 'Médico'
    except Empleados.DoesNotExist:
        return False
    except AttributeError:
        # Maneja el caso en que user no tenga el atributo 'empleados'
        return False

def es_administrador(user):
    """ Verifica si el usuario autenticado tiene el rol de Administrador """
    try:
        return user.empleados.id_rol.nombre_rol == 'Administrador'
    except Empleados.DoesNotExist:
        return False
    except AttributeError:
        return False

# ==========================================================
# 1. AUTENTICACIÓN Y FLUJO DE ACCESO
# ==========================================================

def index(request):
    """ Vista de inicio de sesión (Login) """
    if request.user.is_authenticated:
        return redirect('cashier:menu')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # 1. Autenticar usando el backend que usa 'email' como USERNAME_FIELD
        user = authenticate(request, email=email, password=password)
        
        if user is None:
            messages.error(request, "Correo electrónico o contraseña incorrectos.")
        else:
            try:
                # 2. Verificar que la Persona esté registrada como Empleado y activa
                empleado = Empleados.objects.get(persona=user)
                if not empleado.activo:
                    messages.error(request, "Su cuenta de empleado está inactiva. Contacte al administrador.")
                else:
                    # 3. Acceso exitoso
                    login(request, user)
                    return redirect('cashier:menu')
            except Empleados.DoesNotExist:
                messages.error(request, "El correo electrónico no corresponde a un empleado activo en el sistema.")
            except Exception as e:
                 messages.error(request, f"Ocurrió un error inesperado. {e}")
                
    context = {}
    return render(request, "cashier/index.html", context)


def sign_up(request):
    """ 
    Vista de registro de Empleados. 
    Idealmente, solo debería ser accesible por administradores o mediante un token.
    """
    if request.method == 'POST':
        form = PersonaRegistrationForm(request.POST)
        if form.is_valid():
            # El método save() del formulario ya crea la Persona y el Empleado asociado
            form.save()
            messages.success(request, "Empleado registrado exitosamente. Puede iniciar sesión.")
            return redirect('cashier:index')
        else:
            messages.error(request, "Hubo un error en el registro. Revise los datos.")
            context = {'form': form}
            return render(request, 'cashier/sign_up.html', context)
    
    # Restringir el acceso directo al formulario si no está autenticado como Admin
    if not request.user.is_authenticated or not es_administrador(request.user):
        messages.warning(request, "Esta función es solo para Administradores del sistema.")
        return redirect('cashier:index')
        
    form = PersonaRegistrationForm()
    context = {'form': form}
    return render(request, 'cashier/sign_up.html', context)


@login_required(login_url='cashier:index')
def menu(request):
    """ Menú principal del HIS+ """
    # Lógica para mostrar mensajes de estado, si los hay
    context = {}
    try:
        # Obtenemos el objeto Empleados para mostrar info de rol/departamento
        empleado = Empleados.objects.get(persona=request.user)
        # Aquí se podrían añadir chequeos de permisos o notificaciones
    except Empleados.DoesNotExist:
        messages.error(request, "Error de perfil: Su cuenta no tiene asignado un rol de empleado. Contacte a soporte.")
        logout(request)
        return redirect('cashier:index')
    
    return render(request, 'cashier/menu.html', context)


@login_required(login_url='cashier:index')
def logout_user(request):
    """ Cierra la sesión del usuario """
    logout(request)
    return redirect('cashier:index')


# ==========================================================
# 2. VISTAS DE GESTIÓN HOSPITALARIA (HIS+)
# ==========================================================

# --- Módulo Pacientes y Historias ---

@login_required(login_url='cashier:index')
def gestion_pacientes(request):
    """ 
    Permite buscar, listar y registrar nuevos pacientes.
    También es la puerta de entrada a la gestión de Historias Clínicas.
    """
    # Lógica de búsqueda de pacientes por num_doc o nombre
    query = request.GET.get('q')
    if query:
        pacientes = Pacientes.objects.filter(persona__num_doc__icontains=query) | \
                    Pacientes.objects.filter(persona__first_name__icontains=query) | \
                    Pacientes.objects.filter(persona__last_name__icontains=query)
        if not pacientes.exists():
             messages.info(request, f"No se encontraron pacientes para la búsqueda: '{query}'.")
    else:
        pacientes = Pacientes.objects.all() # Lista inicial, puede ser paginada
        
    # Aquí se manejaría el formulario de registro de un nuevo Paciente si se necesita
    
    context = {
        'pacientes': pacientes,
        'query': query
    }
    return render(request, 'cashier/gestion_pacientes.html', context)


@login_required(login_url='cashier:index')
def ver_historia(request, paciente_pk):
    """
    Muestra el historial de citas y diagnósticos de un paciente específico.
    """
    paciente = get_object_or_404(Pacientes, persona__pk=paciente_pk)
    # Obtenemos todas las citas realizadas del paciente
    citas_completadas = Citas.objects.filter(
        cod_pac=paciente,
        estado='REALIZADA'
    ).order_by('-fecha_hora')
    
    historias = Historias_Clinicas.objects.filter(id_cita__in=citas_completadas).select_related('id_cita__id_emp')

    context = {
        'paciente': paciente.persona, # Usamos el objeto Persona para obtener nombre, doc, etc.
        'historias': historias,
        'citas_completadas': citas_completadas
    }
    return render(request, 'cashier/ver_historia.html', context)

# --- Módulo Citas ---

@login_required(login_url='cashier:index')
def programar_citas(request):
    """
    Formulario para programar una nueva cita.
    """
    if request.method == 'POST':
        form = GestionCitasForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)
            # Podríamos añadir lógica de negocio aquí, ej: verificar disponibilidad del médico.
            cita.estado = 'PROGRAMADA'
            cita.save()
            messages.success(request, f"Cita programada exitosamente para {cita.cod_pac}.")
            return redirect('cashier:citas_pendientes')
        else:
            messages.error(request, "Error al programar la cita. Revise los datos.")
    else:
        form = GestionCitasForm()
        
    context = {'form': form}
    return render(request, 'cashier/programar_citas.html', context)


@login_required(login_url='cashier:index')
def citas_pendientes(request):
    """
    Lista las citas programadas. Para el médico, lista solo sus citas.
    """
    citas = Citas.objects.filter(estado='PROGRAMADA').select_related('cod_pac', 'id_emp')
    
    if es_medico(request.user):
        # Filtra las citas solo para el médico logueado
        try:
            empleado = Empleados.objects.get(persona=request.user)
            citas = citas.filter(id_emp=empleado)
        except Empleados.DoesNotExist:
            citas = Citas.objects.none()
            messages.error(request, "Perfil de médico no encontrado.")
            
    context = {'citas': citas}
    return render(request, 'cashier/citas_pendientes.html', context)


# --- Módulo Clínico / Diagnóstico ---

@login_required(login_url='cashier:index')
@user_passes_test(es_medico, login_url='cashier:menu', redirect_field_name=None)
def registrar_diagnostico(request, cita_pk):
    """
    Permite al médico registrar el diagnóstico y la historia clínica después de una cita.
    """
    cita = get_object_or_404(Citas, pk=cita_pk)
    
    # 1. Asegurarse de que el médico logueado sea el asignado a la cita
    if cita.id_emp.persona != request.user:
        messages.error(request, "No está autorizado para registrar el diagnóstico de esta cita.")
        return redirect('cashier:citas_pendientes')

    # Intentar obtener la historia clínica existente (si se edita) o crear una nueva
    try:
        historia = Historias_Clinicas.objects.get(id_cita=cita)
    except Historias_Clinicas.DoesNotExist:
        historia = Historias_Clinicas(id_cita=cita)
        
    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST, instance=historia)
        if form.is_valid():
            historia = form.save(commit=False)
            historia.id_cita = cita
            historia.save()
            
            # Actualizar el estado de la cita
            cita.estado = 'REALIZADA'
            cita.save()
            
            messages.success(request, "Diagnóstico y Historia Clínica registrados exitosamente.")
            return redirect('cashier:prescribir_medicamento', historia_pk=historia.pk)
        else:
            messages.error(request, "Error al registrar el diagnóstico.")
    else:
        form = HistoriaClinicaForm(instance=historia)
        
    context = {'form': form, 'cita': cita, 'paciente': cita.cod_pac.persona}
    return render(request, 'cashier/registrar_diagnostico.html', context)


@login_required(login_url='cashier:index')
@user_passes_test(es_medico, login_url='cashier:menu', redirect_field_name=None)
def prescribir_medicamento(request, historia_pk):
    """
    Permite al médico añadir prescripciones a una historia clínica.
    """
    historia = get_object_or_404(Historias_Clinicas, pk=historia_pk)
    
    # Aquí iría la lógica y el formulario para añadir Prescripciones
    
    messages.info(request, "Pendiente implementar el formulario de Prescripciones.")
    context = {'historia': historia}
    return render(request, 'cashier/prescribir_medicamento.html', context)


# --- Módulo Farmacia / Inventario ---

@login_required(login_url='cashier:index')
@user_passes_test(lambda u: es_administrador(u) or u.empleados.id_rol.nombre_rol == 'Farmacéutico', login_url='cashier:menu', redirect_field_name=None)
def gestion_farmacia(request):
    """
    Muestra el inventario de medicamentos por sede para Farmacéuticos y Admins.
    """
    inventario = Inventario_Farmacia.objects.all().select_related('id_sede', 'cod_med')
    
    # Lógica de filtrado por sede si el empleado tiene una sede asignada (ej. si no es Admin Central)
    
    context = {'inventario': inventario}
    messages.info(request, "Esta vista requiere el desarrollo de formularios de alta y edición de inventario.")
    return render(request, 'cashier/gestion_farmacia.html', context)


@login_required(login_url='cashier:index')
@user_passes_test(lambda u: es_administrador(u) or u.empleados.id_rol.nombre_rol == 'Farmacéutico', login_url='cashier:menu', redirect_field_name=None)
def actualizar_stock(request, inv_pk):
    """
    Permite a Farmacéuticos actualizar el stock de un medicamento.
    """
    # Lógica de actualización de Inventario_Farmacia
    messages.info(request, f"Vista para actualizar stock del inventario {inv_pk} (Implementación pendiente).")
    return redirect('cashier:gestion_farmacia')

# --- Módulo Reportes y Analítica (Consultas Requeridas) ---

@login_required(login_url='cashier:index')
@user_passes_test(lambda u: es_administrador(u) or es_medico(u), login_url='cashier:menu', redirect_field_name=None)
def reportes_analitica(request):
    """
    Vista principal de reportes y analítica.
    Implementa algunas de las consultas analíticas requeridas en el PDF.
    """
    # 1. Reporte: Total de Citas por Estado
    citas_por_estado = Citas.objects.values('estado').annotate(total=Count('estado')).order_by('-total')
    
    # 2. Reporte: Reportar el tiempo promedio entre la cita y el registro de diagnóstico (Consulta 3 del PDF)
    # Solo en citas realizadas
    tiempo_promedio = Historias_Clinicas.objects.filter(
        id_cita__estado='REALIZADA'
    ).annotate(
        diferencia=F('fecha_registro') - F('id_cita__fecha_hora')
    ).aggregate(
        tiempo_promedio_diag=Avg('diferencia')
    )
    
    # 3. Reporte: Médicos con mayor número de consultas atendidas por semana (Consulta 2 del PDF)
    hace_una_semana = timezone.now() - timedelta(days=7)
    medicos_top = Citas.objects.filter(
        estado='REALIZADA',
        fecha_hora__gte=hace_una_semana
    ).values(
        nombre=F('id_emp__persona__first_name'),
        apellido=F('id_emp__persona__last_name'),
        rol=F('id_emp__id_rol__nombre_rol')
    ).annotate(
        conteo=Count('id_cita')
    ).order_by('-conteo')[:5] # Top 5
    
    
    context = {
        'citas_por_estado': citas_por_estado,
        'tiempo_promedio': tiempo_promedio['tiempo_promedio_diag'],
        'medicos_top': medicos_top,
    }
    return render(request, 'cashier/reportes_analitica.html', context)


@login_required(login_url='cashier:index')
@user_passes_test(lambda u: es_administrador(u) or es_medico(u), login_url='cashier:menu', redirect_field_name=None)
def analitica_medicamentos(request):
    """
    Vista de analítica específica sobre uso de medicamentos.
    Implementa la consulta "Listar los medicamentos más recetados por sede en el último mes" (Consulta 1 del PDF).
    """
    hace_un_mes = timezone.now() - timedelta(days=30)
    
    medicamentos_top = Prescripciones.objects.filter(
        fecha_emision__gte=hace_un_mes
    ).values(
        medicamento=F('cod_med__nom_med'),
        sede=F('cod_hist__id_cita__id_dept__id_sede__nom_sede')
    ).annotate(
        total_recetas=Count('cod_med')
    ).order_by('sede', '-total_recetas')

    context = {
        'medicamentos_top': medicamentos_top
    }
    return render(request, 'cashier/analitica_medicamentos.html', context)


# --- Módulo Auditoría y Recursos ---

@login_required(login_url='cashier:index')
@user_passes_test(es_administrador, login_url='cashier:menu', redirect_field_name=None)
def auditoria_logs(request):
    """
    Muestra los logs de acceso y acciones del sistema (Consulta 4 del PDF).
    """
    # Implementa la consulta "Generar un informe de auditoría con los últimos 10 accesos a la tabla Historias_Clinicas."
    logs_historias = Auditoria_Accesos.objects.filter(
        tabla_afectada='Historias_Clinicas'
    ).select_related('id_emp__persona').order_by('-fecha_evento')[:10]
    
    context = {
        'logs_historias': logs_historias
    }
    return render(request, 'cashier/auditoria_logs.html', context)


@login_required(login_url='cashier:index')
@user_passes_test(es_administrador, login_url='cashier:menu', redirect_field_name=None)
def gestion_equipamiento(request):
    """
    Permite la gestión del equipamiento hospitalario.
    """
    equipos = Equipamiento.objects.all().select_related('id_dept__id_sede', 'responsable_id__persona')
    
    context = {
        'equipos': equipos
    }
    messages.info(request, "Pendiente implementar el formulario de gestión de equipamiento.")
    return render(request, 'cashier/gestion_equipamiento.html', context)