# Scraping ético de precios en MercadoLibre Colombia

Proyecto de la asignatura *Programación para Análisis de Datos* (Institución Universitaria Digital de Antioquia).
Extrae de forma ética datos de **MercadoLibre Colombia**: un artículo piloto (Apple iPhone 17 Pro Max 256 GB, plata)
y los primeros **8 artículos del listado de búsqueda «iphone»**. Los resultados se guardan en un CSV y se muestran en un
**sitio web** publicado automáticamente con **GitHub Actions** y **GitHub Pages**.

- Sitio desplegado: <https://juanrenteria-ai.github.io/Scraping/>
- Reporte del notebook ejecutado: <https://juanrenteria-ai.github.io/Scraping/reporte/>

## Contenido

1. [Introducción](#introducción)
2. [Estructura del proyecto](#estructura-del-proyecto)
3. [Instalación](#instalación)
4. [Uso](#uso)
5. [Automatización (GitHub Actions)](#automatización-github-actions)
6. [Despliegue (GitHub Pages)](#despliegue-github-pages)
7. [Sitio web](#sitio-web)
8. [Pruebas](#pruebas)
9. [Ética y limitaciones](#ética-y-limitaciones)

## Introducción

El proyecto combina dos técnicas: **Selenium** (controla Chrome sin interfaz para obtener la página ya renderizada) y
**BeautifulSoup** (extrae los datos con selectores CSS). Como MercadoLibre puede mostrar una pantalla de verificación a las
peticiones que llegan desde servidores en la nube, el cuaderno tiene un **plan alternativo**: analizar el HTML renderizado que
la persona guardó desde su navegador (`data/`). El origen de cada dato queda registrado en la columna `origen_datos`.

Datos que se obtienen:

| Origen | Datos | Salida |
|---|---|---|
| Ficha del artículo piloto | nombre, precio sin descuento, precio con descuento, descuento (COP y %), URL | `precios_iphone_17_pro_max.csv` (histórico, solo con datos en vivo) |
| Listado «iphone» (8 artículos) | posición, nombre, id, precios, descuento (sitio y calculado), vendedor, cuotas, envío, URL, imagen | `data/articulos.csv` |

## Estructura del proyecto

```
.
├── scraping_mercadolibre.ipynb      # Notebook: scraping, validación y CSV (Selenium + BeautifulSoup)
├── data/
│   ├── pagina_articulo.html         # HTML renderizado de la ficha del artículo piloto (27/10/2026)
│   ├── pagina_listado.html          # HTML renderizado del listado «iphone» (25/11/2026)
│   └── articulos.csv                # Artículos del listado extraídos por el notebook (alimenta el sitio)
├── sitio/                           # Sitio web estático
│   ├── index.html                   #   estructura
│   ├── styles.css                   #   estilos
│   └── app.js                       #   lee data/articulos.csv y pinta tarjetas, resumen y tabla
├── scripts/construir_sitio.py       # Ensambla la carpeta _site/ que se publica en Pages
├── tests/                           # Pruebas automatizadas (pytest)
│   ├── test_extraccion.py           #   ficha del artículo piloto
│   └── test_listado.py              #   listado, CSV y construcción del sitio
├── requirements.txt                 # Dependencias
└── .github/workflows/ci-cd.yml      # Pipeline CI/CD
```

## Instalación

Requisitos: Python 3.11+, Git y (solo para el modo en vivo) Google Chrome.

```bash
git clone https://github.com/juanrenteria-ai/Scraping.git
cd Scraping
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

En **Google Colab** no hace falta instalar nada a mano: la celda 1 del notebook instala Chrome y las librerías cuando detecta Colab.

## Uso

**Variable de entorno `SCRAPING_MODO`**

| Valor | Comportamiento |
|---|---|
| `en_vivo` (por defecto) | Consulta `robots.txt`, abre la ficha una vez con Chrome headless y, si no hubo bloqueo, el listado una vez. Si el sitio bloquea, usa los HTML guardados en `data/`. |
| `offline` | No hace ninguna petición: analiza solo los HTML guardados en `data/`. |

Ejecutar el notebook sin interfaz (equivale a lo que hace el pipeline):

```bash
# Linux / macOS
SCRAPING_MODO=offline jupyter nbconvert --to notebook --execute scraping_mercadolibre.ipynb \
  --output-dir executed --output scraping_mercadolibre_ejecutado.ipynb
# Windows (PowerShell): $env:SCRAPING_MODO="offline"  antes de ejecutar el comando anterior
```

Esto regenera `data/articulos.csv`. Para ver el sitio localmente:

```bash
python scripts/construir_sitio.py            # crea _site/
python -m http.server 8000 --directory _site # abrir http://localhost:8000
```

**Actualizar los datos del listado a mano** (cuando el sitio bloquea el acceso automatizado):

1. Abre `https://listado.mercadolibre.com.co/iphone` en tu navegador y espera a que carguen los resultados.
2. F12 → pestaña *Elements* → clic derecho sobre `<html>` → *Copy → Copy outerHTML*.
3. Pega el contenido en `data/pagina_listado.html` y actualiza `FECHA_CAPTURA_HTML` en el notebook.
4. Ejecuta el notebook en modo `offline` y haz commit de `data/pagina_listado.html` y `data/articulos.csv`.

## Automatización (GitHub Actions)

El flujo está en `.github/workflows/ci-cd.yml` y tiene tres trabajos encadenados (`test` → `run-notebook` → `deploy`).

**Eventos que lo disparan**

| Evento | Qué ocurre |
|---|---|
| *Pull request* a `main` | Pruebas + ejecución del notebook en `offline`. No despliega. |
| *Push* / merge a `main` | Pruebas + ejecución en `offline` + despliegue en GitHub Pages. |
| Programado (`cron: "0 13 1 * *"`, día 1 de cada mes, 8:00 a. m. en Colombia) o manual (*Run workflow*) | Pruebas + ejecución en `en_vivo` + despliegue. |

**Configuración global**

- `permissions: contents: read`: el token solo puede leer el repositorio (mínimo privilegio).
- `concurrency`: si llega una ejecución nueva sobre la misma rama, cancela la anterior.
- `SCRAPING_MODO` (variable de entorno del trabajo `run-notebook`): vale `en_vivo` si el evento es `schedule` o `workflow_dispatch`, y `offline` en los demás casos, de modo que los cambios de código no generan tráfico hacia MercadoLibre.

**Pasos de cada trabajo**

| Trabajo | Paso | Comando / acción | Para qué |
|---|---|---|---|
| `test` | Checkout | `actions/checkout` | Descarga el código |
| | Python 3.11 con caché | `actions/setup-python` | Entorno reproducible |
| | Dependencias | `pip install -r requirements.txt` | Instala librerías |
| | Pruebas | `pytest -v` | Valida el analizador, el CSV y la construcción del sitio, sin red |
| `run-notebook` | Dependencias y Chrome | `pip install …`, `google-chrome --version` | El runner ya trae Chrome |
| | Ejecutar notebook | `jupyter nbconvert --to notebook --execute …` | Corre todas las celdas y guarda el resultado en `executed/` |
| | Convertir a HTML | `jupyter nbconvert --to html …` | Genera el reporte legible |
| | Construir sitio | `python scripts/construir_sitio.py --reporte executed/reporte.html --salida _site` | Une sitio + CSV + reporte |
| | Artefactos | `actions/upload-artifact` | Guarda `executed/` y `data/articulos.csv` |
| | Preparar Pages | `actions/upload-pages-artifact` (solo si no es PR) | Empaqueta `_site/` |
| `deploy` | Desplegar | `actions/deploy-pages` (solo desde `main`) | Publica en GitHub Pages |

## Despliegue (GitHub Pages)

1. En el repositorio: **Settings → Pages → Build and deployment → Source: GitHub Actions**. Es un ajuste del repositorio que el workflow no puede activar por sí solo; sin él, el despliegue falla con el error 404 *“Ensure GitHub Pages has been enabled”*.
2. El trabajo `deploy` declara `permissions: pages: write` e `id-token: write` y el entorno `github-pages`, que GitHub crea automáticamente.
3. No se necesitan secretos ni variables adicionales: el token de Actions (`GITHUB_TOKEN`) basta. La única variable de entorno del proyecto es `SCRAPING_MODO`.
4. Tras un *push* a `main` (o *Run workflow*), el sitio queda en <https://juanrenteria-ai.github.io/Scraping/> y la URL aparece en el resumen de la ejecución.

## Sitio web

Sitio estático (sin dependencias ni compilación) que carga `data/articulos.csv` con `fetch`:

- Tarjetas por artículo con imagen, precio, descuento, cuotas, envío y enlace a la publicación.
- Resumen (cantidad, artículos con descuento, mayor descuento, promedio y precio más bajo).
- Búsqueda por texto, orden (posición, precio, descuento) y filtro «solo con descuento».
- Tabla con todos los datos y enlace de descarga del CSV.

## Pruebas

```bash
pytest -v
```

Validan el analizador de la ficha y del listado (con HTML de muestra y con las capturas reales), el CSV versionado y el
ensamblado del sitio. Se ejecutan en cada *pull request* y *push*.

## Ética y limitaciones

- Se consulta `robots.txt`; una ejecución en vivo hace como máximo **dos** cargas de página (ficha y listado), con pausa de 3 s y un *User-Agent* que declara el uso educativo.
- No se evaden captchas, inicios de sesión ni verificaciones. Si el sitio bloquea, se usa el HTML guardado.
- Los datos son públicos y de uso exclusivamente académico. Los precios varían con el tiempo, el vendedor y la ubicación.
- Los selectores CSS dependen del diseño actual de MercadoLibre; si cambia, hay que actualizarlos (las pruebas ayudan a distinguir un error de código de un cambio del sitio).
- Las imágenes del sitio se cargan desde los servidores de MercadoLibre y pertenecen a sus titulares.
