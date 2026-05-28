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

CREATE TABLE estado_validacion (
    id     SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
    -- valores esperados: 'pendiente', 'aprobado', 'rechazado'
);

CREATE TABLE persona (
    id               SERIAL PRIMARY KEY,
    nombre           TEXT NOT NULL,
    apellido         TEXT NOT NULL,
    email            TEXT NOT NULL,
    telefono         TEXT,
    dni              TEXT NOT NULL,
    pais_id          INT  NOT NULL REFERENCES pais(id),
    fecha_nacimiento DATE
);

CREATE TABLE usuario (
    id         SERIAL PRIMARY KEY,
    persona_id INT  REFERENCES persona(id),   -- NULL válido: el bot no tiene persona
    password   TEXT,                           -- NULL válido: el bot no tiene password
    rol_id     INT  NOT NULL REFERENCES rol(id),
    estado_id  INT  NOT NULL REFERENCES estado(id)
);

-- -------------------------------------------------------
-- VEHÍCULOS Y DOCUMENTACIÓN
-- -------------------------------------------------------
CREATE TABLE marca (
    id     SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE modelo (
    id       SERIAL PRIMARY KEY,
    nombre   TEXT NOT NULL,
    marca_id INT  NOT NULL REFERENCES marca(id)
);

CREATE TABLE vehiculo (
    id                SERIAL PRIMARY KEY,
    usuario_id        INT  NOT NULL REFERENCES usuario(id),
    modelo_id         INT  NOT NULL REFERENCES modelo(id),
    anio              INT  NOT NULL,
    fecha_ingreso     DATE NOT NULL,
    patente           TEXT NOT NULL,
    estado_vehiculo_id INT NOT NULL REFERENCES estado_vehiculo(id)
);

CREATE TABLE tipo_licencia (
    id     SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
);

CREATE TABLE carnet_conducir (
    id                  SERIAL PRIMARY KEY,
    usuario_id          INT  NOT NULL REFERENCES usuario(id),
    nombre_titular      TEXT NOT NULL,
    fecha_emision       DATE NOT NULL,
    fecha_vencimiento   DATE NOT NULL,
    imagen              TEXT NOT NULL,
    estado_validacion_id INT NOT NULL REFERENCES estado_validacion(id),
    motivo_rechazo      TEXT          -- NULL cuando no fue rechazado
);

CREATE TABLE carnet_clase (
    id                 SERIAL PRIMARY KEY,
    carnet_id          INT  NOT NULL REFERENCES carnet_conducir(id),
    tipo_licencia_id   INT  NOT NULL REFERENCES tipo_licencia(id),
    fecha_otorgamiento DATE NOT NULL,
    fecha_vencimiento  DATE NOT NULL
);

CREATE TABLE tipo_documento_vehiculo (
    id     SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL
    -- valores esperados: 'seguro', 'vtv', 'cedula_verde', etc.
);

CREATE TABLE documento_vehiculo (
    id                   SERIAL PRIMARY KEY,
    vehiculo_id          INT  NOT NULL REFERENCES vehiculo(id),
    tipo_id              INT  NOT NULL REFERENCES tipo_documento_vehiculo(id),
    nombre_titular       TEXT NOT NULL,
    fecha_vencimiento    DATE NOT NULL,
    imagen               TEXT NOT NULL,
    estado_validacion_id INT  NOT NULL REFERENCES estado_validacion(id),
    motivo_rechazo       TEXT,          -- NULL cuando no fue rechazado
    estado_id            INT  NOT NULL REFERENCES estado(id)
);

-- -------------------------------------------------------
-- BOT
-- -------------------------------------------------------
CREATE TABLE bot_tema (
    id            SERIAL PRIMARY KEY,
    nombre        TEXT NOT NULL,     -- "Términos y condiciones"
    descripcion   TEXT,              -- subtítulo opcional del botón
    system_prompt TEXT NOT NULL,     -- contexto acotado que recibe el LLM
    orden         INT  NOT NULL,     -- orden de aparición en el menú
    activo        BOOLEAN NOT NULL DEFAULT TRUE
);

-- -------------------------------------------------------
-- CONVERSACIÓN Y MENSAJERÍA
-- -------------------------------------------------------
CREATE TABLE fase_conversacion (
    id     SERIAL PRIMARY KEY,
    estado TEXT NOT NULL
    -- valores esperados: 'bot_menu', 'bot_libre', 'operario', 'cerrada'
);

CREATE TABLE conversacion (
    id         SERIAL PRIMARY KEY,
    fase_id    INT       NOT NULL REFERENCES fase_conversacion(id),
    abierta_at TIMESTAMP NOT NULL DEFAULT NOW(),
    tema_id         INT       NOT NULL REFERENCES bot_tema(id),
    cerrada_at TIMESTAMP           -- NULL = conversación activa
);


CREATE TABLE mensaje (
    id              SERIAL PRIMARY KEY,
    conversacion_id INT       NOT NULL REFERENCES conversacion(id),
    autor_id        INT       NOT NULL REFERENCES usuario(id),  -- bot, operario o cliente
    cuerpo          TEXT      NOT NULL,
    enviado_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE derivacion (
    id              SERIAL PRIMARY KEY,
    conversacion_id INT       NOT NULL REFERENCES conversacion(id),
    operario_id     INT       NOT NULL REFERENCES usuario(id),
    motivo          TEXT,              -- 'bot_no_resolvio', 'solicitud_usuario'
    asignada_at     TIMESTAMP NOT NULL DEFAULT NOW(),
    liberada_at     TIMESTAMP          -- NULL = operario actualmente activo
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

INSERT INTO tipo_licencia (nombre) VALUES
('A1'), ('A2'), ('A3'), ('A4'),
('B1'), ('B2'),
('C1'), ('C2'),
('D1'), ('D2'), ('D3'),
('E1'), ('E2'),
('F'), ('G1'), ('G2'), ('G3');

INSERT INTO persona (nombre, apellido, email, telefono, dni, pais_id, fecha_nacimiento) VALUES
('Juan', 'Pérez', 'juan.cliente@email.com', '+5491123456789', '35123456', 1, '1990-05-14'),--cliente
('Ana', 'Martínez', 'ana.socio@email.com', '+5493794123456', '38765432', 1, '1985-11-23'),--socio
('Carlos', 'López', 'carlos.admin@email.com', '+549114445555', '29345678', 1, '1978-03-07'),--admin
('Mariana', 'Vaca', 'mariana.op@govehiculos.com', '+5493794001122', '40123987', 1, '1995-08-30'),--operador
('Elena', 'Torres', 'elena.soporte@govehiculos.com', '+5493794990011', '41555666', 1, '1993-01-19'),--soporte
('María Del Rosario', 'Sosa', 'maria.del.rosario@sosa.com', '+5493794880011', '42666777', 1, '2003-09-20');--cliente

INSERT INTO usuario (persona_id, password, rol_id, estado_id) VALUES
(1, '1234', 1, 1), --cliente
(2, '1234', 2, 1), --socio
(3, '1234', 3, 1),-- admin
(4, '1234', 4, 1), -- Mariana: Operador
(5, '1234', 5, 1), -- Facundo: Soporte
(6, '1234', 1, 1); -- Maria del Rosario: Cliente