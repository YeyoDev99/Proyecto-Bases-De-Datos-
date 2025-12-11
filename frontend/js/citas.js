document.addEventListener('DOMContentLoaded', function () {
    const currentFilter = 'todas'; // Default filter
    fetchCitas(currentFilter);

    // Handle Filter Clicks
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const filter = e.target.getAttribute('data-filter');
            fetchCitas(filter);
        });
    });

    // Check for ID param in URL to show detail view
    const urlParams = new URLSearchParams(window.location.search);
    const citaId = urlParams.get('id');
    if (citaId) {
        showDetail(citaId);
    }
});

async function fetchCitas(filter) {
    try {
        let url = 'http://127.0.0.1:8000/api/v2/citas/';
        if (filter && filter !== 'todas') {
            url += `?estado=${filter.toUpperCase()}`; // Example mapping
        }

        const response = await fetch(url, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderCitas(data.citas);
        } else {
            console.error('Failed to fetch citas');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function renderCitas(citas) {
    const tbody = document.getElementById('citas-table-body');
    tbody.innerHTML = '';

    if (!citas || citas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text text-center">No hay citas registradas</td></tr>';
        return;
    }

    citas.forEach(c => {
        let badgeClass = 'bg-secondary';
        if (c.estado === 'COMPLETADA') badgeClass = 'bg-success';
        else if (c.estado === 'CANCELADA') badgeClass = 'bg-danger';
        else if (c.estado === 'PROGRAMADA') badgeClass = 'bg-warning text-dark';

        const tr = document.createElement('tr');
        tr.className = 'text';
        tr.innerHTML = `
            <td>${c.id_cita}</td>
            <td>${c.fecha_hora}</td>
            <td>${c.paciente}</td>
            <td>${c.tipo_servicio || '-'}</td>
            <td><span class="badge ${badgeClass}">${c.estado}</span></td>
            <td>${c.motivo || '-'}</td>
            <td>
                <button onclick="showDetail(${c.id_cita})" class="btn btn-sm btn-info"><i class="bi bi-eye"></i></button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function showDetail(id) {
    document.getElementById('citas-list-view').classList.add('d-none');
    document.getElementById('cita-detail-view').classList.remove('d-none');

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/v2/citas/${id}/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            const detail = data.cita;

            document.getElementById('detail-id').textContent = detail.id_cita;
            document.getElementById('detail-paciente').textContent = detail.paciente;
            document.getElementById('detail-medico').textContent = detail.medico;
            document.getElementById('detail-sede').textContent = detail.sede;
            document.getElementById('detail-departamento').textContent = detail.departamento || '-';
            document.getElementById('detail-fecha').textContent = detail.fecha_hora;
            document.getElementById('detail-servicio').textContent = detail.tipo_servicio;
            document.getElementById('detail-estado').textContent = detail.estado;
            document.getElementById('detail-motivo').textContent = detail.motivo;
        }
    } catch (error) {
        console.error('Error fetching details:', error);
    }

    // Inject actions
    const actionsDiv = document.getElementById('detail-actions');
    actionsDiv.innerHTML = `
        <a href="#" class="p-2 ms-2" onclick="goBack()"><i class="bi bi-arrow-left"></i> Volver</a>
    `;
}

function goBack() {
    document.getElementById('cita-detail-view').classList.add('d-none');
    document.getElementById('citas-list-view').classList.remove('d-none');
    // Clear URL param
    const url = new URL(window.location);
    url.searchParams.delete('id');
    window.history.pushState({}, '', url);
}

// Global scope
window.goBack = goBack;
window.showDetail = showDetail;
