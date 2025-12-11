
-- SCRIPT DE INSERCIÓN DE DATOS DE PRUEBA

TRUNCATE TABLE 
    Reportes_Generados,
    Auditoria_Accesos,
    Prescripciones,
    Diagnostico,
    Historias_Clinicas,
    Equipamiento,
    Citas,
    Inventario_Farmacia,
    Emp_Posee_Esp,
    Empleados,
    Pacientes,
    Departamentos,
    Enfermedades,
    Catalogo_Medicamentos,
    Sedes_Hospitalarias,
    Especialidades,
    Roles,
    Personas
RESTART IDENTITY CASCADE;


-- 1. PERSONAS
INSERT INTO Personas (id_persona, nom_persona, apellido_persona, tipo_doc, num_doc, fecha_nac, genero, dir_persona, tel_persona, email_persona, ciudad_residencia) VALUES
-- Empleados
(1, 'Carlos', 'Rodríguez', 'CC', '1234567890', '1980-05-15', 'M', 'Calle 10 #20-30', '3101234567', 'carlos.rodriguez@hospital.com', 'Bogotá'),
(2, 'María', 'González', 'CC', '1234567891', '1985-08-22', 'F', 'Carrera 15 #30-40', '3101234568', 'maria.gonzalez@hospital.com', 'Bogotá'),
(3, 'Juan', 'Martínez', 'CC', '1234567892', '1978-03-10', 'M', 'Avenida 20 #50-60', '3101234569', 'juan.martinez@hospital.com', 'Medellín'),
(4, 'Ana', 'López', 'CC', '1234567893', '1990-11-05', 'F', 'Calle 25 #15-20', '3101234570', 'ana.lopez@hospital.com', 'Cali'),
(5, 'Pedro', 'Sánchez', 'CC', '1234567894', '1982-07-18', 'M', 'Carrera 30 #40-50', '3101234571', 'pedro.sanchez@hospital.com', 'Bogotá'),
(6, 'Laura', 'Ramírez', 'CC', '1234567895', '1988-12-30', 'F', 'Calle 35 #25-35', '3101234572', 'laura.ramirez@hospital.com', 'Medellín'),
(7, 'Diego', 'Torres', 'CC', '1234567896', '1975-09-14', 'M', 'Avenida 45 #55-65', '3101234573', 'diego.torres@hospital.com', 'Cali'),
(8, 'Carmen', 'Hernández', 'CC', '1234567897', '1992-04-20', 'F', 'Calle 50 #60-70', '3101234574', 'carmen.hernandez@hospital.com', 'Bogotá'),
(9, 'Roberto', 'García', 'CC', '1234567898', '1986-01-25', 'M', 'Carrera 55 #65-75', '3101234575', 'roberto.garcia@hospital.com', 'Medellín'),
(10, 'Isabel', 'Moreno', 'CC', '1234567899', '1991-06-08', 'F', 'Calle 60 #70-80', '3101234576', 'isabel.moreno@hospital.com', 'Cali'),
-- Pacientes
(11, 'Luis', 'Pérez', 'CC', '2234567890', '1995-02-14', 'M', 'Calle 70 #80-90', '3201234567', 'luis.perez@email.com', 'Bogotá'),
(12, 'Sandra', 'Jiménez', 'CC', '2234567891', '1988-09-23', 'F', 'Carrera 75 #85-95', '3201234568', 'sandra.jimenez@email.com', 'Bogotá'),
(13, 'Jorge', 'Castro', 'CC', '2234567892', '1972-12-05', 'M', 'Avenida 80 #90-100', '3201234569', 'jorge.castro@email.com', 'Medellín'),
(14, 'Patricia', 'Vargas', 'CC', '2234567893', '1983-07-17', 'F', 'Calle 85 #95-105', '3201234570', 'patricia.vargas@email.com', 'Cali'),
(15, 'Miguel', 'Rojas', 'CC', '2234567894', '1990-04-30', 'M', 'Carrera 90 #100-110', '3201234571', 'miguel.rojas@email.com', 'Bogotá'),
(16, 'Elena', 'Mendoza', 'CC', '2234567895', '1979-11-12', 'F', 'Calle 95 #105-115', '3201234572', 'elena.mendoza@email.com', 'Medellín'),
(17, 'Fernando', 'Silva', 'CC', '2234567896', '1985-08-25', 'M', 'Avenida 100 #110-120', '3201234573', 'fernando.silva@email.com', 'Cali'),
(18, 'Gloria', 'Ortiz', 'CC', '2234567897', '1993-03-08', 'F', 'Calle 105 #115-125', '3201234574', 'gloria.ortiz@email.com', 'Bogotá'),
(19, 'Ricardo', 'Navarro', 'CC', '2234567898', '1987-10-19', 'M', 'Carrera 110 #120-130', '3201234575', 'ricardo.navarro@email.com', 'Medellín'),
(20, 'Beatriz', 'Ruiz', 'CC', '2234567899', '1981-05-22', 'F', 'Calle 115 #125-135', '3201234576', 'beatriz.ruiz@email.com', 'Cali');

