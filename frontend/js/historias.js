document.addEventListener('DOMContentLoaded', async function () {
    await loadHistorias();
});

async function loadHistorias() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/historias/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderHistorias(data.historias);
        } else {
            console.error('Failed to fetch historias');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function renderHistorias(historias) {
    const tbody = document.getElementById('historias-table-body');
    tbody.innerHTML = '';

    if (!historias || historias.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text text-center">No hay historias clínicas registradas</td></tr>';
        return;
    }

    historias.forEach(h => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${h.cod_hist}</td>
                <td>${h.paciente}</td>
                <td>${h.documento || '-'}</td>
                <td>${h.fecha_registro}</td>
                <td><button onclick="showDetail(${h.cod_hist})" class="btn btn-sm btn-info"><i class="bi bi-eye"></i></button></td>
            </tr>
        `;
    });
}

async function showDetail(codHist) {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    document.getElementById('list-view').classList.add('d-none');
    document.getElementById('detail-view').classList.remove('d-none');

    try {
        const response = await fetch(`${API_BASE}/historias/${codHist}/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            const h = data.historia;

            // Display patient info
            document.getElementById('detail-codigo').textContent = h.cod_hist;
            document.getElementById('detail-paciente').textContent = h.paciente || '-';
            document.getElementById('detail-doc').textContent = h.documento || '-';
            document.getElementById('detail-fecha').textContent = h.fecha_registro || '-';

            // Display first cita info if exists
            if (data.citas && data.citas.length > 0) {
                const firstCita = data.citas[0];
                document.getElementById('detail-cita').textContent = '#' + firstCita.id_cita;
                document.getElementById('detail-medico').textContent = firstCita.medico || '-';
                document.getElementById('detail-sede').textContent = firstCita.sede || '-';
                document.getElementById('detail-dept').textContent = firstCita.departamento || '-';

                // Display diagnosis from first cita
                if (firstCita.diagnostico) {
                    document.getElementById('detail-enfermedad').textContent = firstCita.diagnostico.enfermedad || '-';
                    document.getElementById('detail-observacion').textContent = firstCita.diagnostico.observaciones || '-';
                } else {
                    document.getElementById('detail-enfermedad').textContent = '-';
                    document.getElementById('detail-observacion').textContent = '-';
                }
            }

            // Render Citas table
            const citasBody = document.getElementById('citas-table-body');
            citasBody.innerHTML = '';

            if (data.citas && data.citas.length > 0) {
                data.citas.forEach(cita => {
                    // Concatenate prescriptions
                    let prescText = 'Ninguno';
                    if (cita.prescripciones && cita.prescripciones.length > 0) {
                        prescText = cita.prescripciones.map(p =>
                            `${p.medicamento} (${p.dosis})`
                        ).join(' || ');
                    }

                    // Get diagnosis
                    const diagText = cita.diagnostico ? cita.diagnostico.enfermedad : 'Sin Diagnóstico';

                    citasBody.innerHTML += `
                        <tr class="text">
                            <td>${cita.id_cita}</td>
                            <td>${cita.medico || '-'}</td>
                            <td>${diagText}</td>
                            <td>${prescText}</td>
                        </tr>
                    `;
                });
            } else {
                citasBody.innerHTML = '<tr><td colspan="4" class="text-center">No hay registros</td></tr>';
            }
        }
    } catch (error) {
        console.error('Error fetching historia details:', error);
    }
}

function showList() {
    document.getElementById('detail-view').classList.add('d-none');
    document.getElementById('list-view').classList.remove('d-none');
}

window.loadHistorias = loadHistorias;
window.showDetail = showDetail;
window.showList = showList;
