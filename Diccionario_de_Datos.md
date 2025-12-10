# DICCIONARIO DE DATOS
## Sistema de Gestión Hospitalaria Inteligente (HIS+)

---

## 1. PERSONAS
Almacena información personal de todos los individuos del sistema.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_persona | INT | NO | PK | Identificador único de la persona |
| nom_persona | VARCHAR(100) | NO | - | Nombre de la persona |
| apellido_persona | VARCHAR(100) | NO | - | Apellido de la persona |
| tipo_doc | VARCHAR(10) | NO | - | Tipo de documento (CC, CE, TI, etc.) |
| num_doc | VARCHAR(20) | NO | UK | Número de documento (único) |
| fecha_nac | DATE | NO | - | Fecha de nacimiento |
| genero | CHAR(1) | SÍ | - | Género (M/F/O) |
| dir_persona | VARCHAR(200) | SÍ | - | Dirección de residencia |
| tel_persona | VARCHAR(20) | SÍ | - | Teléfono de contacto |
| email_persona | VARCHAR(150) | NO | UK | Correo electrónico (único) |
| ciudad_residencia | VARCHAR(50) | SÍ | - | Ciudad donde reside |

---

## 2. ROLES
Catálogo de roles de usuario del sistema.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_rol | INT | NO | PK | Identificador único del rol |
| nombre_rol | VARCHAR(50) | NO | - | Nombre del rol (Administrador, Medico, Enfermero, Personal Administrativo, Auditor) |
| descripcion | VARCHAR(200) | SÍ | - | Descripción de las funciones del rol |

---

## 3. ESPECIALIDADES
Catálogo de especialidades médicas.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_especialidad | INT | NO | PK | Identificador único de la especialidad |
| nombre_esp | VARCHAR(100) | NO | - | Nombre de la especialidad médica |

---

## 4. SEDES_HOSPITALARIAS
Información de cada sede/hospital de la red.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_sede | INT | NO | PK | Identificador único de la sede |
| nom_sede | VARCHAR(100) | NO | - | Nombre de la sede hospitalaria |
| ciudad | VARCHAR(50) | NO | - | Ciudad donde está ubicada |
| direccion | VARCHAR(150) | SÍ | - | Dirección física |
| telefono | VARCHAR(20) | SÍ | - | Teléfono de contacto |
| es_nodo_central | BOOLEAN | NO | - | Indica si es el nodo central de replicación (default FALSE) |

---

## 5. CATALOGO_MEDICAMENTOS
Catálogo maestro de medicamentos disponibles.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| cod_med | INT | NO | PK | Código único del medicamento |
| nom_med | VARCHAR(150) | NO | - | Nombre comercial del medicamento |
| principio_activo | VARCHAR(150) | SÍ | - | Principio activo |
| descripcion | TEXT | SÍ | - | Descripción detallada |
| unidad_medida | VARCHAR(20) | SÍ | - | Unidad (mg, ml, tabletas, etc.) |
| proveedor_principal | VARCHAR(100) | SÍ | - | Nombre del proveedor principal |

---

## 6. ENFERMEDADES
Catálogo de enfermedades para diagnósticos.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_enfermedad | BIGINT | NO | PK | Identificador único de la enfermedad |
| nombre_enfermedad | VARCHAR(50) | NO | - | Nombre de la enfermedad |
| descripcion | VARCHAR(200) | SÍ | - | Descripción de la enfermedad |

---

## 7. DEPARTAMENTOS
Departamentos de cada sede hospitalaria.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_sede | INT | NO | PK, FK | ID de la sede (referencia a Sedes_Hospitalarias) |
| id_dept | INT | NO | PK | ID del departamento (único por sede) |
| nom_dept | VARCHAR(100) | NO | - | Nombre del departamento |

**Clave Primaria Compuesta:** (id_sede, id_dept)

---

## 8. PACIENTES
Registro de pacientes del sistema.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| cod_pac | INT | NO | PK | Código único del paciente |
| id_persona | INT | NO | FK | Referencia a datos personales (Personas) |

---

## 9. EMPLEADOS
Personal que trabaja en las sedes hospitalarias.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_emp | INT | NO | PK | Identificador único del empleado |
| id_persona | INT | SÍ | FK | Referencia a datos personales (Personas) |
| id_rol | INT | NO | FK | Rol del empleado (referencia a Roles) |
| id_sede | INT | NO | FK | Sede donde trabaja |
| id_dept | INT | NO | FK | Departamento asignado |
| hash_contra | VARCHAR(255) | NO | - | Contraseña encriptada con pgcrypto (bcrypt) |
| activo | BOOLEAN | NO | - | Estado del empleado (default TRUE) |

---

## 10. EMP_POSEE_ESP
Relación entre empleados y especialidades.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_emp_posee_esp | INT | NO | PK | Identificador único de la relación |
| id_especialidad | INT | NO | FK | Especialidad que posee (Especialidades) |
| id_emp | INT | NO | FK | Empleado que tiene la especialidad (Empleados) |

---

## 11. INVENTARIO_FARMACIA
Stock de medicamentos por sede.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_inv | INT | NO | PK | Identificador único del registro |
| cod_med | INT | NO | FK | Medicamento (Catalogo_Medicamentos) |
| id_sede | INT | NO | FK | Sede del inventario (Sedes_Hospitalarias) |
| stock_actual | INT | NO | - | Cantidad disponible (CHECK >= 0) |
| fecha_actualizacion | TIMESTAMP | SÍ | - | Última actualización del stock |

