# Plan TDD - US-001: Parser de Markdown con Embeddings

## Objetivo

Parser de Markdown siguiendo TDD: **Red** → **Green** → **Refactor**. Cada párrafo incluye embedding de Jina AI (768 dims).

## Setup Inicial

```bash
uv venv && .venv\Scripts\activate
uv pip install pydantic pytest pytest-cov pytest-mock requests python-dotenv
```

---

## Casos de Prueba (Diseñados ANTES de implementar)

### Ciclos 1-4: Parser Básico

**Tests**: `test_parse_single_heading_no_content`, `test_parse_single_heading_with_one_paragraph`, `test_parse_section_with_multiple_paragraphs`, `test_parse_multiple_sections_same_level`

**Valida**:
- Headings (`#` a `######`) con niveles 1-6
- Párrafos = bloques separados por línea vacía
- Múltiples secciones del mismo nivel
- Cada `Paragraph` tiene `embedding: list[float]` (768 dims de Jina AI)
- Tracking de `start_line` y `end_line`

---

### Ciclo 3: Múltiples párrafos en una sección

**Test**: `test_parse_section_with_multiple_paragraphs`

**Entrada**:
```markdown
# Capítulo 1

Primer párrafo con varias líneas
que continúan aquí.

Segundo párrafo separado por línea vacía.

Tercer párrafo.
```

**Salida esperada**:
```python
Section(
    paragraphs=[
        Paragraph(
            text="Primer párrafo con varias líneas\nque continúan aquí.",
            index=0,
            line_number=3,
            embedding=[...]  # Embedding del párrafo completo
        ),
        Paragraph(
            text="Segundo párrafo separado por línea vacía.",
            index=1,
            line_number=6,
            embedding=[...]
        ),
        Paragraph(
            text="Tercer párrafo.",
            index=2,
            line_number=8,
            embedding=[...]
        )
    ]
)
```

**Criterios validados**: ✓ Párrafos = bloques separados por línea vacía ✓ Cada párrafo tiene embedding

---

### Ciclo 4: Múltiples secciones de mismo nivel

**Test**: `test_parse_multiple_sections_same_level`

**Entrada**:
```markdown
# Capítulo 1

Contenido del capítulo 1.

# Capítulo 2

Contenido del capítulo 2.
```

**Salida esperada**:
```python
Document(
    sections=[
        Section(level=1, title="Capítulo 1", ...),
        Section(level=1, title="Capítulo 2", ...)
    ]
)
```

**Criterios validados**: ✓ Contenido incluye hasta el siguiente heading del mismo nivel

---

### Ciclo 5: Jerarquía de secciones (subsecciones)

**Test**: `test_parse_nested_sections`

**Entrada**:
```markdown
# Capítulo 1

Introducción al capítulo.

## Sección 1.1

Contenido de la sección 1.1.

## Sección 1.2

Contenido de la sección 1.2.

# Capítulo 2

Nuevo capítulo.
```

**Salida esperada**:
```python
Document(
    sections=[
        Section(
            level=1,
            title="Capítulo 1",
            paragraphs=[Paragraph(text="Introducción al capítulo.", ...)],
            subsections=[
                Section(level=2, title="Sección 1.1", ...),
                Section(level=2, title="Sección 1.2", ...)
            ]
        ),
        Section(
            level=1,
            title="Capítulo 2",
            paragraphs=[Paragraph(text="Nuevo capítulo.", ...)],
            subsections=[]
        )
    ]
)
```

**Criterios validados**: ✓ Jerarquía correcta ✓ Subsecciones anidadas

---

### Ciclo 6: Todos los niveles de headings

**Test**: `test_parse_all_heading_levels`

**Entrada**:
```markdown
# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6
```

**Salida esperada**:
```python
# Cada heading parseado con su nivel correcto (1-6)
# La jerarquía se respeta
```

**Criterios validados**: ✓ Parsea niveles 1-6 correctamente

---

### Ciclo 7: Headings con caracteres especiales

**Test**: `test_parse_heading_with_special_characters`

