-- ELIMINAR VISTAS
DROP VIEW IF EXISTS vista_consumo_medicamentos_dept CASCADE;
DROP VIEW IF EXISTS vista_tiempos_atencion CASCADE;
DROP VIEW IF EXISTS vista_auditoria_historias CASCADE;
DROP VIEW IF EXISTS vista_equipamiento_departamentos CASCADE;
DROP VIEW IF EXISTS vista_inventario_consolidado CASCADE;
DROP VIEW IF EXISTS vista_enfermedades_por_sede CASCADE;
DROP VIEW IF EXISTS vista_medicos_consultas CASCADE;
DROP VIEW IF EXISTS vista_medicamentos_recetados_sede CASCADE;
DROP VIEW IF EXISTS vista_historias_consolidadas CASCADE;
DROP VIEW IF EXISTS vista_utilizacion_recursos CASCADE;

-- ELIMINAR TABLAS
DROP TABLE IF EXISTS Reportes_Generados CASCADE;
DROP TABLE IF EXISTS Auditoria_Accesos CASCADE;
DROP TABLE IF EXISTS Prescripciones CASCADE;
DROP TABLE IF EXISTS Diagnostico CASCADE;
DROP TABLE IF EXISTS Historias_Clinicas CASCADE;
DROP TABLE IF EXISTS Equipamiento CASCADE;
DROP TABLE IF EXISTS Citas CASCADE;
DROP TABLE IF EXISTS Inventario_Farmacia CASCADE;
DROP TABLE IF EXISTS Emp_Posee_Esp CASCADE;
DROP TABLE IF EXISTS Empleados CASCADE;
DROP TABLE IF EXISTS Pacientes CASCADE;
DROP TABLE IF EXISTS Departamentos CASCADE;
DROP TABLE IF EXISTS Enfermedades CASCADE;
DROP TABLE IF EXISTS Catalogo_Medicamentos CASCADE;
DROP TABLE IF EXISTS Sedes_Hospitalarias CASCADE;
DROP TABLE IF EXISTS Especialidades CASCADE;
DROP TABLE IF EXISTS Roles CASCADE;
DROP TABLE IF EXISTS Personas CASCADE;

-- ELIMINAR ROLES
DROP ROLE IF EXISTS auditor;
DROP ROLE IF EXISTS administrativo;
DROP ROLE IF EXISTS enfermero;
DROP ROLE IF EXISTS medico;
DROP ROLE IF EXISTS administrador;

-- TABLAS PRINCIPALES
CREATE TABLE Personas (
    id_persona INT PRIMARY KEY,
    nom_persona VARCHAR(100) NOT NULL,
    apellido_persona VARCHAR(100) NOT NULL,
    tipo_doc VARCHAR(10) NOT NULL,
    num_doc VARCHAR(20) UNIQUE NOT NULL,
    fecha_nac DATE NOT NULL,
    genero CHAR(1),
    dir_persona VARCHAR(200),
    tel_persona VARCHAR(20),
    email_persona VARCHAR(150) UNIQUE NOT NULL,
    ciudad_residencia VARCHAR(50)
);

CREATE TABLE Roles (
    id_rol INT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200)
);

CREATE TABLE Especialidades (
    id_especialidad INT PRIMARY KEY,
    nombre_esp VARCHAR(100) NOT NULL
);

CREATE TABLE Sedes_Hospitalarias (
    id_sede INT PRIMARY KEY,
    nom_sede VARCHAR(100) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    direccion VARCHAR(150),
    telefono VARCHAR(20),
    es_nodo_central BOOLEAN DEFAULT FALSE
);

CREATE TABLE Catalogo_Medicamentos (
    cod_med INT PRIMARY KEY,
    nom_med VARCHAR(150) NOT NULL,
    principio_activo VARCHAR(150),
    descripcion TEXT,
    unidad_medida VARCHAR(20),
    proveedor_principal VARCHAR(100)
);

CREATE TABLE Enfermedades (
    id_enfermedad BIGINT PRIMARY KEY,
    nombre_enfermedad VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200)
);

