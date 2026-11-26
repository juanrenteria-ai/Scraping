"""Ensambla la carpeta _site/ que se publica en GitHub Pages.

Estructura resultante:
    _site/index.html, styles.css, app.js   <- sitio web (carpeta sitio/)
    _site/data/articulos.csv               <- datos del scraping (los lee app.js)
    _site/reporte/index.html               <- notebook ejecutado convertido a HTML (opcional)

Uso:
    python scripts/construir_sitio.py [--reporte RUTA_HTML] [--salida _site]
"""
import argparse
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def construir(salida: Path, reporte: Path | None = None) -> Path:
    origen_sitio = RAIZ / "sitio"
    csv = RAIZ / "data" / "articulos.csv"
    for requerido in (origen_sitio / "index.html", origen_sitio / "styles.css", origen_sitio / "app.js", csv):
        if not requerido.exists():
            raise FileNotFoundError(f"Falta {requerido.relative_to(RAIZ)}")

    if salida.exists():
        shutil.rmtree(salida)
    shutil.copytree(origen_sitio, salida)
    (salida / "data").mkdir()
    shutil.copy2(csv, salida / "data" / "articulos.csv")

    if reporte is not None:
        if not reporte.exists():
            raise FileNotFoundError(f"No existe el reporte {reporte}")
        (salida / "reporte").mkdir()
        shutil.copy2(reporte, salida / "reporte" / "index.html")
    (salida / ".nojekyll").touch()          # Pages sirve los archivos tal cual, sin procesarlos con Jekyll
    return salida


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--salida", default="_site", type=Path)
    p.add_argument("--reporte", default=None, type=Path, help="HTML del notebook ejecutado (opcional)")
    a = p.parse_args()
    try:
        destino = construir(a.salida, a.reporte)
    except FileNotFoundError as e:
        sys.exit(f"ERROR: {e}")
    print(f"Sitio listo en {destino}/")
