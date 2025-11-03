# Pipeline de IA: De Contenido Web a Citas Bibliográficas

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Coverage Status](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://shields.io/)
[![Built with Click](https://img.shields.io/badge/Built%20with-Click-brightgreen)](https://click.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Una herramienta de línea de comandos con IA para automatizar la recolección, análisis y citación de fuentes web. Este pipeline simplifica tu flujo de investigación al extraer el contenido de páginas web, generar resúmenes basados en tus preguntas y crear un archivo de bibliografía BibTeX listo para usar.

## El Problema

Si eres investigador, estudiante o profesional, sabes que guardar contenido web, leerlo para encontrar información clave y dar formato a las citas es un proceso lento y repetitivo. Esta herramienta elimina ese trabajo manual para que puedas concentrarte en lo que de verdad importa: analizar y escribir.

## Características Principales

-   **Extracción Automática**: Dale un archivo CSV con URLs y la herramienta guardará el contenido principal de cada página en archivos Markdown limpios.
-   **Análisis con IA**: Haz una pregunta específica para cada URL y la IA leerá el contenido para generar un resumen preciso que responda a tu pregunta.
-   **Datos Bibliográficos Automáticos**: La IA extrae automáticamente la información clave para las citas (título, autor, año), ahorrándote el trabajo de buscarla.
-   **Citas en Formato BibTeX**: Genera un archivo `bibliography.bib` estándar, compatible con cualquier gestor de referencias como Zotero o Mendeley.
-   **Integración con Google Docs**: (Opcional) Actualiza las citas en tu manuscrito de Google Docs con un solo comando.

## Cómo Empezar

Sigue estos pasos para tener el proyecto funcionando en tu computadora.

### Requisitos

-   Python 3.6 o superior.
-   [uv](https://github.com/astral-sh/uv) (un instalador de paquetes de Python muy rápido).

### Instalación

1.  **Clona el repositorio:**
    ```bash
    git clone https://github.com/tu-usuario/CiteCrawl.git
    cd CiteCrawl
    ```

2.  **Crea y activa un entorno virtual:**
    ```bash
    uv venv
    source .venv/bin/activate  # En Windows, usa: .venv\Scripts\activate
    ```

3.  **Instala las dependencias:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Configura tus claves de API:**
    Crea un archivo llamado `.env` en la raíz del proyecto. Necesitarás claves de API de [Firecrawl](https://www.firecrawl.dev/) (para la extracción) y [Google AI Studio](https://aistudio.google.com/) (para el análisis con IA).

    ```
    # .env
    FIRECRAWL_API_KEY="tu_clave_de_firecrawl"
    GEMINI_API_KEY="tu_clave_de_gemini"
    ```

## Modo de Uso

La herramienta funciona con dos comandos principales: `extract` y `cite`.

### Paso 1: Extraer y Enriquecer Contenido

Este comando lee tu archivo CSV de URLs, extrae el contenido de cada página, lo enriquece con la IA y lo guarda en archivos Markdown dentro de la carpeta `output/`.

-   **Entrada**: Un archivo CSV con una columna `Enlace/URL`.

    *Ejemplo `input.csv`:*
    ```csv
    ID,Título,Autor(es),Año de Publicación,Tipo de Recurso,Enlace/URL,Resumen Principal,Aspectos Más Relevantes (Relacionado con Bibliotecas),Comentarios / Ideas para la Guía,Extracted
    1,"","","",,"https://ejemplo.com/articulo1","","","","",FALSE
    2,"","","",,"https://ejemplo.org/articulo2","","","","",FALSE
    ```

-   **Comando:**
    ```bash
    uv run python -m citecrawl extract ruta/a/tu/input.csv
    ```
    *Puedes usar la opción `--output` para elegir otra carpeta de destino.*

### Paso 2: Generar Citas

Este comando crea el archivo `bibliography.bib` con toda tu bibliografía. Si quieres, también puede actualizar un documento de Google Docs.

-   **Comando:**
    ```bash
    # Para generar solo el archivo local bibliography.bib
    uv run python -m citecrawl cite ruta/a/tu/input.csv

    # Para también actualizar un Google Doc
    uv run python -m citecrawl cite ruta/a/tu/input.csv --doc-id "el_id_de_tu_documento"
    ```

## Desarrollo

Para ejecutar las pruebas del proyecto, usa el siguiente comando:

```bash
uv run pytest
```

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE.md` para más detalles.