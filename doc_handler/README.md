# doc_handler

**Editor Markdown con IA** - Herramienta CLI para edición inteligente de documentos Markdown con detección de redundancias basada en embeddings.

## 🎯 Características (MVP v0.1 - COMPLETO)

### ✅ US-001: Parser de Markdown
- **Parser completo**: Soporta headings (niveles 1-6), párrafos, jerarquía de secciones, bloques de código
- **Embeddings automáticos**: Genera vectores de 768 dimensiones usando Jina AI para cada párrafo
- **API de búsqueda**: Encuentra secciones por título con sugerencias en caso de error
- **Manejo robusto**: Caracteres especiales, code blocks, listas

### ✅ US-002: Detección de Redundancias
- **Análisis por sección**: Detecta párrafos redundantes en una sección específica
- **Análisis de documento completo**: Encuentra redundancias cross-sección
- **Similaridad semántica**: Usa cosine similarity de embeddings (threshold configurable, default 70%)
- **Output visual**: Tablas Rich con colores, similitud porcentual, líneas de código

### ✅ US-003: Aplicación de Cambios
- **Diff visual**: Muestra cambios propuestos con syntax highlighting
- **Confirmación interactiva**: Pregunta antes de aplicar (default: No)
- **Backup automático**: Crea `.backup` antes de modificar
- **Preservación de formato**: UTF-8, espaciado, líneas vacías intactas
- **Modo interactivo**: Revisa múltiples redundancias una por una

## 📦 Instalación

```bash
# Clonar el repositorio
cd doc_handler

# Instalar dependencias (usa uv, no necesitas activar venv)
uv pip install -r requirements.txt

# O instalar manualmente
uv pip install pydantic click rich numpy pytest pytest-cov pytest-mock requests python-dotenv

# Configurar API key de Jina AI
cp .env.example .env
# Editar .env y agregar tu JINA_API_KEY
```

## 🚀 Uso CLI

### 1. Detectar redundancias en una sección

```bash
uv run python -m doc_handler check-redundancy-section documento.md "Capítulo 2"
```

**Output:**
```
┌─────────────────────────────────────────────────┐
│ Análisis de redundancias en "Capítulo 2"       │
└─────────────────────────────────────────────────┘

Documento parseado: 5 secciones encontradas

Encontradas 2 redundancias:

┌─────────────────────────────────────────────────┐
│ Redundancia #1 • Similitud: 87%                │
├─────────────────────────────────────────────────┤
│ Párrafo  │ Línea │ Contenido                    │
│ #1       │ 15    │ El machine learning permite..│
│ #3       │ 21    │ Los modelos de ML facilitan..│
└─────────────────────────────────────────────────┘
```

### 2. Detectar redundancias en todo el documento

```bash
uv run python -m doc_handler check-redundancy documento.md --threshold 0.75
```

### 3. Proponer y aplicar correcciones (¡NUEVO!)

```bash
uv run python -m doc_handler propose-fix documento.md "Capítulo 2"
```

**Flujo interactivo:**
1. Muestra redundancias encontradas
2. Para cada una, propone eliminar el párrafo redundante
3. Muestra diff con cambios propuestos
4. Pregunta confirmación: `¿Aplicar cambio? [s/N]:`
5. Si acepta: crea backup y aplica cambios
6. Si rechaza: pasa a la siguiente redundancia

**Modo interactivo** (revisa todas las redundancias):
```bash
uv run python -m doc_handler propose-fix documento.md "Capítulo 2" --interactive
```

### Opciones comunes

```bash
--threshold FLOAT    # Umbral de similitud (0.0-1.0, default: 0.7)
--interactive        # Revisar todas las redundancias (propose-fix)
```

## 📚 Uso Programático

```python
from doc_handler.domain.parser import parse_markdown
from doc_handler.infrastructure.embedding_analyzer import EmbeddingAnalyzer
from pathlib import Path

# 1. Parsear documento con embeddings
content = Path("documento.md").read_text(encoding='utf-8')
doc = parse_markdown(content, generate_embeddings=True)

# 2. Buscar sección
section = doc.find_section("Capítulo 2")

# 3. Analizar redundancias
analyzer = EmbeddingAnalyzer()
report = analyzer.analyze_section(section, threshold=0.7)

# 4. Revisar resultados
if report.has_redundancies:
    for redundancy in report.redundancies:
        print(f"Similitud: {redundancy.similarity_percentage}%")
        print(f"P1: {redundancy.paragraph1.text[:50]}...")
        print(f"P2: {redundancy.paragraph2.text[:50]}...")
```

## Testing

