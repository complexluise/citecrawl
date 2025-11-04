# Guía para Colaboradores

¡Gracias por tu interés en contribuir a CiteCrawl! Este proyecto necesita personas como tú que quieran ayudar a hacer la IA más accesible y útil para bibliotecas y comunidades.

## Filosofía del Proyecto: IA Crítica y Ética

CiteCrawl no es solo una herramienta - es también un ejemplo vivo de cómo usar IA de forma responsable.

### Nuestra Misión

Este proyecto nació para ayudar a bibliotecas públicas y comunitarias en Ibero-América a integrar la inteligencia artificial de forma:
- **Crítica**: No aceptar ciegamente lo que la IA produce
- **Ética**: Ser transparente sobre limitaciones y riesgos
- **Humano-céntrica**: La IA asiste, el humano decide

### Lo que esto significa para colaboradores

Cuando contribuyes a este proyecto, **practicamos lo que predicamos**:

1. **La IA es tu asistente, no tu reemplazo**
   - Está bien usar herramientas como ChatGPT, Claude, Copilot o Gemini para ayudarte
   - Pero TÚ eres responsable del código que envías
   - Entiende lo que el código hace antes de enviarlo

2. **Sé transparente sobre el uso de IA**
   - Si la IA te ayudó significativamente con algo, menciónalo en el PR
   - Si encontraste que la IA se equivocó, compártelo - todos aprendemos

3. **La verificación es obligatoria**
   - Si la IA generó tests, ejecútalos y entiéndelos
   - Si la IA escribió documentación, verifica que sea precisa
   - Si la IA sugirió una solución, pregúntate si es la mejor opción

## Archivos de Contexto para IA: GEMINI.md y CLAUDE.md

Este proyecto incluye dos archivos especiales:

- **GEMINI.md**: Contexto para Google Gemini (la IA que usamos en la herramienta)
- **CLAUDE.md**: Contexto para Claude Code (otra IA útil para desarrollo)

### ¿Por qué existen?

Estos archivos le dan a las IAs contexto sobre cómo funciona el proyecto. Es como darle a un nuevo colaborador un manual de bienvenida. Contienen:
- Estructura del proyecto
- Comandos comunes
- Convenciones de código
- Decisiones arquitectónicas importantes

### ¿Debes actualizarlos?

Si haces cambios significativos a la arquitectura o comandos principales, considera actualizar estos archivos para que futuras personas (y IAs) entiendan mejor el proyecto.

## Configuración del Entorno de Desarrollo

### Requisitos Previos

- Python 3.6 o superior
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes rápido)
- Git

### Setup

1. **Haz un fork del repositorio** en GitHub

2. **Clona tu fork:**
   ```bash
   git clone https://github.com/tu-usuario/CiteCrawl.git
   cd CiteCrawl
   ```

3. **Crea un entorno virtual:**
   ```bash
   uv venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

4. **Instala dependencias:**
   ```bash
   uv pip install -r requirements.txt
   ```

5. **Configura las claves de API** (para correr la herramienta):

   Crea un archivo `.env` en la raíz:
   ```
   FIRECRAWL_API_KEY="tu_clave_aquí"
   GEMINI_API_KEY="tu_clave_aquí"
   ```

   > **Nota**: Las claves de API son necesarias solo si vas a probar la extracción real. Para desarrollo y tests unitarios no las necesitas.

## Metodología de Desarrollo: TDD

Este proyecto sigue **Test-Driven Development** (Desarrollo Guiado por Tests):

### El Ciclo TDD

1. 🔴 **Rojo**: Escribe un test que falle
2. 🟢 **Verde**: Escribe el código mínimo para que pase
3. 🔵 **Refactor**: Mejora el código manteniendo los tests verdes

### Ejecutar Tests

```bash
# Todos los tests
uv run pytest

# Tests con cobertura
uv run pytest --cov=citecrawl

# Tests de un módulo específico
uv run pytest tests/test_extraction.py

# Un test específico
uv run pytest tests/test_extraction.py::test_load_urls_from_csv
```

### Cobertura de Tests

Apuntamos a mantener **alta cobertura de tests** (idealmente >80%). Esto no es por perfeccionismo, sino porque:
- Los tests documentan cómo usar el código
- Previenen que cambios futuros rompan funcionalidad existente
- Dan confianza a los usuarios de que la herramienta es confiable

### Actualizar el Badge de Coverage

Después de agregar tests:

```bash
# 1. Correr tests con coverage
uv run pytest --cov=citecrawl

# 2. Generar el badge actualizado
uv run coverage-badge -o coverage.svg

