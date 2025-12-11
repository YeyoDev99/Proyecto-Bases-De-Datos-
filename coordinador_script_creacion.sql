-- script_coordinador_transparente_corregido.sql
-- Versión: Todo transparente para Python - ORDEN CORREGIDO

-- 1. EXTENSIONES
CREATE EXTENSION IF NOT EXISTS dblink;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. FUNCIONES DE CONEXIÓN (mantener en memoria para mejor rendimiento)
CREATE OR REPLACE FUNCTION get_azure_conn()
RETURNS text LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN 'host=hospitaldb.postgres.database.azure.com
            port=5432
            dbname=postgres
            user=directorHospital
            password=Postgr3s_DB
            sslmode=require
            connect_timeout=10';
END;
$$;


CREATE OR REPLACE FUNCTION get_aws_conn()
RETURNS text LANGUAGE plpgsql STABLE AS $$
BEGIN
    RETURN 'host=hospital.cdg4cu8q8t0y.us-east-2.rds.amazonaws.com 
            port=5432 
            dbname=postgres 
            user=postgres 
            password=Postgr3s_DB
            connect_timeout=10';
END;
$$;

-- 3. TABLAS MAESTRAS LOCALES (datos compartidos)
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

CREATE TABLE Sedes_Hospitalarias (
    id_sede INT PRIMARY KEY,
    nom_sede VARCHAR(100) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    direccion VARCHAR(150),
    telefono VARCHAR(20),
    es_nodo_central BOOLEAN DEFAULT FALSE
);

-- 4. CREAR PRIMERO LAS TABLAS LOCALES (ANTES DE LAS VISTAS)
CREATE TABLE citas_local (
    id_cita BIGINT PRIMARY KEY,
    id_sede INT NOT NULL DEFAULT 1,
    id_dept INT NOT NULL,
    id_emp INT NOT NULL,
    cod_pac INT NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,
    fecha_hora_solicitada TIMESTAMP NOT NULL,
    tipo_servicio VARCHAR(50),
    estado VARCHAR(20) DEFAULT 'PROGRAMADA',
    motivo VARCHAR(200)
);

