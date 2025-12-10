# INFORME TÉCNICO FINAL
## Sistema de Gestión Hospitalaria Inteligente (HIS+)

**Versión:** 1.0  
**Fecha:** Diciembre 2024  
**Curso:** Fundamentos de Bases de Datos  

---

## 1. RESUMEN EJECUTIVO

El sistema HIS+ es una plataforma de gestión hospitalaria distribuida que permite la interoperabilidad entre múltiples centros médicos de una red hospitalaria. El sistema implementa una base de datos PostgreSQL con mecanismos de replicación, seguridad basada en roles, y un módulo de analítica médica para generación de reportes.

**Tecnologías utilizadas:**
- **Base de datos:** PostgreSQL 14+
- **Framework web:** Django 5.0.14
- **Lenguaje:** Python 3.11
- **Encriptación:** pgcrypto (bcrypt)

---

## 2. ARQUITECTURA DISTRIBUIDA

### 2.1 Topología de Red

El sistema implementa una arquitectura de 3 nodos:

| Nodo | Sede | Ciudad | Rol |
|------|------|--------|-----|
| Nodo Central | Hospital Central | Bogotá | Maestro (coordinador) |
| Nodo 2 | Clínica Norte | Medellín | Secundario |
| Nodo 3 | Unidad Urgencias Móvil | Cali | Secundario |

### 2.2 Distribución de Datos

**Datos Locales (particionados por sede):**
- Citas médicas
- Empleados
- Equipamiento
- Inventario de farmacia

**Datos Replicados (sincronizados entre sedes):**
- Historias clínicas
- Catálogo de medicamentos
- Datos de pacientes
- Auditoría de accesos

### 2.3 Vistas Distribuidas

Se implementaron 10 vistas consolidadas que permiten acceso a datos de múltiples sedes:

1. `vista_historias_consolidadas` - Historias clínicas de toda la red
2. `vista_medicamentos_recetados_sede` - Prescripciones por sede
3. `vista_medicos_consultas` - Productividad médica
4. `vista_enfermedades_por_sede` - Estadísticas epidemiológicas
5. `vista_inventario_consolidado` - Stock de todas las farmacias
6. `vista_equipamiento_departamentos` - Equipos compartidos
7. `vista_auditoria_historias` - Trazabilidad de accesos
8. `vista_tiempos_atencion` - Tiempos de espera
9. `vista_consumo_medicamentos_dept` - Consumo por departamento
10. `vista_utilizacion_recursos` - Utilización de recursos

---

## 3. MECANISMOS DE SEGURIDAD

### 3.1 Autenticación

La autenticación se realiza mediante encriptación de contraseñas con la extensión `pgcrypto`:

```sql
-- Verificación de credenciales
SELECT * FROM Empleados e
INNER JOIN Personas p ON e.id_persona = p.id_persona
WHERE p.email_persona = %s 
AND e.hash_contra = crypt(%s, e.hash_contra)

-- Creación de contraseña nueva
UPDATE Empleados 
SET hash_contra = crypt(%s, gen_salt('bf'))
WHERE id_emp = %s
```

**Algoritmo:** bcrypt (blowfish) con salt aleatorio.

### 3.2 Control de Acceso por Roles

Se implementaron 5 roles con privilegios diferenciados:

| Rol | Permisos |
|-----|----------|
| **Administrador** | CRUD completo en todas las tablas |
| **Médico** | SELECT en catálogos; CRUD en citas, historias, diagnósticos y prescripciones |
| **Enfermero** | SELECT en catálogos; UPDATE en citas; INSERT en prescripciones |
| **Personal Administrativo** | CRUD en pacientes y citas; SELECT en catálogos |
| **Auditor** | SELECT solo en auditoría e historias clínicas |

### 3.3 Restricciones Adicionales en Aplicación

En el módulo de Django se implementaron restricciones adicionales:

- **Médicos** solo pueden ver prescripciones e historias de **sus propios pacientes**
- **Modificación de stock** restringida a Enfermeros y Administradores
- **Gestión de equipamiento** restringida a Administradores
- **Auditoría** solo visible para Administradores y Auditores

### 3.4 Auditoría de Accesos

Cada operación sensible se registra automáticamente:

```sql
INSERT INTO Auditoria_Accesos 
(id_emp, accion, tabla_afectada, id_registro_afectado, ip_origen)
VALUES (%s, %s, %s, %s, %s)
```

Acciones registradas: LOGIN, LOGOUT, SELECT, INSERT, UPDATE, DELETE

---

## 4. CONSULTAS ANALÍTICAS

### 4.1 Consultas Requeridas Implementadas

#### Consulta 1: Medicamentos más recetados por sede (último mes)
```sql
SELECT s.nom_sede, m.nom_med, COUNT(pr.id_presc) AS total
FROM Prescripciones pr
INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
INNER JOIN Citas c ON pr.id_cita = c.id_cita
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE pr.fecha_emision >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY s.nom_sede, m.nom_med
ORDER BY total DESC;
```

#### Consulta 2: Médicos con más consultas por semana
```sql
SELECT nombre_medico, nom_sede, semana, total_consultas
FROM vista_medicos_consultas
ORDER BY semana DESC, total_consultas DESC;
```

#### Consulta 3: Tiempo promedio cita → diagnóstico
```sql
SELECT nom_sede, nom_dept, 
       ROUND(AVG(EXTRACT(EPOCH FROM (fecha_registro - fecha_hora))/3600), 2) AS horas
FROM Citas c
INNER JOIN Diagnostico d ON d.id_cita = c.id_cita
INNER JOIN Historias_Clinicas hc ON d.cod_hist = hc.cod_hist
GROUP BY nom_sede, nom_dept;
```

#### Consulta 4: Últimos 10 accesos a Historias_Clinicas
```sql
SELECT * FROM vista_auditoria_historias
LIMIT 10;
```

#### Consulta 5: Departamentos que comparten equipamiento
```sql
WITH equipo_compartido AS (
    SELECT nom_eq, marca_modelo
    FROM Equipamiento
    GROUP BY nom_eq, marca_modelo
    HAVING COUNT(DISTINCT id_sede) > 1
)
SELECT ec.nom_eq, s.nom_sede, d.nom_dept
FROM equipo_compartido ec
INNER JOIN Equipamiento eq ON ec.nom_eq = eq.nom_eq
INNER JOIN Sedes_Hospitalarias s ON eq.id_sede = s.id_sede
INNER JOIN Departamentos d ON eq.id_dept = d.id_dept;
```

#### Consulta 6: Pacientes por enfermedad y sede
```sql
SELECT nom_sede, nombre_enfermedad, 
       COUNT(DISTINCT cod_pac) AS total_pacientes
FROM vista_enfermedades_por_sede
GROUP BY nom_sede, nombre_enfermedad;
```

#### Consulta 7: Vista consolidada de historias clínicas
```sql
SELECT * FROM vista_historias_consolidadas
ORDER BY fecha_registro DESC;
```

### 4.2 Consultas Adicionales Implementadas

El sistema incluye 8 consultas analíticas adicionales:

1. Top 5 enfermedades en último trimestre
2. Consumo de medicamentos por departamento
3. Utilización de recursos por sede
4. Índices de atención y tiempos de espera
5. Especialidades más demandadas
6. Inventario crítico con proyección de consumo
7. Productividad del personal médico
8. Tendencias de enfermedades con variación porcentual

---

## 5. MODELO DE DATOS

### 5.1 Normalización

El esquema está normalizado hasta **Tercera Forma Normal (3FN)**:

- **1FN:** Todos los atributos son atómicos
- **2FN:** No hay dependencias parciales (claves simples o compuestas completas)
- **3FN:** No hay dependencias transitivas (separación de Personas de Empleados/Pacientes)