```bash
# Todos los tests
uv run pytest

# Con coverage
uv run pytest --cov=doc_handler --cov-report=term-missing

# Tests específicos
uv run pytest tests/domain/test_parser.py -v
uv run pytest tests/infrastructure/test_embeddings.py -v
```

## 📁 Estructura del Proyecto

```
doc_handler/
├── doc_handler/
│   ├── domain/              # Lógica de negocio (sin dependencias externas)
│   │   ├── models.py        # Pydantic models (Document, Section, Paragraph, Redundancy)
│   │   ├── parser.py        # Markdown parser con embeddings
│   │   ├── analyzer.py      # Protocol para análisis de redundancias
│   │   └── exceptions.py    # Excepciones personalizadas
│   │
│   ├── infrastructure/      # Implementaciones concretas
│   │   ├── embeddings.py    # Cliente Jina AI para embeddings
│   │   ├── embedding_analyzer.py  # Análisis con cosine similarity
│   │   └── file_handler.py  # Backup, diff, modificación de archivos
│   │
│   ├── cli/                 # Interfaz de usuario
│   │   └── commands.py      # Comandos Click con Rich formatting
│   │
│   └── __main__.py          # Entry point
│
└── tests/                   # 58 tests, 69% coverage
    ├── domain/              # Tests unitarios del dominio
    ├── infrastructure/      # Tests con mocks de APIs
    └── fixtures/            # Datos de prueba
```

## 🧪 Testing

```bash
# Todos los tests (58 tests)
uv run pytest

# Con coverage detallado
uv run pytest --cov=doc_handler --cov-report=term-missing

# Tests específicos por módulo
uv run pytest tests/domain/test_parser.py -v
uv run pytest tests/infrastructure/test_embedding_analyzer.py -v
uv run pytest tests/infrastructure/test_file_handler.py -v

# Coverage HTML
uv run pytest --cov=doc_handler --cov-report=html
# Abrir htmlcov/index.html
```

### 📊 Coverage Actual

**Total: 69% overall**

| Módulo                 | Coverage |
|------------------------|----------|
| models.py              | 94%      |
| parser.py              | 95%      |
| embedding_analyzer.py  | 98%      |
| file_handler.py        | 90%      |
| embeddings.py          | 81%      |

## 🏗️ Desarrollo

Este proyecto fue desarrollado siguiendo **TDD estricto**:
1. **Red**: Escribir test que falla
2. **Green**: Implementar lo mínimo para que pase
3. **Refactor**: Mejorar sin romper tests

### Planes TDD disponibles:
- [TDD_PLAN_US001.md](TDD_PLAN_US001.md) - Parser de Markdown con embeddings
- [TDD_PLAN_US002.md](TDD_PLAN_US002.md) - Detección de redundancias
- [TDD_PLAN_US003.md](TDD_PLAN_US003.md) - Aplicación de cambios con aprobación

## 🔧 Stack Tecnológico

- **Python**: >= 3.11
- **CLI Framework**: Click
- **UI/Output**: Rich (colores, tablas, progress bars)
- **Data Validation**: Pydantic
- **Embeddings**: Jina AI API (jina-embeddings-v3, 768 dims)
- **Vector Operations**: NumPy (cosine similarity)
- **Testing**: pytest, pytest-cov, pytest-mock

## 🎯 Estado del MVP

**v0.1 - COMPLETO** ✅

| User Story | Descripción                           | Story Points | Estado |
|------------|---------------------------------------|--------------|--------|
| US-001     | Parser de Markdown + embeddings       | 5            | ✅ Done |
| US-002A    | Detección de redundancias (sección)   | 5            | ✅ Done |
| US-002B    | Detección de redundancias (documento) | 3            | ✅ Done |
| US-003     | Aplicación de cambios con aprobación  | 3            | ✅ Done |
| **Total**  |                                       | **16**       | **COMPLETE** |

**Métricas finales:**
- ✅ 58 tests pasando
- ✅ 69% coverage general
- ✅ 90%+ coverage en módulos core
- ✅ 3 comandos CLI funcionando
- ✅ TDD completo con planes documentados

## 📖 Documentación Adicional

- [USER_STORIES.md](USER_STORIES.md) - Historias de usuario y criterios de aceptación
- [PRD.md](PRD.md) - Product Requirements Document
- [ARCHITECTURE.md](ARCHITECTURE.md) - Arquitectura en capas
- [CLAUDE.md](CLAUDE.md) - Guía para Claude Code

## 🚧 Próximas Versiones (Backlog)

- **v0.2**: Sugerir citas desde corpus RAG
- **v0.3**: Generar transiciones entre secciones
- **v0.4**: Interfaz gráfica (Streamlit/web)

## 📝 Licencia

MIT