**Entrada**:
```markdown
# ¿Qué es la IA?

# Título con "comillas"

# Título con @#$%&*

# Título con émojis 🚀
```

**Salida esperada**:
```python
Section(title="¿Qué es la IA?", ...)
Section(title='Título con "comillas"', ...)
Section(title="Título con @#$%&*", ...)
Section(title="Título con émojis 🚀", ...)
```

**Criterios validados**: ✓ Headings con caracteres especiales

---

### Ciclo 8: Bloques de código NO son headings

**Test**: `test_parse_ignore_headings_in_code_blocks`

**Entrada**:
````markdown
# Capítulo Real

Este es contenido normal.

```python
# Este es un comentario en código
def funcion():
    # Otro comentario
    pass
```

Texto después del código.
````

**Salida esperada**:
```python
Section(
    title="Capítulo Real",
    paragraphs=[
        Paragraph(text="Este es contenido normal.", ...),
        Paragraph(text="```python\n# Este es un comentario...", ...),
        Paragraph(text="Texto después del código.", ...)
    ]
)
# NO debe crear secciones con títulos "Este es un comentario..."
```

**Criterios validados**: ✓ Bloques de código no se parsean como headings

---

### Ciclo 9: Listas con # no son headings

**Test**: `test_parse_lists_starting_with_hash`

**Entrada**:
```markdown
# Capítulo

Lista de items:

1. Item 1
2. Item 2
#3 esto podría confundirse
# Pero esto SÍ es un heading
```

**Salida esperada**:
```python
# Solo "Capítulo" y "Pero esto SÍ es un heading" son Sections
# El "#3" se trata como contenido
```

**Criterios validados**: ✓ Listas con `#` no se parsean como headings

---

### Ciclo 10: document.find_section() - caso exitoso

**Test**: `test_find_section_by_title_success`

**Entrada**:
```python
doc = parse_markdown("# Introducción\n\n# Metodología")
section = doc.find_section("Metodología")
```

**Salida esperada**:
```python
assert section.title == "Metodología"
assert section.level == 1
```

**Criterios validados**: ✓ Referencia por título exacto

---

### Ciclo 11: document.find_section() - caso-sensitive

**Test**: `test_find_section_case_sensitive`

**Entrada**:
```python
doc = parse_markdown("# Metodología")
doc.find_section("metodología")  # minúscula
```

**Salida esperada**:
```python
# Debe lanzar SectionNotFoundError
```

**Criterios validados**: ✓ Case-sensitive

---

### Ciclo 12: document.find_section() - no existe con sugerencias

**Test**: `test_find_section_not_found_with_suggestions`

**Entrada**:
```python
doc = parse_markdown("# Introducción\n\n# Metodología\n\n# Conclusiones")
doc.find_section("Metadología")  # typo
```

**Salida esperada**:
```python
# Lanza SectionNotFoundError con:
# - title="Metadología"
# - available=["Introducción", "Metodología", "Conclusiones"]
```

**Criterios validados**: ✓ Error con sugerencias

---

### Ciclo 13: Sección vacía (solo heading, sin contenido antes del siguiente)

**Test**: `test_parse_empty_section`

**Entrada**:
```markdown
# Sección 1
# Sección 2

Contenido de sección 2.
```

**Salida esperada**:
```python
Section(title="Sección 1", paragraphs=[], ...)
Section(title="Sección 2", paragraphs=[...], ...)
```

---

### Ciclo 14: Document con metadata (path y raw_content)

**Test**: `test_document_preserves_metadata`

**Entrada**:
```python
content = "# Test\n\nContent."
doc = parse_markdown(content)
```

**Salida esperada**:
```python
assert doc.raw_content == content
assert doc.path == Path("test.md")  # si se pasa como argumento
```

---

### Ciclo 15: Section.content reconstruye desde paragraphs

**Test**: `test_section_content_property`

**Entrada**:
```python
section = Section(
    paragraphs=[
        Paragraph(text="Para 1", ...),
        Paragraph(text="Para 2", ...)
    ]
)
```

**Salida esperada**:
```python
assert section.content == "Para 1\n\nPara 2"
```

