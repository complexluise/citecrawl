#%% 1. Imports y configuración
import os
from pathlib import Path

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

# Agregar el path del proyecto para imports locales
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from doc_handler.domain.parser import parse_markdown

load_dotenv()

#%% 2. Configurar LLM
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

#%% 3. Función para generar descripción de imagen

def get_image_description(section_title: str, section_content: str) -> str:
    """Genera una descripción visual para ilustrar un capítulo."""

    prompt = f"""Eres un diseñador visual especializado en contenido técnico sobre inteligencia artificial.

A partir del siguiente capítulo de una guía técnica de IA, genera una descripción detallada para crear una imagen ilustrativa.

La descripción debe incluir:
- Concepto visual central que represente la idea principal del capítulo
- Elementos concretos a incluir (objetos, iconografía, diagramas simplificados)
- Composición sugerida (qué va en primer plano, fondo, disposición)
- Paleta de colores recomendada
- Estilo visual (flat design, isométrico, minimalista, tech-futurista, etc.)

Criterios:
- Debe ser comprensible sin leer el capítulo
- Evitar representaciones demasiado abstractas o genéricas
- Preferir metáforas visuales claras sobre literalidad técnica
- Mantener coherencia con una guía profesional pero accesible

Capítulo: {section_title}
---
{section_content}
---

Genera únicamente la descripción de la imagen, lista para usar como prompt en un modelo de generación de imágenes."""

    response = model.generate_content(prompt)
    return response.text.strip()

#%% 4. Cargar documento
ARCHIVO_MD = Path("guia.md")  # <- Cambia esto

content = ARCHIVO_MD.read_text(encoding="utf-8")
doc = parse_markdown(content, path=ARCHIVO_MD)

# Mostrar secciones disponibles (nivel 1)
print("Secciones nivel 1 encontradas:")
for s in doc.sections:
    print(f"  - {s.title}")

#%% 5. Procesar secciones nivel 1
resultados = []

for section in doc.sections:
    print(f"Procesando: {section.title}...")

    contenido = section.content

    if not contenido.strip():
        print(f"  (sin contenido, saltando)")
        continue

    descripcion = get_image_description(section.title, contenido)
    resultados.append({
        "seccion": section.title,
        "descripcion_imagen": descripcion
    })
    print(f"  ✓ completado")

print(f"\nTotal procesadas: {len(resultados)}")

#%% 6. Guardar CSV
df = pd.DataFrame(resultados)

OUTPUT_CSV = Path("descripciones_imagenes.csv")  # <- Cambia si quieres
df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

print(f"Guardado en: {OUTPUT_CSV}")