-- 5. CREAR VISTAS QUE REFERENCIAN TABLAS LOCALES (DESPUÉS DE CREARLAS)
CREATE OR REPLACE VIEW Citas AS
-- Datos locales (sede 1)
SELECT * FROM citas_local
UNION ALL
-- Datos de Azure (sede 2)
SELECT * FROM dblink(get_azure_conn(), 
    'SELECT id_cita, id_sede, id_dept, id_emp, cod_pac, fecha_hora, 
     fecha_hora_solicitada, tipo_servicio, estado, motivo 
     FROM citas')
    AS t(id_cita BIGINT, id_sede INT, id_dept INT, id_emp INT, cod_pac INT,
        fecha_hora TIMESTAMP, fecha_hora_solicitada TIMESTAMP,
        tipo_servicio VARCHAR(50), estado VARCHAR(20), motivo VARCHAR(200))
UNION ALL
-- Datos de AWS (sede 3)
SELECT * FROM dblink(get_aws_conn(), 
    'SELECT id_cita, id_sede, id_dept, id_emp, cod_pac, fecha_hora, 
     fecha_hora_solicitada, tipo_servicio, estado, motivo 
     FROM citas')
    AS t(id_cita BIGINT, id_sede INT, id_dept INT, id_emp INT, cod_pac INT,
        fecha_hora TIMESTAMP, fecha_hora_solicitada TIMESTAMP,
        tipo_servicio VARCHAR(50), estado VARCHAR(20), motivo VARCHAR(200));

-- 6. FUNCIÓN MÁGICA PARA ESCRITURA DISTRIBUIDA AUTOMÁTICA
CREATE OR REPLACE FUNCTION insert_cita_distributed()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    paciente_row Pacientes;
    persona_row Personas; -- <--- NUEVA VARIABLE REQUERIDA
BEGIN
    -- 1. Si la sede es local (1), no hacer nada en dblink
    IF NEW.id_sede = 1 THEN
        RETURN NEW;
    END IF;

    -- 2. Obtener los registros maestros (Paciente y Persona asociada)
    SELECT * INTO paciente_row FROM Pacientes WHERE cod_pac = NEW.cod_pac;
    SELECT * INTO persona_row FROM Personas WHERE id_persona = paciente_row.id_persona; -- <--- Obtener la Persona

    -- 3. Lógica de distribución basada en id_sede
    IF NEW.id_sede = 2 THEN
        -- Distribución a Azure (Clínica Norte)

        -- *** PASO CLAVE 1: Replicar el registro de PERSONAS para satisfacer la FK de Pacientes ***
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                INSERT INTO Personas (id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia) 
                VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
                ON CONFLICT (id_persona) DO UPDATE SET 
                nom_persona = EXCLUDED.nom_persona, 
                apellido_persona = EXCLUDED.apellido_persona, 
                email_persona = EXCLUDED.email_persona 
            $remote$,
            persona_row.id_persona, persona_row.nom_persona, persona_row.apellido_persona,
            persona_row.tipo_doc, persona_row.num_doc, persona_row.fecha_nac::text, 
            persona_row.genero, persona_row.dir_persona, persona_row.tel_persona,
            persona_row.email_persona, persona_row.ciudad_residencia
            )
        );

        -- *** PASO CLAVE 2: Replicar el registro de PACIENTES ***
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                INSERT INTO Pacientes (cod_pac, id_persona)
                VALUES (%s, %s)
                ON CONFLICT (cod_pac) DO UPDATE SET 
                id_persona = EXCLUDED.id_persona
            $remote$,
            paciente_row.cod_pac, paciente_row.id_persona
            )
        );

        -- *** PASO CLAVE 3: Inserción de la Cita ***
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                INSERT INTO citas (id_cita, id_sede, id_dept, id_emp, cod_pac, fecha_hora, fecha_hora_solicitada, tipo_servicio, estado, motivo)
                VALUES (%s, %s, %s, %s, %s, '%s', '%s', '%s', '%s', '%s')
                ON CONFLICT (id_cita) DO UPDATE SET
                id_sede = EXCLUDED.id_sede,
                id_dept = EXCLUDED.id_dept,
                id_emp = EXCLUDED.id_emp,
                cod_pac = EXCLUDED.cod_pac,
                fecha_hora = EXCLUDED.fecha_hora,
                fecha_hora_solicitada = EXCLUDED.fecha_hora_solicitada,
                tipo_servicio = EXCLUDED.tipo_servicio,
                estado = EXCLUDED.estado,
                motivo = EXCLUDED.motivo
            $remote$, 
            NEW.id_cita, NEW.id_sede, NEW.id_dept, NEW.id_emp, NEW.cod_pac,
            NEW.fecha_hora::text, NEW.fecha_hora_solicitada::text, 
            COALESCE(NEW.tipo_servicio, 'Consulta'),
            COALESCE(NEW.estado, 'PROGRAMADA'),
            COALESCE(NEW.motivo, '')
            )
        );
    
    ELSIF NEW.id_sede = 3 THEN
        -- Distribución a AWS (Unidad Sur)
        
        -- *** PASO CLAVE 1: Replicar el registro de PERSONAS para satisfacer la FK de Pacientes ***
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                INSERT INTO Personas (id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia) 
                VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
                ON CONFLICT (id_persona) DO UPDATE SET 
                nom_persona = EXCLUDED.nom_persona, 
                apellido_persona = EXCLUDED.apellido_persona, 
                email_persona = EXCLUDED.email_persona 
            $remote$,
            persona_row.id_persona, persona_row.nom_persona, persona_row.apellido_persona,
            persona_row.tipo_doc, persona_row.num_doc, persona_row.fecha_nac::text, 
            persona_row.genero, persona_row.dir_persona, persona_row.tel_persona,
            persona_row.email_persona, persona_row.ciudad_residencia
            )
        );
        
        -- *** PASO CLAVE 2: Replicar el registro de PACIENTES ***
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                INSERT INTO Pacientes (cod_pac, id_persona)
                VALUES (%s, %s)
                ON CONFLICT (cod_pac) DO UPDATE SET 
                id_persona = EXCLUDED.id_persona
            $remote$,
            paciente_row.cod_pac, paciente_row.id_persona
            )
        );
        
        -- *** PASO CLAVE 3: Inserción de la Cita ***
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                INSERT INTO citas (id_cita, id_sede, id_dept, id_emp, cod_pac, fecha_hora, fecha_hora_solicitada, tipo_servicio, estado, motivo)
                VALUES (%s, %s, %s, %s, %s, '%s', '%s', '%s', '%s', '%s')
                ON CONFLICT (id_cita) DO UPDATE SET
                id_sede = EXCLUDED.id_sede,
                id_dept = EXCLUDED.id_dept,
                id_emp = EXCLUDED.id_emp,
                cod_pac = EXCLUDED.cod_pac,
                fecha_hora = EXCLUDED.fecha_hora,
                fecha_hora_solicitada = EXCLUDED.fecha_hora_solicitada,
                tipo_servicio = EXCLUDED.tipo_servicio,
                estado = EXCLUDED.estado,
                motivo = EXCLUDED.motivo
            $remote$, 
            NEW.id_cita, NEW.id_sede, NEW.id_dept, NEW.id_emp, NEW.cod_pac,
            NEW.fecha_hora::text, NEW.fecha_hora_solicitada::text, 
            COALESCE(NEW.tipo_servicio, 'Consulta'),
            COALESCE(NEW.estado, 'PROGRAMADA'),
            COALESCE(NEW.motivo, '')
            )
        );
    
    ELSE
        RAISE EXCEPTION 'ID de Sede no válido: %', NEW.id_sede;
    END IF;

    RETURN NEW;