-- 2. ROLES
INSERT INTO Roles (id_rol, nombre_rol, descripcion) VALUES
(1, 'Administrador', 'Control total del sistema'),
(2, 'Medico', 'Atención médica y diagnósticos'),
(3, 'Enfermero', 'Apoyo en atención médica'),
(4, 'Administrativo', 'Gestión de citas y pacientes');

-- 3. ESPECIALIDADES
INSERT INTO Especialidades (id_especialidad, nombre_esp) VALUES
(1, 'Cardiología'),
(2, 'Pediatría'),
(3, 'Medicina General'),
(4, 'Traumatología'),
(5, 'Ginecología'),
(6, 'Neurología');

-- 4. SEDES HOSPITALARIAS
INSERT INTO Sedes_Hospitalarias (id_sede, nom_sede, ciudad, direccion, telefono, es_nodo_central) VALUES
(1, 'Hospital Central', 'Bogotá', 'Calle 1 #1-1', '6011234567', TRUE),
(2, 'Clínica Norte', 'Medellín', 'Carrera 2 #2-2', '6042345678', FALSE),
(3, 'Unidad de Urgencias Sur', 'Cali', 'Avenida 3 #3-3', '6023456789', FALSE);

CALL sync_master_data();

-- 5. DEPARTAMENTOS
INSERT INTO Departamentos (id_sede, id_dept, nom_dept) VALUES
(1, 1, 'Urgencias'),
(1, 2, 'Cardiología'),
(1, 3, 'Pediatría'),
(1, 4, 'Farmacia'),
(2, 1, 'Urgencias'),
(2, 2, 'Traumatología'),
(2, 3, 'Medicina General'),
(2, 4, 'Farmacia'),
(3, 1, 'Urgencias'),
(3, 2, 'Ginecología'),
(3, 3, 'Neurología'),
(3, 4, 'Farmacia');

-- 6. EMPLEADOS (con contraseñas encriptadas usando pgcrypto)
INSERT INTO Empleados (id_emp, id_persona, id_rol, id_sede, id_dept, hash_contra, activo) VALUES
(1, 1, 1, 1, 1, crypt('admin123', gen_salt('bf')), TRUE),
(2, 2, 2, 1, 2, crypt('medico123', gen_salt('bf')), TRUE),
(3, 3, 2, 1, 3, crypt('medico123', gen_salt('bf')), TRUE),
(4, 4, 3, 1, 1, crypt('enfermero123', gen_salt('bf')), TRUE),
(5, 5, 2, 2, 2, crypt('medico123', gen_salt('bf')), TRUE),
(6, 6, 2, 2, 3, crypt('medico123', gen_salt('bf')), TRUE),
(7, 7, 3, 2, 1, crypt('enfermero123', gen_salt('bf')), TRUE),
(8, 8, 2, 3, 2, crypt('medico123', gen_salt('bf')), TRUE),
(9, 9, 2, 3, 3, crypt('medico123', gen_salt('bf')), TRUE),
(10, 10, 4, 3, 1, crypt('admin123', gen_salt('bf')), TRUE);

-- 7. RELACIÓN EMPLEADOS-ESPECIALIDADES
INSERT INTO Emp_Posee_Esp (id_emp_posee_esp, id_especialidad, id_emp) VALUES
(1, 3, 2),  -- María González - Medicina General
(2, 1, 2),  -- María González - Cardiología
(3, 2, 3),  -- Juan Martínez - Pediatría
(4, 4, 5),  -- Pedro Sánchez - Traumatología
(5, 3, 6),  -- Laura Ramírez - Medicina General
(6, 5, 8),  -- Carmen Hernández - Ginecología
(7, 6, 9);  -- Roberto García - Neurología

-- 8. PACIENTES
INSERT INTO Pacientes (cod_pac, id_persona) VALUES
(1, 11),
(2, 12),
(3, 13),
(4, 14),
(5, 15),
(6, 16),
(7, 17),
(8, 18),
(9, 19),
(10, 20);

