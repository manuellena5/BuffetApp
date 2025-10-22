import os
import json
import sqlite3
import traceback
from datetime import datetime
from typing import List, Dict, Optional, Tuple

try:
    import requests
except Exception:
    print("[ERROR] Falta dependencia 'requests'. Instalá con: pip install requests")
    raise

# Config: leer de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_REST = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal,resolution=merge-duplicates"
}

# Ruta a la base local
HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
DB_PATH = os.path.join(ROOT, 'BuffetApp', 'barcancha.db')
LOG_PATH = os.path.join(HERE, 'upload_snapshot_supabase.log')


def _log(msg: str):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(f"{ts} | {msg}\n")
    except Exception:
        pass


def _require_env():
    if not SUPABASE_URL:
        print("[ERROR] SUPABASE_URL no está configurado.")
    if not SUPABASE_ANON_KEY:
        print("[ERROR] SUPABASE_ANON_KEY no está configurado.")
    if not SUPABASE_REST or not SUPABASE_ANON_KEY:
        raise SystemExit("Configura SUPABASE_URL y SUPABASE_ANON_KEY en variables de entorno.")


def _diagnose():
    """Muestra info útil antes de subir: envs, DB path, y prueba de conexión REST."""
    print(f"SUPABASE_URL: {SUPABASE_URL or '(vacío)'}")
    print(f"SUPABASE_REST: {SUPABASE_REST or '(vacío)'}")
    print(f"DB_PATH efectivo: {os.getenv('LOCAL_SQLITE_PATH') or DB_PATH}")
    if SUPABASE_REST and SUPABASE_ANON_KEY:
        try:
            url = f"{SUPABASE_REST}/categorias?select=id&limit=1"
            r = requests.get(url, headers={k: v for k, v in HEADERS.items() if k != "Content-Type"})
            print(f"Prueba GET categorias: HTTP {r.status_code}")
            if r.status_code >= 300:
                print(f"Respuesta: {r.text[:300]}")
        except Exception as e:
            print(f"[WARN] Prueba REST falló: {e}")


def _post_rows(table: str, rows: List[Dict]):
    if not rows:
        return
    url = f"{SUPABASE_REST}/{table}"
    payload = json.dumps(rows, ensure_ascii=False).encode('utf-8')
    r = requests.post(url, headers=HEADERS, data=payload)
    if r.status_code >= 300:
        _log(f"POST {table} failed {r.status_code}: {r.text[:500]}")
        raise RuntimeError(f"POST {table} {r.status_code}: {r.text}")


def upload_categorias(conn: sqlite3.Connection) -> int:
    # La app usa 'Categoria_Producto' con columna 'descripcion'
    cur = conn.cursor()
    try:
        rows = cur.execute("SELECT id, descripcion FROM Categoria_Producto").fetchall()
    except Exception:
        try:
            # fallback: otra variante de nombre
            rows = cur.execute("SELECT id, nombre as descripcion FROM categorias").fetchall()
        except Exception:
            _log("No se encontró tabla Categoria_Producto ni categorias en SQLite local.")
            rows = []
    if not rows:
        return 0
    payload = [{"id": int(r[0]), "descripcion": r[1]} for r in rows if r and r[1]]
    _post_rows("categorias", payload)
    return len(payload)


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    try:
        cur = conn.cursor()
        rows = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        return [r[0] for r in rows]
    except Exception:
        return []


def _find_products_table(conn: sqlite3.Connection) -> Tuple[Optional[str], List[str]]:
    """Busca la tabla de productos y devuelve (nombre_tabla, columnas)."""
    candidates = ["products", "Productos", "producto", "Producto", "product"]
    cur = conn.cursor()
    for name in candidates:
        try:
            cur.execute(f"SELECT 1 FROM {name} LIMIT 1")
            cols = [row[1] for row in cur.execute(f"PRAGMA table_info({name})").fetchall()]
            return name, cols
        except Exception:
            continue
    return None, []


def upload_products(conn: sqlite3.Connection) -> int:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    tbl, cols = _find_products_table(conn)
    if not tbl:
        tables = _list_tables(conn)
        _log(f"No se encontró tabla de productos. Tablas disponibles: {tables}")
        print("[AVISO] No se encontró tabla de productos en la base local.")
        return 0

    # Estrategia: leer todas las filas y mapear columnas existentes
    try:
        rows = cur.execute(f"SELECT * FROM {tbl} ORDER BY 1").fetchall()
    except Exception as e:
        _log(f"No se pudo leer tabla {tbl} en SQLite local: {e}")
        print(f"[ERROR] No se pudo leer tabla {tbl}. Detalle en log.")
        return 0

    def get_val(r: sqlite3.Row, *names, default=None):
        for n in names:
            try:
                if n in r.keys():
                    v = r[n]
                    return v
            except Exception:
                pass
        return default

    payload: List[Dict] = []
    for r in rows:
        pid = get_val(r, 'id')
        cod = get_val(r, 'codigo_producto', 'codigo')
        nombre = get_val(r, 'nombre', 'descripcion')
        precio = get_val(r, 'precio_venta', 'precio', default=0)
        stock = get_val(r, 'stock_actual', default=0)
        contab = get_val(r, 'contabiliza_stock', default=1)
        visible = get_val(r, 'visible', default=1)
        cat_id = get_val(r, 'categoria_id')

        # Requisitos mínimos
        if not nombre:
            # sin nombre no subimos el producto
            continue
        if not cod:
            # si no hay código, usamos el id como código texto para no fallar
            cod = str(pid) if pid is not None else None
        if not cod:
            continue

        payload.append({
            "codigo_producto": str(cod),
            "nombre": str(nombre),
            "precio_venta": float(precio or 0),
            "stock_actual": int(stock or 0),
            "contabiliza_stock": bool(contab) if contab is not None else True,
            "visible": bool(visible) if visible is not None else True,
            "categoria_id": int(cat_id) if cat_id is not None else None,
        })

    if not payload:
        print("[AVISO] No se encontraron productos para subir (payload vacío).")
        return 0

    # Enviar en bloques para evitar payloads muy grandes
    batch_size = 500
    total = 0
    for i in range(0, len(payload), batch_size):
        chunk = payload[i:i+batch_size]
        _post_rows("products", chunk)
        total += len(chunk)
    return total


def main():
    try:
        _require_env()
        _diagnose()
        # Determinar DB local: usar la del paquete si existe; si no, pedir ruta por env DB_PATH
        db_path = os.getenv('LOCAL_SQLITE_PATH', DB_PATH)
        if not os.path.exists(db_path):
            print(f"[ERROR] No se encontró base local en {db_path}")
            print("Sugerencia: seteá $env:LOCAL_SQLITE_PATH con la ruta a tu barcancha.db")
            raise SystemExit(1)

        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            ncat = upload_categorias(conn)
            nprod = upload_products(conn)
            print(f"Categorías subidas: {ncat}")
            print(f"Productos subidos: {nprod}")
            if ncat == 0 and nprod == 0:
                print("[AVISO] No se encontraron filas para subir. Verificá que la base local tenga datos.")
            print("Listo.")
    except SystemExit as se:
        _log(f"SystemExit: {se}")
        raise
    except Exception as e:
        print(f"[ERROR] {e}")
        _log(f"Exception: {e}\n{traceback.format_exc()}")
        raise


if __name__ == "__main__":
    main()
