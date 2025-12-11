document.addEventListener('DOMContentLoaded', async function () {
    await loadPrescripciones();
});

async function loadPrescripciones() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/prescripciones/`, { credentials: 'include' });
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'index.html';
                return;
            }
            throw new Error('Error al cargar prescripciones');
        }

        const data = await response.json();
        renderPrescripciones(data.prescripciones);
    } catch (error) {
        console.error('Error loading prescripciones:', error);
        document.getElementById('prescripciones-table-body').innerHTML =
            '<tr><td colspan="7" class="text-center text-danger">Error al cargar datos</td></tr>';
    }
}

function renderPrescripciones(prescripciones) {
    const tbody = document.getElementById('prescripciones-table-body');
    tbody.innerHTML = '';

    if (!prescripciones || prescripciones.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text text-center">No hay prescripciones registradas</td></tr>';
        return;
    }

    prescripciones.forEach(p => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${p.fecha_emision || '-'}</td>
                <td>${p.paciente || '-'}</td>
                <td>${p.medico || '-'}</td>
                <td>${p.medicamento || '-'}</td>
                <td>${p.dosis || '-'}</td>
                <td>${p.frecuencia || '-'}</td>
                <td>${p.duracion_dias || '-'}</td>
            </tr>
        `;
    });
}
