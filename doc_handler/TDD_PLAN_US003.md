# Plan TDD - US-003: Aplicar Cambios con Aprobación Manual

## Objetivo

Implementar sistema de modificación de archivos con aprobación del usuario siguiendo TDD: **Red** → **Green** → **Refactor**.

Permite al usuario revisar cambios propuestos (diff visual) y decidir si aplicarlos, con backup automático y preservación del formato original.

---

## Setup Inicial

```bash
# Dependencias ya instaladas:
# - pydantic, pytest, pytest-mock, rich

# No se necesitan nuevas dependencias para US-003
```

---

## Arquitectura de la Solución

### Componentes

```
doc_handler/
├── infrastructure/
│   └── file_handler.py      # NUEVO - Manejo de archivos, backup, patching
│
├── cli/
│   └── commands.py           # MODIFICAR - Añadir flujo de aprobación
│
└── domain/
    └── models.py             # Existente - Ya tenemos Redundancy
```

### Funciones principales

```python
# infrastructure/file_handler.py

def create_backup(file_path: Path) -> Path:
    """Crea backup con extensión .backup antes de modificar"""

def show_diff(original: str, modified: str, console: Console) -> None:
    """Muestra diff colorido usando Rich"""

def prompt_confirmation(console: Console) -> bool:
    """Pregunta al usuario si aplicar cambios [s/N]"""

def apply_changes(file_path: Path, new_content: str) -> None:
    """Escribe el nuevo contenido preservando formato y encoding"""

def remove_redundant_paragraph(
    content: str,
    paragraph_to_remove: Paragraph
) -> str:
    """Remueve un párrafo redundante del contenido"""
```

---

## Casos de Prueba (Diseñados ANTES de implementar)

### Sprint 1: Backup y File Operations (Ciclos 1-4)

#### Ciclo 1: create_backup - básico

**Test**: `test_create_backup_success`

**Entrada**:
```python
from pathlib import Path
import tempfile

# Crear archivo temporal
with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
    f.write("# Test\n\nContent here.")
    temp_path = Path(f.name)

backup_path = create_backup(temp_path)
```

**Salida esperada**:
```python
# Debe crear archivo.md.backup
assert backup_path.exists()
assert backup_path.suffix == '.backup'
assert backup_path.stem == temp_path.stem
assert backup_path.read_text() == "# Test\n\nContent here."
```

**Criterios validados**: ✓ Backup se crea con extensión .backup ✓ Contenido idéntico

---

#### Ciclo 2: create_backup - sobrescribe backup existente

**Test**: `test_create_backup_overwrites_existing`

**Entrada**:
```python
# Crear archivo y backup viejo
file_path = Path("test.md")
file_path.write_text("New content")
backup_old = Path("test.md.backup")
backup_old.write_text("Old backup content")

backup_path = create_backup(file_path)
```

**Salida esperada**:
```python
# Backup debe tener el contenido nuevo, no el viejo
assert backup_path.read_text() == "New content"
```

**Criterios validados**: ✓ Sobrescribe backup anterior

---

#### Ciclo 3: apply_changes - preserva encoding UTF-8

**Test**: `test_apply_changes_preserves_utf8`

**Entrada**:
```python
file_path = Path("test.md")
file_path.write_text("Original", encoding='utf-8')

new_content = "Nuevo contenido con tildes: áéíóú ñ"
apply_changes(file_path, new_content)
```

**Salida esperada**:
```python
result = file_path.read_text(encoding='utf-8')
assert result == "Nuevo contenido con tildes: áéíóú ñ"
# No debe haber errores de encoding
```

**Criterios validados**: ✓ UTF-8 preservation

---

#### Ciclo 4: apply_changes - preserva formato (líneas vacías, espaciado)

**Test**: `test_apply_changes_preserves_formatting`

**Entrada**:
```python
original = """# Title

Paragraph 1 with spaces.

Paragraph 2.


Multiple blank lines above.
"""

apply_changes(file_path, original)
```

