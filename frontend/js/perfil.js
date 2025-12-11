document.addEventListener('DOMContentLoaded', function () {
    loadProfile();

    // Password Change Form
    document.getElementById('change-password-form').addEventListener('submit', function (e) {
        e.preventDefault();
        alert('Contraseña cambiada exitosamente');
        showProfile();
    });
});

async function loadProfile() {
    try {
        const response = await fetch('http://127.0.0.1:8000/api/v2/perfil/', {
            credentials: 'include'
        });

        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = 'login.html';
                return;
            }
            throw new Error('Error al cargar perfil');
        }

        const data = await response.json();
        const profile = data.perfil;

        // Map gender code to full text
        const genderMap = {
            'M': 'Masculino',
            'F': 'Femenino',
            'O': 'Otro'
        };

        document.getElementById('profile-name').textContent = `${profile.nombre} ${profile.apellido}`;
        document.getElementById('profile-doc').textContent = `${profile.tipo_doc || ''} - ${profile.num_doc || ''}`;
        document.getElementById('profile-dob').textContent = profile.fecha_nac || 'No especificado';
        document.getElementById('profile-gender').textContent = genderMap[profile.genero] || profile.genero || 'No especificado';
        document.getElementById('profile-address').textContent = profile.direccion || 'No especificado';
        document.getElementById('profile-phone').textContent = profile.telefono || 'No especificado';
        document.getElementById('profile-email').textContent = profile.email || 'No especificado';
        document.getElementById('profile-city').textContent = profile.ciudad || 'No especificado';
        document.getElementById('profile-role').textContent = profile.rol || 'No especificado';
        document.getElementById('profile-sede').textContent = profile.sede || 'No especificado';
        document.getElementById('profile-dept').textContent = profile.departamento || 'No asignado';

    } catch (error) {
        console.error('Error loading profile:', error);
        alert('Error al cargar el perfil');
    }
}

function showChangePassword() {
    document.getElementById('profile-view').classList.add('d-none');
    document.getElementById('password-view').classList.remove('d-none');
}

function showProfile() {
    document.getElementById('password-view').classList.add('d-none');
    document.getElementById('profile-view').classList.remove('d-none');
}

window.showChangePassword = showChangePassword;
window.showProfile = showProfile;
