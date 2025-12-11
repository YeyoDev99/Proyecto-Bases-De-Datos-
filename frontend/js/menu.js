document.addEventListener('DOMContentLoaded', function () {
    // Check if user is logged in
    const storedUser = localStorage.getItem('user');
    if (!storedUser) {
        window.location.href = 'index.html';
        return;
    }

    const user = JSON.parse(storedUser);

    // Populate Header
    const userNameEl = document.getElementById('header-user-name');
    const userRoleEl = document.getElementById('header-user-role');
    const userSedeEl = document.getElementById('header-user-sede');

    if (userNameEl) userNameEl.textContent = user.nombre;
    if (userRoleEl) userRoleEl.textContent = user.rol;
    if (userSedeEl) userSedeEl.textContent = user.sede_nombre || 'N/A';

    // Handle Role-Based Visibility
    const restrictedElements = document.querySelectorAll('.role-restricted');
    restrictedElements.forEach(el => {
        const allowedRoles = el.getAttribute('data-roles').split(',');
        if (!allowedRoles.includes(user.rol)) {
            el.style.display = 'none';
            el.classList.add('d-none');
        } else {
            el.classList.remove('d-none');
        }
    });

    // Fetch Dashboard Stats
    fetchDashboardStats();
});

async function fetchDashboardStats() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/v2/dashboard/stats/', {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const stats = data.stats;

            const elCitasHoy = document.getElementById('stat-citas-hoy');
            const elAtendidos = document.getElementById('stat-pacientes-atendidos');
            const elPendientes = document.getElementById('stat-citas-pendientes');
            const elStock = document.getElementById('stat-alertas-stock');

            if (elCitasHoy) elCitasHoy.textContent = stats.citas_hoy;
            if (elAtendidos) elAtendidos.textContent = stats.pacientes_atendidos;
            if (elPendientes) elPendientes.textContent = stats.citas_pendientes;
            if (elStock) {
                elStock.textContent = stats.alertas_stock;
                if (stats.alertas_stock > 0) {
                    elStock.style.color = '#dc3545';
                }
            }
        } else {
            console.warn('Failed to fetch stats');
        }
    } catch (error) {
        console.error('Error fetching stats:', error);
    }
}
