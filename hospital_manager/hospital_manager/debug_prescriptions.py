import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospital_manager.settings')
django.setup()

def debug_prescriptions():
    with connection.cursor() as cursor:
        print("--- Dumping Last 5 Prescriptions ---")
        cursor.execute("""
            SELECT pr.id_presc, pr.cod_med, pr.cod_hist, pr.id_cita, pr.fecha_emision,
                   m.nom_med,
                   p.nom_persona || ' ' || p.apellido_persona as paciente
            FROM Prescripciones pr
            LEFT JOIN Catalogo_Medicamentos m ON pr.cod_med = m.cod_med
            LEFT JOIN Historias_Clinicas hc ON pr.cod_hist = hc.cod_hist
            LEFT JOIN Pacientes pac ON hc.cod_pac = pac.cod_pac
            LEFT JOIN Personas p ON pac.id_persona = p.id_persona
            ORDER BY pr.id_presc DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        for row in rows:
            print(f"ID: {row[0]}, Med: {row[5]}, Hist: {row[2]}, Cita: {row[3]}, Date: {row[4]}, Patient: {row[6]}")

        print("\n--- Checking Doctor-Patient Links (Citas) ---")
        # Check if any doctor has a link to Patricia Vargas (assuming we can find her)
        cursor.execute("SELECT cod_pac, id_emp FROM Citas ORDER BY fecha_hora DESC LIMIT 10")
        links = cursor.fetchall()
        for link in links:
            print(f"Pac: {link[0]} linked to Emp: {link[1]}")

if __name__ == '__main__':
    debug_prescriptions()
