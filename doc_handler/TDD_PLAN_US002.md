# Plan TDD - US-002: Detección de Redundancias con Embeddings

## Objetivo

Implementar análisis de redundancias siguiendo TDD: **Red** → **Green** → **Refactor**.

Usa **similaridad coseno de embeddings** (ya calculados en US-001) para detectar párrafos redundantes en:
- **US-002A**: Una sección específica (análisis acotado, puede incluir contexto LLM)
- **US-002B**: Documento completo (solo embeddings, optimizado)

---

## Setup Inicial

```bash
# Dependencias ya instaladas en US-001:
# - pydantic, pytest, pytest-cov, pytest-mock, requests, python-dotenv

# Nuevas dependencias para US-002:
uv pip install numpy  # Para cálculos de similaridad coseno
```

---

## Arquitectura de la Solución

### Separación de responsabilidades

```
doc_handler/
├── domain/
│   ├── analyzer.py          # Protocol: RedundancyAnalyzer (interfaz)
│   └── models.py            # Nuevo: Redundancy, RedundancyReport
│
├── infrastructure/
│   ├── embedding_analyzer.py    # Implementación con embeddings
│   └── llm_analyzer.py          # (Opcional) Implementación con LLM
│
└── cli/
    └── commands.py              # check-redundancy-section, check-redundancy
```

### Diseño de modelos (Pydantic)

```python
# doc_handler/domain/models.py (añadir)

class Redundancy(BaseModel):
    """Representa un par de párrafos redundantes."""
    paragraph1: Paragraph
    paragraph2: Paragraph
    similarity_score: float  # 0.0 - 1.0 (cosine similarity)

    @property
    def similarity_percentage(self) -> int:
        """Retorna similaridad como porcentaje (70-100)."""
        return int(self.similarity_score * 100)

class RedundancyReport(BaseModel):
    """Reporte de análisis de redundancias."""
    section_title: str | None  # None para análisis global
    total_paragraphs: int
    redundancies: list[Redundancy]
    threshold: float = 0.7  # Threshold de similaridad

    @property
    def has_redundancies(self) -> bool:
        return len(self.redundancies) > 0

    @property
    def redundancy_count(self) -> int:
        return len(self.redundancies)
```

### Protocol para analyzer (domain/analyzer.py)

```python
from typing import Protocol

class RedundancyAnalyzer(Protocol):
    """Protocol for redundancy detection strategies."""

    def analyze_section(
        self,
        section: Section,
        threshold: float = 0.7
    ) -> RedundancyReport:
        """Analiza redundancias en una sección específica."""
        ...

    def analyze_document(
        self,
        document: Document,
        threshold: float = 0.7
    ) -> RedundancyReport:
        """Analiza redundancias en todo el documento."""
        ...
```

---

## Casos de Prueba (Diseñados ANTES de implementar)

### Sprint 1: Modelos y Cálculo de Similaridad (Ciclos 1-4)

#### Ciclo 1: Modelo Redundancy

**Test**: `test_redundancy_model`

**Entrada**:
```python
from doc_handler.domain.models import Redundancy, Paragraph

p1 = Paragraph(
    text="El aprendizaje automático permite entrenar modelos.",
    index=0,
    line_number=5,
    embedding=[0.1] * 768
)
p2 = Paragraph(
    text="Los modelos se entrenan usando machine learning.",
    index=1,
    line_number=7,
    embedding=[0.15] * 768
)

redundancy = Redundancy(
    paragraph1=p1,
    paragraph2=p2,
    similarity_score=0.87
)
```

**Salida esperada**:
```python
assert redundancy.paragraph1 == p1
assert redundancy.paragraph2 == p2
assert redundancy.similarity_score == 0.87
assert redundancy.similarity_percentage == 87
```

**Criterios validados**: ✓ Modelo Pydantic válido ✓ Property `similarity_percentage`

---

#### Ciclo 2: Modelo RedundancyReport