-- TABLAS CON DEPENDENCIAS
CREATE TABLE Departamentos (
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    nom_dept VARCHAR(100) NOT NULL,
    PRIMARY KEY(id_sede, id_dept),
    FOREIGN KEY (id_sede) REFERENCES Sedes_Hospitalarias(id_sede)
);

CREATE TABLE Pacientes (
    cod_pac INT PRIMARY KEY, 
    id_persona INT NOT NULL, 
    FOREIGN KEY (id_persona) REFERENCES Personas(id_persona)
);

-- CAMBIO IMPORTANTE: Cambiar hash_contra de VARCHAR(255) a TEXT para Azure
CREATE TABLE Empleados (
    id_emp INT PRIMARY KEY, 
    id_persona INT,
    id_rol INT NOT NULL,
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    hash_contra TEXT NOT NULL,  -- CAMBIADO A TEXT (antes era VARCHAR(255))
    activo BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (id_sede, id_dept) REFERENCES Departamentos(id_sede, id_dept),
    FOREIGN KEY (id_rol) REFERENCES Roles(id_rol),
    FOREIGN KEY (id_persona) REFERENCES Personas(id_persona)
);

CREATE TABLE Emp_Posee_Esp (
    id_emp_posee_esp INT PRIMARY KEY,
    id_especialidad INT NOT NULL,
    id_emp INT NOT NULL,
    FOREIGN KEY (id_especialidad) REFERENCES Especialidades(id_especialidad),
    FOREIGN KEY (id_emp) REFERENCES Empleados(id_emp)
);

CREATE TABLE Inventario_Farmacia (
    id_inv INT PRIMARY KEY, 
    cod_med INT NOT NULL,
    id_sede INT NOT NULL,
    stock_actual INT NOT NULL CHECK (stock_actual >= 0),
    fecha_actualizacion TIMESTAMP,
    FOREIGN KEY (id_sede) REFERENCES Sedes_Hospitalarias(id_sede),
    FOREIGN KEY (cod_med) REFERENCES Catalogo_Medicamentos(cod_med)
);

CREATE TABLE Citas (
    id_cita BIGINT PRIMARY KEY, 
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    id_emp INT NOT NULL,
    cod_pac INT NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,
    fecha_hora_solicitada TIMESTAMP NOT NULL,
    tipo_servicio VARCHAR(50),
    estado VARCHAR(20) DEFAULT 'PROGRAMADA',
    motivo VARCHAR(200),
    FOREIGN KEY (id_emp) REFERENCES Empleados(id_emp), 
    FOREIGN KEY (id_sede, id_dept) REFERENCES Departamentos(id_sede, id_dept),
    FOREIGN KEY (cod_pac) REFERENCES Pacientes(cod_pac)
);

CREATE TABLE Equipamiento (
    cod_eq INT PRIMARY KEY, 
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    nom_eq VARCHAR(100) NOT NULL,
    marca_modelo VARCHAR(100),
    estado_equipo VARCHAR(20) NOT NULL,
    fecha_ultimo_maint DATE,
    responsable_id INT,
    FOREIGN KEY (id_sede, id_dept) REFERENCES Departamentos(id_sede, id_dept),
    FOREIGN KEY (responsable_id) REFERENCES Empleados(id_emp) 
);

CREATE TABLE Historias_Clinicas (
    cod_hist BIGINT PRIMARY KEY, 
    cod_pac INT NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cod_pac) REFERENCES Pacientes(cod_pac)
);

CREATE TABLE Diagnostico (
    id_diagnostico INT PRIMARY KEY,
    id_enfermedad BIGINT NOT NULL,
    id_cita BIGINT NOT NULL,
    cod_hist BIGINT NOT NULL,
    observacion TEXT,
    FOREIGN KEY (id_enfermedad) REFERENCES Enfermedades(id_enfermedad),
    FOREIGN KEY (id_cita) REFERENCES Citas(id_cita),
    FOREIGN KEY (cod_hist) REFERENCES Historias_Clinicas(cod_hist)
);

