"""Pruebas del listado de artículos (vista de resultados de MercadoLibre) y del sitio web.

Se extrae del notebook el código de `a_entero` y `extraer_listado` para probarlo sin red ni navegador.
"""
import csv
import re
import sys
from datetime import datetime
from pathlib import Path

import nbformat
import pytest
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent.parent
NOTEBOOK = RAIZ / "scraping_mercadolibre.ipynb"
HTML_LISTADO = RAIZ / "data" / "pagina_listado.html"
CSV_ARTICULOS = RAIZ / "data" / "articulos.csv"

TARJETA = """
<li class="ui-search-layout__item"><div class="poly-card">
  <a class="poly-component__title" href="https://www.mercadolibre.com.co/apple-iphone-16/p/MCO40287800#polycard_client=search">Apple iPhone 16 (128 GB) - color azul</a>
  <div class="poly-component__price">
    <s class="andes-money-amount--previous" aria-label="Antes: 6349000 pesos colombianos"><span class="andes-money-amount__fraction">6.349.000</span></s>
    <div class="poly-price__current">
      <span class="andes-money-amount" aria-label="2879900 pesos colombianos"><span class="andes-money-amount__fraction">2.879.900</span></span>
      <span class="poly-price__discount-polylabel"><span class="polylabel-pill">54% OFF</span></span>
    </div>
    <span class="poly-price__installments">12 cuotas de $ 239.992 con 0% interés</span>
  </div>
  <div class="poly-component__shipping-v2"><span>Envío gratis Envío gratis</span></div>
  <img class="poly-component__picture" src="https://http2.mlstatic.com/foto.webp">
</div></li>
"""


@pytest.fixture(scope="module")
def ns():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    espacio = {"re": re, "datetime": datetime, "BeautifulSoup": BeautifulSoup}
    for marca in ("def extraer_datos", "def extraer_listado"):
        exec(next(c.source for c in nb.cells if c.cell_type == "code" and marca in c.source), espacio)
    return espacio


def test_tarjeta_con_descuento(ns):
    (a,) = ns["extraer_listado"](TARJETA, n=3, fecha_extraccion="2026-11-25")
    assert a["id_producto"] == "MCO40287800"
    assert "#" not in a["url"] and a["url"].endswith("/p/MCO40287800")      # sin parámetros de seguimiento
    assert (a["precio_sin_descuento"], a["precio_con_descuento"], a["descuento_total_cop"]) == (6349000, 2879900, 3469100)
    assert a["descuento_pct_sitio"] == 54.0 and a["descuento_pct_calculado"] == 54.64
    assert a["envio"] == "Envío gratis"                                       # etiqueta duplicada colapsada


def test_tarjeta_sin_precio_tachado_es_sin_descuento(ns):
    html = re.sub(r"<s class=.*?</s>", "", TARJETA, flags=re.S).replace(
        '<span class="poly-price__discount-polylabel"><span class="polylabel-pill">54% OFF</span></span>', "")
    (a,) = ns["extraer_listado"](html)
    assert a["precio_sin_descuento"] == a["precio_con_descuento"] == 2879900
    assert a["descuento_total_cop"] == 0 and a["descuento_pct_sitio"] == 0.0


def test_n_limita_la_cantidad(ns):
    assert len(ns["extraer_listado"](TARJETA * 5, n=3)) == 3


@pytest.mark.skipif(not HTML_LISTADO.exists(), reason="no existe data/pagina_listado.html")
def test_listado_real_guardado(ns):
    arts = ns["extraer_listado"](HTML_LISTADO.read_text(encoding="utf-8", errors="ignore"), n=8)
    assert len(arts) == 8
    assert len({a["id_producto"] for a in arts}) == 8                         # artículos independientes
    for a in arts:
        assert a["nombre"] and a["url"].startswith("https://www.mercadolibre.com.co/")
        assert a["precio_con_descuento"] <= a["precio_sin_descuento"]
        assert abs(a["descuento_pct_sitio"] - a["descuento_pct_calculado"]) <= 1.0


@pytest.mark.skipif(not CSV_ARTICULOS.exists(), reason="aún no existe data/articulos.csv")
def test_csv_versionado():
    with open(CSV_ARTICULOS, encoding="utf-8-sig", newline="") as f:
        filas = list(csv.DictReader(f))
    assert 3 <= len(filas) <= 8
    assert {"posicion", "nombre", "id_producto", "precio_sin_descuento", "precio_con_descuento",
            "descuento_pct_sitio", "url", "imagen", "fecha_extraccion", "origen_datos"} <= set(filas[0])


@pytest.mark.skipif(not CSV_ARTICULOS.exists(), reason="aún no existe data/articulos.csv")
def test_construir_sitio(tmp_path):
    sys.path.insert(0, str(RAIZ / "scripts"))
    import construir_sitio
    reporte = tmp_path / "reporte.html"
    reporte.write_text("<html></html>", encoding="utf-8")
    salida = construir_sitio.construir(tmp_path / "_site", reporte)
    for archivo in ("index.html", "styles.css", "app.js", "data/articulos.csv", "reporte/index.html", ".nojekyll"):
        assert (salida / archivo).exists(), archivo
