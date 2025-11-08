# Arquitectura - doc_handler

## Principio Rector

**Amplificación sobre automatización**: El sistema amplifica las capacidades humanas en lugar de reemplazar la toma de decisiones. El humano siempre está en el loop de aprobación.

---

## Decisiones de Diseño

### AD-001: Document es mutable
**Decisión**: Los objetos `Document` se modifican en memoria.

**Razón**: Simplicidad para el MVP. Operaciones como "aplicar cambio" mutan el documento directamente.

**Implicación**:
- No hay inmutabilidad funcional
- El rollback se maneja con backups de archivo, no con historial de objetos
- Tests deben crear copias si necesitan preservar estado

---

### AD-002: Parser solo estructura
**Decisión**: El parser NO valida ni normaliza. Solo convierte texto → árbol.

**Razón**: Separación de responsabilidades. La validación (si se necesita) es un servicio aparte.

**Implicación**:
- Permite duplicados de títulos
- Acepta cualquier estructura válida de Markdown
- Si hay headings malformados, se parsean tal cual

---

### AD-003: Section contiene Paragraphs pre-parseados
**Decisión**: Una `Section` tiene `paragraphs: list[Paragraph]`, no solo `content: str`.

**Razón**: El dominio es rico. El análisis de redundancias trabaja sobre párrafos, entonces los párrafos son entidades de primera clase.

**Implicación**:
- El parser divide el contenido en párrafos durante la carga
- Un `Paragraph` es un value object con `text: str` y `index: int`
- Los análisis trabajan directamente con `section.paragraphs`

---

### AD-004: Redundancy es solo reporte (centrado en humanos)
**Decisión**: `Redundancy` es un value object con datos, NO ejecuta cambios.

**Razón**: Filosofía de amplificación. El reporte informa, el humano decide, el sistema ejecuta.

**Implicación**:
```python
class Redundancy:
    paragraph_indices: tuple[int, int]  # Cuáles párrafos
    similarity_score: float              # Qué tan similares
    suggestion: str                      # Propuesta de consolidación
    # NO tiene método .apply()
```

---

### AD-005: Consolidación híbrida con humano en el loop
**Decisión**: LLM sugiere consolidación → Humano aprueba/rechaza → Dominio aplica.

**Razón**: Balance entre capacidad de IA y control humano.

**Flujo**:
1. `find_redundancies(section, llm)` → lista de `Redundancy`
2. CLI muestra cada `Redundancy` con su `suggestion`
3. Humano acepta/rechaza cada una
4. `apply_patch(document, patch)` aplica solo las aceptadas

---

### AD-006: Cambios como Patch con operaciones
**Decisión**: Los cambios se representan como `Patch` con operaciones específicas.

**Razón**: Trazabilidad y precisión. No es "reemplaza todo el archivo", sino "elimina líneas X-Y, inserta texto en Z".

**Modelo**:
```python
class PatchOperation:
    type: Literal["delete", "insert", "replace"]
    line_start: int
    line_end: int | None
    new_content: str | None

class Patch:
    operations: list[PatchOperation]
```

---

### AD-007: Analyzer como función con dependency injection
**Decisión**: No hay clase `Analyzer`. Hay función pura que recibe el LLM client.

**Razón**: Simplicidad y testabilidad. No necesitamos estado ni polimorfismo complejo.

**Uso**:
```python
# domain/analyzer.py
def find_redundancies(
    section: Section,
    llm_client: LLMClient  # Interface/Protocol
) -> list[Redundancy]:
    ...

# En CLI
from infrastructure.gemini_client import GeminiClient
redundancies = find_redundancies(section, GeminiClient())
```

---

### AD-008: Excepciones custom del dominio
**Decisión**: El dominio lanza excepciones específicas, no genéricas de Python.

**Razón**: Errores de dominio tienen semántica propia. El CLI puede manejarlos de forma específica.

**Jerarquía**:
```python
class DocumentError(Exception):
    """Base para errores de dominio"""

class SectionNotFoundError(DocumentError):
    def __init__(self, title: str, available: list[str]):
        self.title = title
        self.available = available

class ParseError(DocumentError):
    def __init__(self, line: int, reason: str):
        ...

class PatchApplicationError(DocumentError):
    ...
```

---

## Modelo de Dominio

### Entidades

