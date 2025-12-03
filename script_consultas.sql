
-- SCRIPT DE CONSULTAS ANALÍTICAS Y FUNCIONALES

-- 1. Listar los medicamentos más recetados por sede en el último mes
SELECT 
    s.nom_sede,
    s.ciudad,
    m.nom_med,
    COUNT(pr.id_presc) AS total_prescripciones,
    SUM(pr.cantidad_total) AS cantidad_total_recetada
FROM Prescripciones pr
INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
INNER JOIN Citas c ON pr.id_cita = c.id_cita
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE pr.fecha_emision >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY s.id_sede, s.nom_sede, s.ciudad, m.cod_med, m.nom_med
ORDER BY s.nom_sede, total_prescripciones DESC;

-- 2. Mostrar los médicos con mayor número de consultas atendidas por semana
SELECT 
    p.nom_persona || ' ' || p.apellido_persona AS nombre_medico,
    s.nom_sede,
    d.nom_dept,
    esp.nombre_esp AS especialidad,
    DATE_TRUNC('week', c.fecha_hora) AS semana,
    COUNT(c.id_cita) AS total_consultas
FROM Citas c
INNER JOIN Empleados e ON c.id_emp = e.id_emp
INNER JOIN Personas p ON e.id_persona = p.id_persona
INNER JOIN Roles r ON e.id_rol = r.id_rol
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
LEFT JOIN Emp_Posee_Esp epe ON e.id_emp = epe.id_emp
LEFT JOIN Especialidades esp ON epe.id_especialidad = esp.id_especialidad
WHERE r.nombre_rol = 'Medico'
  AND c.estado = 'COMPLETADA'
GROUP BY e.id_emp, p.nom_persona, p.apellido_persona, s.nom_sede, d.nom_dept, 
         esp.nombre_esp, DATE_TRUNC('week', c.fecha_hora)
ORDER BY semana DESC, total_consultas DESC
LIMIT 10;

-- 3. Reportar el tiempo promedio entre la cita y el registro de diagnóstico
SELECT 
    s.nom_sede,
    d.nom_dept,
    ROUND(AVG(EXTRACT(EPOCH FROM (hc.fecha_registro - c.fecha_hora))/3600)::numeric, 2) AS horas_promedio,
    COUNT(*) AS total_casos,
    MIN(EXTRACT(EPOCH FROM (hc.fecha_registro - c.fecha_hora))/3600) AS min_horas,
    MAX(EXTRACT(EPOCH FROM (hc.fecha_registro - c.fecha_hora))/3600) AS max_horas
FROM Citas c
INNER JOIN Diagnostico diag ON diag.id_cita = c.id_cita
INNER JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
WHERE c.estado = 'COMPLETADA'
GROUP BY s.id_sede, s.nom_sede, d.nom_dept
ORDER BY horas_promedio ASC;

-- 4. Generar un informe de auditoría con los últimos 10 accesos a Historias_Clinicas
SELECT 
    aa.id_evento,
    aa.fecha_evento,
    p.nom_persona || ' ' || p.apellido_persona AS empleado,
    r.nombre_rol AS rol,
    s.nom_sede,
    aa.accion,
    aa.id_registro_afectado AS historia_clinica,
    aa.ip_origen
FROM Auditoria_Accesos aa
LEFT JOIN Empleados e ON aa.id_emp = e.id_emp
LEFT JOIN Personas p ON e.id_persona = p.id_persona
LEFT JOIN Roles r ON e.id_rol = r.id_rol
LEFT JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
WHERE aa.tabla_afectada = 'Historias_Clinicas'
ORDER BY aa.fecha_evento DESC
LIMIT 10;

-- 5. Consultar los departamentos que comparten equipamiento con otra sede
WITH equipo_compartido AS (
    SELECT 
        eq.nom_eq,
        eq.marca_modelo,
        COUNT(DISTINCT eq.id_sede) AS sedes_con_equipo
    FROM Equipamiento eq
    GROUP BY eq.nom_eq, eq.marca_modelo
    HAVING COUNT(DISTINCT eq.id_sede) > 1
)
SELECT 
    ec.nom_eq,
    ec.marca_modelo,
    s.nom_sede,
    s.ciudad,
    d.nom_dept,
    eq.estado_equipo,
    eq.fecha_ultimo_maint
