function mostrarArchivo(id) {
    fetch(`/archivo/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                let contenido = '';
                const tipo = data.tipo;

                if (tipo.startsWith('image/')) {
                    contenido = `<img src="data:${tipo};base64,${data.contenido}" class="img-fluid" alt="${data.nombre}">`;
                } else if (tipo === 'application/pdf') {
                    contenido = `<embed src="data:${tipo};base64,${data.contenido}" type="${tipo}" width="100%" height="600px" />`;
                } else {
                    contenido = `<pre>${atob(data.contenido)}</pre>`;
                }

                document.getElementById('archivoContenido').innerHTML = contenido;
                document.getElementById('archivoModal').style.display = 'block';
            }
        })
        .catch(error => console.error('Error:', error));
}

function eliminarArchivo(id) {
    if (confirm('¿Está seguro de que desea eliminar este archivo?')) {
        fetch(`/archivo/${id}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert(data.message);
                const row = document.getElementById('archivoRow' + id);
                row.parentNode.removeChild(row);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function cambiarNombreArchivo(id) {
    const nuevoNombre = prompt('Ingrese el nuevo nombre del archivo:');
    if (nuevoNombre) {
        fetch(`/archivo/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nuevoNombre: nuevoNombre })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
            } else {
                alert(data.message);
                location.reload();
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function cerrarModal() {
    document.getElementById('archivoModal').style.display = 'none';
}

function buscarArchivos() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    fetch(`/buscar_archivos?q=${query}`)
        .then(response => response.json())
        .then(data => {
            const container = document.querySelector('.row');
            container.innerHTML = '';
            data.forEach(archivo => {
                const card = `
                    <div class="col-sm-12 col-md-6 col-lg-4 mb-4">
                        <div class="card text-bg-light" style="width: 18rem;">
                           
                            <div class="card-body">
                                <h6>Nombre</h6>
                                <p class="card-text">${archivo.NombreArchivo}</p>
                                <h6>Fecha</h6>
                                <span class="card-title">${archivo.FechaSubida}</span>
                                <div class="dropdown">
                                    <button class="btn btn-primary dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false">
                                        opciones
                                    </button>
                                    <ul class="dropdown-menu">
                                        ${['txt', 'imagen', 'PDF'].includes(archivo.formatoAchi) ? 
                                            `<li><a class="dropdown-item" href="#" onclick="mostrarArchivo(${archivo.ID})">Ver</a></li>` 
                                            : ''}
                                        <li><a class="dropdown-item" href="/archivo/${archivo.ID}/descargar">Descargar</a></li>
                                        <li><a class="dropdown-item" href="#" onclick="eliminarArchivo(${archivo.ID})">Eliminar</a></li>
                                        <li><a class="dropdown-item" href="#" onclick="cambiarNombreArchivo(${archivo.ID})">Cambiar Nombre</a></li>
                                    </ul>
                                </div>
                            </div>
                        </div>
                    </div>`;
                container.insertAdjacentHTML('beforeend', card);
            });
        })
        .catch(error => console.error('Error:', error));
}