-- 9. ENFERMEDADES
INSERT INTO Enfermedades (id_enfermedad, nombre_enfermedad, descripcion) VALUES
(1, 'Hipertensión Arterial', 'Presión arterial elevada persistente'),
(2, 'Diabetes Tipo 2', 'Trastorno metabólico de azúcar en sangre'),
(3, 'Gripe Común', 'Infección viral respiratoria'),
(4, 'Fractura de Tibia', 'Ruptura del hueso de la pierna'),
(5, 'Migraña Crónica', 'Dolores de cabeza recurrentes'),
(6, 'Gastritis', 'Inflamación del revestimiento del estómago'),
(7, 'Asma Bronquial', 'Enfermedad respiratoria crónica'),
(8, 'Infección Urinaria', 'Infección en el tracto urinario');

-- 10. CITAS
INSERT INTO Citas (id_cita, id_sede, id_dept, id_emp, cod_pac, fecha_hora, fecha_hora_solicitada, tipo_servicio, estado, motivo) VALUES
(1, 1, 2, 2, 1, '2025-07-15 09:00:00', '2025-07-10 14:30:00', 'Consulta', 'COMPLETADA', 'Control de hipertensión'),
(2, 1, 3, 3, 2, '2025-07-16 10:00:00', '2025-07-11 08:00:00', 'Consulta', 'COMPLETADA', 'Control pediatría'),
(3, 2, 2, 5, 3, '2025-07-20 11:00:00', '2025-07-15 16:00:00', 'Urgencia', 'COMPLETADA', 'Fractura en pierna'),
(4, 1, 1, 2, 4, '2025-08-05 14:00:00', '2025-07-30 10:00:00', 'Urgencia', 'COMPLETADA', 'Dolor abdominal'),
(5, 3, 2, 8, 5, '2025-08-12 15:00:00', '2025-08-07 11:00:00', 'Consulta', 'COMPLETADA', 'Control ginecológico'),
(6, 2, 3, 6, 6, '2025-08-18 09:00:00', '2025-08-12 15:00:00', 'Consulta', 'COMPLETADA', 'Gripe'),
(7, 1, 2, 2, 7, '2025-08-25 10:00:00', '2025-08-20 09:00:00', 'Consulta', 'COMPLETADA', 'Control cardiológico'), 
(8, 3, 3, 9, 8, '2025-09-05 11:00:00', '2025-08-30 13:00:00', 'Consulta', 'COMPLETADA', 'Dolor de cabeza'),
(9, 1, 3, 3, 9, '2025-09-10 14:00:00', '2025-09-03 10:00:00', 'Consulta', 'COMPLETADA', 'Control niño sano'),
(10, 2, 2, 5, 10, '2025-09-15 15:00:00', '2025-09-08 14:00:00', 'Urgencia', 'COMPLETADA', 'Caída y dolor'),
(11, 1, 2, 2, 1, '2025-09-20 09:00:00', '2025-09-13 10:00:00', 'Consulta', 'COMPLETADA', 'Control seguimiento'),
(12, 2, 3, 6, 3, '2025-09-25 10:00:00', '2025-09-18 11:00:00', 'Consulta', 'COMPLETADA', 'Revisión post-fractura'),
(13, 3, 2, 8, 5, '2025-10-05 11:00:00', '2025-09-28 09:00:00', 'Consulta', 'COMPLETADA', 'Control rutinario'),
(14, 1, 1, 4, 2, '2025-10-10 08:30:00', '2025-10-03 14:00:00', 'Urgencia', 'COMPLETADA', 'Fiebre alta'),
(15, 2, 2, 5, 4, '2025-10-15 09:30:00', '2025-10-08 16:00:00', 'Consulta', 'COMPLETADA', 'Dolor articular'),
(16, 3, 3, 9, 6, '2025-10-20 10:30:00', '2025-10-13 11:00:00', 'Consulta', 'COMPLETADA', 'Cefalea persistente'),
(17, 1, 2, 2, 8, '2025-10-25 14:00:00', '2025-10-18 09:00:00', 'Consulta', 'COMPLETADA', 'Revisión cardiológica'),
(18, 2, 3, 6, 7, '2025-10-28 15:00:00', '2025-10-21 10:00:00', 'Consulta', 'COMPLETADA', 'Control general'),
(19, 1, 3, 3, 9, '2025-11-05 10:00:00', '2025-10-29 15:00:00', 'Consulta', 'COMPLETADA', 'Vacunación'),
(20, 3, 2, 8, 5, '2025-11-08 11:00:00', '2025-11-01 13:00:00', 'Consulta', 'COMPLETADA', 'Control prenatal'),
(21, 1, 2, 2, 1, '2025-11-12 09:00:00', '2025-11-05 14:00:00', 'Consulta', 'COMPLETADA', 'Control mensual hipertensión'),
(22, 2, 2, 5, 3, '2025-11-15 10:00:00', '2025-11-08 11:00:00', 'Consulta', 'COMPLETADA', 'Revisión traumatología'),
(23, 3, 3, 9, 8, '2025-11-18 11:00:00', '2025-11-11 09:00:00', 'Consulta', 'COMPLETADA', 'Control neurológico'),
(24, 1, 1, 4, 6, '2025-11-20 08:00:00', '2025-11-13 16:00:00', 'Urgencia', 'COMPLETADA', 'Dolor intenso'),
(25, 2, 3, 6, 4, '2025-11-22 09:30:00', '2025-11-15 10:00:00', 'Consulta', 'COMPLETADA', 'Chequeo general'),
(26, 1, 2, 2, 7, '2025-11-25 14:00:00', '2025-11-18 11:00:00', 'Consulta', 'COMPLETADA', 'Control cardiológico'),
(27, 3, 2, 8, 9, '2025-11-28 15:00:00', '2025-11-21 13:00:00', 'Consulta', 'COMPLETADA', 'Control ginecológico'),
(28, 2, 3, 6, 1, '2025-12-01 09:00:00', '2025-11-24 10:00:00', 'Consulta', 'COMPLETADA', 'Control general'),
(29, 1, 3, 3, 2, '2025-12-02 10:00:00', '2025-11-25 15:00:00', 'Consulta', 'COMPLETADA', 'Vacunación infantil'),
(30, 3, 2, 8, 5, '2025-12-02 11:00:00', '2025-11-26 13:00:00', 'Consulta', 'COMPLETADA', 'Seguimiento embarazo'),
(31, 1, 2, 2, 1, '2025-12-05 09:00:00', '2025-11-28 14:00:00', 'PROGRAMADA', 'Consulta', 'Control mensual'),
(32, 2, 2, 5, 3, '2025-12-06 10:00:00', '2025-11-29 11:00:00', 'PROGRAMADA', 'Consulta', 'Revisión final traumatología'),
(33, 3, 3, 9, 8, '2025-12-07 11:00:00', '2025-11-30 09:00:00', 'PROGRAMADA', 'Consulta', 'Control neurológico'),
(34, 1, 1, 4, 10, '2025-12-10 14:00:00', '2025-12-02 16:00:00', 'PROGRAMADA', 'Urgencia', 'Seguimiento'),
(35, 2, 3, 6, 6, '2025-12-12 15:00:00', '2025-12-03 10:00:00', 'PROGRAMADA', 'Consulta', 'Control post-gripe');