**Criterios validados**: ✓ Property reconstructor

---

### Ciclo 16: Embeddings con Jina AI

**Test**: `test_paragraph_embeddings_generation`

**Entrada**:
```python
# Mock de la API de Jina AI
paragraph_text = "Este es un párrafo de ejemplo."
```

**Salida esperada**:
```python
# POST a https://api.jina.ai/v1/embeddings
# Headers: {
#     "Content-Type": "application/json",
#     "Authorization": "Bearer jina_api_key"
# }
# Body: {
#     "model": "jina-embeddings-v3",
#     "task": "text-matching",
#     "dimensions": 768,
#     "input": ["Este es un párrafo de ejemplo."]
# }

# Respuesta:
{
    "data": [
        {
            "embedding": [0.123, -0.456, 0.789, ...],  # 768 dimensiones
            "index": 0
        }
    ]
}

# Paragraph debe tener:
Paragraph(
    text="Este es un párrafo de ejemplo.",
    embedding=[0.123, -0.456, 0.789, ...]  # Lista de 768 floats
)
```

**Criterios validados**: ✓ Llamada HTTP a Jina AI ✓ Embedding de 768 dims ✓ Manejo de errores

---

### Ciclo 17: Embeddings en batch para eficiencia

**Test**: `test_batch_embeddings_generation`

**Entrada**:
```python
paragraphs = [
    "Primer párrafo.",
    "Segundo párrafo.",
    "Tercer párrafo."
]
```

**Salida esperada**:
```python
# Una sola llamada a la API con múltiples textos
# Body: {
#     "input": [
#         "Primer párrafo.",
#         "Segundo párrafo.",
#         "Tercer párrafo."
#     ]
# }

# Respuesta con 3 embeddings:
{
    "data": [
        {"embedding": [...], "index": 0},
        {"embedding": [...], "index": 1},
        {"embedding": [...], "index": 2}
    ]
}
```

**Criterios validados**: ✓ Batch processing ✓ Eficiencia (1 llamada en lugar de N)

---

### Ciclo 18: Manejo de errores de API

**Test**: `test_embedding_api_error_handling`

**Escenarios**:
- API key inválida → Error claro con mensaje
- Timeout → Retry con exponential backoff
- Rate limit → Esperar y reintentar
- Texto vacío → Devolver embedding nulo o default

**Salida esperada**:
```python
# Para texto vacío:
Paragraph(text="", embedding=None)

# Para error de API:
raise EmbeddingAPIError("Jina AI API error: 401 Unauthorized")
```

**Criterios validados**: ✓ Error handling robusto ✓ Mensajes claros

---

## Orden de Implementación TDD

### Sprint 1: Fundamentos (Ciclos 1-4)
1. ✅ Modelo Pydantic básico (Document, Section, Paragraph)
2. ✅ Parser para heading único sin contenido
3. ✅ Parser para heading con un párrafo
4. ✅ Parser para múltiples párrafos
5. ✅ Parser para múltiples secciones mismo nivel

**Entregable**: Parser básico funcional para documentos planos

---

### Sprint 2: Jerarquía (Ciclos 5-6)
6. ✅ Parsing de subsecciones (jerarquía)
7. ✅ Todos los niveles de headings (1-6)

**Entregable**: Parser maneja estructuras jerárquicas

---

### Sprint 3: Casos Edge (Ciclos 7-9)
8. ✅ Caracteres especiales en headings
9. ✅ Ignorar `#` dentro de bloques de código
10. ✅ Distinguir listas de headings reales

**Entregable**: Parser robusto ante casos edge

---

### Sprint 4: API de búsqueda (Ciclos 10-12)
11. ✅ `document.find_section()` exitoso
12. ✅ Validación case-sensitive
13. ✅ Excepciones con sugerencias

**Entregable**: API de navegación completa

---

### Sprint 5: Refinamiento (Ciclos 13-15)
14. ✅ Secciones vacías
15. ✅ Metadata del documento
16. ✅ Property `section.content`

**Entregable**: Parser completo y pulido

---

