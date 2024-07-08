
CREATE DATABASE Proyecto_CS50_1;
GO

USE Proyecto_CS50_1;
GO


CREATE TABLE Usuarios (
    ID INT PRIMARY KEY IDENTITY(1,1),
    Usuario NVARCHAR(50) UNIQUE NOT NULL,
    Hash NVARCHAR(256) NOT NULL,
    Correo NVARCHAR(100) UNIQUE NOT NULL,
    Digitos8 NVARCHAR(8) NULL, -- Contraseña temporal de 8 dígitos
    Activo BIT DEFAULT 0, -- Estado de la cuenta, 0 = inactiva, 1 = activa
    FotoPerfil VARBINARY(MAX) NULL -- Foto de perfil
);
GO

-- Crear la tabla Archivos
CREATE TABLE Archivos (
    ID INT PRIMARY KEY IDENTITY(1,1),
    NombreArchivo NVARCHAR(255) NOT NULL,
    TipoArchivo NVARCHAR(350) NOT NULL,
	formatoAchi NVARCHAR(50) NOT NULL,
    Contenido VARBINARY(MAX) NOT NULL,
    Tamaño BIGINT NOT NULL CHECK (Tamaño <= 52428800), -- 50 MB
    FechaSubida DATETIME DEFAULT GETDATE(),
    UsuarioID INT NOT NULL,
    FOREIGN KEY (UsuarioID) REFERENCES Usuarios(ID)
);
GO