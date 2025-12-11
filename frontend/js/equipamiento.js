document.addEventListener('DOMContentLoaded', async function () {
    await loadEquipamiento();

    // Create Form
    document.getElementById('create-equipo-form').addEventListener('submit', async function (e) {
        e.preventDefault();
        const formData = new FormData(e.target);
        const equipoData = {
            nom_eq: formData.get('nom_eq'),
            marca_modelo: formData.get('marca_modelo'),
            // id_dept removed - backend will use user's department
            estado_equipo: formData.get('estado_equipo'),
            fecha_ultimo_maint: formData.get('fecha_ultimo_maint')
        };

        try {
            const response = await fetch('http://127.0.0.1:8000/api/v2/equipamiento/crear/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(equipoData),
                credentials: 'include'
            });

            const data = await response.json();
            if (response.ok && data.success) {
                alert('Equipo registrado exitosamente');
                showList();
                await loadEquipamiento();
            } else {
                alert('Error: ' + (data.error || 'No se pudo registrar'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error de conexión');
        }
    });
});

async function loadEquipamiento() {
    const API_BASE = 'http://127.0.0.1:8000/api/v2';
    try {
        const response = await fetch(`${API_BASE}/equipamiento/`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderEquipamiento(data.equipamiento);
        } else {
            console.error('Failed to fetch equipamiento');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function renderEquipamiento(equipos) {
    const tbody = document.getElementById('equipos-table-body');
    tbody.innerHTML = '';

    if (!equipos || equipos.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text text-center">No hay equipamiento registrado</td></tr>';
        return;
    }

    equipos.forEach(e => {
        let badgeClass = 'bg-secondary';
        if (e.estado === 'Disponible' || e.estado === 'OPERATIVO') badgeClass = 'bg-success';
        else if (e.estado === 'En Mantenimiento' || e.estado === 'MANTENIMIENTO') badgeClass = 'bg-warning text-dark';
        else if (e.estado === 'Fuera de Servicio') badgeClass = 'bg-danger';

        tbody.innerHTML += `
            <tr class="text">
                <td>${e.nombre || '-'}</td>
                <td>${e.marca || e.tipo || '-'}</td>
                <td>${e.sede || '-'}</td>
                <td>${e.departamento || '-'}</td>
                <td><span class="badge ${badgeClass}">${e.estado || '-'}</span></td>
                <td>${e.ultimo_mantenimiento || '-'}</td>
                <td>${e.responsable || '-'}</td>
                <td><button class="btn btn-sm btn-info"><i class="bi bi-eye"></i></button></td>
            </tr>
        `;
    });
}

function showList() {
    document.getElementById('create-view').classList.add('d-none');
    document.getElementById('list-view').classList.remove('d-none');
}

function showCreate() {
    document.getElementById('list-view').classList.add('d-none');
    document.getElementById('create-view').classList.remove('d-none');
}

window.showList = showList;
window.showCreate = showCreate;
window.loadEquipamiento = loadEquipamiento;