# 3. Incluir el SVG en tu commit
git add coverage.svg
```

## Convenciones de Código

### Style Guide

- Seguimos [PEP 8](https://pep8.org/) para estilo de Python
- Usa nombres descriptivos de variables (mejor `csv_file_path` que `cfp`)
- Escribe docstrings para funciones públicas
- Mantén funciones pequeñas y con una sola responsabilidad

### Convenciones de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/) con emojis:

**Formato:** `<type>(<scope>): <emoji> <subject>`

**Ejemplos:**
```bash
feat(extraction): ✨ Add support for PDF files
fix(cli): 🐛 Handle missing CSV columns gracefully
docs(readme): 📝 Clarify API key setup process
test(enrichment): ✅ Add test for empty content case
refactor(models): ♻️ Simplify Publication class
chore(deps): 🔧 Update firecrawl-py to v2.0
```

**Tipos comunes:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Solo cambios en documentación
- `test`: Agregar o actualizar tests
- `refactor`: Cambio de código que no es feat ni fix
- `chore`: Cambios en build, dependencias, etc.

**Emojis:**
- ✨ `:sparkles:` - Nueva feature
- 🐛 `:bug:` - Bug fix
- 📝 `:memo:` - Documentación
- ✅ `:white_check_mark:` - Tests
- ♻️ `:recycle:` - Refactoring
- 🔧 `:wrench:` - Configuración

### Estructura de Archivos

```
CiteCrawl/
├── citecrawl/          # Código fuente principal
│   ├── cli.py          # Comandos de la CLI
│   ├── extraction.py   # Lógica de scraping
│   ├── enrichment.py   # Lógica de enriquecimiento con IA
│   ├── bibtex.py       # Generación de bibliografía
│   ├── gdocs.py        # Integración con Google Docs
│   └── models.py       # Modelos Pydantic
├── tests/              # Tests unitarios (mirror de citecrawl/)
├── data/               # Datos de ejemplo
├── output/             # Contenido extraído (gitignored)
└── .env                # Claves de API (gitignored)
```

## Workflow de Contribución

### 1. Encuentra o Crea un Issue

- Busca un issue existente que te interese
- O crea uno nuevo describiendo lo que quieres hacer
- Comenta en el issue diciendo que trabajarás en ello

### 2. Crea una Branch

```bash
# Desde main, actualiza tu repo
git checkout main
git pull upstream main

# Crea tu branch de trabajo
git checkout -b feature/descripcion-corta
# o
git checkout -b fix/descripcion-del-bug
```

### 3. Desarrolla con TDD

1. Escribe un test que falle (documenta qué quieres lograr)
2. Implementa la funcionalidad
3. Asegúrate de que todos los tests pasen
4. Refactoriza si es necesario

### 4. Commits Frecuentes

Haz commits pequeños y frecuentes con mensajes descriptivos:

```bash
git add archivo_modificado.py
git commit -m "feat(scope): ✨ Brief description"
```

### 5. Actualiza Coverage

Antes de hacer el PR:

```bash
uv run pytest --cov=citecrawl
uv run coverage-badge -o coverage.svg
git add coverage.svg
git commit -m "chore: 🔧 Update coverage badge"
```

### 6. Push y Pull Request

```bash
git push origin tu-branch

# Luego en GitHub, crea un Pull Request
```

**En tu PR, incluye:**
- Descripción clara de qué cambia y por qué
- Referencias al issue que resuelve (`Closes #123`)
- Screenshots si es relevante (para cambios en CLI)
- Nota sobre uso de IA si fue significativo

## Preguntas sobre IA y Desarrollo

### ¿Puedo usar Copilot/ChatGPT/Claude para programar?

**Sí, pero con responsabilidad:**

✅ **Está bien:**
- Pedir explicaciones de conceptos
- Generar boilerplate repetitivo
- Sugerir nombres de variables
- Ayuda con sintaxis que no recuerdas
- Generar tests basados en código existente

⚠️ **Con cuidado:**
- Aceptar soluciones completas sin entenderlas
- Copiar código que implemente lógica crítica
- Confiar en sugerencias de seguridad sin verificar

❌ **No está bien:**
- Enviar código que no entiendes
- Depender 100% de la IA sin aprender
- Ignorar problemas de seguridad que la IA introduce

### ¿Qué hago si la IA sugiere algo que parece mal?

1. **Confía en tu intuición** - Si algo se siente raro, probablemente lo es
2. **Investiga** - Busca en la documentación oficial
3. **Pregunta** - Abre una discusión en GitHub
4. **Documenta** - Si encontraste un problema común con la IA, compártelo

### ¿Debo decir si usé IA?

**Transparencia apreciada pero no obligatoria:**
- Si la IA escribió la mayoría de tu código → Menciona en el PR
- Si usaste IA para tareas pequeñas → No es necesario mencionar
- Si encontraste un bug de IA → Definitivamente comparte, es educativo

## Reportar Bugs

Si encuentras un bug, abre un issue con:

1. **Descripción clara** del problema
2. **Pasos para reproducir**
3. **Comportamiento esperado** vs. **actual**
4. **Contexto**: Tu OS, versión de Python, etc.
5. **Logs o screenshots** si son relevantes

## Proponer Nuevas Features

Antes de implementar algo grande:

1. **Abre un issue** para discutir la idea
2. **Explica el caso de uso** - ¿Qué problema resuelve?
3. **Considera alternativas** - ¿Hay formas más simples?
4. **Espera feedback** antes de escribir mucho código

Recuerda: La simplicidad es un valor del proyecto. No todas las features son necesarias.

## Código de Conducta

### Esperamos que todos:

- Sean respetuosos y empáticos
- Acepten críticas constructivas
- Se enfoquen en lo que es mejor para la comunidad
- Asuman buenas intenciones

### No toleramos:

- Lenguaje ofensivo o discriminatorio
- Ataques personales o trolling
- Acoso de cualquier tipo
- Publicar información privada de otros

## ¿Preguntas?

- Abre un issue con la etiqueta `question`
- Revisa issues existentes - quizás alguien ya preguntó
- Consulta los archivos GEMINI.md y CLAUDE.md para contexto técnico

---

**Recuerda**: Todos empezamos sin saber. Las preguntas "tontas" no existen. Tu perspectiva como nuevo colaborador es valiosa - si algo no está claro, probablemente tampoco lo esté para otros. ¡Ayúdanos a mejorar la documentación!

¡Gracias por contribuir a un proyecto que promueve el uso responsable de la IA! 🎉