**Test**: `test_redundancy_report_model`

**Entrada**:
```python
report = RedundancyReport(
    section_title="Introducción",
    total_paragraphs=10,
    redundancies=[redundancy1, redundancy2],
    threshold=0.7
)
```

**Salida esperada**:
```python
assert report.section_title == "Introducción"
assert report.total_paragraphs == 10
assert report.redundancy_count == 2
assert report.has_redundancies is True
assert report.threshold == 0.7
```

**Criterios validados**: ✓ Properties `has_redundancies` y `redundancy_count`

---

#### Ciclo 3: Cálculo de similaridad coseno (helpers)

**Test**: `test_cosine_similarity_calculation`

**Entrada**:
```python
from doc_handler.infrastructure.embedding_analyzer import cosine_similarity

vec1 = [1.0, 0.0, 0.0]
vec2 = [1.0, 0.0, 0.0]  # Idénticos
vec3 = [0.0, 1.0, 0.0]  # Perpendiculares
vec4 = [0.5, 0.5, 0.0]  # Parcialmente similares
```

**Salida esperada**:
```python
assert cosine_similarity(vec1, vec2) == 1.0  # Idénticos
assert cosine_similarity(vec1, vec3) == 0.0  # Perpendiculares
assert 0.5 < cosine_similarity(vec1, vec4) < 1.0  # Parcial
```

**Criterios validados**: ✓ Implementación correcta de cosine similarity

---

#### Ciclo 4: Manejo de vectores nulos o embeddings None

**Test**: `test_cosine_similarity_with_none_embeddings`

**Entrada**:
```python
p1 = Paragraph(text="", index=0, line_number=1, embedding=None)
p2 = Paragraph(text="Test", index=1, line_number=2, embedding=[0.1] * 768)
```

**Salida esperada**:
```python
# cosine_similarity debe retornar 0.0 si cualquier embedding es None
assert cosine_similarity(None, [0.1] * 768) == 0.0
assert cosine_similarity([0.1] * 768, None) == 0.0
assert cosine_similarity(None, None) == 0.0
```

**Criterios validados**: ✓ Manejo robusto de embeddings nulos

---

### Sprint 2: US-002A - Análisis de Sección (Ciclos 5-10)

#### Ciclo 5: Analyzer básico - sin redundancias

**Test**: `test_analyze_section_no_redundancies`

**Entrada**:
```python
from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer

markdown = """
# Introducción

Este es el primer párrafo sobre inteligencia artificial.

Este es el segundo párrafo sobre bases de datos relacionales.

Este es el tercer párrafo sobre redes neuronales.
"""
doc = parse_markdown(markdown, generate_embeddings=True)
section = doc.find_section("Introducción")

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.7)
```

**Salida esperada**:
```python
assert report.section_title == "Introducción"
assert report.total_paragraphs == 3
assert report.has_redundancies is False
assert report.redundancy_count == 0
assert report.redundancies == []
```

**Criterios validados**: ✓ Análisis básico funcional ✓ Identificación correcta de no-redundancias

---

#### Ciclo 6: Analyzer - detecta redundancias altas (≥70%)

**Test**: `test_analyze_section_with_redundancies`

**Entrada**:
```python
markdown = """
# Metodología

El enfoque cualitativo permite explorar experiencias.

La metodología cualitativa facilita la exploración de vivencias.

Este párrafo es completamente diferente sobre bases de datos.
"""
# Mock: Los embeddings de párrafos 1 y 2 son muy similares (similaridad 0.85)
doc = parse_markdown_with_mock_embeddings(markdown, similarities={
    (0, 1): 0.85,  # P1 y P2 similares
    (0, 2): 0.2,   # P1 y P3 diferentes
    (1, 2): 0.15   # P2 y P3 diferentes
})
section = doc.find_section("Metodología")

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.7)
```

