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

-- Tablas con dependencias 
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

CREATE TABLE Empleados (
    id_emp INT PRIMARY KEY, 
    id_persona INT,
    id_rol INT NOT NULL,
    id_sede INT NOT NULL,
    id_dept INT NOT NULL,
    hash_contra VARCHAR(255) NOT NULL,
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

-- Creación de Roles de Usuario
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