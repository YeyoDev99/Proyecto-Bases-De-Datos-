document.addEventListener('DOMContentLoaded', async function () {
    const sedeSelect = document.getElementById('id_sede_select');
    const deptSelect = document.getElementById('id_dept_select');
    const medSelect = document.getElementById('id_emp_select');
    const pacSelect = document.getElementById('cod_pac_select');

    const API_BASE = 'http://127.0.0.1:8000/api/v2';

    // Fetch Sedes
    async function fetchSedes() {
        try {
            const response = await fetch(`${API_BASE}/sedes/`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                sedeSelect.innerHTML = '<option value="">Seleccione una sede</option>';
                data.sedes.forEach(s => {
                    sedeSelect.add(new Option(s.nombre, s.id));
                });
            }
        } catch (error) {
            console.error('Error fetching sedes:', error);
        }
    }

    // Fetch Pacientes
    async function fetchPacientes() {
        try {
            const response = await fetch(`${API_BASE}/pacientes/`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                pacSelect.innerHTML = '<option value="">Seleccione un paciente</option>';
                data.pacientes.forEach(p => {
                    const nombre = `${p.nombre} ${p.apellido}`;
                    pacSelect.add(new Option(nombre, p.cod_pac));
                });
            }
        } catch (error) {
            console.error('Error fetching pacientes:', error);
        }
    }

    // Fetch Departamentos by Sede
    async function fetchDepartamentos(sedeId) {
        try {
            const response = await fetch(`${API_BASE}/departamentos/?sede_id=${sedeId}`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                deptSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
                data.departamentos.forEach(d => {
                    deptSelect.add(new Option(d.nombre, d.id));
                });
            }
        } catch (error) {
            console.error('Error fetching departamentos:', error);
        }
    }

    // Fetch Medicos by Sede and Department
    async function fetchMedicos(sedeId, deptId) {
        try {
            let url = `${API_BASE}/medicos/?sede_id=${sedeId}`;
            if (deptId) {
                url += `&dept_id=${deptId}`;
            }
            const response = await fetch(url, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                medSelect.innerHTML = '<option value="">Seleccione un médico</option>';
                data.medicos.forEach(m => {
                    medSelect.add(new Option(m.nombre, m.id));
                });
            }
        } catch (error) {
            console.error('Error fetching medicos:', error);
        }
    }

    // Initial Load
    await fetchSedes();
    await fetchPacientes();

    // Cascade Logic
    sedeSelect.addEventListener('change', async function () {
        const sedeId = this.value;
        deptSelect.innerHTML = '<option value="">Seleccione un departamento</option>';
        medSelect.innerHTML = '<option value="">Seleccione un departamento primero</option>';

        if (sedeId) {
            await fetchDepartamentos(sedeId);
        }
    });

    deptSelect.addEventListener('change', async function () {
        const sedeId = sedeSelect.value;
        const deptId = this.value;
        medSelect.innerHTML = '<option value="">Seleccione un médico</option>';

        if (sedeId && deptId) {
            await fetchMedicos(sedeId, deptId);
        }
    });

    // Form Submit
    document.getElementById('nueva-cita-form').addEventListener('submit', async function (e) {
        e.preventDefault();

        const formData = new FormData(this);
        const citaData = {
            cod_pac: formData.get('cod_pac'),
            id_emp: formData.get('id_emp'),
            id_sede: formData.get('id_sede'),
            id_dept: formData.get('id_dept'),
            fecha_hora: formData.get('fecha_hora'),
            tipo_servicio: formData.get('tipo_servicio'),
            motivo: formData.get('motivo')
        };

        try {
            const response = await fetch(`${API_BASE}/citas/crear/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(citaData),
                credentials: 'include'
            });

            const data = await response.json();
            if (response.ok && data.success) {
                alert('Cita programada exitosamente');
                window.location.href = 'lista_citas.html';
            } else {
                alert('Error: ' + (data.error || 'No se pudo crear la cita'));
            }
        } catch (error) {
            console.error('Error creating cita:', error);
            alert('Error de conexión al servidor');
        }
    });
});