---

## 12. CITAS
Citas médicas programadas.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_cita | BIGINT | NO | PK | Identificador único de la cita |
| id_sede | INT | NO | FK | Sede donde se realiza |
| id_dept | INT | NO | FK | Departamento |
| id_emp | INT | NO | FK | Médico asignado (Empleados) |
| cod_pac | INT | NO | FK | Paciente (Pacientes) |
| fecha_hora | TIMESTAMP | NO | - | Fecha y hora de la cita |
| fecha_hora_solicitada | TIMESTAMP | NO | - | Cuándo se solicitó la cita |
| tipo_servicio | VARCHAR(50) | SÍ | - | Tipo (Consulta, Urgencia, Control, etc.) |
| estado | VARCHAR(20) | NO | - | Estado (PROGRAMADA, COMPLETADA, CANCELADA) |
| motivo | VARCHAR(200) | SÍ | - | Motivo de la consulta |

---

## 13. EQUIPAMIENTO
Equipos médicos de cada departamento.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| cod_eq | INT | NO | PK | Código único del equipo |
| id_sede | INT | NO | FK | Sede donde está ubicado |
| id_dept | INT | NO | FK | Departamento asignado |
| nom_eq | VARCHAR(100) | NO | - | Nombre del equipo |
| marca_modelo | VARCHAR(100) | SÍ | - | Marca y modelo |
| estado_equipo | VARCHAR(20) | NO | - | Estado (OPERATIVO, EN_MANTENIMIENTO, FUERA_SERVICIO) |
| fecha_ultimo_maint | DATE | SÍ | - | Fecha del último mantenimiento |
| responsable_id | INT | SÍ | FK | Empleado responsable |

---

## 14. HISTORIAS_CLINICAS
Historias clínicas de los pacientes.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| cod_hist | BIGINT | NO | PK | Código único de la historia |
| cod_pac | INT | NO | FK | Paciente (Pacientes) |
| fecha_registro | TIMESTAMP | NO | - | Fecha de creación (default CURRENT_TIMESTAMP) |

---

## 15. DIAGNOSTICO
Diagnósticos registrados en las historias clínicas.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_diagnostico | INT | NO | PK | Identificador único del diagnóstico |
| id_enfermedad | BIGINT | NO | FK | Enfermedad diagnosticada (Enfermedades) |
| id_cita | BIGINT | NO | FK | Cita donde se realizó (Citas) |
| cod_hist | BIGINT | NO | FK | Historia clínica (Historias_Clinicas) |
| observacion | TEXT | SÍ | - | Observaciones del médico |

---

## 16. PRESCRIPCIONES
Medicamentos prescritos a pacientes.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_presc | BIGINT | NO | PK | Identificador único de la prescripción |
| cod_med | INT | NO | FK | Medicamento prescrito (Catalogo_Medicamentos) |
| cod_hist | BIGINT | NO | FK | Historia clínica (Historias_Clinicas) |
| id_cita | BIGINT | NO | FK | Cita relacionada (Citas) |
| dosis | VARCHAR(50) | NO | - | Dosis indicada |
| frecuencia | VARCHAR(100) | NO | - | Frecuencia de administración |
| duracion_dias | INT | NO | - | Duración del tratamiento en días |
| cantidad_total | INT | SÍ | - | Cantidad total de unidades |
| fecha_emision | DATE | NO | - | Fecha de emisión de la receta |

---

## 17. AUDITORIA_ACCESOS
Registro de auditoría de accesos al sistema.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_evento | SERIAL | NO | PK | ID auto-incrementable del evento |
| id_emp | INT | SÍ | FK | Empleado que realizó la acción |
| accion | VARCHAR(50) | NO | - | Tipo de acción (LOGIN, LOGOUT, SELECT, INSERT, UPDATE, DELETE) |
| tabla_afectada | VARCHAR(50) | SÍ | - | Tabla sobre la que se realizó la acción |
| id_registro_afectado | VARCHAR(50) | SÍ | - | ID del registro afectado |
| fecha_evento | TIMESTAMP | NO | - | Fecha y hora del evento (default CURRENT_TIMESTAMP) |
| ip_origen | VARCHAR(45) | SÍ | - | Dirección IP del cliente |

---

## 18. REPORTES_GENERADOS
Registro de reportes generados por los usuarios.

| Campo | Tipo | Nulo | Clave | Descripción |
|-------|------|------|-------|-------------|
| id_reporte | INT | NO | PK | Identificador único del reporte |
| id_sede | INT | NO | FK | Sede que generó el reporte |
| id_emp_generador | INT | NO | FK | Empleado que generó el reporte |
| fecha_generacion | TIMESTAMP | SÍ | - | Fecha de generación |
| tipo_reporte | VARCHAR(50) | SÍ | - | Tipo de reporte generado |
| parametros_json | TEXT | SÍ | - | Parámetros usados (formato JSON) |

---

## LEYENDA
- **PK**: Clave Primaria (Primary Key)
- **FK**: Clave Foránea (Foreign Key)
- **UK**: Clave Única (Unique Key)
- **NO**: No permite valores nulos
- **SÍ**: Permite valores nulos