**Salida esperada**:
```python
assert report.has_redundancies is True
assert report.redundancy_count == 1
assert report.redundancies[0].paragraph1.index == 0
assert report.redundancies[0].paragraph2.index == 1
assert report.redundancies[0].similarity_score == 0.85
assert report.redundancies[0].similarity_percentage == 85
```

**Criterios validados**: ✓ Detección de redundancias ✓ Threshold de 70%

---

#### Ciclo 7: Analyzer - respeta threshold personalizado

**Test**: `test_analyze_section_custom_threshold`

**Entrada**:
```python
# Mismo markdown del Ciclo 6, pero con threshold 0.9
analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.9)
```

**Salida esperada**:
```python
# Similaridad de 0.85 < 0.9, por lo tanto NO se detecta como redundante
assert report.has_redundancies is False
assert report.redundancy_count == 0
```

**Criterios validados**: ✓ Threshold configurable

---

#### Ciclo 8: Analyzer - múltiples redundancias en una sección

**Test**: `test_analyze_section_multiple_redundancies`

**Entrada**:
```python
markdown = """
# Resultados

Párrafo 1: contenido sobre IA.

Párrafo 2: contenido similar a párrafo 1 sobre IA.

Párrafo 3: contenido sobre bases de datos.

Párrafo 4: contenido similar a párrafo 3 sobre DB.
"""
# Mock: (P1, P2) similares 0.80 y (P3, P4) similares 0.75
doc = parse_markdown_with_mock_embeddings(markdown, similarities={
    (0, 1): 0.80,
    (2, 3): 0.75,
    # Resto < 0.7
})
section = doc.find_section("Resultados")

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.7)
```

**Salida esperada**:
```python
assert report.redundancy_count == 2
assert report.redundancies[0].paragraph1.index == 0
assert report.redundancies[0].paragraph2.index == 1
assert report.redundancies[1].paragraph1.index == 2
assert report.redundancies[1].paragraph2.index == 3
```

**Criterios validados**: ✓ Detección de múltiples pares redundantes

---

#### Ciclo 9: Analyzer - sección vacía (sin párrafos)

**Test**: `test_analyze_empty_section`

**Entrada**:
```python
markdown = """
# Sección Vacía
# Otra Sección

Contenido de otra sección.
"""
doc = parse_markdown(markdown, generate_embeddings=True)
section = doc.find_section("Sección Vacía")

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.7)
```

**Salida esperada**:
```python
assert report.total_paragraphs == 0
assert report.has_redundancies is False
assert report.redundancy_count == 0
```

**Criterios validados**: ✓ Manejo de secciones vacías

---

#### Ciclo 10: Analyzer - párrafos con embeddings None

**Test**: `test_analyze_section_with_missing_embeddings`

**Entrada**:
```python
# Sección con algunos párrafos sin embeddings (None)
section = Section(
    level=1,
    title="Test",
    paragraphs=[
        Paragraph(text="P1", index=0, line_number=1, embedding=[0.1]*768),
        Paragraph(text="P2", index=1, line_number=2, embedding=None),  # Sin embedding
        Paragraph(text="P3", index=2, line_number=3, embedding=[0.1]*768)
    ],
    subsections=[]
)

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.7)
```

**Salida esperada**:
```python
# Solo se comparan P1 y P3 (P2 se ignora porque tiene embedding=None)
# Si P1 y P3 no son similares:
assert report.total_paragraphs == 3
assert report.has_redundancies is False
```

**Criterios validados**: ✓ Ignorar párrafos sin embeddings ✓ No crashea con None

---

### Sprint 3: US-002B - Análisis de Documento Completo (Ciclos 11-14)

#### Ciclo 11: Analyzer - documento completo sin redundancias

**Test**: `test_analyze_document_no_redundancies`

**Entrada**:
```python
markdown = """
# Capítulo 1

Contenido único sobre IA en educación.

## Sección 1.1

Contenido único sobre evaluación docente.

# Capítulo 2

Contenido único sobre bases de datos NoSQL.
"""
doc = parse_markdown(markdown, generate_embeddings=True)

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_document(doc, threshold=0.7)
```

