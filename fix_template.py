content = r'''{% extends 'main.html' %}
{% load static %}

{% block content %}
<div class="container-fluid">
    <!-- Header -->
    <div class="row py-3" style="background-color: #84407b;">
        <div class="col-md-6">
            <a href="{% url 'hospital:dashboard' %}" class="text-white text-decoration-none"
                style="font-family: 'Pixelify Sans'; font-size: 1.5rem;">
                <i class="bi bi-hospital"></i> HIS+ | Programar Cita
            </a>
        </div>
        <div class="col-md-6 text-end">
            <a href="{% url 'hospital:lista_citas' %}" class="exit"><i class="bi bi-arrow-left"></i> Citas</a>
            <a href="{% url 'hospital:logout' %}" class="exit ms-3"><i class="bi bi-box-arrow-right"></i> Salir</a>
        </div>
    </div>

    {% if messages %}
    <div class="row mt-2">
        <div class="col-12">
            {% for message in messages %}
            <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
                {{ message }}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <div class="row mt-4 justify-content-center">
        <div class="col-md-8">
            <div class="identification">
                <h4 class="title"><i class="bi bi-calendar-plus"></i> Programar Nueva Cita</h4>

                <form method="post" class="mt-4">
                    {% csrf_token %}
                    <div class="row">
                        <div class="col-md-12 mb-3">
                            <label class="title">Sede</label>
                            {{ form.id_sede_field }}
                        </div>
                        <div class="col-md-12 mb-3">
                            <label class="title">Paciente</label>
                            <select name="cod_pac" class="form-select" required>
                                <option value="">Seleccione un paciente</option>
                                {% for choice in form.cod_pac.field.widget.choices %}
                                <option value="{{ choice.0 }}" {% if form.cod_pac.value|stringformat:"s" == choice.0|stringformat:"s" %}selected{% endif %}>{{ choice.1 }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="title">Departamento</label>
                            <select name="id_dept" class="form-select" id="id_dept_select" required>
                                <option value="">Seleccione un departamento</option>
                                {% for choice in form.id_dept.field.widget.choices %}
                                <option value="{{ choice.0 }}" {% if form.id_dept.value|stringformat:"s" == choice.0|stringformat:"s" %}selected{% endif %}>{{ choice.1 }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="title">Medico</label>
                            <select name="id_emp" class="form-select" id="id_emp_select" required>
                                <option value="">Seleccione un medico</option>
                                {% for choice in form.id_emp.field.widget.choices %}
                                <option value="{{ choice.0 }}" {% if form.id_emp.value|stringformat:"s" == choice.0|stringformat:"s" %}selected{% endif %}>{{ choice.1 }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="title">Fecha y Hora</label>
                            <input type="datetime-local" name="fecha_hora" class="form-control"
                                value="{{ form.fecha_hora.value|default:'' }}" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label class="title">Tipo de Servicio</label>
                            <select name="tipo_servicio" class="form-select" required>
                                <option value="Consulta" {% if form.tipo_servicio.value == "Consulta" %}selected{% endif %}>Consulta</option>
                                <option value="Urgencia" {% if form.tipo_servicio.value == "Urgencia" %}selected{% endif %}>Urgencia</option>
                                <option value="Control" {% if form.tipo_servicio.value == "Control" %}selected{% endif %}>Control</option>
                                <option value="Especialidad" {% if form.tipo_servicio.value == "Especialidad" %}selected{% endif %}>Especialidad</option>
                            </select>
                        </div>
                        <div class="col-md-12 mb-3">
                            <label class="title">Motivo de la Consulta</label>
                            <textarea name="motivo" class="form-control" rows="3" required>{{ form.motivo.value|default:'' }}</textarea>
                        </div>
                        <input type="hidden" name="estado" value="PROGRAMADA">
                    </div>
                    <button type="submit" class="btn btn-primary mt-3">
                        <i class="bi bi-check-circle"></i> Programar Cita
                    </button>
                    <a href="{% url 'hospital:lista_citas' %}" class="btn btn-secondary mt-3">Cancelar</a>
                </form>
            </div>
        </div>
    </div>
</div>

<script>
    document.addEventListener('DOMContentLoaded', function () {
        const sedeSelect = document.getElementById('id_sede_select');
        const deptSelect = document.getElementById('id_dept_select');
        const medSelect = document.getElementById('id_emp_select');

        if (sedeSelect && !sedeSelect.disabled) {
            sedeSelect.addEventListener('change', function () {
                const sedeId = this.value;
                deptSelect.innerHTML = '<option value="">Cargando...</option>';
                medSelect.innerHTML = '<option value="">Seleccione un departamento primero</option>';

                if (sedeId) {
                    fetch("{% url 'hospital:api_obtener_departamentos' %}?sede_id=" + sedeId)
                        .then(response => response.json())
                        .then(data => {
                            deptSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
                            data.departamentos.forEach(dept => {
                                deptSelect.innerHTML += '<option value="' + dept.id + '">' + dept.nombre + '</option>';
                            });
                        });
                } else {
                    deptSelect.innerHTML = '<option value="">Seleccione una sede primero</option>';
                }
            });
        }

        if (deptSelect) {
            deptSelect.addEventListener('change', function () {
                const deptId = this.value;
                let sedeId = sedeSelect ? sedeSelect.value : null;
                medSelect.innerHTML = '<option value="">Cargando...</option>';

                if (sedeId && deptId) {
                    fetch("{% url 'hospital:api_obtener_medicos_por_dept' %}?sede_id=" + sedeId + "&dept_id=" + deptId)
                        .then(response => response.json())
                        .then(data => {
                            medSelect.innerHTML = '<option value="">Seleccione un medico</option>';
                            data.medicos.forEach(med => {
                                medSelect.innerHTML += '<option value="' + med.id + '">' + med.nombre + '</option>';
                            });
                        });
                } else {
                    medSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
                }
            });
        }
    });
</script>
{% endblock content %}
'''

with open(r'c:\Users\ediso\Desktop\Bases de Datos\Proyecto-Bases-De-Datos-\hospital_manager\hospital_manager\cashier\templates\cashier\programar_cita.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Template written successfully!')
