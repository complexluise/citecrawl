# Historias de Usuario - MVP v0.1

## US-001: Parsear documento en árbol navegable

**Como** autor de documentos largos
**Quiero** que el sistema cargue mi archivo .md y lo represente como árbol de secciones
**Para** poder trabajar sobre partes específicas sin navegar manualmente

### Criterios de aceptación

- [ ] Parsea correctamente `#`, `##`, `###`, `####`, `#####`, `######` como niveles jerárquicos (1-6)
- [ ] Cada sección incluye: nivel, título, contenido, líneas de inicio/fin
- [ ] Puedo referirme a secciones por título exacto (case-sensitive)
- [ ] Si el título no existe, muestra error claro con sugerencias
- [ ] El parser maneja correctamente:
  - Headings con caracteres especiales
  - Bloques de código que contienen `#` (no deben parsearse como headings)
  - Listas que empiezan con `#`
- [ ] El contenido de una sección incluye todo hasta el siguiente heading del mismo nivel o superior
- [ ] Cada parrafo debe tener su embedding (usa jinaai y request para llamado directo api)

### Prioridad
🔴 **ALTA** - Bloqueante para todas las demás funcionalidades

### Story Points
**5** - Complejidad media, requiere parser robusto

### Definition of Done
- Código implementado en `domain/parser.py`
- Tests unitarios cubren casos edge (código, listas, caracteres especiales)
- Documentación del modelo `Document` y `Section` en docstrings

---

# Historias de Usuario Revisadas - US-002

## US-002A: Detectar redundancias en sección específica

**Como** editor de contenido
**Quiero** identificar párrafos redundantes en una sección específica
**Para** consolidar ideas y mejorar la claridad en partes acotadas del texto

### Criterios de aceptación

- [ ] Comando: `check-redundancy-section <archivo.md> "<Título de sección>"`
- [ ] Analiza **solo** la sección especificada (no todo el documento)
- [ ] Considera como "párrafo" cualquier bloque de texto separado por línea vacía
- [ ] Reporta pares de párrafos con similitud ≥70% (similaridad coseno embeddings)
- [ ] Muestra resumen claro: "Párrafos X e Y son Z% similares"
- [ ] Usa **embeddings de Jina AI** para análisis semántico
- [ ] Si no hay redundancias, muestra mensaje positivo: "✓ No se encontraron redundancias"
- [ ] Si la sección no existe, muestra error claro con sugerencias
- [ ] Puede enviar contenido completo de la sección al LLM para análisis contextual

### Prioridad
🔴 **ALTA** - Funcionalidad core del MVP

### Story Points
**5** - Análisis basado en embeddings con scope limitado

### Definition of Done
- Implementado en `domain/analyzer.py` (interfaz) + `infrastructure/embedding_analyzer.py` (impl)
- Tests con mock de API Jina verifican la lógica de comparación
- Comando Click funcional en `cli/commands.py`
- Output usa Rich para formateo visual

---

## US-002B: Detectar redundancias en documento completo

**Como** editor de contenido
**Quiero** identificar párrafos redundantes en todo el documento
**Para** tener una visión global de contenido duplicado sin analizar sección por sección

### Criterios de aceptación

- [ ] Comando: `check-redundancy <archivo.md>`
- [ ] Analiza **todo el documento** usando únicamente embeddings (aquí vendría bien una matriz de similaridad, calcularla una vez y así disponer del analizis completo)
- [ ] Considera como "párrafo" cualquier bloque de texto separado por línea vacía
- [ ] Reporta pares de párrafos con similitud ≥70% (similaridad coseno embeddings)
- [ ] Muestra resumen general y e información de los casos top.
- [ ] **NO envía texto completo al LLM** (solo usa embeddings pre-calculados de US-001)
- [ ] Si no hay redundancias, muestra mensaje positivo: "✓ No se encontraron redundancias globales"
- [ ] Muestra estadísticas: total de párrafos analizados, pares redundantes encontrados
- [ ] Optimizado para documentos grandes (usa embeddings cacheados)

### Prioridad
🟡 **MEDIA** - Útil pero no crítico para MVP (la versión por sección es suficiente)

### Story Points
**3** - Reutiliza embeddings de US-001, solo cambia scope del análisis

### Definition of Done
- Implementado reutilizando `infrastructure/embedding_analyzer.py`
- Tests verifican eficiencia con documentos de 50+ párrafos
- Comando Click funcional en `cli/commands.py`
- Output usa Rich con agrupación visual por secciones


---

## US-003: Aplicar cambios con aprobación manual

**Como** autor
**Quiero** revisar propuestas de consolidación antes de aplicarlas
**Para** mantener control sobre mi texto y evitar cambios no deseados

### Criterios de aceptación

- [x] Muestra diff lado a lado
- [x] Pregunta confirmación: "¿Aplicar cambio? [s/N]" (default: No)
- [x] Solo actualiza el archivo si el usuario escribe explícitamente `s` o `S`
- [x] Preserva:
  - Formato original (espaciado, líneas vacías)
  - Codificación del archivo (UTF-8)
  - Estructura de headings no afectados
- [x] Backup automático antes de aplicar cambios: `archivo.md.backup`
- [x] Mensaje de éxito muestra ruta del backup: "✓ Cambios aplicados. Backup en archivo.md.backup"
- [x] Si el usuario rechaza, no modifica nada y muestra: "Cambios descartados"

### Prioridad
🟡 **MEDIA** - Importante para UX, pero puede ser simple inicialmente

### Story Points
**3** - Relativamente simple, usar Rich para prompts interactivos

### Definition of Done
- Implementado en `infrastructure/file_handler.py`
- Tests verifican que el archivo solo se modifica tras confirmación
- Tests verifican que se crea backup antes de modificar
- UI usa Rich para diff colorido

---

## Backlog (NO MVP)

Estas historias están fuera del alcance de v0.1:

### US-004: Sugerir citas desde corpus RAG
**Prioridad**: Baja | **Versión**: v0.2

### US-005: Generar transiciones entre secciones
**Prioridad**: Baja | **Versión**: v0.3

### US-006: Análisis lingüístico completo
**Prioridad**: Baja | **Versión**: Futuro

### US-007: Reordenar secciones mediante CLI
**Prioridad**: Baja | **Versión**: Futuro

---

## Resumen del Sprint

| ID     | Título                              | Prioridad | Story Points | Estado    |
|--------|-------------------------------------|-----------|--------------|-----------|
| US-001 | Parsear documento en árbol          | 🔴 ALTA   | 5            | ✅ Done   |
| US-002A| Detectar redundancias en sección   | 🔴 ALTA   | 5            | ✅ Done   |
| US-002B| Detectar redundancias en documento  | 🟡 MEDIA  | 3            | ✅ Done   |
| US-003 | Aplicar cambios con aprobación      | 🟡 MEDIA  | 3            | ✅ Done   |
| **Total** |                                  |           | **16**       | **COMPLETE** |

**Velocidad estimada**: 16 puntos en 1 semana (sprint MVP)