FROM equipo_compartido ec
INNER JOIN Equipamiento eq ON ec.nom_eq = eq.nom_eq AND ec.marca_modelo = eq.marca_modelo
INNER JOIN Sedes_Hospitalarias s ON eq.id_sede = s.id_sede
INNER JOIN Departamentos d ON eq.id_dept = d.id_dept AND eq.id_sede = d.id_sede
ORDER BY ec.nom_eq, s.nom_sede;

-- 6. Calcular el total de pacientes atendidos por enfermedad y por sede
SELECT 
    s.nom_sede,
    s.ciudad,
    enf.nombre_enfermedad,
    COUNT(DISTINCT hc.cod_pac) AS total_pacientes,
    COUNT(diag.id_diagnostico) AS total_diagnosticos,
    ROUND((COUNT(DISTINCT hc.cod_pac)::numeric / 
           (SELECT COUNT(DISTINCT hc2.cod_pac) 
            FROM Historias_Clinicas hc2
            INNER JOIN Citas c2 ON hc2.cod_pac = c2.cod_pac
            WHERE c2.id_sede = s.id_sede) * 100), 2) AS porcentaje_pacientes
FROM Diagnostico diag
INNER JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
INNER JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
INNER JOIN Citas c ON diag.id_cita = c.id_cita
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
GROUP BY s.id_sede, s.nom_sede, s.ciudad, enf.id_enfermedad, enf.nombre_enfermedad
ORDER BY s.nom_sede, total_pacientes DESC;

-- 7. Vista consolidada de historias clínicas replicadas entre todas las sedes
--    (Utilizando la vista ya creada)
SELECT * FROM vista_historias_consolidadas
ORDER BY fecha_registro DESC;

-- CONSULTAS ADICIONALES PARA ANÁLISIS MÉDICO

-- 8. Top 5 enfermedades más tratadas por departamento en el último trimestre
SELECT 
    d.nom_dept,
    s.nom_sede,
    enf.nombre_enfermedad,
    COUNT(diag.id_diagnostico) AS total_casos,
    COUNT(DISTINCT hc.cod_pac) AS pacientes_unicos
FROM Diagnostico diag
INNER JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
INNER JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
INNER JOIN Citas c ON diag.id_cita = c.id_cita
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '3 months'
GROUP BY d.id_dept, d.nom_dept, s.nom_sede, enf.id_enfermedad, enf.nombre_enfermedad
ORDER BY d.nom_dept, total_casos DESC
LIMIT 5;

-- 9. Consumo de medicamentos por departamento (últimos 30 días)
SELECT 
    d.nom_dept,
    s.nom_sede,
    m.nom_med,
    m.principio_activo,
    COUNT(pr.id_presc) AS total_prescripciones,
    SUM(pr.cantidad_total) AS cantidad_consumida,
    ROUND(AVG(pr.duracion_dias)::numeric, 1) AS duracion_promedio_dias
FROM Prescripciones pr
INNER JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
INNER JOIN Citas c ON pr.id_cita = c.id_cita
INNER JOIN Departamentos d ON c.id_dept = d.id_dept AND c.id_sede = d.id_sede
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE pr.fecha_emision >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY d.id_dept, d.nom_dept, s.nom_sede, m.cod_med, m.nom_med, m.principio_activo
ORDER BY s.nom_sede, cantidad_consumida DESC;

-- 10. Utilización de recursos por sede (último mes)
SELECT 
    s.id_sede,
    s.nom_sede,
    s.ciudad,
    COUNT(DISTINCT c.id_cita) AS total_citas,
    COUNT(DISTINCT CASE WHEN c.estado = 'COMPLETADA' THEN c.id_cita END) AS citas_completadas,
    COUNT(DISTINCT CASE WHEN c.estado = 'PROGRAMADA' THEN c.id_cita END) AS citas_programadas,
    COUNT(DISTINCT hc.cod_hist) AS historias_clinicas,
    COUNT(DISTINCT eq.cod_eq) AS total_equipamiento,
    COUNT(DISTINCT CASE WHEN eq.estado_equipo = 'OPERATIVO' THEN eq.cod_eq END) AS equipo_operativo,
    COUNT(DISTINCT e.id_emp) AS total_empleados,
    COUNT(DISTINCT pac.cod_pac) AS pacientes_atendidos,
    ROUND((COUNT(DISTINCT CASE WHEN c.estado = 'COMPLETADA' THEN c.id_cita END)::numeric / 
           NULLIF(COUNT(DISTINCT c.id_cita), 0) * 100), 2) AS tasa_efectividad