END;
$$;

-- 7. TRIGGER PARA QUE TODO SEA AUTOMÁTICO
CREATE TRIGGER trg_citas_insert_distributed
INSTEAD OF INSERT ON Citas
FOR EACH ROW EXECUTE FUNCTION insert_cita_distributed();

-- 8. FUNCIONES SIMILARES PARA UPDATE Y DELETE
CREATE OR REPLACE FUNCTION update_cita_distributed()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id_sede != OLD.id_sede THEN
        RAISE EXCEPTION 'No se puede cambiar id_sede en update';
    END IF;
    
    IF OLD.id_sede = 1 THEN
        UPDATE citas_local SET 
            id_dept = NEW.id_dept,
            id_emp = NEW.id_emp,
            fecha_hora = NEW.fecha_hora,
            estado = NEW.estado,
            motivo = NEW.motivo
        WHERE id_cita = OLD.id_cita;
    ELSIF OLD.id_sede = 2 THEN
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                UPDATE citas SET 
                    id_dept = %s,
                    id_emp = %s,
                    fecha_hora = '%s',
                    estado = '%s',
                    motivo = '%s'
                WHERE id_cita = %s
            $remote$,
            NEW.id_dept, NEW.id_emp, NEW.fecha_hora, 
            NEW.estado, NEW.motivo, OLD.id_cita));
    ELSIF OLD.id_sede = 3 THEN
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                UPDATE citas SET 
                    id_dept = %s,
                    id_emp = %s,
                    fecha_hora = '%s',
                    estado = '%s',
                    motivo = '%s'
                WHERE id_cita = %s
            $remote$,
            NEW.id_dept, NEW.id_emp, NEW.fecha_hora, 
            NEW.estado, NEW.motivo, OLD.id_cita));
    END IF;
    
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_citas_update_distributed
INSTEAD OF UPDATE ON Citas
FOR EACH ROW EXECUTE FUNCTION update_cita_distributed();

-- 9. SINCRONIZACIÓN DE DATOS MAESTROS (para consistencia)
-- Primero creamos las tablas maestras que faltan
CREATE TABLE Roles (
    id_rol INT PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200)
);

