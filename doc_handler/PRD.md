# MVP: Editor Markdown con IA

## El problema

Escribir documentos largos en Markdown es caótico:
- No hay forma de trabajar sobre "Capítulo 3" sin navegar manualmente
- Encuentras redundancias cuando ya escribiste 50 páginas
- No hay herramientas que entiendan la estructura del documento

## La solución (v0.1)

Un script Python que:

1. **Carga un archivo .md y lo parsea en árbol de secciones**
   - Cada `#`, `##`, `###` es un nodo con su contenido
   - Puedes referirte a secciones por título o índice

2. **Detecta redundancias en una sección específica**
   - Llamas al script: `python editor.py doc.md --check-redundancy "Capítulo 2"`
   - Un LLM analiza los párrafos y encuentra repeticiones
   - Te muestra: "Párrafos 3 y 7 son 85% similares"

3. **Propone cambios con aprobación humana**
   - Te muestra un diff: texto original vs. sugerencia
   - Aceptas o rechazas
   - Solo si aceptas, actualiza el archivo

## Historias de usuario

### US-001: Parsear documento en árbol navegable
**Como** autor de documentos largos
**Quiero** que el sistema cargue mi archivo .md y lo represente como árbol de secciones
**Para** poder trabajar sobre partes específicas sin navegar manualmente

**Criterios de aceptación**:
- Parsea correctamente `#`, `##`, `###` como niveles jerárquicos
- Cada sección incluye: nivel, título, contenido, líneas de inicio/fin
- Puedo referirme a secciones por título exacto o índice numérico

### US-002: Detectar redundancias en una sección
**Como** editor de contenido
**Quiero** identificar párrafos redundantes en una sección específica
**Para** consolidar ideas y mejorar la claridad del texto

**Criterios de aceptación**:
- Comando: `check-redundancy "Título de sección"`
- Analiza solo la sección especificada (no todo el documento)
- Reporta pares de párrafos con similitud ≥70%
- Muestra un resumen claro: "Párrafos X e Y son Z% similares"

### US-003: Aplicar cambios con aprobación manual
**Como** autor
**Quiero** revisar propuestas de consolidación antes de aplicarlas
**Para** mantener control sobre mi texto y evitar cambios no deseados

**Criterios de aceptación**:
- Muestra diff lado a lado (original vs. propuesta)
- Pregunta confirmación: "¿Aplicar cambio? [s/N]"
- Solo actualiza el archivo si el usuario acepta explícitamente
- Preserva formato y espaciado del documento original

## Roadmap de Versiones

### ✅ v0.1 (MVP) - COMPLETO
- Parser de Markdown con embeddings
- Detección de redundancias (sección y documento)
- Aplicación de cambios con aprobación manual
- Batching inteligente para API de embeddings
- Cacha simple con json de archivos


### 🔮 Backlog futuro
- ❌ RAG o sugerencias de citas → v0.3
- ❌ Generar transiciones entre secciones → v0.4
- ❌ UI gráfica (Streamlit, web) → v0.5
- ❌ Reordenar secciones mediante CLI → Futuro
- ❌ Análisis lingüístico complejo (coherencia, sentimiento) → Futuro

## Criterio de éxito

Puedo hacer esto en 5 minutos:

```bash
# 1. Detectar redundancias
python -m doc_handler check-redundancy mi_tesis.md "Capítulo 2: Metodología"

# Output esperado (con Rich formatting):
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  🔍 Análisis de redundancias en "Capítulo 2: Metodología"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# ✓ Documento parseado: 8 secciones encontradas
# ⚙ Analizando sección (3 párrafos)...
#
# ⚠ Encontradas 2 redundancias:
#
# ┌─────────────────────────────────────────────────────┐
# │ Redundancia #1 • Similitud: 87%                    │
# ├─────────────────────────────────────────────────────┤
# │ Párrafo 3: "El enfoque cualitativo permite..."     │
# │ Párrafo 7: "La metodología cualitativa facilita..."│
# └─────────────────────────────────────────────────────┘
#
# Propuesta: Consolidar en párrafo 3 y eliminar párrafo 7
# ¿Ver diff completo? [s/N]

s

# Muestra diff con colores (verde/rojo)
# ¿Aplicar cambio? [s/N]

s

# ✓ Cambios aplicados a mi_tesis.md
```

## Stack técnico

- **CLI**: Click (comandos y argumentos)
- **UI**: Rich (outputs coloridos, tablas, progreso)
- **Validación**: Pydantic (modelos de datos robustos)
- **LLM**: API de tu elección (Gemini, OpenAI, etc.)

## Arquitectura en capas

Diseño modular que separa dominio de infraestructura:

```
doc_handler/
├── domain/              # Lógica de negocio (sin dependencias externas)
│   ├── models.py        # Pydantic: Document, Section, Redundancy
│   ├── parser.py        # Markdown → Document tree
│   └── analyzer.py      # Interface para análisis (protocolo)
│
├── infrastructure/      # Implementaciones concretas
│   ├── llm_analyzer.py  # Implementa analyzer con LLM real
│   └── file_handler.py  # Lee/escribe archivos
│
└── cli/                 # Interfaz de usuario
    └── commands.py      # Click commands + Rich output
```

**Principios**:
- El dominio NO conoce Click, Rich, ni APIs externas
- Puedes testear `domain/` sin mocks complejos
- Cambiar de LLM o UI no toca la lógica core
- La capa CLI orquesta: llama al dominio y renderiza con Rich

## Entregables

Para considerar v0.1 completo:

1. Script funcional que cumple el criterio de éxito
2. README con 3 ejemplos de uso
3. 5 tests que validen el parseo y la detección de redundancias

Tiempo estimado: **1 semana**.