FROM Sedes_Hospitalarias s
LEFT JOIN Citas c ON s.id_sede = c.id_sede 
    AND c.fecha_hora >= CURRENT_DATE - INTERVAL '1 month'
LEFT JOIN Historias_Clinicas hc ON c.cod_pac = hc.cod_pac
LEFT JOIN Equipamiento eq ON s.id_sede = eq.id_sede
LEFT JOIN Empleados e ON s.id_sede = e.id_sede AND e.activo = TRUE
LEFT JOIN Pacientes pac ON c.cod_pac = pac.cod_pac
GROUP BY s.id_sede, s.nom_sede, s.ciudad
ORDER BY s.nom_sede;

-- 11. Índices de atención y tiempos promedio de espera por sede
SELECT 
    s.nom_sede,
    s.ciudad,
    COUNT(c.id_cita) AS total_citas,
    ROUND(AVG(EXTRACT(EPOCH FROM (c.fecha_hora - c.fecha_hora_solicitada))/86400)::numeric, 1) AS dias_espera_promedio,
    MIN(EXTRACT(EPOCH FROM (c.fecha_hora - c.fecha_hora_solicitada))/86400) AS min_dias_espera,
    MAX(EXTRACT(EPOCH FROM (c.fecha_hora - c.fecha_hora_solicitada))/86400) AS max_dias_espera,
    COUNT(CASE WHEN c.tipo_servicio = 'Urgencia' THEN 1 END) AS urgencias,
    COUNT(CASE WHEN c.tipo_servicio = 'Consulta' THEN 1 END) AS consultas_programadas
FROM Citas c
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY s.id_sede, s.nom_sede, s.ciudad
ORDER BY dias_espera_promedio ASC;

-- 12. Análisis de especialidades más demandadas
SELECT 
    esp.nombre_esp AS especialidad,
    s.nom_sede,
    COUNT(c.id_cita) AS total_consultas,
    COUNT(DISTINCT c.cod_pac) AS pacientes_unicos,
    COUNT(DISTINCT e.id_emp) AS medicos_disponibles,
    ROUND(COUNT(c.id_cita)::numeric / NULLIF(COUNT(DISTINCT e.id_emp), 0), 1) AS consultas_por_medico
FROM Especialidades esp
INNER JOIN Emp_Posee_Esp epe ON esp.id_especialidad = epe.id_especialidad
INNER JOIN Empleados e ON epe.id_emp = e.id_emp
INNER JOIN Citas c ON e.id_emp = c.id_emp
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '1 month'
GROUP BY esp.id_especialidad, esp.nombre_esp, s.nom_sede
ORDER BY total_consultas DESC;

-- 13. Análisis de inventario crítico por sede
SELECT 
    s.nom_sede,
    s.ciudad,
    m.nom_med,
    m.principio_activo,
    i.stock_actual,
    CASE 
        WHEN i.stock_actual < 10 THEN 'CRÍTICO'
        WHEN i.stock_actual < 50 THEN 'BAJO'
        WHEN i.stock_actual < 100 THEN 'MEDIO'
        ELSE 'ÓPTIMO'
    END AS nivel_alerta,
    i.fecha_actualizacion,
    -- Proyección de consumo basado en prescripciones del último mes
    COALESCE(
        (SELECT SUM(pr.cantidad_total) 
         FROM Prescripciones pr
         INNER JOIN Citas c ON pr.id_cita = c.id_cita
         WHERE pr.cod_med = m.cod_med 
           AND c.id_sede = s.id_sede
           AND pr.fecha_emision >= CURRENT_DATE - INTERVAL '30 days'), 0
    ) AS consumo_ultimo_mes
