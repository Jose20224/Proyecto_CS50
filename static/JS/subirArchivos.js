const dropArea = document.getElementById('drop-area');
const fileInput = document.getElementById('file-input');
const maxFileSize = 5 * 1024 * 1024; // 5 MB en bytes

dropArea.addEventListener('dragover', (event) => {
    event.preventDefault();
    dropArea.style.borderColor = 'green';
});

dropArea.addEventListener('dragleave', () => {
    dropArea.style.borderColor = '#ccc';
});

dropArea.addEventListener('drop', (event) => {
    event.preventDefault();
    dropArea.style.borderColor = '#ccc';
    const files = event.dataTransfer.files;
    fileInput.files = files;
    validateFileAndSubmit();
});

function validateFileAndSubmit() {
    const file = fileInput.files[0];
    if (file.size > maxFileSize) {
        alert('El tamaño máximo de archivo permitido es de 5 MB.');
        fileInput.value = ''; // Limpiar la selección del archivo
    } else {
        document.getElementById('file-form').submit();
    }
}