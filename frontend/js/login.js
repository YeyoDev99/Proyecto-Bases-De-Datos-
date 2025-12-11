document.getElementById('login-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const alertContainer = document.getElementById('alert-container');

    // Simple client-side validation
    if (!email || !password) {
        showAlert('Por favor complete todos los campos', 'danger');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/v2/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            console.log('Login successful');
            // Store user data in localStorage for simple frontend access (though sessions are cookie based)
            localStorage.setItem('user', JSON.stringify(data.user));

            // Redirect to menu
            window.location.href = 'menu.html';
        } else {
            throw new Error(data.error || 'Credenciales inválidas');
        }

    } catch (error) {
        console.error('Error:', error);
        showAlert(error.message, 'danger');
    }
});

function showAlert(message, type) {
    const alertContainer = document.getElementById('alert-container');
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    alertContainer.innerHTML = alertHtml;
}