FROM Inventario_Farmacia i
INNER JOIN Sedes_Hospitalarias s ON i.id_sede = s.id_sede
INNER JOIN Catalogo_Medicamentos m ON i.cod_med = m.cod_med
WHERE i.stock_actual < 100
ORDER BY 
    CASE 
        WHEN i.stock_actual < 10 THEN 1
        WHEN i.stock_actual < 50 THEN 2
        ELSE 3
    END,
    s.nom_sede, i.stock_actual ASC;

-- 14. Reporte de productividad del personal médico
SELECT 
    p.nom_persona || ' ' || p.apellido_persona AS nombre_medico,
    r.nombre_rol,
    s.nom_sede,
    d.nom_dept,
    STRING_AGG(DISTINCT esp.nombre_esp, ', ') AS especialidades,
    COUNT(c.id_cita) AS total_consultas,
    COUNT(CASE WHEN c.estado = 'COMPLETADA' THEN 1 END) AS consultas_completadas,
    COUNT(DISTINCT c.cod_pac) AS pacientes_unicos,
    COUNT(DISTINCT hc.cod_hist) AS historias_generadas,
    ROUND((COUNT(CASE WHEN c.estado = 'COMPLETADA' THEN 1 END)::numeric / 
           NULLIF(COUNT(c.id_cita), 0) * 100), 2) AS tasa_cumplimiento
FROM Empleados e
INNER JOIN Personas p ON e.id_persona = p.id_persona
INNER JOIN Roles r ON e.id_rol = r.id_rol
INNER JOIN Sedes_Hospitalarias s ON e.id_sede = s.id_sede
INNER JOIN Departamentos d ON e.id_dept = d.id_dept AND e.id_sede = d.id_sede
LEFT JOIN Emp_Posee_Esp epe ON e.id_emp = epe.id_emp
LEFT JOIN Especialidades esp ON epe.id_especialidad = esp.id_especialidad
LEFT JOIN Citas c ON e.id_emp = c.id_emp 
    AND c.fecha_hora >= CURRENT_DATE - INTERVAL '1 month'
LEFT JOIN Diagnostico diag ON c.id_cita = diag.id_cita
LEFT JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
WHERE r.nombre_rol IN ('Medico', 'Enfermero')
  AND e.activo = TRUE
GROUP BY e.id_emp, p.nom_persona, p.apellido_persona, r.nombre_rol, s.nom_sede, d.nom_dept
ORDER BY total_consultas DESC;

-- 15. Análisis de tendencias de enfermedades por mes
SELECT 
    DATE_TRUNC('month', c.fecha_hora) AS mes,
    enf.nombre_enfermedad,
    s.nom_sede,
    COUNT(diag.id_diagnostico) AS casos,
    COUNT(DISTINCT hc.cod_pac) AS pacientes_unicos,
    LAG(COUNT(diag.id_diagnostico)) OVER (
        PARTITION BY enf.id_enfermedad, s.id_sede 
        ORDER BY DATE_TRUNC('month', c.fecha_hora)
    ) AS casos_mes_anterior,
    ROUND(
        (COUNT(diag.id_diagnostico) - 
         LAG(COUNT(diag.id_diagnostico)) OVER (
             PARTITION BY enf.id_enfermedad, s.id_sede 
             ORDER BY DATE_TRUNC('month', c.fecha_hora)
         ))::numeric / 
        NULLIF(LAG(COUNT(diag.id_diagnostico)) OVER (
            PARTITION BY enf.id_enfermedad, s.id_sede 
            ORDER BY DATE_TRUNC('month', c.fecha_hora)
        ), 0) * 100, 2
    ) AS variacion_porcentual
FROM Diagnostico diag
INNER JOIN Enfermedades enf ON diag.id_enfermedad = enf.id_enfermedad
INNER JOIN Historias_Clinicas hc ON diag.cod_hist = hc.cod_hist
INNER JOIN Citas c ON diag.id_cita = c.id_cita
INNER JOIN Sedes_Hospitalarias s ON c.id_sede = s.id_sede
WHERE c.fecha_hora >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', c.fecha_hora), enf.id_enfermedad, enf.nombre_enfermedad, s.id_sede, s.nom_sede
ORDER BY mes DESC, casos DESC;