**Salida esperada**:
```python
result = file_path.read_text()
assert result == original  # Idéntico, bit a bit
assert result.count('\n\n') == 2  # Líneas vacías preservadas
```

**Criterios validados**: ✓ Preserva espaciado y líneas vacías

---

### Sprint 2: Diff Display (Ciclos 5-7)

#### Ciclo 5: show_diff - cambios simples

**Test**: `test_show_diff_simple_change`

**Entrada**:
```python
from rich.console import Console
from io import StringIO

original = "Line 1\nLine 2\nLine 3"
modified = "Line 1\nLine 2 modified\nLine 3"

output = StringIO()
console = Console(file=output, force_terminal=True)

show_diff(original, modified, console)
captured = output.getvalue()
```

**Salida esperada**:
```python
# Debe mostrar diff colorido
assert "Line 1" in captured
assert "Line 2" in captured  # Original
assert "modified" in captured  # Cambio
assert "Line 3" in captured
# Rich usa colores ANSI
assert "\x1b[" in captured  # Códigos de color presentes
```

**Criterios validados**: ✓ Muestra diff ✓ Usa Rich para colores

---

#### Ciclo 6: show_diff - contenido largo (solo contexto relevante)

**Test**: `test_show_diff_shows_context_only`

**Entrada**:
```python
original = "\n".join([f"Line {i}" for i in range(100)])
modified = original.replace("Line 50", "Line 50 CHANGED")

show_diff(original, modified, console)
captured = output.getvalue()
```

**Salida esperada**:
```python
# Debe mostrar contexto alrededor del cambio, no todo
assert "Line 50 CHANGED" in captured
assert "Line 49" in captured or "Line 51" in captured  # Contexto
# No debe mostrar línea 1 (muy lejos del cambio)
assert "Line 1" not in captured or "..." in captured  # Truncado
```

**Criterios validados**: ✓ Contexto relevante ✓ No abruma con todo el contenido

---

#### Ciclo 7: show_diff - sin cambios

**Test**: `test_show_diff_no_changes`

**Entrada**:
```python
original = "Same content"
modified = "Same content"

show_diff(original, modified, console)
captured = output.getvalue()
```

**Salida esperada**:
```python
assert "No hay cambios" in captured or "Sin diferencias" in captured
```

**Criterios validados**: ✓ Detecta contenido idéntico

---

### Sprint 3: User Confirmation (Ciclos 8-10)

#### Ciclo 8: prompt_confirmation - usuario acepta

**Test**: `test_prompt_confirmation_user_accepts`

**Entrada**:
```python
from unittest.mock import patch

with patch('rich.console.Console.input', return_value='s'):
    result = prompt_confirmation(console)
```

**Salida esperada**:
```python
assert result is True
```

**Criterios validados**: ✓ Acepta 's'

---

#### Ciclo 9: prompt_confirmation - usuario rechaza (default)

**Test**: `test_prompt_confirmation_user_rejects_default`

**Entrada**:
```python
# Usuario presiona Enter sin escribir nada
with patch('rich.console.Console.input', return_value=''):
    result = prompt_confirmation(console)
```

**Salida esperada**:
```python
assert result is False  # Default es No
```

**Criterios validados**: ✓ Default es No

---

#### Ciclo 10: prompt_confirmation - acepta mayúscula

**Test**: `test_prompt_confirmation_accepts_uppercase`

**Entrada**:
```python
with patch('rich.console.Console.input', return_value='S'):
    result = prompt_confirmation(console)
```

**Salida esperada**:
```python
assert result is True  # 'S' también es válido
```

**Criterios validados**: ✓ Case-insensitive para 's'

---

### Sprint 4: Paragraph Removal (Ciclos 11-13)

#### Ciclo 11: remove_redundant_paragraph - párrafo en medio

