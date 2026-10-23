"""
Juegos de PS5 - Juegos y desarrolladores en SQLite
---------------------------------------------------
Crea la carpeta "datos" (junto a este script) y guarda ahí:
  - juegos_ps5.db        -> base de datos SQLite
  - reporte_juegos.txt   -> reporte de juegos (opción G)

Tablas:
  desarrolladores (id, nombre, pais)
  juegos          (id, titulo, desarrollador_id, estado)

Relación: un desarrollador puede tener muchos juegos (1 a N).
El campo "estado" del juego puede ser:
  'disponible' | 'vendido' | 'prestado'

Los datos se conservan entre ejecuciones.

Uso:  python juegos_ps5.py
"""

import sqlite3
from pathlib import Path

CARPETA_DATOS = Path(__file__).resolve().parent / "datos"
DB_NAME = CARPETA_DATOS / "juegos_ps5.db"
REPORTE = CARPETA_DATOS / "reporte_juegos.txt"

ESQUEMA = """
CREATE TABLE IF NOT EXISTS desarrolladores (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    pais   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS juegos (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo           TEXT    NOT NULL,
    desarrollador_id INTEGER NOT NULL,
    estado           TEXT    NOT NULL DEFAULT 'disponible'
                     CHECK (estado IN ('disponible', 'vendido', 'prestado')),
    FOREIGN KEY (desarrollador_id) REFERENCES desarrolladores(id)
);
"""

# ----------------------------- Datos iniciales -----------------------------

DESARROLLADORES = [
    ("Insomniac Games", "Estados Unidos"),
    ("Santa Monica Studio", "Estados Unidos"),
    ("Team Asobi", "Japón"),
    ("Guerrilla Games", "Países Bajos"),
    ("Housemarque", "Finlandia"),
]

# (titulo, desarrollador_id)
JUEGOS = [
    ("Marvel's Spider-Man 2", 1),
    ("God of War Ragnarök", 2),
    ("Astro Bot", 3),
    ("Horizon Forbidden West", 4),
    ("Returnal", 5),
]

ETIQUETAS = {
    "disponible": "DISPONIBLE",
    "vendido": "VENDIDO",
    "prestado": "PRESTADO",
}

# ------------------------------ Base de datos ------------------------------


def conectar() -> sqlite3.Connection:
    CARPETA_DATOS.mkdir(parents=True, exist_ok=True)  # crea la carpeta "datos"
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA foreign_keys = ON;")
    con.executescript(ESQUEMA)
    sembrar_datos(con)
    return con


def sembrar_datos(con: sqlite3.Connection) -> None:
    """Inserta los 5 desarrolladores y los 5 juegos solo la primera vez."""
    if con.execute("SELECT COUNT(*) FROM juegos").fetchone()[0] > 0:
        return
    con.executemany(
        "INSERT INTO desarrolladores (nombre, pais) VALUES (?, ?)", DESARROLLADORES)
    con.executemany(
        "INSERT INTO juegos (titulo, desarrollador_id) VALUES (?, ?)", JUEGOS)
    con.commit()


# --------------------------------- Consultas --------------------------------


def lista_desarrolladores(con: sqlite3.Connection) -> str:
    lineas = ["=== DESARROLLADORES ==="]
    for did, nombre, pais in con.execute(
            "SELECT id, nombre, pais FROM desarrolladores ORDER BY id"):
        lineas.append(f"  {did}. {nombre} ({pais})")
    return "\n".join(lineas)


def lista_juegos(con: sqlite3.Connection) -> str:
    lineas = ["=== JUEGOS DE PS5 ==="]
    for jid, titulo, estudio, estado in con.execute("""
        SELECT j.id, j.titulo, d.nombre, j.estado
        FROM juegos j
        JOIN desarrolladores d ON d.id = j.desarrollador_id
        ORDER BY j.id
    """):
        lineas.append(f"  {jid}. {titulo} - {estudio} [{ETIQUETAS[estado]}]")
    return "\n".join(lineas)


def buscar_juego(con: sqlite3.Connection, juego_id: int):
    return con.execute("""
        SELECT j.titulo, d.nombre, j.estado
        FROM juegos j
        JOIN desarrolladores d ON d.id = j.desarrollador_id
        WHERE j.id = ?
    """, (juego_id,)).fetchone()


# --------------------------------- Acciones ---------------------------------


def cambiar_estado(con: sqlite3.Connection, juego_id: int) -> None:
    juego = buscar_juego(con, juego_id)
    if juego is None:
        print("No existe un juego con ese número.\n")
        return

    titulo, estudio, estado = juego
    print(f"Juego seleccionado: {titulo} - {estudio} (estado actual: {ETIQUETAS[estado]})")
    print("  1 = Vendido   2 = Prestado   3 = Disponible (devuelto)")
    opcion = input("Elige 1, 2 o 3: ").strip()
    nuevo = {"1": "vendido", "2": "prestado", "3": "disponible"}.get(opcion)
    if nuevo is None:
        print("Opción no válida.\n")
        return

    con.execute("UPDATE juegos SET estado = ? WHERE id = ?", (nuevo, juego_id))
    con.commit()  # se guarda en datos/juegos_ps5.db
    print(f"Listo: '{titulo}' ahora está {ETIQUETAS[nuevo]}.\n")


def guardar_reporte(con: sqlite3.Connection) -> None:
    texto = "\n".join([
        "REPORTE DE JUEGOS DE PS5", "",
        lista_desarrolladores(con), "",
        lista_juegos(con), "",
    ])
    REPORTE.write_text(texto, encoding="utf-8")
    print(f"Reporte guardado en: {REPORTE}\n")


# ------------------------------------ Menú ----------------------------------


def main() -> None:
    con = conectar()
    print(f"Base de datos: {DB_NAME}\n")
    try:
        while True:
            print(lista_desarrolladores(con))
            print()
            print(lista_juegos(con))
            entrada = input(
                "\nEscribe el NÚMERO del juego para marcarlo como vendido o prestado | "
                "G = guardar reporte | S = salir: "
            ).strip().lower()
            print()

            if entrada == "s":
                break
            elif entrada == "g":
                guardar_reporte(con)
            elif entrada.isdigit():
                cambiar_estado(con, int(entrada))
            else:
                print("Opción no válida.\n")
    finally:
        con.close()
        print("Datos guardados en la carpeta 'datos'. ¡Hasta la próxima!")


if __name__ == "__main__":
    main()
