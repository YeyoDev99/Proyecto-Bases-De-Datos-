from django.db import connection

# ============================================================================
# FUNCIONES HELPER PARA CONSULTAS SQL
# ============================================================================

def ejecutar_query(query, params=None):
    """Ejecuta una query y retorna los resultados"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.fetchall()


def ejecutar_query_one(query, params=None):
    """Ejecuta una query y retorna un solo resultado"""
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, params or [])
            return cursor.fetchone()
    except Exception:
        # En caso de error o sin resultados que pueda lanzar excepción en fetchone si cursor closed?
        # Normalmente fetchone retorna None si no hay data.
        return None


def obtener_choices_from_db(query, params=None):
    """
    Ejecuta una query y retorna choices para un campo Select.
    La query debe retornar (id, nombre)
    """
    results = ejecutar_query(query, params)
    return [(row[0], row[1]) for row in results]


def ejecutar_insert(query, params=None):
    """Ejecuta un INSERT y retorna el ID insertado"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.lastrowid


def ejecutar_update(query, params=None):
    """Ejecuta un UPDATE/DELETE y retorna filas afectadas"""
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        return cursor.rowcount