**Salida esperada**:
```python
assert report.section_title is None  # Análisis global
assert report.total_paragraphs == 3
assert report.has_redundancies is False
```

**Criterios validados**: ✓ Análisis de documento completo ✓ Atraviesa todas las secciones

---

#### Ciclo 12: Analyzer - documento con redundancias cross-sección

**Test**: `test_analyze_document_cross_section_redundancies`

**Entrada**:
```python
markdown = """
# Introducción

El machine learning permite entrenar modelos predictivos.

# Metodología

Los modelos predictivos se entrenan usando ML.

# Conclusiones

Párrafo completamente diferente sobre ética.
"""
# Mock: P1 (Introducción) y P2 (Metodología) son similares (0.82)
doc = parse_markdown_with_mock_embeddings(markdown, similarities={
    (0, 1): 0.82,
    # Resto < 0.7
})

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_document(doc, threshold=0.7)
```

**Salida esperada**:
```python
assert report.has_redundancies is True
assert report.redundancy_count == 1
# Detecta redundancia entre secciones diferentes
assert report.redundancies[0].paragraph1.text.startswith("El machine learning")
assert report.redundancies[0].paragraph2.text.startswith("Los modelos predictivos")
```

**Criterios validados**: ✓ Detecta redundancias cross-sección ✓ Análisis global completo

---

#### Ciclo 13: Analyzer - documento con múltiples redundancias

**Test**: `test_analyze_document_multiple_redundancies`

**Entrada**:
```python
markdown = """
# Capítulo 1
P1: Contenido sobre IA.
P2: Contenido similar a P1 sobre IA.

# Capítulo 2
P3: Contenido sobre DB.
P4: Contenido similar a P3 sobre DB.

# Capítulo 3
P5: Contenido repetido como P1.
"""
# Mock: (P1, P2) 0.8, (P3, P4) 0.75, (P1, P5) 0.78
doc = parse_markdown_with_mock_embeddings(markdown, similarities={
    (0, 1): 0.80,
    (2, 3): 0.75,
    (0, 4): 0.78,
})

analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_document(doc, threshold=0.7)
```

**Salida esperada**:
```python
assert report.redundancy_count == 3
# Verifica los 3 pares detectados
```

**Criterios validados**: ✓ Múltiples redundancias en documento completo

---

#### Ciclo 14: Performance - documento grande (50+ párrafos)

**Test**: `test_analyze_document_performance_large_doc`

**Entrada**:
```python
# Documento con 50 párrafos distribuidos en 10 secciones
markdown = generate_large_markdown(num_sections=10, paragraphs_per_section=5)
doc = parse_markdown(markdown, generate_embeddings=True)

import time
start = time.time()
analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_document(doc, threshold=0.7)
elapsed = time.time() - start
```

**Salida esperada**:
```python
assert report.total_paragraphs == 50
# Debe completarse en menos de 5 segundos (solo cálculos de similaridad)
assert elapsed < 5.0
# Verifica que usa embeddings cacheados, no llamadas a API
```

**Criterios validados**: ✓ Eficiencia con docs grandes ✓ Usa embeddings pre-calculados

---

### Sprint 4: CLI y Rich Output (Ciclos 15-18)

#### Ciclo 15: CLI command - check-redundancy-section

**Test**: `test_cli_check_redundancy_section_no_redundancies`

**Entrada**:
```bash
uv run python -m doc_handler check-redundancy-section test.md "Introducción"
```

**Salida esperada (Rich formatted)**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🔍 Análisis de redundancias en "Introducción"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Documento parseado: 5 secciones encontradas
⚙  Analizando sección (3 párrafos)...

