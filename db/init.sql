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
    FOREIGN KEY (rol_id) REFERENCES rol(id)
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
    modelo TEXT,
    anio INT,
    fecha_ingreso DATE,
    patente TEXT,
    estado INT,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id)
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

INSERT INTO rol (nombre)
SELECT seed.nombre
FROM (VALUES ('Cliente'), ('Socio'), ('Administrador'), ('Operador'), ('Soporte')) AS seed(nombre)
WHERE NOT EXISTS (
    SELECT 1
    FROM rol existing
    WHERE existing.nombre = seed.nombre
);

INSERT INTO estado (nombre)
SELECT seed.nombre
FROM (VALUES ('Activo'), ('Inactivo'), ('Pendiente'), ('Rechazado')) AS seed(nombre)
WHERE NOT EXISTS (
    SELECT 1
    FROM estado existing
    WHERE existing.nombre = seed.nombre
);

INSERT INTO pais (nombre)
SELECT seed.nombre
FROM (VALUES ('Argentina'), ('Chile'), ('Uruguay'), ('Paraguay'), ('Brasil')) AS seed(nombre)
WHERE NOT EXISTS (
    SELECT 1
    FROM pais existing
    WHERE existing.nombre = seed.nombre
);