-- 11. HISTORIAS CLÍNICAS
INSERT INTO Historias_Clinicas (cod_hist, cod_pac, fecha_registro) VALUES
(1, 1, '2025-07-15 10:30:00'),
(2, 2, '2025-07-16 11:15:00'),
(3, 3, '2025-07-20 12:30:00'),
(4, 4, '2025-08-05 15:00:00'),
(5, 5, '2025-08-12 16:00:00'),
(6, 6, '2025-08-18 10:00:00'),
(7, 7, '2025-08-25 11:00:00'),
(8, 8, '2025-09-05 12:00:00'),
(9, 9, '2025-09-10 15:00:00'),
(10, 10, '2025-09-15 16:00:00'),
(11, 1, '2025-09-20 10:30:00'),
(12, 3, '2025-09-25 11:00:00'),
(13, 5, '2025-10-05 12:00:00'),
(14, 2, '2025-10-10 09:30:00'),
(15, 4, '2025-10-15 10:30:00'),
(16, 6, '2025-10-20 11:30:00'),
(17, 8, '2025-10-25 15:00:00'),
(18, 7, '2025-10-28 16:00:00'),
(19, 9, '2025-11-05 11:00:00'),
(20, 5, '2025-11-08 12:00:00'),
(21, 1, '2025-11-12 10:00:00'),
(22, 3, '2025-11-15 11:00:00'),
(23, 8, '2025-11-18 12:00:00'),
(24, 6, '2025-11-20 09:00:00'),
(25, 4, '2025-11-22 10:30:00'),
(26, 7, '2025-11-25 15:00:00'),
(27, 9, '2025-11-28 16:00:00'),
(28, 1, '2025-12-01 10:00:00'),
(29, 2, '2025-12-02 11:00:00'),
(30, 5, '2025-12-02 12:00:00');