**Test**: `test_remove_paragraph_middle`

**Entrada**:
```python
content = """# Section

Paragraph 1.

Paragraph 2 to remove.

Paragraph 3.
"""

paragraph = Paragraph(
    text="Paragraph 2 to remove.",
    index=1,
    line_number=5,
    embedding=None
)

result = remove_redundant_paragraph(content, paragraph)
```

**Salida esperada**:
```python
expected = """# Section

Paragraph 1.

Paragraph 3.
"""
assert result == expected
# No debe dejar líneas vacías extra
```

**Criterios validados**: ✓ Remueve párrafo ✓ Preserva formato

---

#### Ciclo 12: remove_redundant_paragraph - primer párrafo

**Test**: `test_remove_paragraph_first`

**Entrada**:
```python
content = """# Section

First paragraph to remove.

Second paragraph stays.
"""

paragraph = Paragraph(text="First paragraph to remove.", index=0, line_number=3)
result = remove_redundant_paragraph(content, paragraph)
```

**Salida esperada**:
```python
expected = """# Section

Second paragraph stays.
"""
assert result == expected
```

**Criterios validados**: ✓ Maneja primer párrafo

---

#### Ciclo 13: remove_redundant_paragraph - último párrafo

**Test**: `test_remove_paragraph_last`

**Entrada**:
```python
content = """# Section

First paragraph.

Last paragraph to remove.
"""

paragraph = Paragraph(text="Last paragraph to remove.", index=1, line_number=5)
result = remove_redundant_paragraph(content, paragraph)
```

**Salida esperada**:
```python
expected = """# Section

First paragraph.
"""
assert result == expected
# No debe dejar líneas vacías trailing
```

**Criterios validados**: ✓ Maneja último párrafo

---

### Sprint 5: Integration (Ciclos 14-16)

#### Ciclo 14: Flujo completo - usuario acepta

**Test**: `test_full_workflow_user_accepts`

**Entrada**:
```python
# Setup
file_path = Path("test.md")
original_content = """# Test

Paragraph 1.

Paragraph 2 redundant.

Paragraph 3.
"""
file_path.write_text(original_content)

paragraph_to_remove = Paragraph(text="Paragraph 2 redundant.", index=1, line_number=5)

# Mock user input
with patch('rich.console.Console.input', return_value='s'):
    # Simulate workflow
    backup = create_backup(file_path)
    new_content = remove_redundant_paragraph(original_content, paragraph_to_remove)

    show_diff(original_content, new_content, console)

    if prompt_confirmation(console):
        apply_changes(file_path, new_content)
```

**Salida esperada**:
```python
# Backup existe
assert backup.exists()
assert backup.read_text() == original_content

# Archivo modificado
result = file_path.read_text()
assert "Paragraph 2 redundant." not in result
assert "Paragraph 1." in result
assert "Paragraph 3." in result
```

**Criterios validados**: ✓ Backup creado ✓ Cambios aplicados ✓ Formato preservado

---

#### Ciclo 15: Flujo completo - usuario rechaza

**Test**: `test_full_workflow_user_rejects`

**Entrada**:
```python
file_path.write_text(original_content)

with patch('rich.console.Console.input', return_value='n'):
    backup = create_backup(file_path)
    new_content = remove_redundant_paragraph(original_content, paragraph_to_remove)

    if prompt_confirmation(console):
        apply_changes(file_path, new_content)
```

**Salida esperada**:
```python
# Archivo NO modificado
assert file_path.read_text() == original_content
# Backup se creó de todas formas
assert backup.exists()
```

**Criterios validados**: ✓ No modifica si usuario rechaza ✓ Backup existe

---

#### Ciclo 16: CLI integration - comando con propuesta de cambio

**Test**: `test_cli_propose_changes_command`

**Entrada**:
```bash
# Nuevo comando CLI
python -m doc_handler propose-fix test.md "Section" --redundancy-index 0
```