✓ No se encontraron redundancias
```

**Criterios validados**: ✓ Comando CLI funcional ✓ Output con Rich

---

#### Ciclo 16: CLI command - check-redundancy-section con redundancias

**Test**: `test_cli_check_redundancy_section_with_redundancies`

**Salida esperada (Rich formatted)**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🔍 Análisis de redundancias en "Metodología"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Documento parseado: 5 secciones encontradas
⚙  Analizando sección (7 párrafos)...

⚠  Encontradas 2 redundancias:

┌─────────────────────────────────────────────────────┐
│ Redundancia #1 • Similitud: 87%                    │
├─────────────────────────────────────────────────────┤
│ Párrafo 3 (línea 15):                              │
│ "El enfoque cualitativo permite explorar..."       │
│                                                     │
│ Párrafo 7 (línea 31):                              │
│ "La metodología cualitativa facilita..."           │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Redundancia #2 • Similitud: 75%                    │
├─────────────────────────────────────────────────────┤
│ ...                                                 │
└─────────────────────────────────────────────────────┘
```

**Criterios validados**: ✓ Tabla Rich con redundancias ✓ Info detallada de párrafos

---

#### Ciclo 17: CLI command - check-redundancy (documento completo)

**Test**: `test_cli_check_redundancy_full_document`

**Entrada**:
```bash
uv run python -m doc_handler check-redundancy test.md
```

**Salida esperada (Rich formatted)**:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 🔍 Análisis de redundancias globales
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Documento parseado: 8 secciones, 45 párrafos
⚙  Analizando documento completo...

📊 Estadísticas:
  • Total de párrafos analizados: 45
  • Comparaciones realizadas: 990
  • Pares redundantes encontrados: 5

⚠  Top 5 redundancias encontradas:

┌─────────────────────────────────────────────────────┐
│ Redundancia #1 • Similitud: 92%                    │
├─────────────────────────────────────────────────────┤
│ Sección "Introducción" - Párrafo 2 (línea 10)      │
│ Sección "Conclusiones" - Párrafo 1 (línea 120)     │
└─────────────────────────────────────────────────────┘

...
```

**Criterios validados**: ✓ Estadísticas globales ✓ Agrupación visual

---

#### Ciclo 18: CLI error handling - sección no existe

**Test**: `test_cli_section_not_found_error`

**Entrada**:
```bash
uv run python -m doc_handler check-redundancy-section test.md "Metadología"
```

**Salida esperada (Rich formatted)**:
```
❌ Error: Sección "Metadología" no encontrada

📋 Secciones disponibles:
  • Introducción
  • Metodología
  • Resultados
  • Conclusiones