#### Document (Mutable Entity)
```python
class Document(BaseModel):
    path: Path
    sections: list[Section]
    raw_content: str  # Texto original completo

    def find_section(self, title: str) -> Section:
        """Lanza SectionNotFoundError si no existe"""
        ...

    def get_section_by_index(self, index: int) -> Section:
        ...
```

#### Section (Mutable Entity)
```python
class Section(BaseModel):
    level: int = Field(ge=1, le=6)
    title: str
    paragraphs: list[Paragraph]
    subsections: list["Section"] = []
    start_line: int
    end_line: int

    @property
    def content(self) -> str:
        """Reconstruye el texto desde paragraphs"""
        return "\n\n".join(p.text for p in self.paragraphs)
```

### Value Objects

#### Paragraph
```python
class Paragraph(BaseModel):
    text: str
    index: int  # Posición dentro de la sección (0-indexed)
    line_number: int  # Línea en el archivo original
```

#### Redundancy
```python
class Redundancy(BaseModel):
    paragraph_indices: tuple[int, int]
    similarity_score: float = Field(ge=0, le=1)
    suggestion: str  # Texto consolidado propuesto por LLM
    reasoning: str   # Por qué son redundantes (para mostrar al humano)
```

#### Patch & PatchOperation
```python
class PatchOperation(BaseModel):
    type: Literal["delete", "insert", "replace"]
    line_start: int
    line_end: int | None = None
    new_content: str | None = None

class Patch(BaseModel):
    operations: list[PatchOperation]
    description: str  # Descripción humana del cambio
```

### Servicios de Dominio

#### Parser (domain/parser.py)
```python
def parse_markdown(content: str) -> Document:
    """
    Convierte texto Markdown → Document tree.

    - Identifica headings (#, ##, etc.)
    - Divide contenido en párrafos (separados por línea vacía)
    - Construye jerarquía de secciones
    - NO valida ni normaliza

    Raises:
        ParseError: Si hay problemas estructurales críticos
    """
    ...
```

#### Analyzer (domain/analyzer.py)
```python
def find_redundancies(
    section: Section,
    llm_client: LLMClient,
    threshold: float = 0.7
) -> list[Redundancy]:
    """
    Encuentra párrafos redundantes en una sección.

    Args:
        section: Sección a analizar
        llm_client: Cliente LLM para análisis semántico
        threshold: Similitud mínima (0.7 = 70%)

    Returns:
        Lista de redundancias encontradas (puede estar vacía)

    Nota:
        - Usa LLM para análisis semántico, no solo léxico
        - Cada Redundancy incluye sugerencia de consolidación del LLM
    """
    ...
```

#### Patcher (domain/patcher.py)
```python
def create_patch_for_redundancy(
    document: Document,
    section: Section,
    redundancy: Redundancy
) -> Patch:
    """
    Convierte una Redundancy aprobada en un Patch aplicable.

    - Calcula líneas exactas a eliminar/modificar
    - Genera operaciones de patch
    """
    ...

def apply_patch(document: Document, patch: Patch) -> None:
    """
    Aplica un patch al documento (muta el objeto).

    Raises:
        PatchApplicationError: Si el patch no puede aplicarse
    """
    ...
```

---

### AD-009: Caché automático con JSON sidecar (v0.2)
**Decisión**: El sistema cachea automáticamente documentos parseados con embeddings en archivos JSON sidecar.

**Razón**: Performance crítica - generar embeddings para documentos grandes puede tomar 10-30 segundos. El caché reduce ejecuciones subsecuentes a <100ms.

**Implementación**:
```python
# Cache format: documento.md.doccache
{
  "version": "0.1",
  "source_file": "documento.md",
  "file_hash": "sha256...",  # SHA256 del contenido
  "last_modified": "2025-11-05T16:30:00Z",
  "document": {
    # Serialized Document model con embeddings (Pydantic .model_dump())
  }
}
```

**Invalidación**:
- Hash SHA256 del archivo fuente no coincide
- Archivo fuente modificado (mtime check)
- Flag `--reparse` forzado por usuario

**Ventajas**:
- Transparente: Usuarios no necesitan comandos extra
- Portable: Archivos JSON pueden moverse con el documento
- Simple: No requiere base de datos
- Visible: Usuarios ven archivos `.doccache`

**Implicación**:
- `parse_markdown()` verifica cache antes de generar embeddings
- Todos los comandos CLI soportan `--reparse` flag
- Comandos `cache-clear` y `cache-info` para gestión manual
- Cache se guarda después de generación exitosa de embeddings

---

## Capa de Infraestructura