**Salida esperada**:
```
[Muestra diff]
Redundancia detectada:
  Párrafo 1 (línea 3): "Text..."
  Párrafo 2 (línea 5): "Similar text..."

Propuesta: Eliminar párrafo 2

¿Aplicar cambio? [s/N]:
```

**Criterios validados**: ✓ CLI funcional ✓ Integración end-to-end

---

## Orden de Implementación TDD

### Sprint 1: File Operations (Ciclos 1-4) - 1 día
1. ✅ Test `test_create_backup_success` (ROJO)
2. ✅ Implementar `create_backup()` (VERDE)
3. ✅ Test `test_create_backup_overwrites_existing` (ROJO)
4. ✅ Manejar sobrescritura (VERDE)
5. ✅ Test `test_apply_changes_preserves_utf8` (ROJO)
6. ✅ Implementar `apply_changes()` (VERDE)
7. ✅ Test `test_apply_changes_preserves_formatting` (ROJO)
8. ✅ Preservar formato (VERDE)
9. ✅ Refactor: extraer lógica común

**Entregable**: Backup y escritura de archivos funcionando

---

### Sprint 2: Diff Display (Ciclos 5-7) - 1 día
10. ✅ Test `test_show_diff_simple_change` (ROJO)
11. ✅ Implementar `show_diff()` con Rich (VERDE)
12. ✅ Test `test_show_diff_shows_context_only` (ROJO)
13. ✅ Implementar contexto limitado (VERDE)
14. ✅ Test `test_show_diff_no_changes` (ROJO)
15. ✅ Detectar contenido idéntico (VERDE)
16. ✅ Refactor: mejorar formato de diff

**Entregable**: Diff visual con Rich funcionando

---

### Sprint 3: User Prompts (Ciclos 8-10) - 0.5 días
17. ✅ Test `test_prompt_confirmation_user_accepts` (ROJO)
18. ✅ Implementar `prompt_confirmation()` (VERDE)
19. ✅ Test `test_prompt_confirmation_user_rejects_default` (ROJO)
20. ✅ Default a No (VERDE)
21. ✅ Test `test_prompt_confirmation_accepts_uppercase` (ROJO)
22. ✅ Case-insensitive (VERDE)

**Entregable**: Confirmación interactiva

---

### Sprint 4: Paragraph Removal (Ciclos 11-13) - 1 día
23. ✅ Test `test_remove_paragraph_middle` (ROJO)
24. ✅ Implementar `remove_redundant_paragraph()` (VERDE)
25. ✅ Test `test_remove_paragraph_first` (ROJO)
26. ✅ Manejar primer párrafo (VERDE)
27. ✅ Test `test_remove_paragraph_last` (ROJO)
28. ✅ Manejar último párrafo (VERDE)
29. ✅ Refactor: simplificar lógica de remoción

**Entregable**: Remoción de párrafos funcionando

---

### Sprint 5: Integration (Ciclos 14-16) - 1 día
30. ✅ Test `test_full_workflow_user_accepts` (ROJO)
31. ✅ Integrar todos los componentes (VERDE)
32. ✅ Test `test_full_workflow_user_rejects` (ROJO)
33. ✅ Validar flujo de rechazo (VERDE)
34. ✅ Test `test_cli_propose_changes_command` (ROJO)
35. ✅ Añadir comando CLI (VERDE)
36. ✅ Refactor: limpiar CLI commands

**Entregable**: US-003 completo end-to-end

---

## Estructura de Archivos

```
doc_handler/
├── doc_handler/
│   ├── infrastructure/
│   │   ├── embedding_analyzer.py      # Existente
│   │   └── file_handler.py            # NUEVO - US-003
│   │
│   └── cli/
│       └── commands.py                # MODIFICAR - Añadir propose-fix
│
├── tests/
│   ├── infrastructure/
│   │   ├── test_embedding_analyzer.py # Existente
│   │   └── test_file_handler.py       # NUEVO - 16 tests
│   │
│   └── cli/
│       └── test_commands_integration.py  # NUEVO - tests E2E
│
└── TDD_PLAN_US003.md                  # Este archivo
```