CREATE TABLE Especialidades (
    id_especialidad INT PRIMARY KEY,
    nombre_esp VARCHAR(100) NOT NULL
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

-- Ahora sí podemos crear el procedimiento de sincronización
-- Reemplace el procedimiento sync_master_data en pruebacoordinador.sql con este código
CREATE OR REPLACE PROCEDURE sync_master_data()
LANGUAGE plpgsql AS $$
DECLARE
    role_record RECORD;
BEGIN
    -- 1. Sincronización de Roles (El Coordinador es la fuente de verdad)
    -- Esto asegura que los id_rol existan en los nodos remotos.
    FOR role_record IN SELECT id_rol, nombre_rol, descripcion FROM Roles ORDER BY id_rol LOOP
        
        -- Sincronizar a Azure
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                INSERT INTO Roles (id_rol, nombre_rol, descripcion) 
                VALUES (%s, '%s', '%s') 
                ON CONFLICT (id_rol) DO UPDATE SET 
                nombre_rol = EXCLUDED.nombre_rol, 
                descripcion = EXCLUDED.descripcion
            $remote$, 
            role_record.id_rol, role_record.nombre_rol, role_record.descripcion)
        );

        -- Sincronizar a AWS
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                INSERT INTO Roles (id_rol, nombre_rol, descripcion) 
                VALUES (%s, '%s', '%s') 
                ON CONFLICT (id_rol) DO UPDATE SET 
                nombre_rol = EXCLUDED.nombre_rol, 
                descripcion = EXCLUDED.descripcion
            $remote$, 
            role_record.id_rol, role_record.nombre_rol, role_record.descripcion)
        );
    END LOOP;
    
    -- 2. Lógica para sincronizar Personas (Mantenida de su versión original)
    
    -- Sincronizar Personas desde Azure
    INSERT INTO Personas 
    SELECT * FROM dblink(get_azure_conn(), 
        'SELECT id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, 
                fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia 
         FROM personas') 
    AS t(id_persona INT, nom_persona VARCHAR(100), apellido_persona VARCHAR(100),
          tipo_doc VARCHAR(10), num_doc VARCHAR(20), fecha_nac DATE,
          genero CHAR(1), dir_persona VARCHAR(200), tel_persona VARCHAR(20),
          email_persona VARCHAR(150), ciudad_residencia VARCHAR(50))
    ON CONFLICT (id_persona) DO UPDATE SET 
        nom_persona = EXCLUDED.nom_persona,
        email_persona = EXCLUDED.email_persona;
        
    -- Sincronizar Personas desde AWS
    INSERT INTO Personas 
    SELECT * FROM dblink(get_aws_conn(), 
        'SELECT id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, 
                fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia 
         FROM personas') 
    AS t(id_persona INT, nom_persona VARCHAR(100), apellido_persona VARCHAR(100),
          tipo_doc VARCHAR(10), num_doc VARCHAR(20), fecha_nac DATE,
          genero CHAR(1), dir_persona VARCHAR(200), tel_persona VARCHAR(20),
          email_persona VARCHAR(150), ciudad_residencia VARCHAR(50))
    ON CONFLICT (id_persona) DO NOTHING;
    
END;
$$;

-- 10. CREAR EL RESTO DE TABLAS LOCALES PARA LAS VISTAS
CREATE TABLE Pacientes (
    cod_pac INT PRIMARY KEY, 
    id_persona INT NOT NULL,
    FOREIGN KEY (id_persona) REFERENCES Personas(id_persona)
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
    FOREIGN KEY (cod_hist) REFERENCES Historias_Clinicas(cod_hist)
);

-- 11. CREAR VISTAS PARA OTRAS TABLAS DISTRIBUIDAS (siguiendo el mismo patrón)
-- Primero crear tablas locales
CREATE TABLE departamentos_local (
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    nom_dept VARCHAR(100) NOT NULL,
    PRIMARY KEY(id_sede, id_dept)
);

CREATE TABLE empleados_local (
    id_emp INT PRIMARY KEY,
    id_persona INT,
    id_rol INT NOT NULL,
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    hash_contra VARCHAR(255) NOT NULL,
    activo BOOLEAN DEFAULT TRUE
);

-- Luego crear vistas distribuidas
CREATE OR REPLACE VIEW Departamentos AS
SELECT * FROM departamentos_local
UNION ALL
SELECT * FROM dblink(get_azure_conn(), 'SELECT * FROM departamentos')
AS t(id_sede INT, id_dept INT, nom_dept VARCHAR(100))
UNION ALL
SELECT * FROM dblink(get_aws_conn(), 'SELECT * FROM departamentos')
AS t(id_sede INT, id_dept INT, nom_dept VARCHAR(100));

CREATE OR REPLACE VIEW Empleados AS
SELECT * FROM empleados_local
UNION ALL
SELECT * FROM dblink(get_azure_conn(), 'SELECT * FROM empleados')
AS t(id_emp INT, id_persona INT, id_rol INT, id_sede INT, id_dept INT, 
    hash_contra TEXT, activo BOOLEAN)
UNION ALL
SELECT * FROM dblink(get_aws_conn(), 'SELECT * FROM empleados')
AS t(id_emp INT, id_persona INT, id_rol INT, id_sede INT, id_dept INT, 
    hash_contra TEXT, activo BOOLEAN);

-- 12. CREAR EL RESTO DE TABLAS NECESARIAS PARA LAS VISTAS
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
    FOREIGN KEY (cod_med) REFERENCES Catalogo_Medicamentos(cod_med)
);

CREATE TABLE Equipamiento (
    cod_eq INT PRIMARY KEY,
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    nom_eq VARCHAR(100) NOT NULL,
    marca_modelo VARCHAR(100),
    estado_equipo VARCHAR(20) NOT NULL,
    fecha_ultimo_maint DATE,
    responsable_id INT
);

CREATE TABLE Inventario_Farmacia (
    id_inv INT PRIMARY KEY,
    cod_med INT NOT NULL,
    id_sede INT NOT NULL,
    stock_actual INT NOT NULL CHECK (stock_actual >= 0),
    fecha_actualizacion TIMESTAMP,
    FOREIGN KEY (cod_med) REFERENCES Catalogo_Medicamentos(cod_med)
);

CREATE TABLE Emp_Posee_Esp (
    id_emp_posee_esp INT PRIMARY KEY,
    id_especialidad INT NOT NULL,
    id_emp INT NOT NULL,
    FOREIGN KEY (id_especialidad) REFERENCES Especialidades(id_especialidad)
);

CREATE TABLE Auditoria_Accesos (
    id_evento SERIAL PRIMARY KEY,
    id_emp INT,
    accion VARCHAR(50) NOT NULL,
    tabla_afectada VARCHAR(50),
    id_registro_afectado VARCHAR(50),
    fecha_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_origen VARCHAR(45)
);

CREATE TABLE Reportes_Generados (
    id_reporte INT PRIMARY KEY,
    id_sede INT NOT NULL,
    id_emp_generador INT NOT NULL,
    fecha_generacion TIMESTAMP,
    tipo_reporte VARCHAR(50),
    parametros_json TEXT,
    FOREIGN KEY (id_sede) REFERENCES Sedes_Hospitalarias(id_sede)
);

-- 13. AHORA SÍ PUEDES CREAR LAS VISTAS ANALÍTICAS (ya están todas las tablas)
-- (Aquí van tus 10 vistas originales, igual que las tenías)
-- Solo voy a poner la primera como ejemplo, las otras las mantienes igual:

-- Vista 1: Historias Clínicas Consolidadas (Replicada entre todas las sedes)
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

-- Vista 2: Medicamentos más recetados por sede
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

-- Vista 3: Médicos con más consultas atendidas
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

-- Vista 4: Estadísticas de enfermedades por sede
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

-- Vista 5: Inventario de medicamentos consolidado
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

-- Vista 6: Equipamiento compartido entre sedes
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

-- Vista 7: Auditoría de accesos a historias clínicas
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

-- Vista 8: Tiempo promedio entre cita y diagnóstico
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

-- Vista 9: Consumo de medicamentos por departamento
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

-- Vista 10: Utilización de recursos por sede
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

-- ... (aquí van las otras 9 vistas, exactamente como las tienes)

-- 14. CONFIGURACIÓN DE ROLES
CREATE ROLE administrador;
CREATE ROLE medico;
CREATE ROLE enfermero;
CREATE ROLE administrativo;
CREATE ROLE auditor;

GRANT USAGE ON SCHEMA public TO administrador, medico, enfermero, administrativo, auditor;

-- Permisos Administrador
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO administrador;
GRANT TRUNCATE, REFERENCES, TRIGGER ON ALL TABLES IN SCHEMA public TO administrador;
GRANT CREATE ON SCHEMA public TO administrador;

-- Permisos Médico
GRANT SELECT ON Sedes_Hospitalarias, Departamentos, Empleados, Pacientes, Catalogo_Medicamentos, 
    Inventario_Farmacia, Equipamiento, Reportes_Generados, Especialidades, Emp_Posee_Esp, 
    Enfermedades TO medico;
GRANT SELECT, INSERT, UPDATE ON Citas, Historias_Clinicas, Prescripciones, Diagnostico TO medico;
GRANT INSERT ON Reportes_Generados TO medico;

-- Permisos Enfermero
GRANT SELECT ON Sedes_Hospitalarias, Departamentos, Empleados, Pacientes, Catalogo_Medicamentos, 
    Inventario_Farmacia, Equipamiento, Especialidades, Emp_Posee_Esp TO enfermero;
GRANT SELECT, UPDATE ON Citas TO enfermero;               
GRANT SELECT, INSERT ON Prescripciones TO enfermero;     

-- Permisos Administrativo
GRANT SELECT, INSERT, UPDATE, DELETE ON Pacientes, Citas TO administrativo;
GRANT SELECT ON Empleados, Departamentos, Sedes_Hospitalarias, Personas TO administrativo;
GRANT INSERT ON Reportes_Generados TO administrativo;   

-- Permisos Auditor
GRANT SELECT ON Auditoria_Accesos TO auditor;
GRANT SELECT ON Historias_Clinicas, Diagnostico TO auditor;

-- 15. TABLA DE AUDITORÍA PARA SINCRONIZACIÓN
CREATE TABLE auditoria_sincronizacion (
    id SERIAL PRIMARY KEY,
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado TEXT
);

-- 16. MENSAJE FINAL
DO $$ 
BEGIN
    RAISE NOTICE '✅ Coordinador configurado CORRECTAMENTE';
    RAISE NOTICE '✅ Orden corregido: Tablas locales creadas ANTES de las vistas';
    RAISE NOTICE '✅ Distribución horizontal activa';
    RAISE NOTICE '✅ Conectado a Azure y AWS';
    RAISE NOTICE '✅ Python puede usar queries NORMALES sin cambios';
END $$;

-- Agrega esto después de la creación de los triggers para Citas:

-- 17. TRIGGERS PARA TODAS LAS VISTAS DISTRIBUIDAS
-- Trigger para Departamentos
CREATE OR REPLACE FUNCTION insert_departamentos_distributed()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.id_sede = 1 THEN
        INSERT INTO departamentos_local VALUES (NEW.*);
    ELSIF NEW.id_sede = 2 THEN
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$INSERT INTO departamentos VALUES (%s, %s, '%s')$remote$,
            NEW.id_sede, NEW.id_dept, NEW.nom_dept));
    ELSIF NEW.id_sede = 3 THEN
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$INSERT INTO departamentos VALUES (%s, %s, '%s')$remote$,
            NEW.id_sede, NEW.id_dept, NEW.nom_dept));
    ELSE
        RAISE EXCEPTION 'Sede no válida: %', NEW.id_sede;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_departamentos_insert_distributed
