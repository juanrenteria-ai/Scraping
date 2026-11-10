"""Pruebas automatizadas del notebook de scraping.

Se extrae del propio notebook el código de `a_entero` y `extraer_datos` para probarlo
sin necesidad de red ni de navegador (misma lógica que ejecuta el pipeline).
"""
import re
from datetime import datetime
from pathlib import Path

import nbformat
import pytest
from bs4 import BeautifulSoup

RAIZ = Path(__file__).resolve().parent.parent
NOTEBOOK = RAIZ / "scraping_mercadolibre.ipynb"
HTML_REAL = RAIZ / "data" / "pagina_articulo.html"

URL = "https://www.mercadolibre.com.co/apple-iphone-17-pro-max-256-gb-color-plata/p/MCO55308605"
NOMBRE = "Apple iPhone 17 Pro Max (256 GB) - Color plata"

HTML_MUESTRA = """
<html><head><link rel="canonical" href="@@URL@@"/></head><body>
<h1 class="ui-pdp-title">@@NOMBRE@@</h1>
<div class="ui-pdp-price"><div class="ui-pdp-price__main-container">
  <s class="andes-money-amount andes-money-amount--previous" aria-label="Antes: 6999000 pesos">
    <span class="andes-money-amount__fraction">6.999.000</span></s>
  <div class="ui-pdp-price__second-line">
    <span class="andes-money-amount" aria-label="4409900 pesos"><meta itemprop="price" content="4409900"/>
      <span class="andes-money-amount__fraction">4.409.900</span></span>
    <span class="andes-money-amount__discount">36% OFF</span>
  </div></div></div></body></html>
""".replace("@@URL@@", URL).replace("@@NOMBRE@@", NOMBRE)


@pytest.fixture(scope="module")
def notebook():
    return nbformat.read(NOTEBOOK, as_version=4)


@pytest.fixture(scope="module")
def ns(notebook):
    """Ejecuta la celda que define el analizador y devuelve su espacio de nombres."""
    celda = next(c.source for c in notebook.cells
                 if c.cell_type == "code" and "def extraer_datos" in c.source)
    espacio = {"re": re, "datetime": datetime, "BeautifulSoup": BeautifulSoup}
    exec(celda, espacio)
    return espacio


def test_notebook_es_valido(notebook):
    nbformat.validate(notebook)


def test_notebook_sin_dependencias_colab_obligatorias(notebook):
    """Las importaciones de google.colab solo pueden ocurrir dentro de un bloque condicional."""
    for c in notebook.cells:
        if c.cell_type != "code":
            continue
        for linea in c.source.splitlines():
            if "from google.colab import" in linea:
                assert linea.startswith((" ", "\t")), f"Import de Colab sin proteger: {linea}"


def test_a_entero(ns):
    assert ns["a_entero"]("6.999.000") == 6999000
    assert ns["a_entero"]("Antes: 6999000 pesos") == 6999000
    assert ns["a_entero"](None) is None


def test_extraer_datos_html_muestra(ns):
    d = ns["extraer_datos"](HTML_MUESTRA, URL)
    assert d["nombre"] == NOMBRE
    assert d["precio_sin_descuento"] == 6999000
    assert d["precio_con_descuento"] == 4409900
    assert d["descuento_total_cop"] == 2589100
    assert d["descuento_pct_sitio"] == 36.0
    assert d["url"] == URL


def test_extraer_datos_sin_descuento(ns):
    html = HTML_MUESTRA.replace('<s class="andes-money-amount andes-money-amount--previous"'
                                ' aria-label="Antes: 6999000 pesos">', "<s hidden>")
    d = ns["extraer_datos"](html, URL)
    assert d["descuento_total_cop"] == 0 or d["precio_sin_descuento"] == d["precio_con_descuento"]


@pytest.mark.skipif(not HTML_REAL.exists(), reason="no existe la captura data/pagina_articulo.html")
def test_extraer_datos_captura_real(ns):
    """El HTML real guardado del navegador debe cumplir las métricas de éxito del informe."""
    d = ns["extraer_datos"](HTML_REAL.read_text(encoding="utf-8", errors="ignore"), URL)
    assert d["nombre"] == NOMBRE
    assert "MCO55308605" in d["url"]
    assert d["precio_con_descuento"] <= d["precio_sin_descuento"]
    assert abs(d["descuento_pct_sitio"] - d["descuento_pct_calculado"]) <= 1.0