---

## Comandos de Testing

```bash
# Correr tests de file_handler
uv run pytest tests/infrastructure/test_file_handler.py -v

# Correr tests de integración
uv run pytest tests/cli/test_commands_integration.py -v

# Coverage específico de US-003
uv run pytest --cov=doc_handler.infrastructure.file_handler --cov-report=term-missing

# Todos los tests
uv run pytest --cov=doc_handler --cov-report=term-missing
```

---

## Checklist de Implementación

### Paso 1: Crear módulo file_handler
- [ ] Crear `infrastructure/file_handler.py`
- [ ] Crear `tests/infrastructure/test_file_handler.py`

### Paso 2: Backup (Ciclos 1-2)
- [ ] Test `test_create_backup_success` (ROJO)
- [ ] Implementar `create_backup()` (VERDE)
- [ ] Test `test_create_backup_overwrites_existing` (ROJO)
- [ ] Manejar sobrescritura (VERDE)
- [ ] `uv run pytest tests/infrastructure/test_file_handler.py::test_create_backup* -v`

### Paso 3: Apply Changes (Ciclos 3-4)
- [ ] Test `test_apply_changes_preserves_utf8` (ROJO)
- [ ] Implementar `apply_changes()` (VERDE)
- [ ] Test `test_apply_changes_preserves_formatting` (ROJO)
- [ ] Preservar formato (VERDE)
- [ ] Refactor
- [ ] `uv run pytest tests/infrastructure/test_file_handler.py::test_apply_changes* -v`

### Paso 4: Diff Display (Ciclos 5-7)
- [ ] Test `test_show_diff_simple_change` (ROJO)
- [ ] Implementar `show_diff()` con Rich (VERDE)
- [ ] Test `test_show_diff_shows_context_only` (ROJO)
- [ ] Implementar contexto (VERDE)
- [ ] Test `test_show_diff_no_changes` (ROJO)
- [ ] Detectar sin cambios (VERDE)
- [ ] Refactor
- [ ] `uv run pytest tests/infrastructure/test_file_handler.py::test_show_diff* -v`

### Paso 5: User Prompts (Ciclos 8-10)
- [ ] Test `test_prompt_confirmation_user_accepts` (ROJO)
- [ ] Implementar `prompt_confirmation()` (VERDE)
- [ ] Test `test_prompt_confirmation_user_rejects_default` (ROJO)
- [ ] Default a No (VERDE)
- [ ] Test `test_prompt_confirmation_accepts_uppercase` (ROJO)
- [ ] Case-insensitive (VERDE)
- [ ] `uv run pytest tests/infrastructure/test_file_handler.py::test_prompt* -v`

### Paso 6: Paragraph Removal (Ciclos 11-13)
- [ ] Test `test_remove_paragraph_middle` (ROJO)
- [ ] Implementar `remove_redundant_paragraph()` (VERDE)
- [ ] Test `test_remove_paragraph_first` (ROJO)
- [ ] Manejar primer párrafo (VERDE)
- [ ] Test `test_remove_paragraph_last` (ROJO)
- [ ] Manejar último párrafo (VERDE)
- [ ] Refactor
- [ ] `uv run pytest tests/infrastructure/test_file_handler.py::test_remove_paragraph* -v`

### Paso 7: Integration Tests (Ciclos 14-15)
- [ ] Test `test_full_workflow_user_accepts` (ROJO)
- [ ] Integrar componentes (VERDE)
- [ ] Test `test_full_workflow_user_rejects` (ROJO)
- [ ] Validar rechazo (VERDE)
- [ ] `uv run pytest tests/infrastructure/test_file_handler.py -v`