### 5.2 Tablas Implementadas

Se implementaron **18 tablas** organizadas en:

| Categoría | Tablas |
|-----------|--------|
| **Catálogos** | Roles, Especialidades, Enfermedades, Catalogo_Medicamentos |
| **Estructura** | Sedes_Hospitalarias, Departamentos |
| **Actores** | Personas, Empleados, Pacientes, Emp_Posee_Esp |
| **Operaciones** | Citas, Historias_Clinicas, Diagnostico, Prescripciones |
| **Recursos** | Equipamiento, Inventario_Farmacia |
| **Sistema** | Auditoria_Accesos, Reportes_Generados |

---

## 6. APLICACIÓN WEB

### 6.1 Módulos Implementados

| Módulo | Funcionalidades |
|--------|-----------------|
| **Autenticación** | Login, logout, cambio de contraseña |
| **Pacientes** | CRUD de pacientes, historial de citas |
| **Citas** | Programación, seguimiento, cancelación |
| **Historias Clínicas** | Consulta, diagnósticos, prescripciones |
| **Farmacia** | Inventario, alertas de stock, catálogo |
| **Equipamiento** | Gestión de equipos, mantenimiento |
| **Reportes** | 15 reportes analíticos |
| **Auditoría** | Logs de acceso, filtros por tabla |
| **Administración** | Gestión de empleados, sedes, roles |

### 6.2 Arquitectura de la Aplicación

```
hospital_manager/
├── cashier/
│   ├── views.py          # 1400+ líneas de vistas
│   ├── forms.py          # Formularios y validación
│   ├── urls.py           # Rutas de la aplicación
│   └── templates/        # Plantillas HTML
├── templates/
│   └── main.html         # Template base
└── static/
    └── styles.css        # Estilos CSS
```

---

## 7. RESULTADOS

### 7.1 Métricas del Sistema

| Métrica | Valor |
|---------|-------|
| Tablas creadas | 18 |
| Vistas distribuidas | 10 |
| Consultas analíticas | 15 |
| Roles de usuario | 5 |
| Endpoints de API | 6 |
| Plantillas HTML | 12 |

### 7.2 Funcionalidades Clave

✅ Base de datos distribuida con particionamiento por sede  
✅ Replicación de datos críticos (historias, catálogos)  
✅ Encriptación de contraseñas con bcrypt  
✅ Control de acceso basado en roles (RBAC)  
✅ Auditoría completa de accesos  
✅ Módulo de analítica con 15 reportes  
✅ Aplicación web funcional con Django  

---

## 8. CONCLUSIONES

El sistema HIS+ cumple con todos los requisitos especificados:

1. **Distribución de datos:** Implementada mediante particionamiento por `id_sede` y vistas consolidadas.

2. **Gestión de roles:** 5 roles con privilegios específicos tanto a nivel de base de datos como en la aplicación.

3. **Seguridad:** Contraseñas encriptadas con pgcrypto, control de acceso por rol, y auditoría completa.

4. **Replicación:** Vistas distribuidas que consolidan datos de todas las sedes con acceso en tiempo real.

5. **Analítica:** 15 consultas que cubren todas las métricas requeridas (frecuencia de enfermedades, consumo de medicamentos, utilización de recursos, tiempos de espera).

El sistema está listo para su despliegue en un entorno de producción con múltiples sedes hospitalarias.

---

## 9. ANEXOS

### Archivos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `script_creacion.sql` | Creación de tablas, roles, permisos y vistas |
| `script_datos_prueba.sql` | Datos de prueba para testing |
| `script_consultas.sql` | Consultas analíticas requeridas |
| `Diccionario_de_Datos.md` | Documentación de campos y tipos |
| `Esquema_Distribucion_Replicacion.md` | Mapa de nodos y estrategia de sync |

### Credenciales de Prueba

Ver archivo `usuarios_hospital.txt` para credenciales de acceso de prueba.