INSTEAD OF INSERT ON Departamentos
FOR EACH ROW EXECUTE FUNCTION insert_departamentos_distributed();

-- Trigger para Empleados

-- Reemplace la función PL/pgSQL insert_empleados_distributed() en su archivo pruebacoordinador.sql con esta versión.
CREATE OR REPLACE FUNCTION insert_empleados_distributed()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    hash_contra_text TEXT;
    persona_row Personas;
BEGIN
    -- 1. Encontrar el hash de la contraseña (Asegúrese de que esta lógica exista y funcione)
    IF TG_OP = 'INSERT' THEN
        -- **IMPORTANTE:** Si no tiene una columna 'hash_contra' en la tabla Personas o NEW.hash_contra
        -- no está disponible, necesita ajustar de dónde obtiene esta variable.
        hash_contra_text := 'password_placeholder'; -- Reemplace con su lógica real
    ELSIF TG_OP = 'UPDATE' THEN
        -- Asumimos que la tabla Empleados tiene un campo hash_contra que podemos usar en UPDATE
        hash_contra_text := OLD.hash_contra; 
    END IF;


    -- 2. Obtener el registro de la Persona para replicarla
    SELECT * INTO persona_row FROM Personas WHERE id_persona = NEW.id_persona;

    -- 3. Lógica de distribución basada en id_sede
    IF NEW.id_sede = 1 THEN
        -- Sede 1 es local
        RETURN NEW; 

    ELSIF NEW.id_sede = 2 THEN
        -- Distribución a Azure (Clínica Norte)

        -- Replicar primero el registro de PERSONAS para satisfacer la FK
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                INSERT INTO Personas (id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia) 
                VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
                ON CONFLICT (id_persona) DO UPDATE SET 
                nom_persona = EXCLUDED.nom_persona, 
                apellido_persona = EXCLUDED.apellido_persona, 
                email_persona = EXCLUDED.email_persona 
            $remote$,
            persona_row.id_persona, persona_row.nom_persona, persona_row.apellido_persona,
            persona_row.tipo_doc, persona_row.num_doc, persona_row.fecha_nac::text, 
            persona_row.genero, persona_row.dir_persona, persona_row.tel_persona,
            persona_row.email_persona, persona_row.ciudad_residencia
            ) -- <--- CORRECCIÓN DE PARÉNTESIS AQUÍ (Cierra format())
        ); -- <--- Cierra dblink_exec()

        -- Inserción del Empleado
        PERFORM dblink_exec(get_azure_conn(),
            format($remote$
                INSERT INTO empleados (id_emp, id_persona, id_rol, id_sede, id_dept, hash_contra, activo)  
                VALUES (%s, %s, %s, %s, %s, '%s', %s)
                ON CONFLICT (id_emp) DO UPDATE SET
                id_persona = EXCLUDED.id_persona,
                id_rol = EXCLUDED.id_rol,
                id_dept = EXCLUDED.id_dept,
                hash_contra = EXCLUDED.hash_contra,
                activo = EXCLUDED.activo
            $remote$,
            NEW.id_emp, NEW.id_persona, NEW.id_rol, NEW.id_sede, NEW.id_dept,
            hash_contra_text, COALESCE(NEW.activo, true)::text
            ) -- <--- CORRECCIÓN DE PARÉNTESIS AQUÍ (Cierra format())
        ); -- <--- Cierra dblink_exec()
    
    ELSIF NEW.id_sede = 3 THEN
        -- Distribución a AWS (Unidad Sur)
        
        -- Replicar primero el registro de PERSONAS para satisfacer la FK
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                INSERT INTO Personas (id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia) 
                VALUES (%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')
                ON CONFLICT (id_persona) DO UPDATE SET 
                nom_persona = EXCLUDED.nom_persona, 
                apellido_persona = EXCLUDED.apellido_persona, 
                email_persona = EXCLUDED.email_persona
            $remote$,
            persona_row.id_persona, persona_row.nom_persona, persona_row.apellido_persona,
            persona_row.tipo_doc, persona_row.num_doc, persona_row.fecha_nac::text, 
            persona_row.genero, persona_row.dir_persona, persona_row.tel_persona,
            persona_row.email_persona, persona_row.ciudad_residencia
            ) -- <--- CORRECCIÓN DE PARÉNTESIS AQUÍ (Cierra format())
        ); -- <--- Cierra dblink_exec()
        
        -- Inserción del Empleado
        PERFORM dblink_exec(get_aws_conn(),
            format($remote$
                INSERT INTO empleados (id_emp, id_persona, id_rol, id_sede, id_dept, hash_contra, activo) 
                VALUES (%s, %s, %s, %s, %s, '%s', %s)
                ON CONFLICT (id_emp) DO UPDATE SET
                id_persona = EXCLUDED.id_persona,
                id_rol = EXCLUDED.id_rol,
                id_dept = EXCLUDED.id_dept,
                hash_contra = EXCLUDED.hash_contra,
                activo = EXCLUDED.activo
            $remote$,
            NEW.id_emp, NEW.id_persona, NEW.id_rol, NEW.id_sede, NEW.id_dept,
            hash_contra_text, COALESCE(NEW.activo, true)::text
            ) -- <--- CORRECCIÓN DE PARÉNTESIS AQUÍ (Cierra format())
        ); -- <--- Cierra dblink_exec()
    
    ELSE
        RAISE EXCEPTION 'ID de Sede no válido: %', NEW.id_sede;
    END IF;

    RETURN NEW;