💡 ¿Quisiste decir "Metodología"?
```

**Criterios validados**: ✓ Error handling ✓ Sugerencias amigables

---

## Orden de Implementación TDD

### Sprint 1: Fundamentos (Ciclos 1-4) - 2 días
1. ✅ Modelo `Redundancy` (Pydantic)
2. ✅ Modelo `RedundancyReport` (Pydantic)
3. ✅ Función `cosine_similarity()` en `infrastructure/embedding_analyzer.py`
4. ✅ Manejo de embeddings None

**Entregable**: Modelos y función de similaridad testeados

---

### Sprint 2: US-002A - Análisis de Sección (Ciclos 5-10) - 3 días
5. ✅ Protocol `RedundancyAnalyzer` en `domain/analyzer.py`
6. ✅ Implementación `EmbeddingAnalyzer` básica (sin redundancias)
7. ✅ Detección de redundancias con threshold 0.7
8. ✅ Threshold personalizado
9. ✅ Múltiples redundancias
10. ✅ Edge cases: sección vacía, embeddings None

**Entregable**: `EmbeddingAnalyzer.analyze_section()` completamente funcional

---

### Sprint 3: US-002B - Análisis de Documento (Ciclos 11-14) - 2 días
11. ✅ `analyze_document()` básico
12. ✅ Redundancias cross-sección
13. ✅ Múltiples redundancias en documento
14. ✅ Performance test con documento grande

**Entregable**: `EmbeddingAnalyzer.analyze_document()` optimizado

---

### Sprint 4: CLI y Rich Output (Ciclos 15-18) - 2 días
15. ✅ Comando `check-redundancy-section`
16. ✅ Output Rich con tablas y colores
17. ✅ Comando `check-redundancy` (documento completo)
18. ✅ Error handling y mensajes amigables

**Entregable**: CLI funcional con excelente UX

---

## Estructura de Archivos

```
doc_handler/
├── doc_handler/
│   ├── domain/
│   │   ├── models.py           # ✅ Ya existe - AÑADIR Redundancy, RedundancyReport
│   │   ├── analyzer.py         # NUEVO - Protocol RedundancyAnalyzer
│   │   └── exceptions.py       # ✅ Ya existe
│   │
│   ├── infrastructure/
│   │   ├── embeddings.py       # ✅ Ya existe
│   │   └── embedding_analyzer.py   # NUEVO - Implementación con embeddings
│   │
│   └── cli/
│       ├── __init__.py
│       └── commands.py         # NUEVO - Click commands
│
├── tests/
│   ├── domain/
│   │   ├── test_models.py      # MODIFICAR - añadir tests de Redundancy
│   │   └── test_analyzer.py    # NUEVO - tests del protocol
│   │
│   ├── infrastructure/
│   │   └── test_embedding_analyzer.py  # NUEVO - 14 tests
│   │
│   ├── cli/
│   │   └── test_commands.py    # NUEVO - tests de CLI
│   │
│   └── fixtures/
│       └── markdown_samples.py # MODIFICAR - añadir docs con redundancias
│
├── pyproject.toml              # MODIFICAR - añadir numpy, click, rich
└── TDD_PLAN_US002.md          # Este archivo
```

---

## Comandos de Testing con uv

```bash
# Correr todos los tests de US-002
uv run pytest tests/infrastructure/test_embedding_analyzer.py -v
uv run pytest tests/cli/test_commands.py -v

# Correr un test específico
uv run pytest tests/infrastructure/test_embedding_analyzer.py::test_analyze_section_no_redundancies

# Con coverage de los nuevos módulos
uv run pytest --cov=doc_handler.domain.analyzer --cov=doc_handler.infrastructure.embedding_analyzer

