# doc_handler

Editor Markdown con IA - Parser de Markdown con embeddings para análisis semántico.

## Características

- **Parser completo de Markdown**: Soporta headings (niveles 1-6), párrafos, jerarquía de secciones, bloques de código
- **Embeddings automáticos**: Genera vectores de 768 dimensiones usando Jina AI para cada párrafo
- **API de búsqueda**: Encuentra secciones por título con sugerencias en caso de error
- **Arquitectura limpia**: Separación entre dominio, infraestructura y CLI

## Instalación

```bash
# Crear ambiente virtual
uv venv

# Instalar dependencias
uv pip install pydantic pytest pytest-cov pytest-mock requests python-dotenv

# Configurar API key de Jina AI
cp .env.example .env
# Editar .env y agregar tu JINA_API_KEY
```

## Uso

```python
from doc_handler.domain.parser import parse_markdown
from pathlib import Path

# Parsear sin embeddings
content = """# Capítulo 1

Este es el primer párrafo.

## Sección 1.1

Contenido de la subsección."""

doc = parse_markdown(content, path=Path("documento.md"))

# Acceder a la estructura
print(doc.sections[0].title)  # "Capítulo 1"
print(len(doc.sections[0].paragraphs))  # 1
print(len(doc.sections[0].subsections))  # 1

# Buscar sección
section = doc.find_section("Sección 1.1")
print(section.content)

# Parsear con embeddings (requiere JINA_API_KEY)
doc_with_embeddings = parse_markdown(content, generate_embeddings=True)
embedding = doc_with_embeddings.sections[0].paragraphs[0].embedding
print(len(embedding))  # 768
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

## Estructura del Proyecto

```
doc_handler/
├── doc_handler/
│   ├── domain/          # Lógica de negocio
│   │   ├── models.py    # Pydantic models
│   │   ├── parser.py    # Markdown parser
│   │   └── exceptions.py
│   └── infrastructure/  # Servicios externos
│       └── embeddings.py  # Cliente Jina AI
└── tests/
    ├── domain/
    └── infrastructure/
```

## Desarrollo

Este proyecto fue desarrollado siguiendo TDD estricto:
1. **Red**: Escribir test que falla
2. **Green**: Implementar lo mínimo para que pase
3. **Refactor**: Mejorar sin romper tests

Ver [TDD_PLAN_US001.md](TDD_PLAN_US001.md) para detalles del plan de desarrollo.

## Coverage

Actualmente: **90%+ coverage**

```bash
uv run pytest --cov=doc_handler --cov-report=html
# Abrir htmlcov/index.html
```

## Requisitos

- Python >= 3.11
- Jina AI API key (para embeddings)

## Licencia

MIT