### Paso 8: CLI Integration (Ciclo 16)
- [ ] Diseñar comando `propose-fix`
- [ ] Test CLI integration (ROJO)
- [ ] Implementar en `cli/commands.py` (VERDE)
- [ ] Refactor
- [ ] `uv run pytest tests/cli/ -v`

### Paso 9: E2E Testing
- [ ] Test manual con archivo real
- [ ] Verificar backup se crea
- [ ] Verificar diff se muestra correctamente
- [ ] Verificar confirmación funciona
- [ ] Verificar archivo se modifica correctamente
- [ ] `uv run pytest --cov=doc_handler --cov-report=term-missing`

### Paso 10: Documentación
- [ ] Docstrings en todas las funciones públicas
- [ ] Comentarios en lógica compleja
- [ ] Actualizar README con nuevo comando
- [ ] Actualizar USER_STORIES.md (marcar US-003 como Done)

---

## Criterio de Éxito

✅ **16+ tests pasando** (13 file_handler + 3 integration mínimo)
✅ **Coverage ≥90%** en `infrastructure/file_handler.py`
✅ **CLI funcional**: Comando propose-fix ejecutable
✅ **Backup automático**: Siempre se crea antes de modificar
✅ **Confirmación obligatoria**: Default es No
✅ **Diff visual**: Muestra cambios con Rich
✅ **Formato preservado**: UTF-8, espaciado, líneas vacías
✅ **US-003 marcada como Done** en USER_STORIES.md

---

## Notas de Implementación

### Diff Display con Rich

Rich no tiene diff built-in, pero podemos usar:

```python
from rich.syntax import Syntax
from rich.columns import Columns
from difflib import unified_diff

def show_diff(original: str, modified: str, console: Console) -> None:
    """Muestra diff lado a lado usando Rich"""

    # Opción 1: Unified diff (como git diff)
    diff_lines = unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile='original',
        tofile='modified',
        lineterm=''
    )

    # Syntax highlighting para diff
    diff_text = ''.join(diff_lines)
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
    console.print(syntax)

    # Opción 2: Lado a lado (más complejo)
    # Usar Columns para mostrar original y modificado juntos
```

### Paragraph Removal Strategy

Estrategia para remover párrafos sin romper el formato:

1. **Split por líneas**
2. **Encontrar inicio del párrafo** usando `paragraph.line_number`
3. **Encontrar fin del párrafo** (siguiente línea vacía o heading)
4. **Remover líneas** del rango
5. **Join** de vuelta

```python
def remove_redundant_paragraph(content: str, paragraph: Paragraph) -> str:
    lines = content.split('\n')
    start = paragraph.line_number - 1  # 0-indexed

    # Encontrar fin del párrafo
    end = start
    while end < len(lines) and lines[end].strip():
        end += 1

    # Remover líneas [start:end] y la línea vacía siguiente
    new_lines = lines[:start] + lines[end+1:]  # +1 para línea vacía

    return '\n'.join(new_lines)
```

### CLI Command Design

Comando `propose-fix` para proponer eliminación de redundancia:

```bash
# Proponer fix para primera redundancia en sección
python -m doc_handler propose-fix file.md "Section Title" --redundancy-index 0

# O interactivo: mostrar todas las redundancias y dejar elegir
python -m doc_handler propose-fix file.md "Section Title" --interactive
```

Flujo:
1. Analizar redundancias (como check-redundancy-section)
2. Para cada redundancia, preguntar si quiere fix
3. Si dice sí, mostrar diff y pedir confirmación
4. Si confirma, aplicar cambio

---

## Próximos Pasos (después de US-003)

MVP completo! Posibles extensiones:

- **Consolidación inteligente**: En lugar de solo eliminar, fusionar contenido
- **Múltiples cambios en batch**: Aplicar varios fixes a la vez
- **Undo/Redo**: Historial de cambios
- **Preview sin aplicar**: Guardar propuesta en archivo temporal