-- 12. DIAGNÓSTICOS
INSERT INTO Diagnostico (id_diagnostico, id_enfermedad, id_cita, cod_hist, observacion) VALUES
(1, 1, 1, 1, 'Paciente con hipertensión controlada, continuar tratamiento'),
(2, 3, 2, 2, 'Gripe común, reposo y medicación'),
(3, 4, 3, 3, 'Fractura de tibia, requiere inmovilización'),
(4, 6, 4, 4, 'Gastritis aguda, dieta blanda'),
(5, 5, 5, 5, 'Migraña recurrente, tratamiento preventivo'),
(6, 3, 6, 6, 'Gripe estacional, tratamiento sintomático'),
(7, 1, 7, 7, 'Hipertensión en seguimiento'),
(8, 5, 8, 8, 'Migraña tensional'),
(9, 2, 9, 9, 'Control pediátrico normal'),
(10, 4, 10, 10, 'Esguince de tobillo'),
(11, 1, 11, 11, 'Presión arterial estable'),
(12, 4, 12, 12, 'Fractura consolidando bien'),
(13, 5, 13, 13, 'Migraña bajo control'),
(14, 3, 14, 14, 'Infección viral respiratoria'),
(15, 7, 15, 15, 'Asma bronquial leve'),
(16, 5, 16, 16, 'Cefalea crónica'),
(17, 1, 17, 17, 'Hipertensión requiere ajuste'),
(18, 3, 18, 18, 'Resfriado común'),
(19, 2, 19, 19, 'Esquema de vacunación completo'),
(20, 5, 20, 20, 'Migraña controlada'),
(21, 1, 21, 21, 'Hipertensión estable con medicación'),
(22, 4, 22, 22, 'Recuperación total de fractura'),
(23, 6, 23, 23, 'Cefalea tensional'),
(24, 8, 24, 24, 'Infección urinaria leve'),
(25, 3, 25, 25, 'Gripe común'),
(26, 1, 26, 26, 'Control cardiológico favorable'),
(27, 5, 27, 27, 'Control prenatal normal'),
(28, 3, 28, 28, 'Resfriado estacional'),
(29, 2, 29, 29, 'Vacunación infantil completa'),
(30, 5, 30, 30, 'Embarazo controlado sin complicaciones');

-- 13. CATÁLOGO DE MEDICAMENTOS
INSERT INTO Catalogo_Medicamentos (cod_med, nom_med, principio_activo, descripcion, unidad_medida, proveedor_principal) VALUES
(1, 'Losartán 50mg', 'Losartán', 'Antihipertensivo', 'Tableta', 'Farmacéutica ABC'),
(2, 'Ibuprofeno 400mg', 'Ibuprofeno', 'Antiinflamatorio', 'Tableta', 'Laboratorios XYZ'),
(3, 'Acetaminofén 500mg', 'Paracetamol', 'Analgésico', 'Tableta', 'Farmacéutica ABC'),
(4, 'Amoxicilina 500mg', 'Amoxicilina', 'Antibiótico', 'Cápsula', 'Laboratorios DEF'),
(5, 'Metformina 850mg', 'Metformina', 'Hipoglicemiante', 'Tableta', 'Farmacéutica GHI'),
(6, 'Omeprazol 20mg', 'Omeprazol', 'Inhibidor de bomba de protones', 'Cápsula', 'Laboratorios JKL'),
(7, 'Salbutamol Inhalador', 'Salbutamol', 'Broncodilatador', 'Inhalador', 'Farmacéutica MNO'),
(8, 'Sumatriptán 50mg', 'Sumatriptán', 'Antimigañoso', 'Tableta', 'Laboratorios PQR');

-- 14. INVENTARIO DE FARMACIA
INSERT INTO Inventario_Farmacia (id_inv, cod_med, id_sede, stock_actual, fecha_actualizacion) VALUES
(1, 1, 1, 150, '2025-12-01 08:00:00'),
(2, 2, 1, 200, '2025-12-01 08:00:00'),
(3, 3, 1, 300, '2025-12-01 08:00:00'),
(4, 4, 1, 100, '2025-12-01 08:00:00'),
(5, 5, 1, 80, '2025-12-01 08:00:00'),
(6, 6, 1, 120, '2025-12-01 08:00:00'),
(7, 7, 1, 50, '2025-12-01 08:00:00'),
(8, 8, 1, 60, '2025-12-01 08:00:00'),
(9, 1, 2, 100, '2025-12-01 08:00:00'),
(10, 2, 2, 180, '2025-12-01 08:00:00'),
(11, 3, 2, 250, '2025-12-01 08:00:00'),
(12, 4, 2, 90, '2025-12-01 08:00:00'),
(13, 5, 2, 45, '2025-12-01 08:00:00'),
(14, 6, 2, 110, '2025-12-01 08:00:00'),
(15, 7, 2, 8, '2025-12-01 08:00:00'),
(16, 8, 2, 55, '2025-12-01 08:00:00'),
(17, 1, 3, 120, '2025-12-01 08:00:00'),
(18, 2, 3, 190, '2025-12-01 08:00:00'),
(19, 3, 3, 280, '2025-12-01 08:00:00'),
(20, 4, 3, 95, '2025-12-01 08:00:00'),
(21, 5, 3, 70, '2025-12-01 08:00:00'),
(22, 6, 3, 100, '2025-12-01 08:00:00'),
(23, 7, 3, 40, '2025-12-01 08:00:00'),
(24, 8, 3, 65, '2025-12-01 08:00:00');

