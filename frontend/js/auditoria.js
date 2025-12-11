document.addEventListener('DOMContentLoaded', async function () {
    await loadAuditoria();
});

async function loadAuditoria() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/auditoria/accesos/`, { credentials: 'include' });
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'index.html';
                return;
            }
            if (response.status === 403) {
                document.getElementById('auditoria-table-body').innerHTML =
                    '<tr><td colspan="7" class="text-center text-danger">No tiene permisos para ver auditoría</td></tr>';
                return;
            }
            throw new Error('Error al cargar auditoría');
        }

        const data = await response.json();
        renderAuditoria(data.auditoria);
    } catch (error) {
        console.error('Error loading auditoria:', error);
        document.getElementById('auditoria-table-body').innerHTML =
            '<tr><td colspan="7" class="text-center text-danger">Error al cargar datos</td></tr>';
    }
}

function renderAuditoria(records) {
    const tbody = document.getElementById('auditoria-table-body');
    tbody.innerHTML = '';

    if (!records || records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text text-center">No hay registros de auditoría</td></tr>';
        return;
    }

    records.forEach(r => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${r.fecha || '-'}</td>
                <td>${r.empleado || '-'}</td>
                <td>${r.rol || '-'}</td>
                <td>${r.accion || '-'}</td>
                <td>${r.tabla || '-'}</td>
                <td>${r.registro_id || '-'}</td>
                <td>${r.ip || '-'}</td>
            </tr>
        `;
    });
}