CREATE TABLE Prescripciones (
    id_presc BIGINT PRIMARY KEY, 
    cod_med INT NOT NULL,
    cod_hist BIGINT NOT NULL,
    id_cita BIGINT NOT NULL,
    dosis VARCHAR(50) NOT NULL,
    frecuencia VARCHAR(100) NOT NULL,
    duracion_dias INT NOT NULL,
    cantidad_total INT,
    fecha_emision DATE NOT NULL,
    FOREIGN KEY (cod_hist) REFERENCES Historias_Clinicas(cod_hist),
    FOREIGN KEY (cod_med) REFERENCES Catalogo_Medicamentos(cod_med),
    FOREIGN KEY (id_cita) REFERENCES Citas(id_cita)
);

CREATE TABLE Auditoria_Accesos (
    id_evento SERIAL PRIMARY KEY, 
    id_emp INT,
    accion VARCHAR(50) NOT NULL,
    tabla_afectada VARCHAR(50),
    id_registro_afectado VARCHAR(50),
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_origen VARCHAR(45),
    FOREIGN KEY (id_emp) REFERENCES Empleados(id_emp) 
);

CREATE TABLE Reportes_Generados (
    id_reporte INT PRIMARY KEY, 
    id_sede INT NOT NULL,
    id_emp_generador INT NOT NULL,
    fecha_generacion TIMESTAMP,
    tipo_reporte VARCHAR(50),
    parametros_json TEXT,
    FOREIGN KEY (id_sede) REFERENCES Sedes_Hospitalarias(id_sede),
    FOREIGN KEY (id_emp_generador) REFERENCES Empleados(id_emp) 
);

-- CREACIÓN DE ROLES DE USUARIO
CREATE ROLE administrador;
CREATE ROLE medico;
CREATE ROLE enfermero;
CREATE ROLE administrativo;
CREATE ROLE auditor;

GRANT USAGE ON SCHEMA public TO administrador, medico, enfermero, administrativo, auditor;

-- PERMISOS ADMINISTRADOR
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO administrador;
GRANT TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public TO administrador;
GRANT CREATE ON SCHEMA public TO administrador;

-- PERMISOS MÉDICO
GRANT SELECT ON Sedes_Hospitalarias, Departamentos, Empleados, Pacientes, Catalogo_Medicamentos, 
    Inventario_Farmacia, Equipamiento, Reportes_Generados, Especialidades, Emp_Posee_Esp, 
    Enfermedades TO medico;
GRANT SELECT, INSERT, UPDATE ON Citas, Historias_Clinicas, Prescripciones, Diagnostico TO medico;
GRANT INSERT ON Reportes_Generados TO medico;

-- PERMISOS ENFERMERO
GRANT SELECT ON Sedes_Hospitalarias, Departamentos, Empleados, Pacientes, Catalogo_Medicamentos, 
    Inventario_Farmacia, Equipamiento, Especialidades, Emp_Posee_Esp TO enfermero;
GRANT SELECT, UPDATE ON Citas TO enfermero;               
GRANT SELECT, INSERT ON Prescripciones TO enfermero;     

-- PERMISOS ADMINISTRATIVO
GRANT SELECT, INSERT, UPDATE, DELETE ON Pacientes, Citas TO administrativo;
GRANT SELECT ON Empleados, Departamentos, Sedes_Hospitalarias, Personas TO administrativo;
GRANT INSERT ON Reportes_Generados TO administrativo;   

-- PERMISOS AUDITOR
GRANT SELECT ON Auditoria_Accesos TO auditor;
GRANT SELECT ON Historias_Clinicas, Diagnostico TO auditor;

-- IMPORTANTE: ELIMINAR O COMENTAR ESTA LÍNEA (pgcrypto no funciona en Azure)
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- LINEA PROBLEMÁTICA