-- 15. PRESCRIPCIONES
INSERT INTO Prescripciones (id_presc, cod_med, cod_hist, id_cita, dosis, frecuencia, duracion_dias, cantidad_total, fecha_emision) VALUES
(1, 1, 1, 1, '50mg', 'Cada 12 horas', 30, 60, '2025-07-15'),
(2, 3, 2, 2, '500mg', 'Cada 8 horas', 5, 15, '2025-07-16'),
(3, 2, 3, 3, '400mg', 'Cada 8 horas', 7, 21, '2025-07-20'),
(4, 6, 4, 4, '20mg', 'Cada 24 horas', 14, 14, '2025-08-05'),
(5, 8, 5, 5, '50mg', 'Según necesidad', 10, 10, '2025-08-12'),
(6, 3, 6, 6, '500mg', 'Cada 6 horas', 5, 20, '2025-08-18'),
(7, 4, 6, 6, '500mg', 'Cada 8 horas', 7, 21, '2025-08-18'),
(8, 1, 7, 7, '50mg', 'Cada 12 horas', 30, 60, '2025-08-25'),
(9, 8, 8, 8, '50mg', 'Según necesidad', 10, 10, '2025-09-05'),
(10, 2, 10, 10, '400mg', 'Cada 8 horas', 5, 15, '2025-09-15'),
(11, 1, 11, 11, '50mg', 'Cada 12 horas', 30, 60, '2025-09-20'),
(12, 3, 12, 12, '500mg', 'Cada 8 horas', 5, 15, '2025-09-25'),
(13, 8, 13, 13, '50mg', 'Según necesidad', 10, 10, '2025-10-05'),
(14, 3, 14, 14, '500mg', 'Cada 6 horas', 7, 28, '2025-10-10'),
(15, 7, 15, 15, '2 puff', 'Cada 12 horas', 30, 1, '2025-10-15'),
(16, 8, 16, 16, '50mg', 'Según necesidad', 15, 15, '2025-10-20'),
(17, 1, 17, 17, '50mg', 'Cada 12 horas', 30, 60, '2025-10-25'),
(18, 3, 18, 18, '500mg', 'Cada 8 horas', 5, 15, '2025-10-28'),
(19, 3, 20, 20, '500mg', 'Cada 8 horas', 5, 15, '2025-11-08'),
(20, 1, 21, 21, '50mg', 'Cada 12 horas', 30, 60, '2025-11-12'),
(21, 2, 22, 22, '400mg', 'Según necesidad', 7, 14, '2025-11-15'),
(22, 8, 23, 23, '50mg', 'Según necesidad', 10, 10, '2025-11-18'),
(23, 4, 24, 24, '500mg', 'Cada 8 horas', 7, 21, '2025-11-20'),
(24, 3, 25, 25, '500mg', 'Cada 6 horas', 5, 20, '2025-11-22'),
(25, 1, 26, 26, '50mg', 'Cada 12 horas', 30, 60, '2025-11-25'),
(26, 6, 27, 27, '20mg', 'Cada 24 horas', 14, 14, '2025-11-28'),
(27, 2, 27, 27, '400mg', 'Según necesidad', 7, 14, '2025-11-28'),
(28, 3, 28, 28, '500mg', 'Cada 8 horas', 5, 15, '2025-12-01'),
(29, 5, 30, 30, '850mg', 'Cada 12 horas', 30, 60, '2025-12-02'),
(30, 2, 30, 30, '400mg', 'Según necesidad', 7, 14, '2025-12-02');