# Test de performance (ciclo 14)
uv run pytest tests/infrastructure/test_embedding_analyzer.py::test_analyze_document_performance_large_doc -v -s
```

---

## Checklist de Implementación

### Paso 1: Setup inicial
- [ ] `uv pip install numpy click rich`
- [ ] Actualizar `pyproject.toml` con nuevas dependencias
- [ ] Crear estructura de carpetas: `cli/`, `tests/cli/`

### Paso 2: Modelos (Ciclos 1-2)
- [ ] Test `test_redundancy_model` (ROJO)
- [ ] Definir `Redundancy` en `domain/models.py` (VERDE)
- [ ] Test `test_redundancy_report_model` (ROJO)
- [ ] Definir `RedundancyReport` en `domain/models.py` (VERDE)
- [ ] Refactor: docstrings y validaciones Pydantic
- [ ] `uv run pytest tests/domain/test_models.py -v`

### Paso 3: Similaridad Coseno (Ciclos 3-4)
- [ ] Test `test_cosine_similarity_calculation` (ROJO)
- [ ] Implementar `cosine_similarity()` en `infrastructure/embedding_analyzer.py` (VERDE)
- [ ] Test `test_cosine_similarity_with_none_embeddings` (ROJO)
- [ ] Manejar embeddings None (VERDE)
- [ ] Refactor: optimización con numpy
- [ ] `uv run pytest tests/infrastructure/test_embedding_analyzer.py::test_cosine* -v`

### Paso 4: Protocol RedundancyAnalyzer (Sprint 2, Ciclo 5)
- [ ] Definir `RedundancyAnalyzer` Protocol en `domain/analyzer.py`
- [ ] Test básico de protocol (verificar firma)

### Paso 5: EmbeddingAnalyzer - Análisis de Sección (Ciclos 5-10)
- [ ] Test `test_analyze_section_no_redundancies` (ROJO)
- [ ] Implementar `EmbeddingAnalyzer.analyze_section()` básico (VERDE)
- [ ] Test `test_analyze_section_with_redundancies` (ROJO)
- [ ] Implementar detección de redundancias con threshold (VERDE)
- [ ] Test `test_analyze_section_custom_threshold` (ROJO)
- [ ] Parametrizar threshold (VERDE)
- [ ] Test `test_analyze_section_multiple_redundancies` (ROJO)
- [ ] Detectar múltiples pares (VERDE)
- [ ] Test `test_analyze_empty_section` (ROJO)
- [ ] Manejar sección vacía (VERDE)
- [ ] Test `test_analyze_section_with_missing_embeddings` (ROJO)
- [ ] Ignorar párrafos sin embeddings (VERDE)
- [ ] Refactor: extraer lógica de comparación
- [ ] `uv run pytest tests/infrastructure/test_embedding_analyzer.py -v -k section`

### Paso 6: EmbeddingAnalyzer - Análisis de Documento (Ciclos 11-14)
- [ ] Test `test_analyze_document_no_redundancies` (ROJO)
- [ ] Implementar `analyze_document()` básico (VERDE)
- [ ] Test `test_analyze_document_cross_section_redundancies` (ROJO)
- [ ] Atravesar todas las secciones y subsecciones (VERDE)
- [ ] Test `test_analyze_document_multiple_redundancies` (ROJO)
- [ ] Detectar múltiples pares cross-sección (VERDE)
- [ ] Test `test_analyze_document_performance_large_doc` (ROJO)
- [ ] Optimizar: usar numpy vectorization si es necesario (VERDE)
- [ ] Refactor: reutilizar lógica compartida con analyze_section
- [ ] `uv run pytest tests/infrastructure/test_embedding_analyzer.py -v -k document`

### Paso 7: CLI - check-redundancy-section (Ciclos 15-16)
- [ ] Crear `cli/commands.py` con estructura básica Click
- [ ] Test `test_cli_check_redundancy_section_no_redundancies` (ROJO)
- [ ] Implementar comando `check-redundancy-section` (VERDE)
- [ ] Test `test_cli_check_redundancy_section_with_redundancies` (ROJO)
- [ ] Implementar output Rich con tablas (VERDE)
- [ ] Refactor: extraer funciones de formateo Rich
- [ ] `uv run pytest tests/cli/test_commands.py -v -k section`

### Paso 8: CLI - check-redundancy documento completo (Ciclos 17-18)
- [ ] Test `test_cli_check_redundancy_full_document` (ROJO)
- [ ] Implementar comando `check-redundancy` (VERDE)
- [ ] Test `test_cli_section_not_found_error` (ROJO)
- [ ] Implementar error handling con mensajes amigables (VERDE)
- [ ] Refactor: DRY entre ambos comandos
- [ ] `uv run pytest tests/cli/test_commands.py -v`

### Paso 9: Integración End-to-End
- [ ] Test E2E: archivo real → CLI → output esperado
- [ ] Verificar que funciona con documentos reales de la carpeta `fixtures/`
- [ ] `uv run pytest --cov=doc_handler --cov-report=term-missing`

### Paso 10: Documentación
- [ ] Docstrings en `cosine_similarity()`
- [ ] Docstrings en `EmbeddingAnalyzer`
- [ ] Docstrings en comandos Click
- [ ] Actualizar README con ejemplos de uso de CLI
- [ ] Añadir sección de uso en README

---

## Criterio de Éxito

✅ **18+ tests pasando** (14 analyzer + 4 CLI mínimo)
✅ **Coverage ≥90%** en:
  - `doc_handler/domain/models.py` (nuevos modelos)
  - `doc_handler/infrastructure/embedding_analyzer.py`
  - `doc_handler/cli/commands.py`
✅ **CLI funcional**: Ambos comandos ejecutables con outputs Rich
✅ **Performance**: Documentos de 50 párrafos analizados en <5s
✅ **Docstrings completos** en funciones públicas
✅ **US-002A y US-002B marcadas como Done** en USER_STORIES.md

---

## Helpers de Testing

### Fixture: parse_markdown_with_mock_embeddings

```python
# tests/fixtures/markdown_samples.py