-- EN SU LUGAR, CREAR FUNCIONES DE ENCRIPTACIÓN COMPATIBLES
-- Función para generar salt aleatorio
CREATE OR REPLACE FUNCTION generar_salt() 
RETURNS TEXT AS $$
DECLARE
    caracteres TEXT := 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789./';
    salt TEXT := '';
    i INTEGER;
BEGIN
    FOR i IN 1..16 LOOP
        salt := salt || substr(caracteres, floor(random() * length(caracteres) + 1)::integer, 1);
    END LOOP;
    RETURN salt;
END;
$$ LANGUAGE plpgsql;

-- Función para generar hash de contraseña (SHA-256 nativo de PostgreSQL)
CREATE OR REPLACE FUNCTION hash_contrasena(contrasena TEXT, salt TEXT DEFAULT NULL)
RETURNS TEXT AS $$
DECLARE
    salt_usado TEXT;
BEGIN
    -- Si no se proporciona salt, generar uno
    IF salt IS NULL THEN
        salt_usado := generar_salt();
    ELSE
        salt_usado := salt;
    END IF;
    
    -- Usar SHA-256 que está disponible en PostgreSQL estándar
    -- digest() es una función nativa de PostgreSQL
    RETURN salt_usado || ':' || encode(digest(salt_usado || contrasena, 'sha256'), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Función para verificar contraseña
CREATE OR REPLACE FUNCTION verificar_contrasena(contrasena TEXT, hash_almacenado TEXT)
RETURNS BOOLEAN AS $$
DECLARE
    partes TEXT[];
    salt TEXT;
    hash_calculado TEXT;
BEGIN
    -- Separar salt y hash del valor almacenado
    partes := string_to_array(hash_almacenado, ':');
    
    IF array_length(partes, 1) != 2 THEN
        RETURN FALSE;
    END IF;
    
    salt := partes[1];
    -- Calcular hash con la contraseña proporcionada
    hash_calculado := salt || ':' || encode(digest(salt || contrasena, 'sha256'), 'hex');
    
    RETURN hash_calculado = hash_almacenado;
END;
$$ LANGUAGE plpgsql;

-- VISTAS (IGUAL QUE TU SCRIPT ORIGINAL)
CREATE VIEW vista_historias_consolidadas AS
SELECT 
    hc.cod_hist,
    hc.cod_pac,
    p.nom_persona || ' ' || p.apellido_persona AS nombre_paciente,
    p.num_doc AS documento_paciente,
    hc.fecha_registro,
    c.id_cita,
    c.fecha_hora AS fecha_cita,
    e.id_emp,
    pe.nom_persona || ' ' || pe.apellido_persona AS nombre_empleado,
    s.nom_sede,
    s.ciudad,
    d.nom_dept AS departamento,
    diag.id_diagnostico,
    enf.nombre_enfermedad,
    diag.observacion
FROM Historias_Clinicas hc
INNER JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
INNER JOIN Personas p ON pac.id_persona = p.id_persona
LEFT JOIN Diagnostico diag ON hc.cod_hist = diag.cod_hist
LEFT JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
LEFT JOIN Citas c ON diag.id_cita = c.id_cita
LEFT JOIN Empleados e ON c.id_emp = e.id_emp
LEFT JOIN Personas pe ON e.id_persona = pe.id_persona
LEFT JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
LEFT JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede;

CREATE VIEW vista_medicamentos_recetados_sede AS
SELECT 
    s.id_sede,
    s.nom_sede,
    s.ciudad,
    m.cod_med,
    m.nom_med,
    COUNT(pr.id_presc) AS total_prescripciones,
    SUM(pr.cantidad_total) AS cantidad_total_recetada,
    DATE_TRUNC('month', pr.fecha_emision) AS mes
FROM Prescripciones pr
INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
INNER JOIN Citas c ON pr.id_cita = c.id_cita
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
GROUP BY s.id_sede, s.nom_sede, s.ciudad, m.cod_med, m.nom_med, DATE_TRUNC('month', pr.fecha_emision);

CREATE VIEW vista_medicos_consultas AS
SELECT 
    e.id_emp,
    p.nom_persona || ' ' || p.apellido_persona AS nombre_medico,
    s.nom_sede,
    d.nom_dept,
    esp.nombre_esp AS especialidad,
    COUNT(c.id_cita) AS total_consultas,
    DATE_TRUNC('week', c.fecha_hora) AS semana
FROM Citas c
INNER JOIN Empleados e ON c.id_emp = e.id_emp
INNER JOIN Personas p ON e.id_persona = p.id_persona
INNER JOIN Roles r ON e.id_rol = r.id_rol
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
LEFT JOIN Emp_Posee_Esp epe ON e.id_emp = epe.id_emp
LEFT JOIN Especialidades esp ON epe.id_especialidad = esp.id_especialidad
WHERE r.nombre_rol = 'Medico'
GROUP BY e.id_emp, p.nom_persona, p.apellido_persona, s.nom_sede, d.nom_dept, esp.nombre_esp, DATE_TRUNC('week', c.fecha_hora);

CREATE VIEW vista_enfermedades_por_sede AS
SELECT 
    s.id_sede,
    s.nom_sede,
    s.ciudad,
    enf.id_enfermedad,
    enf.nombre_enfermedad,
    COUNT(DISTINCT diag.id_diagnostico) AS total_diagnosticos,
    COUNT(DISTINCT hc.cod_pac) AS pacientes_afectados,
    DATE_TRUNC('month', hc.fecha_registro) AS mes
FROM Diagnostico diag
INNER JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
INNER JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
INNER JOIN Citas c ON diag.id_cita = c.id_cita
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
GROUP BY s.id_sede, s.nom_sede, s.ciudad, enf.id_enfermedad, enf.nombre_enfermedad, DATE_TRUNC('month', hc.fecha_registro);

CREATE VIEW vista_inventario_consolidado AS
SELECT 
    s.id_sede,
    s.nom_sede,
    s.ciudad,
    m.cod_med,
    m.nom_med,
    m.principio_activo,
    i.stock_actual,
    i.fecha_actualizacion,
    CASE 
        WHEN i.stock_actual < 10 THEN 'CRÍTICO'
        WHEN i.stock_actual < 50 THEN 'BAJO'
        WHEN i.stock_actual < 100 THEN 'MEDIO'
        ELSE 'ÓPTIMO'
    END AS nivel_stock
FROM Inventario_Farmacia i
INNER JOIN Sedes_Hospitalarias s ON i.id_sede = s.id_sede
INNER JOIN Catalogo_Medicamentos m ON i.cod_med = m.cod_med;

CREATE VIEW vista_equipamiento_departamentos AS
SELECT 
    eq.nom_eq,
    eq.marca_modelo,
    s.id_sede,
    s.nom_sede,
    d.id_dept,
    d.nom_dept,
    eq.estado_equipo,
    eq.fecha_ultimo_maint,
    pe.nom_persona || ' ' || pe.apellido_persona AS responsable
FROM Equipamiento eq
INNER JOIN Departamentos d ON eq.id_dept = d.id_dept AND eq.id_sede = d.id_sede
INNER JOIN Sedes_Hospitalarias s ON d.id_sede = s.id_sede
LEFT JOIN Empleados e ON eq.responsable_id = e.id_emp
LEFT JOIN Personas pe ON e.id_persona = pe.id_persona;

CREATE VIEW vista_auditoria_historias AS
SELECT 
    aa.id_evento,
    aa.id_emp,
    p.nom_persona || ' ' || p.apellido_persona AS empleado,
    r.nombre_rol AS rol_empleado,
    s.nom_sede,
    aa.accion,
    aa.tabla_afectada,
    aa.id_registro_afectado,
    aa.fecha_evento,
    aa.ip_origen
FROM Auditoria_Accesos aa
LEFT JOIN Empleados e ON aa.id_emp = e.id_emp
LEFT JOIN Personas p ON e.id_persona = p.id_persona
LEFT JOIN Roles r ON e.id_rol = r.id_rol
LEFT JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
WHERE aa.tabla_afectada = 'Historias_Clinicas'
ORDER BY aa.fecha_evento DESC;

CREATE VIEW vista_tiempos_atencion AS
SELECT 
    s.id_sede,
    s.nom_sede,
    d.nom_dept,
    AVG(EXTRACT(EPOCH FROM (hc.fecha_registro - c.fecha_hora))/3600) AS horas_promedio_atencion,
    COUNT(*) AS total_casos,
    DATE_TRUNC('month', c.fecha_hora) AS mes
FROM Citas c
INNER JOIN Historias_Clinicas hc ON c.cod_pac = hc.cod_pac
INNER JOIN Diagnostico diag ON diag.id_cita = c.id_cita AND diag.cod_hist = hc.cod_hist
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
GROUP BY s.id_sede, s.nom_sede, d.nom_dept, DATE_TRUNC('month', c.fecha_hora);

CREATE VIEW vista_consumo_medicamentos_dept AS
SELECT 
    d.id_dept,
    d.nom_dept,
    s.id_sede,
    s.nom_sede,
    m.cod_med,
    m.nom_med,
    COUNT(pr.id_presc) AS total_prescripciones,
    SUM(pr.cantidad_total) AS cantidad_consumida,
    DATE_TRUNC('month', pr.fecha_emision) AS mes
FROM Prescripciones pr
INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
INNER JOIN Citas c ON pr.id_cita = c.id_cita
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
GROUP BY d.id_dept, d.nom_dept, s.id_sede, s.nom_sede, m.cod_med, m.nom_med, DATE_TRUNC('month', pr.fecha_emision);

CREATE VIEW vista_utilizacion_recursos AS
SELECT 
    s.id_sede,
    s.nom_sede,
    COUNT(DISTINCT c.id_cita) AS total_citas,
    COUNT(DISTINCT hc.cod_hist) AS total_historias,
    COUNT(DISTINCT eq.cod_eq) AS total_equipamiento,
    COUNT(DISTINCT e.id_emp) AS total_empleados,
    COUNT(DISTINCT pac.cod_pac) AS total_pacientes_atendidos,
    DATE_TRUNC('month', c.fecha_hora) AS mes
FROM Sedes_Hospitalarias s
LEFT JOIN Citas c ON s.id_sede = c.id_sede
LEFT JOIN Historias_Clinicas hc ON c.cod_pac = hc.cod_pac
LEFT JOIN Equipamiento eq ON s.id_sede = eq.id_sede
LEFT JOIN Empleados e ON s.id_sede = e.id_sede
LEFT JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
GROUP BY s.id_sede, s.nom_sede, DATE_TRUNC('month', c.fecha_hora);

-- CONCEDER PERMISOS A LAS VISTAS
GRANT SELECT ON vista_historias_consolidadas TO medico, enfermero, auditor, administrador;
GRANT SELECT ON vista_medicamentos_recetados_sede TO medico, enfermero, administrativo, administrador;
GRANT SELECT ON vista_medicos_consultas TO medico, administrativo, administrador;
GRANT SELECT ON vista_enfermedades_por_sede TO medico, auditor, administrador;
GRANT SELECT ON vista_inventario_consolidado TO medico, enfermero, administrativo, administrador;
GRANT SELECT ON vista_equipamiento_departamentos TO medico, enfermero, administrativo, administrador;
GRANT SELECT ON vista_auditoria_historias TO auditor, administrador;
GRANT SELECT ON vista_tiempos_atencion TO medico, administrativo, administrador;
GRANT SELECT ON vista_consumo_medicamentos_dept TO medico, enfermero, administrativo, administrador;
GRANT SELECT ON vista_utilizacion_recursos TO administrador, administrativo;

-- MENSAJE FINAL
DO $$ 
BEGIN
    RAISE NOTICE 'Script ejecutado correctamente para Azure PostgreSQL';
    RAISE NOTICE 'pgcrypto reemplazado por funciones nativas de PostgreSQL (SHA-256)';
    RAISE NOTICE 'hash_contra cambiado de VARCHAR(255) a TEXT';
END $$;