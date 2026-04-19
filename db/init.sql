CREATE TABLE pais (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE rol (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE estado (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE estado_vehiculo (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);


CREATE TABLE persona (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    apellido TEXT,
    email TEXT,
    telefono TEXT,
    dni TEXT,
    pais INT,
    FOREIGN KEY (pais) REFERENCES pais(id)
);

CREATE TABLE usuario (
    id SERIAL PRIMARY KEY,
    persona_id INT,
    password TEXT,
    rol_id INT,
    estado INT,
    FOREIGN KEY (persona_id) REFERENCES persona(id),
    FOREIGN KEY (rol_id) REFERENCES rol(id),
    FOREIGN KEY (estado) REFERENCES estado(id)
);

CREATE TABLE marca (
    id SERIAL PRIMARY KEY,
    nombre TEXT
);

CREATE TABLE modelo (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    marca_id INT,
    FOREIGN KEY (marca_id) REFERENCES marca(id)
);

CREATE TABLE vehiculo (
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    modelo INT,
    anio INT,
    fecha_ingreso DATE,
    patente TEXT,
    estado INT,
    estado_vehiculo INT,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id),
    FOREIGN KEY (modelo) REFERENCES modelo(id),
    FOREIGN KEY (estado_vehiculo) REFERENCES estado_vehiculo(id)
);

CREATE TABLE carnet_conducir (
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    nombre_titular TEXT,
    clase TEXT,
    fecha_vencimiento DATE,
    imagen TEXT,
    estado_validacion INT,
    motivo_rechazo TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

CREATE TABLE documento_vehiculo (
    id SERIAL PRIMARY KEY,
    vehiculo_id INT,
    tipo TEXT,
    nombre_titular TEXT,
    fecha_vencimiento DATE,
    imagen TEXT,
    estado_validacion INT,
    motivo_rechazo TEXT,
    estado INT,
    FOREIGN KEY (vehiculo_id) REFERENCES vehiculo(id)
);

CREATE TABLE conversacion (
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    operario_asignado INT,
    estado INT,
    fecha_ingreso TIMESTAMP,
    fecha_salida TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

CREATE TABLE mensaje (
    id SERIAL PRIMARY KEY,
    conversacion_id INT,
    usuario_id INT,
    origen TEXT,
    cuerpo TEXT,
    fecha_hora TIMESTAMP,
    FOREIGN KEY (conversacion_id) REFERENCES conversacion(id),
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

CREATE TABLE derivacion (
    id SERIAL PRIMARY KEY,
    conversacion_id INT,
    operario_asignado INT,
    motivo TEXT,
    estado INT,
    ingreso TIMESTAMP,
    salida TIMESTAMP,
    FOREIGN KEY (conversacion_id) REFERENCES conversacion(id)
);

CREATE TABLE respuesta_bot (
    id SERIAL PRIMARY KEY,
    palabra_clave TEXT,
    respuesta TEXT,
    estado INT
);

CREATE TABLE estado_bot (
    id SERIAL PRIMARY KEY,
    nombre TEXT
);

CREATE TABLE horario_operador (
    id SERIAL PRIMARY KEY,
    usuario_id INT,
    dia_semana INT,
    hora_inicio TIME,
    hora_fin TIME,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
);

--Inserccion de datos
INSERT INTO pais (nombre) VALUES 
('Argentina'), ('Chile'), ('Uruguay'), ('Paraguay'), ('Brasil');

INSERT INTO rol (nombre) VALUES 
('Cliente'), ('Socio'), ('Administrador'), ('Operador'), ('Soporte');

INSERT INTO estado (nombre) VALUES 
('Activo'), ('Inactivo'), ('En validacion'), ('Rechazado');

INSERT INTO estado_vehiculo (nombre) VALUES 
('Activo'), ('Inactivo'), ('En validacion'), ('Rechazado'), ('Alquilado'), ('En Taller');

INSERT INTO marca (nombre) VALUES 
('Toyota'), ('Fiat'), ('Peugeot'), ('Volkswagen');

INSERT INTO modelo (nombre, marca_id) VALUES 
('Hilux', 1), ('Corolla', 1),
('Cronos', 2), ('Toro', 2),
('208', 3), 
('Amarok', 4), ('Taos', 4);

INSERT INTO persona (nombre, apellido, email, telefono, dni, pais) VALUES
('Juan', 'Pérez', 'juan.cliente@email.com', '+5491123456789', '35123456', 1),--cliente
('Ana', 'Martínez', 'ana.socio@email.com', '+5493794123456', '38765432', 1),--socio
('Carlos', 'López', 'carlos.admin@email.com', '+549114445555', '29345678', 1);--admin
('Mariana', 'Vaca', 'mariana.op@govehiculos.com', '+5493794001122', '40123987', 1),--operador
('Elena', 'Torres', 'elena.soporte@govehiculos.com', '+5493794990011', '41555666', 1);--soporte

INSERT INTO usuario (persona_id, password, rol_id, estado) VALUES
(1, '1234', 1, 1), --cliente
(2, '1234', 2, 1), --socio
(3, '1234', 3, 1);-- admin
(4, '1234', 4, 1), -- Mariana: Operador
(5 '1234', 5, 1), -- Facundo: Soporte