### Sprint 6: Embeddings con Jina AI (Ciclos 16-18)
17. ✅ Generación de embeddings individuales
18. ✅ Batch processing de embeddings
19. ✅ Manejo de errores de API

**Entregable**: US-001 completa con embeddings integrados

---

## Estructura de Archivos

```
doc_handler/
├── doc_handler/            # Código fuente
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic models (Paso 1)
│   │   ├── parser.py           # parse_markdown() (Paso 2+)
│   │   └── exceptions.py       # SectionNotFoundError + EmbeddingAPIError
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   └── embeddings.py       # Cliente Jina AI (requests)
│   └── cli/
│       └── __init__.py
│
├── tests/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── test_models.py       # Tests de Pydantic models
│   │   └── test_parser.py       # Tests del parser (15 tests)
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   └── test_embeddings.py   # Tests de embeddings (3 tests)
│   └── fixtures/
│       ├── __init__.py
│       └── markdown_samples.py  # Ejemplos reusables
│
├── pyproject.toml          # Configuración del proyecto
├── requirements.txt        # Dependencias (opcional con uv)
└── .env.example            # Template para JINA_API_KEY
```

---

## Configuración pyproject.toml

```toml
[project]
name = "doc-handler"
version = "0.1.0"
description = "Editor Markdown con IA"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0",
    "click>=8.0",
    "rich>=13.0",
    "requests>=2.31.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "pytest-mock>=3.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["doc_handler"]
addopts = "-v --cov=doc_handler --cov-report=term-missing"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Comandos de Testing con uv

```bash
# Correr todos los tests
uv run pytest

# Correr solo tests del parser
uv run pytest tests/domain/test_parser.py

# Correr un test específico
uv run pytest tests/domain/test_parser.py::test_parse_single_heading_no_content

# Con coverage detallado
uv run pytest --cov=doc_handler --cov-report=term-missing

# Modo verbose
uv run pytest -vv

# Ver print statements
uv run pytest -s

