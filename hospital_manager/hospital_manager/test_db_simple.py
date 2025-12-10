"""
Script de diagnóstico SIMPLIFICADO (sin Django)
Usa psycopg2 directamente para verificar la base de datos
"""
import sys

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 no está instalado. Intenta: pip install psycopg2-binary")
    sys.exit(1)

# Configuración de conexión (igual que en settings.py)
DB_CONFIG = {
    'dbname': 'Hospital',
    'user': 'postgres',
    'password': 'postgres',
    'host': '127.0.0.1',
    'port': '5432'
}

def test_all():
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DE CONEXIÓN - HOSPITAL HIS+")
    print("=" * 60)
    
    # Test 1: Conexión
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conexión a PostgreSQL: EXITOSA")
    except Exception as e:
        print(f"❌ Conexión a PostgreSQL: FALLIDA")
        print(f"   Error: {e}")
        print("\n⚠️  Verifica que PostgreSQL esté corriendo y que la base de datos 'Hospital' exista")
        return
    
    cursor = conn.cursor()
    
    # Test 2: Verificar tablas
    print("\n" + "-" * 60)
    print("VERIFICACIÓN DE TABLAS")
    print("-" * 60)
    
    tables = ['Personas', 'Empleados', 'Roles', 'Pacientes']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  ✅ {table}: {count} registros")
        except Exception as e:
            print(f"  ❌ {table}: Error - {e}")
    
    # Test 3: pgcrypto
    print("\n" + "-" * 60)
    print("VERIFICACIÓN DE EXTENSIÓN PGCRYPTO")
    print("-" * 60)
    
    try:
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'")
        result = cursor.fetchone()
        if result:
            print("  ✅ Extensión pgcrypto: INSTALADA")
        else:
            print("  ❌ Extensión pgcrypto: NO INSTALADA")
            print("     ⚠️ IMPORTANTE: Ejecuta en PostgreSQL:")
            print("     CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 4: Ver empleados
    print("\n" + "-" * 60)
    print("EMPLEADOS REGISTRADOS")
    print("-" * 60)
    
    try:
        cursor.execute("""
            SELECT p.email_persona, r.nombre_rol, e.activo, 
                   CASE WHEN e.hash_contra IS NOT NULL AND e.hash_contra != '' THEN 'SÍ' ELSE 'NO' END as tiene_hash
            FROM Empleados e
            INNER JOIN Personas p ON e.id_persona = p.id_persona
            INNER JOIN Roles r ON e.id_rol = r.id_rol
            ORDER BY e.id_emp LIMIT 5
        """)
        results = cursor.fetchall()
        
        for email, rol, activo, tiene_hash in results:
            estado = "ACTIVO" if activo else "INACTIVO"
            print(f"  - {email}")
            print(f"    Rol: {rol} | Estado: {estado} | Hash: {tiene_hash}")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Test 5: Probar login
    print("\n" + "-" * 60)
    print("PRUEBA DE LOGIN: carlos.rodriguez@hospital.com")
    print("-" * 60)
    
    try:
        # Verificar que el email existe
        cursor.execute("""
            SELECT p.email_persona FROM Empleados e
            INNER JOIN Personas p ON e.id_persona = p.id_persona
            WHERE p.email_persona = 'carlos.rodriguez@hospital.com'
        """)
        if cursor.fetchone():
            print("  ✅ Email encontrado")
        else:
            print("  ❌ Email NO encontrado")
        
        # Probar login con crypt
        cursor.execute("""
            SELECT e.id_emp FROM Empleados e
            INNER JOIN Personas p ON e.id_persona = p.id_persona
            WHERE p.email_persona = 'carlos.rodriguez@hospital.com'
            AND e.hash_contra = crypt('admin123', e.hash_contra)
        """)
        result = cursor.fetchone()
        if result:
            print("  ✅ LOGIN EXITOSO - Contraseña 'admin123' correcta")
        else:
            print("  ❌ LOGIN FALLIDO - Contraseña 'admin123' incorrecta")
            print("     ⚠️ Puede que las contraseñas no se encriptaron correctamente")
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    test_all()