### CacheManager (infrastructure/cache.py)
```python
class CacheManager:
    """Gestiona cache de documentos parseados con embeddings."""

    def get_cached_document(self, source_path: Path) -> Document | None:
        """
        Retorna documento cacheado si válido, None si no existe/inválido.

        Valida que:
        - Archivo cache existe
        - Hash SHA256 coincide
        - Versión de cache es compatible
        """
        ...

    def save_document_cache(self, source_path: Path, document: Document) -> None:
        """
        Guarda documento en cache JSON sidecar.

        - Serializa Document con Pydantic .model_dump()
        - Calcula hash SHA256 del source file
        - Guarda en {source_path}.doccache
        """
        ...

    def is_cache_valid(self, source_path: Path) -> bool:
        """Verifica si cache es válido (sin cargar documento completo)"""
        ...

    def clear_cache(self, source_path: Path) -> bool:
        """Elimina archivo cache. Retorna True si existía."""
        ...
```

### LLMClient (Protocol)
```python
from typing import Protocol

class LLMClient(Protocol):
    """Interface para clientes LLM."""

    def analyze_similarity(
        self,
        paragraph1: str,
        paragraph2: str
    ) -> tuple[float, str]:
        """
        Retorna (similarity_score, reasoning).

        similarity_score: 0.0 a 1.0
        reasoning: Explicación de por qué son similares
        """
        ...

    def suggest_consolidation(
        self,
        paragraph1: str,
        paragraph2: str
    ) -> str:
        """
        Retorna texto consolidado que fusiona ambos párrafos.
        """
        ...
```

### Implementaciones

#### infrastructure/gemini_client.py
```python
class GeminiClient:
    """Implementación concreta con Gemini API"""

    def __init__(self, api_key: str):
        ...

    def analyze_similarity(self, p1: str, p2: str) -> tuple[float, str]:
        # Llama a Gemini API
        ...
```

#### infrastructure/file_handler.py
```python
def load_markdown(path: Path) -> str:
    """Lee archivo con encoding UTF-8"""
    ...

def save_markdown(path: Path, content: str) -> None:
    """Escribe con backup automático"""
    ...

def create_backup(path: Path) -> Path:
    """Crea path.backup antes de modificar"""
    ...
```

---

## Capa CLI

### cli/commands.py

```python
import click
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

@click.group()
def cli():
    """doc_handler - Editor Markdown con IA"""
    pass

@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.argument("section_title")
@click.option("--threshold", default=0.7, help="Umbral de similitud")
def check_redundancy(file: str, section_title: str, threshold: float):
    """Detecta redundancias en una sección"""
    console = Console()

    try:
        # 1. Cargar documento
        content = load_markdown(Path(file))
        document = parse_markdown(content)

        # 2. Encontrar sección
        section = document.find_section(section_title)

        # 3. Analizar con LLM
        llm = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
        redundancies = find_redundancies(section, llm, threshold)

        if not redundancies:
            console.print("✓ No se encontraron redundancias", style="green")
            return

        # 4. Mostrar resultados con Rich
        for i, red in enumerate(redundancies, 1):
            table = Table(title=f"Redundancia #{i}")
            table.add_row(f"Similitud: {red.similarity_score:.0%}")
            table.add_row(f"Razón: {red.reasoning}")
            console.print(table)

            # 5. Preguntar al humano
            if Confirm.ask("¿Ver sugerencia de consolidación?"):
                console.print(red.suggestion)

                if Confirm.ask("¿Aplicar cambio?", default=False):
                    # 6. Aplicar
                    patch = create_patch_for_redundancy(document, section, red)
                    create_backup(Path(file))
                    apply_patch(document, patch)
                    save_markdown(Path(file), document.raw_content)
                    console.print("✓ Cambio aplicado", style="green")

    except SectionNotFoundError as e:
        console.print(f"[red]Error:[/red] Sección '{e.title}' no encontrada")
        console.print(f"Secciones disponibles: {', '.join(e.available)}")
        raise click.Abort()
```

---

## Flujo de Datos (Redundancy Detection)