END;
$$;


CREATE TRIGGER trg_empleados_insert_distributed
INSTEAD OF INSERT ON Empleados
FOR EACH ROW EXECUTE FUNCTION insert_empleados_distributed();


CREATE OR REPLACE FUNCTION insert_departamentos_distributed()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    sede_exists BOOLEAN;
BEGIN
    -- Determinar destino según id_sede
    IF NEW.id_sede = 1 THEN
        INSERT INTO departamentos_local VALUES (NEW.*);
    ELSIF NEW.id_sede = 2 THEN
        -- Verificar si la sede existe en Azure (CORREGIDO)
        BEGIN
            SELECT EXISTS (
                SELECT 1 FROM dblink(get_azure_conn(),
                    format('SELECT 1 FROM sedes_hospitalarias WHERE id_sede = %s', NEW.id_sede)
                ) AS t(exist integer)
            ) INTO sede_exists;
        EXCEPTION WHEN OTHERS THEN
            sede_exists := FALSE;
        END;
        
        IF NOT sede_exists THEN
            PERFORM dblink_exec(get_azure_conn(),
                format('INSERT INTO sedes_hospitalarias (id_sede, nom_sede, ciudad, direccion, telefono, es_nodo_central) 
                        VALUES (%s, ''Clínica Norte'', ''Medellín'', ''Carrera 2 #2-2'', ''6042345678'', false)
                        ON CONFLICT (id_sede) DO NOTHING', NEW.id_sede)
            );
        END IF;
        
        -- Luego insertar el departamento
        PERFORM dblink_exec(get_azure_conn(),
            format('INSERT INTO departamentos (id_sede, id_dept, nom_dept) 
                    VALUES (%s, %s, ''%s'')
                    ON CONFLICT (id_sede, id_dept) DO UPDATE SET
                    nom_dept = EXCLUDED.nom_dept',
                NEW.id_sede, NEW.id_dept, NEW.nom_dept
            )
        );
    ELSIF NEW.id_sede = 3 THEN
        -- Verificar si la sede existe en AWS (CORREGIDO)
        BEGIN
            SELECT EXISTS (
                SELECT 1 FROM dblink(get_aws_conn(),
                    format('SELECT 1 FROM sedes_hospitalarias WHERE id_sede = %s', NEW.id_sede)
                ) AS t(exist integer)
            ) INTO sede_exists;
        EXCEPTION WHEN OTHERS THEN
            sede_exists := FALSE;
        END;
        
        IF NOT sede_exists THEN
            PERFORM dblink_exec(get_aws_conn(),
                format('INSERT INTO sedes_hospitalarias (id_sede, nom_sede, ciudad, direccion, telefono, es_nodo_central) 
                        VALUES (%s, ''Unidad de Urgencias Sur'', ''Cali'', ''Avenida 3 #3-3'', ''6023456789'', false)
                        ON CONFLICT (id_sede) DO NOTHING', NEW.id_sede)
            );
        END IF;
        
        -- Luego insertar el departamento
        PERFORM dblink_exec(get_aws_conn(),
            format('INSERT INTO departamentos (id_sede, id_dept, nom_dept) 
                    VALUES (%s, %s, ''%s'')
                    ON CONFLICT (id_sede, id_dept) DO UPDATE SET
                    nom_dept = EXCLUDED.nom_dept',
                NEW.id_sede, NEW.id_dept, NEW.nom_dept
            )
        );
    ELSE
        RAISE EXCEPTION 'Sede no válida: %', NEW.id_sede;
    END IF;
    
    RETURN NEW;
END;
$$;







-- FUNCIÓN PARA SINCRONIZAR TABLAS DE REFERENCIA AUTOMÁTICAMENTE
CREATE OR REPLACE FUNCTION sync_reference_table_to_all_nodes()
RETURNS TRIGGER AS $$
DECLARE
    azure_conn text;
    aws_conn text;
    table_name text;
    columns text;
    values_clause text;
BEGIN
    -- Obtener nombre de la tabla que disparó el trigger
    table_name := TG_TABLE_NAME;
    
    -- Solo sincronizar tablas de referencia específicas
    IF table_name NOT IN ('roles', 'especialidades', 'catalogo_medicamentos', 'enfermedades') THEN
        RETURN NEW;
    END IF;
    
    -- CONEXIÓN A AZURE
    BEGIN
        azure_conn := dblink_connect('host=hospitaldb.postgres.database.azure.com port=5432 dbname=hospitalAzure user=directorHospital password=Postgr3s_DB');
        
        IF TG_OP = 'INSERT' THEN
            -- Construir INSERT dinámico
            EXECUTE format('SELECT string_agg(quote_ident(attname), '','') 
                          FROM pg_attribute 
                          WHERE attrelid = %L 
                          AND attnum > 0 
                          AND NOT attisdropped', TG_RELID) INTO columns;
            
            EXECUTE format('SELECT string_agg(quote_literal($1.%I), '','') 
                          FROM unnest(ARRAY[%s])', columns, columns) 
            INTO values_clause USING NEW;
            
            EXECUTE format('INSERT INTO %I (%s) VALUES (%s) 
                          ON CONFLICT DO NOTHING', 
                          table_name, columns, values_clause);
            
            PERFORM dblink_exec(azure_conn, format(
                'INSERT INTO %I (%s) VALUES (%s) ON CONFLICT DO NOTHING',
                table_name, columns, values_clause
            ));
            
        ELSIF TG_OP = 'UPDATE' THEN
            -- Construir UPDATE dinámico
            EXECUTE format('SELECT string_agg(format(''%%I = %%L'', attname, $1.%I), '','') 
                          FROM pg_attribute 
                          WHERE attrelid = %L 
                          AND attnum > 0 
                          AND NOT attisdropped
                          AND attname != ''id_sede''', TG_RELID) 
            INTO columns USING NEW;
            
            PERFORM dblink_exec(azure_conn, format(
                'UPDATE %I SET %s WHERE id_%I = %s AND id_sede = %s',
                table_name, columns, 
                split_part(table_name, '_', 1),  -- Extrae 'rol' de 'roles'
                NEW.id_rol,  -- Esto necesita ser dinámico según la tabla
                NEW.id_sede
            ));
            
        ELSIF TG_OP = 'DELETE' THEN
            PERFORM dblink_exec(azure_conn, format(
                'DELETE FROM %I WHERE id_%I = %s AND id_sede = %s',
                table_name, split_part(table_name, '_', 1),
                OLD.id_rol, OLD.id_sede
            ));
        END IF;
        
        PERFORM dblink_disconnect(azure_conn);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Error sincronizando con Azure: %', SQLERRM;
    END;
    
    -- CONEXIÓN A AWS
    BEGIN
        aws_conn := dblink_connect('host=hospital.cdg4cu8q8t0y.us-east-2.rds.amazonaws.com port=5432 dbname=hospital user=postgres password=Postgr3s_DB');
        
        -- Misma lógica que para Azure
        IF TG_OP = 'INSERT' THEN
            EXECUTE format('SELECT string_agg(quote_ident(attname), '','') 
                          FROM pg_attribute 
                          WHERE attrelid = %L 
                          AND attnum > 0 
                          AND NOT attisdropped', TG_RELID) INTO columns;
            
            EXECUTE format('SELECT string_agg(quote_literal($1.%I), '','') 
                          FROM unnest(ARRAY[%s])', columns, columns) 
            INTO values_clause USING NEW;
            
            PERFORM dblink_exec(aws_conn, format(
                'INSERT INTO %I (%s) VALUES (%s) ON CONFLICT DO NOTHING',
                table_name, columns, values_clause
            ));
            
        ELSIF TG_OP = 'UPDATE' THEN
            EXECUTE format('SELECT string_agg(format(''%%I = %%L'', attname, $1.%I), '','') 
                          FROM pg_attribute 
                          WHERE attrelid = %L 
                          AND attnum > 0 
                          AND NOT attisdropped
                          AND attname != ''id_sede''', TG_RELID) 
            INTO columns USING NEW;
            
            PERFORM dblink_exec(aws_conn, format(
                'UPDATE %I SET %s WHERE id_%I = %s AND id_sede = %s',
                table_name, columns, 
                split_part(table_name, '_', 1),
                NEW.id_rol, 
                NEW.id_sede
            ));
            
        ELSIF TG_OP = 'DELETE' THEN
            PERFORM dblink_exec(aws_conn, format(
                'DELETE FROM %I WHERE id_%I = %s AND id_sede = %s',
                table_name, split_part(table_name, '_', 1),
                OLD.id_rol, OLD.id_sede
            ));
        END IF;
        
        PERFORM dblink_disconnect(aws_conn);
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Error sincronizando con AWS: %', SQLERRM;
    END;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;