-- 16. EQUIPAMIENTO
INSERT INTO Equipamiento (cod_eq, id_sede, id_dept, nom_eq, marca_modelo, estado_equipo, fecha_ultimo_maint, responsable_id) VALUES
(1, 1, 1, 'Monitor de Signos Vitales', 'Philips MX450', 'OPERATIVO', '2025-10-15', 1),
(2, 1, 2, 'Electrocardiógrafo', 'GE MAC 2000', 'OPERATIVO', '2025-09-20', 2),
(3, 1, 3, 'Incubadora Neonatal', 'Dräger Isolette C2000', 'OPERATIVO', '2025-11-01', 3),
(4, 2, 1, 'Desfibrilador', 'Zoll AED Plus', 'OPERATIVO', '2025-10-25', 5),
(5, 2, 2, 'Rayos X Portátil', 'Siemens Mobilett', 'MANTENIMIENTO', '2025-08-15', 5),
(6, 2, 3, 'Monitor de Signos Vitales', 'Philips MX450', 'OPERATIVO', '2025-11-10', 6),
(7, 3, 1, 'Monitor de Signos Vitales', 'Philips MX450', 'OPERATIVO', '2025-10-30', 8),
(8, 3, 2, 'Ecógrafo', 'Samsung HS40', 'OPERATIVO', '2025-09-10', 8),
(9, 3, 3, 'Electroencefalógrafo', 'Nihon Kohden EEG', 'OPERATIVO', '2025-10-05', 9);

-- 17. AUDITORÍA DE ACCESOS
INSERT INTO Auditoria_Accesos (id_emp, accion, tabla_afectada, id_registro_afectado, fecha_evento, ip_origen) VALUES
(2, 'SELECT', 'Historias_Clinicas', '1', '2025-07-15 10:30:00', '192.168.1.10'),
(3, 'INSERT', 'Historias_Clinicas', '2', '2025-07-16 11:15:00', '192.168.1.11'),
(5, 'INSERT', 'Historias_Clinicas', '3', '2025-07-20 12:30:00', '192.168.2.15'),
(2, 'UPDATE', 'Historias_Clinicas', '4', '2025-08-05 15:00:00', '192.168.1.10'),
(8, 'INSERT', 'Historias_Clinicas', '5', '2025-08-12 16:00:00', '192.168.3.20'),
(6, 'SELECT', 'Historias_Clinicas', '6', '2025-08-18 10:00:00', '192.168.2.16'),
(2, 'INSERT', 'Historias_Clinicas', '7', '2025-08-25 11:00:00', '192.168.1.10'),
(9, 'SELECT', 'Historias_Clinicas', '8', '2025-09-05 12:00:00', '192.168.3.21'),
(3, 'UPDATE', 'Historias_Clinicas', '9', '2025-09-10 15:00:00', '192.168.1.11'),
(5, 'SELECT', 'Historias_Clinicas', '10', '2025-09-15 16:00:00', '192.168.2.15'),
(2, 'SELECT', 'Historias_Clinicas', '11', '2025-10-20 10:30:00', '192.168.1.10'),
(6, 'INSERT', 'Historias_Clinicas', '12', '2025-10-25 11:00:00', '192.168.2.16'),
(8, 'SELECT', 'Historias_Clinicas', '13', '2025-10-28 12:00:00', '192.168.3.20'),
(2, 'SELECT', 'Historias_Clinicas', '19', '2025-11-05 11:00:00', '192.168.1.10'),
(8, 'INSERT', 'Historias_Clinicas', '20', '2025-11-08 12:00:00', '192.168.3.20'),
(2, 'UPDATE', 'Historias_Clinicas', '21', '2025-11-12 10:00:00', '192.168.1.10'),
(5, 'SELECT', 'Historias_Clinicas', '22', '2025-11-15 11:00:00', '192.168.2.15'),
(9, 'INSERT', 'Historias_Clinicas', '23', '2025-11-18 12:00:00', '192.168.3.21'),
(2, 'SELECT', 'Historias_Clinicas', '24', '2025-11-20 09:00:00', '192.168.1.10'),
(6, 'UPDATE', 'Historias_Clinicas', '25', '2025-11-22 10:30:00', '192.168.2.16'),
(2, 'INSERT', 'Historias_Clinicas', '26', '2025-11-25 15:00:00', '192.168.1.10'),
(8, 'SELECT', 'Historias_Clinicas', '27', '2025-11-28 16:00:00', '192.168.3.20'),
(6, 'INSERT', 'Historias_Clinicas', '28', '2025-12-01 10:00:00', '192.168.2.16'),
(3, 'INSERT', 'Historias_Clinicas', '29', '2025-12-02 11:00:00', '192.168.1.11'),
(8, 'INSERT', 'Historias_Clinicas', '30', '2025-12-02 12:00:00', '192.168.3.20'),
(2, 'SELECT', 'Historias_Clinicas', '1', '2025-12-02 14:00:00', '192.168.1.10'),
(2, 'SELECT', 'Historias_Clinicas', '21', '2025-12-02 15:00:00', '192.168.1.10'),
(2, 'SELECT', 'Pacientes', '1', '2025-07-15 09:00:00', '192.168.1.10'),
(6, 'SELECT', 'Pacientes', '6', '2025-08-18 09:00:00', '192.168.2.16'),
(9, 'SELECT', 'Pacientes', '8', '2025-09-05 11:00:00', '192.168.3.21'),
(2, 'SELECT', 'Pacientes', '1', '2025-11-12 09:00:00', '192.168.1.10'),
(5, 'UPDATE', 'Pacientes', '3', '2025-11-15 08:30:00', '192.168.2.15'),
(2, 'SELECT', 'Pacientes', '1', '2025-12-01 09:00:00', '192.168.1.10');

