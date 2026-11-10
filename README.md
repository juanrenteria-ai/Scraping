# Scraping ético de precios en MercadoLibre Colombia

Proyecto de la asignatura *Programación para Análisis de Datos* (IU Digital). Extrae de forma ética los datos de **un solo artículo**
(Apple iPhone 17 Pro Max 256 GB, plata) y los valida con métricas objetivas. El código vive en un Jupyter Notebook versionado con Git
y ejecutado automáticamente con GitHub Actions.

## Estructura

```
.
├── scraping_mercadolibre.ipynb     # Notebook (Selenium + BeautifulSoup)
├── data/pagina_articulo.html       # HTML renderizado guardado del navegador (27/10/2026)
├── tests/test_extraccion.py        # Pruebas automatizadas (pytest)
├── requirements.txt                # Dependencias
└── .github/workflows/ci-cd.yml     # Pipeline CI/CD
```

## Modos de ejecución del notebook

| `SCRAPING_MODO` | Qué hace |
|---|---|
| `en_vivo` (por defecto) | Consulta `robots.txt`, abre la ficha **una vez** con Chrome headless y la analiza. Si el sitio bloquea el acceso, usa `data/pagina_articulo.html`. |
| `offline` | No hace ninguna petición: analiza solo `data/pagina_articulo.html`. |

## Pipeline (GitHub Actions)

| Evento | Qué ocurre |
|---|---|
| *Pull request* a `main` | Pruebas + ejecución del notebook en modo `offline` |
| *Push* / merge a `main` | Pruebas + ejecución `offline` + **despliegue** del reporte en GitHub Pages |
| Programado (día 1 de cada mes) o manual (*Run workflow*) | Pruebas + ejecución `en_vivo` + despliegue |

Jobs: `test` → `run-notebook` → `deploy`. El notebook ejecutado y el CSV quedan como artefactos de cada ejecución; el reporte HTML se publica en GitHub Pages.

## Uso local

```bash
pip install -r requirements.txt
pytest -v
SCRAPING_MODO=offline jupyter nbconvert --to notebook --execute scraping_mercadolibre.ipynb --output-dir executed
```

En Windows (PowerShell): `$env:SCRAPING_MODO="offline"` antes de `jupyter nbconvert ...`.

## Ética

Una URL, una carga por ejecución, pausa de 3 s, *User-Agent* que declara el uso educativo, consulta previa de `robots.txt`,
sin evadir captchas ni inicios de sesión y uso exclusivamente académico de datos públicos.
