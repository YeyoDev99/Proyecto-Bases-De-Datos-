"""
Script de Diagnóstico de Conexión a Base de Datos y Login
Ejecutar: python test_db_connection.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automatic_cashier.settings')
django.setup()

from django.db import connection

def test_connection():
    """Prueba la conexión básica a la base de datos"""
    print("=" * 60)
    print("DIAGNÓSTICO DE CONEXIÓN - HOSPITAL HIS+")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print("✅ Conexión a PostgreSQL: EXITOSA")
            return True
    except Exception as e:
        print(f"❌ Conexión a PostgreSQL: FALLIDA")
        print(f"   Error: {e}")
        return False

def test_tables():
    """Verifica que las tablas principales existan"""
    print("\n" + "-" * 60)
    print("VERIFICACIÓN DE TABLAS")
    print("-" * 60)
    
    tables = ['Personas', 'Empleados', 'Roles', 'Pacientes', 'Citas', 'Sedes_Hospitalarias']
    
    try:
        with connection.cursor() as cursor:
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} registros")
    except Exception as e:
        print(f"  ❌ Error verificando tablas: {e}")
        return False
    return True

def test_pgcrypto():
    """Verifica que la extensión pgcrypto esté instalada"""
    print("\n" + "-" * 60)
    print("VERIFICACIÓN DE EXTENSIÓN PGCRYPTO")
    print("-" * 60)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'")
            result = cursor.fetchone()
            if result:
                print("  ✅ Extensión pgcrypto: INSTALADA")
                return True
            else:
                print("  ❌ Extensión pgcrypto: NO INSTALADA")
                print("     Ejecuta: CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                return False
    except Exception as e:
        print(f"  ❌ Error verificando pgcrypto: {e}")
        return False

def test_empleados_login():
    """Verifica los datos de empleados para login"""
    print("\n" + "-" * 60)
    print("VERIFICACIÓN DE EMPLEADOS PARA LOGIN")
    print("-" * 60)
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT p.email_persona, r.nombre_rol, e.activo, e.hash_contra
                FROM Empleados e
                INNER JOIN Personas p ON e.id_persona = p.id_persona
                INNER JOIN Roles r ON e.id_rol = r.id_rol
                ORDER BY e.id_emp
                LIMIT 5
            """)
            results = cursor.fetchall()
            
            if not results:
                print("  ❌ No hay empleados registrados")
                return False
            
            print("  Empleados encontrados:")
            for row in results:
                email, rol, activo, hash_contra = row
                estado = "ACTIVO" if activo else "INACTIVO"
                tiene_hash = "SÍ" if hash_contra else "NO"
                print(f"    - {email}")
                print(f"      Rol: {rol} | Estado: {estado} | Hash Password: {tiene_hash}")
            return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def test_login_query(email, password):
    """Prueba la consulta de login específica"""
    print("\n" + "-" * 60)
    print(f"PRUEBA DE LOGIN: {email}")
    print("-" * 60)
    
    try:
        with connection.cursor() as cursor:
            # Primero verificar si el email existe
            cursor.execute("""
                SELECT p.email_persona, e.id_emp, e.activo
                FROM Empleados e
                INNER JOIN Personas p ON e.id_persona = p.id_persona
                WHERE p.email_persona = %s
            """, [email])
            user_exists = cursor.fetchone()
            
            if not user_exists:
                print(f"  ❌ El email '{email}' NO existe en la base de datos")
                return False
            
            print(f"  ✅ Email encontrado (id_emp: {user_exists[1]}, activo: {user_exists[2]})")
            
            # Ahora probar con la contraseña
            cursor.execute("""
                SELECT e.id_emp, e.activo
                FROM Empleados e
                INNER JOIN Personas p ON e.id_persona = p.id_persona
                WHERE p.email_persona = %s 
                AND e.hash_contra = crypt(%s, e.hash_contra)
            """, [email, password])
            login_result = cursor.fetchone()
            
            if login_result:
                print(f"  ✅ LOGIN EXITOSO - Contraseña correcta")
                return True
            else:
                print(f"  ❌ LOGIN FALLIDO - Contraseña incorrecta")
                return False
    except Exception as e:
        print(f"  ❌ Error en query de login: {e}")
        return False

if __name__ == "__main__":
    print("\n")
    
    # Test 1: Conexión básica
    if not test_connection():
        print("\n⚠️  No se puede continuar sin conexión a la base de datos")
        sys.exit(1)
    
    # Test 2: Verificar tablas
    test_tables()
    
    # Test 3: Verificar pgcrypto
    test_pgcrypto()
    
    # Test 4: Ver empleados
    test_empleados_login()
    
    # Test 5: Probar login con credenciales de prueba
    print("\n" + "=" * 60)
    print("PRUEBAS DE LOGIN CON CREDENCIALES DEL SCRIPT DE DATOS")
    print("=" * 60)
    
    test_login_query("carlos.rodriguez@hospital.com", "admin123")
    test_login_query("maria.gonzalez@hospital.com", "medico123")
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 60 + "\n")