# Parar en el primer fallo
uv run pytest -x
```

---

## Checklist de Implementación

### Paso 1: Setup inicial
- [ ] `uv venv` - Crear ambiente virtual
- [ ] Activar ambiente
- [ ] `uv pip install pydantic pytest pytest-cov pytest-mock requests python-dotenv`
- [ ] Crear `pyproject.toml`
- [ ] Crear estructura de carpetas
- [ ] Crear todos los `__init__.py`
- [ ] Crear `.env.example` con `JINA_API_KEY=your_key_here`

### Paso 2: Modelos (sin lógica)
- [ ] Definir `Paragraph` con campo `embedding: list[float] | None` en `doc_handler/domain/models.py`
- [ ] Definir `Section` en `doc_handler/domain/models.py`
- [ ] Definir `Document` en `doc_handler/domain/models.py`
- [ ] Test: validar que Pydantic funciona (`test_models.py`)
- [ ] `uv run pytest tests/domain/test_models.py`

### Paso 3-7: Parser básico (Ciclos 1-4)
- [ ] Test `test_parse_single_heading_no_content` (ROJO)
- [ ] Implementar parsing de heading único (VERDE)
- [ ] Test `test_parse_single_heading_with_one_paragraph` (ROJO)
- [ ] Implementar parsing de contenido (VERDE)
- [ ] Test `test_parse_section_with_multiple_paragraphs` (ROJO)
- [ ] Implementar separación de párrafos (VERDE)
- [ ] Test `test_parse_multiple_sections_same_level` (ROJO)
- [ ] Implementar múltiples secciones (VERDE)
- [ ] Refactor: extraer funciones auxiliares si es necesario
- [ ] `uv run pytest tests/domain/test_parser.py -v`

### Paso 8-9: Jerarquía (Ciclos 5-6)
- [ ] Test `test_parse_nested_sections` (ROJO)
- [ ] Implementar construcción de árbol jerárquico (VERDE)
- [ ] Test `test_parse_all_heading_levels` (ROJO)
- [ ] Validar niveles 1-6 (VERDE)
- [ ] Refactor: simplificar lógica de jerarquía
- [ ] `uv run pytest tests/domain/test_parser.py -v`

### Paso 10-12: Casos Edge (Ciclos 7-9)
- [ ] Test `test_parse_heading_with_special_characters` (ROJO)
- [ ] Asegurar parsing de caracteres especiales (VERDE)
- [ ] Test `test_parse_ignore_headings_in_code_blocks` (ROJO)
- [ ] Implementar detección de bloques de código (VERDE)
- [ ] Test `test_parse_lists_starting_with_hash` (ROJO)
- [ ] Implementar regex robusto para headings (VERDE)
- [ ] Refactor: mejorar regex y lógica de estado
- [ ] `uv run pytest tests/domain/test_parser.py -v`

### Paso 13-15: API de búsqueda (Ciclos 10-12)
- [ ] Definir `SectionNotFoundError` en `doc_handler/domain/exceptions.py`
- [ ] Test `test_find_section_by_title_success` (ROJO)
- [ ] Implementar `document.find_section()` (VERDE)
- [ ] Test `test_find_section_case_sensitive` (ROJO)
- [ ] Validar case-sensitivity (VERDE)
- [ ] Test `test_find_section_not_found_with_suggestions` (ROJO)
- [ ] Implementar sugerencias (VERDE - algoritmo simple de match)
- [ ] Refactor: extraer lógica de sugerencias
- [ ] `uv run pytest tests/domain/ -v`

### Paso 16-18: Refinamiento (Ciclos 13-15)
- [ ] Test `test_parse_empty_section` (ROJO)
- [ ] Manejar secciones vacías (VERDE)
- [ ] Test `test_document_preserves_metadata` (ROJO)
- [ ] Guardar path y raw_content (VERDE)
- [ ] Test `test_section_content_property` (ROJO)
- [ ] Implementar property `content` (VERDE)
- [ ] Refactor: limpieza y documentación
- [ ] `uv run pytest tests/domain/ -v`

### Paso 19-21: Embeddings con Jina AI (Ciclos 16-18)
- [ ] Definir `EmbeddingAPIError` en `doc_handler/domain/exceptions.py`
- [ ] Crear `doc_handler/infrastructure/embeddings.py`
- [ ] Test `test_paragraph_embeddings_generation` (ROJO)
- [ ] Implementar `generate_embedding(text: str) -> list[float]` con requests (VERDE)
- [ ] Test `test_batch_embeddings_generation` (ROJO)
- [ ] Implementar `generate_embeddings_batch(texts: list[str]) -> list[list[float]]` (VERDE)
- [ ] Test `test_embedding_api_error_handling` (ROJO)
- [ ] Implementar manejo de errores (API key, timeout, rate limit) (VERDE)
- [ ] Integrar embeddings en `parse_markdown()` - generar embeddings para cada párrafo
- [ ] Refactor: extraer configuración (API key, modelo, dimensiones) a variables
- [ ] `uv run pytest tests/infrastructure/test_embeddings.py -v`
- [ ] `uv run pytest --cov=doc_handler --cov-report=term-missing`

### Paso 22: Documentación
- [ ] Docstrings en `parse_markdown()`
- [ ] Docstrings en modelos Pydantic
- [ ] Docstrings en funciones de embeddings
- [ ] Comentarios en lógica compleja (jerarquía, código blocks, batch processing)
- [ ] README con instrucciones para configurar JINA_API_KEY

---

## Criterio de Éxito

✅ **18 tests pasando** (15 del parser + 3 de embeddings)
✅ **Coverage ≥90%** en:
  - `doc_handler/domain/parser.py`
  - `doc_handler/domain/models.py`
  - `doc_handler/infrastructure/embeddings.py`
✅ **Embeddings funcionando**: Cada párrafo tiene su vector de 768 dimensiones
✅ **Docstrings completos** en funciones públicas
✅ **US-001 marcada como Done** en USER_STORIES.md

---

## Próximos Pasos (después de US-001)

- US-002: Analyzer con LLM
- Integración CLI con Click + Rich
- Integración end-to-end