-- 18. REPORTES GENERADOS
INSERT INTO Reportes_Generados (id_reporte, id_sede, id_emp_generador, fecha_generacion, tipo_reporte, parametros_json) VALUES
(1, 1, 1, '2025-07-31 17:00:00', 'Medicamentos Recetados', '{"mes": "julio", "año": 2025}'),
(2, 2, 5, '2025-08-31 17:30:00', 'Consultas por Médico', '{"mes": "agosto", "año": 2025}'),
(3, 3, 10, '2025-09-30 08:00:00', 'Utilización de Recursos', '{"mes": "septiembre", "año": 2025}'),
(4, 1, 1, '2025-10-31 09:00:00', 'Auditoría de Accesos', '{"tabla": "Historias_Clinicas", "límite": 10}'),
(5, 2, 5, '2025-11-15 10:00:00', 'Enfermedades Tratadas', '{"trimestre": 3, "año": 2025}'),
(6, 1, 1, '2025-11-30 17:00:00', 'Inventario Crítico', '{"sede": "Hospital Central"}'),
(7, 3, 10, '2025-11-30 18:00:00', 'Tiempos de Atención', '{"mes": "noviembre", "año": 2025}'),
(8, 2, 5, '2025-12-02 09:00:00', 'Medicamentos más Recetados', '{"mes": "noviembre", "año": 2025}'),
(9, 1, 1, '2025-12-02 10:00:00', 'Productividad Médicos', '{"periodo": "último_trimestre"}');

-- 19. CREACIÓN DE USUARIOS DE BASE DE DATOS

-- Usuarios Administradores
CREATE USER admin_central WITH PASSWORD 'admin123_secure';
GRANT administrador TO admin_central;

CREATE USER admin_norte WITH PASSWORD 'admin123_secure';
GRANT administrador TO admin_norte;

-- Usuarios Médicos
CREATE USER medico_rodriguez WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_rodriguez;
COMMENT ON ROLE medico_rodriguez IS 'Dr. Carlos Rodríguez - Hospital Central';

CREATE USER medico_gonzalez WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_gonzalez;
COMMENT ON ROLE medico_gonzalez IS 'Dra. María González - Hospital Central';

CREATE USER medico_martinez WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_martinez;
COMMENT ON ROLE medico_martinez IS 'Dr. Juan Martínez - Hospital Central';

CREATE USER medico_sanchez WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_sanchez;
COMMENT ON ROLE medico_sanchez IS 'Dr. Pedro Sánchez - Clínica Norte';

CREATE USER medico_ramirez WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_ramirez;
COMMENT ON ROLE medico_ramirez IS 'Dra. Laura Ramírez - Clínica Norte';

CREATE USER medico_hernandez WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_hernandez;
COMMENT ON ROLE medico_hernandez IS 'Dra. Carmen Hernández - Unidad Sur';

CREATE USER medico_garcia WITH PASSWORD 'medico123_secure';
GRANT medico TO medico_garcia;
COMMENT ON ROLE medico_garcia IS 'Dr. Roberto García - Unidad Sur';

-- Usuarios Enfermeros
CREATE USER enfermero_lopez WITH PASSWORD 'enfermero123_secure';
GRANT enfermero TO enfermero_lopez;
COMMENT ON ROLE enfermero_lopez IS 'Enfermera Ana López - Hospital Central';

CREATE USER enfermero_torres WITH PASSWORD 'enfermero123_secure';
GRANT enfermero TO enfermero_torres;
COMMENT ON ROLE enfermero_torres IS 'Enfermero Diego Torres - Clínica Norte';

-- Usuarios Administrativos
CREATE USER admin_moreno WITH PASSWORD 'admin123_secure';
GRANT administrativo TO admin_moreno;
COMMENT ON ROLE admin_moreno IS 'Isabel Moreno - Unidad Sur';

-- Usuario Auditor
CREATE USER auditor_sistema WITH PASSWORD 'auditor123_secure';
GRANT auditor TO auditor_sistema;
COMMENT ON ROLE auditor_sistema IS 'Auditor del Sistema Hospitalario';


select * from pacientes