```
1. Usuario ejecuta comando
   └─> CLI recibe argumentos

2. CLI carga archivo
   └─> infrastructure/file_handler.load_markdown()

3. CLI parsea contenido
   └─> domain/parser.parse_markdown()
   └─> Retorna: Document

4. CLI encuentra sección
   └─> document.find_section(title)
   └─> Retorna: Section (o lanza SectionNotFoundError)

5. CLI analiza redundancias
   └─> domain/analyzer.find_redundancies(section, llm_client)
   └─> Para cada par de párrafos:
       └─> llm_client.analyze_similarity()
       └─> Si similitud >= threshold:
           └─> llm_client.suggest_consolidation()
   └─> Retorna: list[Redundancy]

6. CLI muestra resultados (Rich)
   └─> Para cada Redundancy:
       └─> Muestra tabla con datos
       └─> Pregunta al humano (Confirm)

7. Si humano acepta:
   └─> domain/patcher.create_patch_for_redundancy()
   └─> infrastructure/file_handler.create_backup()
   └─> domain/patcher.apply_patch()
   └─> infrastructure/file_handler.save_markdown()
```

---

## Manejo de Errores

### Jerarquía de Excepciones

```python
# domain/exceptions.py

class DocumentError(Exception):
    """Base para todos los errores de dominio"""
    pass

class SectionNotFoundError(DocumentError):
    """Sección no existe en el documento"""
    def __init__(self, title: str, available: list[str]):
        self.title = title
        self.available = available
        super().__init__(f"Sección '{title}' no encontrada")

class ParseError(DocumentError):
    """Error al parsear Markdown"""
    def __init__(self, line: int, reason: str):
        self.line = line
        self.reason = reason
        super().__init__(f"Error en línea {line}: {reason}")

class PatchApplicationError(DocumentError):
    """No se pudo aplicar el patch"""
    def __init__(self, operation: PatchOperation, reason: str):
        self.operation = operation
        self.reason = reason
        super().__init__(f"No se pudo aplicar operación: {reason}")

class LLMError(DocumentError):
    """Error al comunicarse con LLM"""
    pass
```

### Propagación en CLI

```python
# El CLI captura excepciones de dominio y las presenta con Rich

try:
    # ... operaciones de dominio
except SectionNotFoundError as e:
    console.print(f"[red]✗[/red] {e}")
    console.print(f"Secciones disponibles:")
    for title in e.available:
        console.print(f"  • {title}")
    raise click.Abort()

except ParseError as e:
    console.print(f"[red]✗[/red] No se pudo parsear el archivo")
    console.print(f"Problema en línea {e.line}: {e.reason}")
    raise click.Abort()

except LLMError as e:
    console.print(f"[red]✗[/red] Error de comunicación con LLM")
    console.print(f"Detalles: {e}")
    raise click.Abort()
```

---

## Testing Strategy

### Domain Layer (sin mocks)
```python
# tests/domain/test_parser.py
def test_parse_simple_document():
    content = "# Title\n\nParagraph 1.\n\nParagraph 2."
    doc = parse_markdown(content)
    assert len(doc.sections) == 1
    assert doc.sections[0].title == "Title"
    assert len(doc.sections[0].paragraphs) == 2
```

### Infrastructure Layer (con mocks)
```python
# tests/infrastructure/test_gemini_client.py
@patch("google.generativeai.GenerativeModel")
def test_gemini_analyze_similarity(mock_model):
    client = GeminiClient(api_key="test")
    score, reason = client.analyze_similarity("text1", "text2")
    assert 0 <= score <= 1
```

### CLI Layer (integration-style)
```python
# tests/cli/test_commands.py
from click.testing import CliRunner

def test_check_redundancy_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Setup test file
        Path("test.md").write_text("# Section\n\nPara1.\n\nPara2.")

        result = runner.invoke(cli, ["check-redundancy", "test.md", "Section"])
        assert result.exit_code == 0
```

---

## Dependencias

```
# Core
pydantic>=2.0
click>=8.0
rich>=13.0

# Infrastructure
google-generativeai  # o el LLM que uses

# Dev
pytest>=7.0
pytest-cov
pytest-mock
```

---

## Notas Finales

### Por qué estas decisiones escalan

1. **Domain puro**: Fácil portar a web, API, o Streamlit
2. **LLM como dependencia**: Cambiar de Gemini a Claude sin tocar domain
3. **Patch como operaciones**: Futuro soporte de undo/redo
4. **Paragraphs pre-parseados**: Facilita análisis futuros (sentimiento, keywords, etc.)

### Qué NO hacer

- ❌ No pongas lógica de negocio en CLI
- ❌ No importes Rich, Click, o APIs en `domain/`
- ❌ No uses excepciones genéricas en domain
- ❌ No hagas que Redundancy se auto-aplique (viola principio de amplificación)
