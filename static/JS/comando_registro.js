 // Función para validar la contraseña
 document.querySelector('form').addEventListener('submit', function(event) {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confir_password').value;
    // Expresión regular para validar la contraseña (mínimo 8 caracteres y al menos un número)
    const passwordRegex = /^(?=.*\d).{8,}$/;
    if (!passwordRegex.test(password)) {
        event.preventDefault(); // Evita enviar el formulario
        document.getElementById('password').value = ''; // Limpia el campo de contraseña
        document.getElementById('confir_password').value = ''; // Limpia el campo de confirmación de contraseña
        document.querySelector('.error-message').innerText = 'La contraseña debe tener al menos 8 caracteres y contener al menos un número.';
    }
    else if (password !== confirmPassword) {
        event.preventDefault(); // Evita enviar el formulario
        document.getElementById('password').value = ''; // Limpia el campo de contraseña
        document.getElementById('confir_password').value = ''; // Limpia el campo de confirmación de contraseña
        document.querySelector('.error-message').innerText = 'Las contraseñas no coinciden.';
    }
});