document.addEventListener('DOMContentLoaded', async function () {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';

    // Initial load
    await fetchPacientes();

    // Search
    document.getElementById('search-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = document.getElementById('search-input').value;
        await fetchPacientes(query);
    });

    // Create Form
    document.getElementById('create-paciente-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const pacienteData = {
            nom_persona: formData.get('nom_persona'),
            apellido_persona: formData.get('apellido_persona'),
            tipo_doc: formData.get('tipo_doc'),
            num_doc: formData.get('num_doc'),
            fecha_nac: formData.get('fecha_nac'),
            genero: formData.get('genero'),
            dir_persona: formData.get('dir_persona'),
            tel_persona: formData.get('tel_persona'),
            email_persona: formData.get('email_persona'),
            ciudad_residencia: formData.get('ciudad_residencia'),
            tipo_sangre: formData.get('tipo_sangre'),
            alergias: formData.get('alergias'),
            contacto_emergencia: formData.get('contacto_emergencia')
        };

        try {
            const response = await fetch(`${API_BASE}/pacientes/crear/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(pacienteData),
                credentials: 'include'
            });

            const data = await response.json();
            if (response.ok && data.success) {
                alert('Paciente registrado con éxito');
                showList();
                await fetchPacientes();
            } else {
                alert('Error: ' + (data.error || 'No se pudo registrar'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error de conexión');
        }
    });
});

async function fetchPacientes(busqueda = '') {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        let url = `${API_BASE}/pacientes/`;
        if (busqueda) {
            url += `?busqueda=${encodeURIComponent(busqueda)}`;
        }

        const response = await fetch(url, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderPacientes(data.pacientes);
        } else {
            console.error('Failed to fetch pacientes');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function renderPacientes(pacientes) {
    const tbody = document.getElementById('pacientes-table-body');
    tbody.innerHTML = '';

    if (!pacientes || pacientes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text text-center">No se encontraron pacientes</td></tr>';
        return;
    }

    pacientes.forEach(p => {
        const tr = document.createElement('tr');
        tr.className = 'text';
        tr.innerHTML = `
            <td>${p.cod_pac}</td>
            <td>${p.nombre} ${p.apellido}</td>
            <td>${p.cedula || '-'}</td>
            <td>${p.telefono || '-'}</td>
            <td>${p.email || '-'}</td>
            <td>
                <button onclick="showDetail(${p.cod_pac})" class="btn btn-sm btn-info"><i class="bi bi-eye"></i></button>
                <button onclick="showEdit(${p.cod_pac})" class="btn btn-sm btn-warning"><i class="bi bi-pencil"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function showList() {
    document.getElementById('create-view').classList.add('d-none');
    document.getElementById('detail-view').classList.add('d-none');
    document.getElementById('list-view').classList.remove('d-none');
}

function showCreate() {
    document.getElementById('list-view').classList.add('d-none');
    document.getElementById('detail-view').classList.add('d-none');
    document.getElementById('create-view').classList.remove('d-none');
}

async function showDetail(codPac) {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    document.getElementById('list-view').classList.add('d-none');
    document.getElementById('create-view').classList.add('d-none');
    document.getElementById('detail-view').classList.remove('d-none');

    try {
        const response = await fetch(`${API_BASE}/pacientes/${codPac}/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            const p = data.paciente;

            document.getElementById('detail-nombre').textContent = `${p.nombre} ${p.apellido}`;
            document.getElementById('detail-documento').textContent = p.cedula || '-';
            document.getElementById('detail-email').textContent = p.email || '-';
            document.getElementById('detail-telefono').textContent = p.telefono || '-';
            document.getElementById('detail-direccion').textContent = p.direccion || '-';

            // Load historial if available
            if (data.citas) {
                const histTbody = document.getElementById('historial-table-body');
                histTbody.innerHTML = '';
                data.citas.forEach(c => {
                    histTbody.innerHTML += `
                        <tr class="text">
                            <td>${c.id_cita}</td>
                            <td>${c.fecha_hora}</td>
                            <td>${c.tipo_servicio}</td>
                            <td>${c.estado}</td>
                            <td>${c.medico}</td>
                        </tr>
                    `;
                });
            }
        }
    } catch (error) {
        console.error('Error fetching patient details:', error);
    }
}

function showEdit(codPac) {
    alert('Función de edición en desarrollo');
}

window.showList = showList;
window.showCreate = showCreate;
window.showDetail = showDetail;
window.showEdit = showEdit;
window.fetchPacientes = fetchPacientes;