def parse_markdown_with_mock_embeddings(
    markdown: str,
    similarities: dict[tuple[int, int], float]
) -> Document:
    """
    Parsea markdown y genera embeddings mockeados con similaridades controladas.

    Args:
        markdown: Contenido Markdown
        similarities: Diccionario {(idx1, idx2): similarity_score}

    Returns:
        Document con embeddings mockeados
    """
    # Genera embeddings sintéticos que cumplen las similaridades dadas
    # Usa vectores ortogonales + rotaciones para lograr similaridades exactas
    ...
```

### Fixture: generate_large_markdown

```python
def generate_large_markdown(
    num_sections: int = 10,
    paragraphs_per_section: int = 5
) -> str:
    """
    Genera documento grande para tests de performance.

    Returns:
        Markdown con num_sections * paragraphs_per_section párrafos
    """
    sections = []
    for i in range(num_sections):
        sections.append(f"# Section {i+1}\n")
        for j in range(paragraphs_per_section):
            sections.append(f"Paragraph {i*paragraphs_per_section + j + 1} content.\n")
    return "\n".join(sections)
```

---

## Notas de Implementación

### Optimización de Performance

Para documentos grandes (US-002B), la complejidad es O(n²) donde n = número de párrafos.

**Estrategias de optimización**:

1. **Vectorización con NumPy**: Usar `np.dot()` y broadcasting
   ```python
   # En lugar de loops anidados:
   for i in range(len(paragraphs)):
       for j in range(i+1, len(paragraphs)):
           sim = cosine_similarity(emb[i], emb[j])

   # Usar matriz de similaridad:
   embeddings_matrix = np.array([p.embedding for p in paragraphs])
   similarity_matrix = cosine_similarity_matrix(embeddings_matrix)
   ```

2. **Early stopping**: Si threshold=0.7, podemos usar clustering/hashing para descartar pares obviamente disímiles

3. **Batch comparison**: Comparar todos contra todos en una sola operación matricial

### Formato de Output CLI (Rich)

Usar componentes de Rich:
- `Console` para output principal
- `Table` para mostrar redundancias
- `Panel` para resúmenes
- `Progress` para análisis de documentos grandes
- `Prompt` para confirmaciones (US-003)

Ejemplo:
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Header
console.print(
    Panel.fit(
        f"🔍 Análisis de redundancias en \"{section_title}\"",
        border_style="blue"
    )
)

# Tabla de redundancias
if report.has_redundancies:
    table = Table(title="Redundancias encontradas")
    table.add_column("#", style="cyan")
    table.add_column("Similitud", style="magenta")
    table.add_column("Párrafo 1", style="white")
    table.add_column("Párrafo 2", style="white")

    for i, red in enumerate(report.redundancies, 1):
        table.add_row(
            str(i),
            f"{red.similarity_percentage}%",
            f"P{red.paragraph1.index} (L{red.paragraph1.line_number})",
            f"P{red.paragraph2.index} (L{red.paragraph2.line_number})"
        )

    console.print(table)
else:
    console.print("✓ No se encontraron redundancias", style="green")
```

---

## Próximos Pasos (después de US-002)

- **US-003**: Aplicar cambios con aprobación manual (file_handler + diff)
- **Integración completa**: CLI end-to-end con todos los comandos
- **Documentación de usuario**: README con ejemplos reales
