document.addEventListener('DOMContentLoaded', async function () {
    await loadMedicamentos();
});

async function showView(viewName) {
    // Hide all views
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('d-none'));
    // Show selected view
    document.getElementById(viewName + '-view').classList.remove('d-none');

    // Update active nav link
    document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
    event.target.classList.add('active');

    // Load data for the view
    if (viewName === 'medicamentos' && !document.getElementById('medicamentos-view').dataset.loaded) {
        await loadMedicamentos();
    } else if (viewName === 'medicos' && !document.getElementById('medicos-view').dataset.loaded) {
        await loadMedicos();
    } else if (viewName === 'enfermedades' && !document.getElementById('enfermedades-view').dataset.loaded) {
        await loadEnfermedades();
    }
}

async function loadMedicamentos() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/reportes/medicamentos-recetados/`, { credentials: 'include' });
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'index.html';
                return;
            }
            throw new Error('Error al cargar reporte');
        }

        const data = await response.json();
        renderMedicamentos(data.medicamentos);
        document.getElementById('medicamentos-view').dataset.loaded = 'true';
    } catch (error) {
        console.error('Error loading medicamentos report:', error);
        document.getElementById('medicamentos-table-body').innerHTML =
            '<tr><td colspan="5" class="text-center text-danger">Error al cargar datos</td></tr>';
    }
}

function renderMedicamentos(medicamentos) {
    const tbody = document.getElementById('medicamentos-table-body');
    tbody.innerHTML = '';

    if (!medicamentos || medicamentos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text text-center">No hay datos disponibles</td></tr>';
        return;
    }

    medicamentos.forEach(m => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${m.sede || '-'}</td>
                <td>${m.medicamento || '-'}</td>
                <td>${m.total_prescripciones || 0}</td>
                <td>${m.cantidad_total || 0}</td>
                <td>${m.mes ? m.mes.substring(0, 7) : '-'}</td>
            </tr>
        `;
    });
}


async function loadMedicos() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/reportes/medicos-consultas/`, { credentials: 'include' });
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'index.html';
                return;
            }
            throw new Error('Error al cargar reporte');
        }

        const data = await response.json();
        renderMedicos(data.medicos);
        document.getElementById('medicos-view').dataset.loaded = 'true';
    } catch (error) {
        console.error('Error loading medicos report:', error);
        document.getElementById('medicos-table-body').innerHTML =
            '<tr><td colspan="5" class="text-center text-danger">Error al cargar datos</td></tr>';
    }
}

function renderMedicos(medicos) {
    const tbody = document.getElementById('medicos-table-body');
    tbody.innerHTML = '';

    if (!medicos || medicos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text text-center">No hay datos disponibles</td></tr>';
        return;
    }

    medicos.forEach(m => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${m.medico || '-'}</td>
                <td>${m.sede || '-'}</td>
                <td>${m.departamento || '-'}</td>
                <td>${m.especialidad || 'N/A'}</td>
                <td>${m.total_consultas || 0}</td>
            </tr>
        `;
    });
}


async function loadEnfermedades() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/reportes/enfermedades/`, { credentials: 'include' });
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'index.html';
                return;
            }
            throw new Error('Error al cargar reporte');
        }

        const data = await response.json();
        renderEnfermedades(data.enfermedades);
        document.getElementById('enfermedades-view').dataset.loaded = 'true';
    } catch (error) {
        console.error('Error loading enfermedades report:', error);
        document.getElementById('enfermedades-table-body').innerHTML =
            '<tr><td colspan="5" class="text-center text-danger">Error al cargar datos</td></tr>';
    }
}

function renderEnfermedades(enfermedades) {
    const tbody = document.getElementById('enfermedades-table-body');
    tbody.innerHTML = '';

    if (!enfermedades || enfermedades.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text text-center">No hay datos disponibles</td></tr>';
        return;
    }

    enfermedades.forEach(e => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${e.sede || '-'}</td>
                <td>${e.enfermedad || '-'}</td>
                <td>${e.total_diagnosticos || 0}</td>
                <td>${e.pacientes_afectados || 0}</td>
                <td>${e.mes ? e.mes.substring(0, 7) : '-'}</td>
            </tr>
        `;
    });
}

window.showView = showView;
