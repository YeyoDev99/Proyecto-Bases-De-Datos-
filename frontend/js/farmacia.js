document.addEventListener('DOMContentLoaded', async function () {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';

    // Initial load
    await loadInventario();
    await loadCatalogo();
});

async function loadInventario() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/inventario/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderInventario(data.inventario);

            // Calculate alerts (low stock < 50)
            const alertas = data.inventario.filter(i => i.cantidad < 50);
            renderAlertas(alertas);
        }
    } catch (error) {
        console.error('Error loading inventario:', error);
    }
}

function renderInventario(inventario) {
    const tbody = document.getElementById('inventario-table-body');
    tbody.innerHTML = '';

    if (!inventario || inventario.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text text-center">No hay inventario registrado</td></tr>';
        return;
    }

    inventario.forEach(i => {
        let badgeClass = 'bg-success';
        let estado = 'ÓPTIMO';
        if (i.cantidad < 10) {
            badgeClass = 'bg-danger';
            estado = 'CRÍTICO';
        } else if (i.cantidad < 50) {
            badgeClass = 'bg-warning text-dark';
            estado = 'BAJO';
        }

        tbody.innerHTML += `
            <tr class="text">
                <td>${i.sede || '-'}</td>
                <td>${i.medicamento || '-'}</td>
                <td>${i.principio_activo || '-'}</td>
                <td>${i.cantidad}</td>
                <td><span class="badge ${badgeClass}">${estado}</span></td>
                <td>${i.fecha_actualizacion || '-'}</td>
                <td><button onclick="showUpdateStock(${i.id_inv})" class="btn btn-sm btn-warning"><i class="bi bi-pencil"></i></button></td>
            </tr>
        `;
    });
}

function renderAlertas(alertas) {
    const tbody = document.getElementById('alertas-table-body');
    tbody.innerHTML = '';

    if (!alertas || alertas.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text text-center text-success">No hay alertas de stock</td></tr>';
        return;
    }

    alertas.forEach(a => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${a.sede || '-'}</td>
                <td>${a.medicamento || '-'}</td>
                <td style="color: #dc3545; font-weight: bold;">${a.cantidad}</td>
                <td><span class="badge bg-danger">BAJO</span></td>
                <td><button onclick="showUpdateStock(${a.id_inv})" class="btn btn-sm btn-primary"><i class="bi bi-plus-circle"></i> Reponer</button></td>
            </tr>
        `;
    });
}

async function loadCatalogo() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/medicamentos/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderCatalogo(data.medicamentos);
        }
    } catch (error) {
        console.error('Error loading catalogo:', error);
    }
}

function renderCatalogo(medicamentos) {
    const tbody = document.getElementById('catalogo-table-body');
    tbody.innerHTML = '';

    if (!medicamentos || medicamentos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text text-center">No hay medicamentos en el catálogo</td></tr>';
        return;
    }

    medicamentos.forEach(m => {
        tbody.innerHTML += `
            <tr class="text">
                <td>${m.cod_med}</td>
                <td>${m.nombre}</td>
                <td>${m.principio_activo || '-'}</td>
                <td>${m.unidad || '-'}</td>
                <td>${m.proveedor || '-'}</td>
            </tr>
        `;
    });
}

function showView(viewName) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.add('d-none'));
    document.getElementById(viewName + '-view').classList.remove('d-none');

    const titleMap = {
        'inventario': 'Inventario Consolidado',
        'alertas': 'Alertas De Stock',
        'catalogo': 'Catálogo de Medicamentos'
    };
    document.getElementById('page-title').innerHTML = `<i class="bi bi-capsule"></i> ${titleMap[viewName]}`;
}

function showUpdateStock(idInv) {
    alert('Función de actualización de stock en desarrollo. ID: ' + idInv);
}

window.showView = showView;
window.showUpdateStock = showUpdateStock;
