# PRD — Plataforma Inteligente de Escritura en Markdown (Versión depurada)

## 1) **Visión y Metas**

### **Visión**

Crear una plataforma moderna para escribir en Markdown con apoyo de IA, donde el documento deje de ser “texto plano” y se convierta en un **objeto estructurado e inteligente** que permite analizar, editar y mejorar contenidos con control del autor.
El editor debe permitir al usuario *pensar, reescribir, depurar y conectar secciones* con fluidez, apoyándose en IA solo cuando agrega valor real.

### **Metas del MVP**

* Representar un archivo Markdown como un **árbol navegable de secciones**.
* Permitir operaciones inteligentes sobre partes específicas del documento (capítulos, secciones, párrafos).
* Detectar **redundancias**, proponer síntesis y permitir aplicar cambios con control humano.
* Generar o mejorar **continuidad narrativa** entre secciones (transiciones).
* Integrar RAG para sugerir **citas o fuentes** según el contenido.
* Exponer estas capacidades de forma usable **por humanos y también como herramientas para un agente de IA**.

### **No-Metas del MVP**

* Edición colaborativa en tiempo real.
* Gestión avanzada de bibliografías, estilos o compilación .bib → PDF.
* Control de versiones complejo (se usará un modelo simple).

---

## 2) **Personas (Usuarios objetivo)**

| Persona                                  | Motivación                                               | Necesidad principal                                                          |
| ---------------------------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| **Autor/a** (académico, técnico, ensayo) | Escribir con claridad, coherencia y buen flujo narrativo | Un entorno que facilite estructurar ideas, mejorar texto, evitar redundancia |
| **Editor/a**                             | Curar contenido para publicación o calidad               | Herramientas para diagnóstico, síntesis, revisión y aplicación de mejoras    |
| **Investigador/a**                       | Respaldar ideas con fuentes y rigor                      | Integrar citas y referencias fácilmente desde un corpus de conocimiento      |

---

## 3) **Historias de Usuario (Agile — con valor)**

> Formato: **Como [usuario], quiero [acción/resultado], para [valor/beneficio].**

### **Estructura y navegación del documento**

1. **Como autor**, quiero ver el documento como un *índice estructurado por capítulos y secciones*, **para orientarme rápidamente y entender el flujo global del texto**.
2. **Como editor**, quiero seleccionar una sección desde el índice y trabajar únicamente sobre ella, **para concentrarme sin distracciones y mejorar su calidad**.
3. **Como autor**, quiero poder reordenar secciones fácilmente, **para reorganizar la lógica o narrativa sin perder tiempo con cortes y pegados manuales**.

### **Edición asistida por IA**

4. **Como editor**, quiero que el sistema detecte redundancias dentro de un capítulo o sección, **para consolidar ideas repetidas y mejorar la claridad del texto**.
5. **Como autor**, quiero recibir propuestas de reescritura que mantengan mi estilo, **para mejorar calidad sin perder mi voz propia**.
6. **Como autor**, quiero que el sistema genere transiciones entre dos secciones, **para lograr una lectura fluida y coherente**.
7. **Como autor**, quiero acceder a un tablero de análisis lingüístico y semántico de mi texto (coherencia, legibilidad, sentimiento y diversidad léxica), **para obtener insights objetivos que me permitan decidir estratégicamente cómo mejorar mi escritura**.

### **RAG y fuentes**

8. **Como investigador**, quiero obtener sugerencias de fuentes relevantes para una sección específica, **para respaldar afirmaciones con evidencia y aumentar rigor**.
9. **Como autor académico**, quiero insertar citas sugeridas en el formato @bibkey en el punto adecuado del texto, **para mantener consistencia y rapidez al citar**.

### **Operaciones estructurales**

10. **Como editor**, quiero insertar contenido *antes o después de un título específico*, **para expandir ideas sin alterar manualmente la estructura**.
11. **Como autor**, quiero fusionar dos secciones relacionadas, **para evitar fragmentación y mejorar cohesión temática**.

---

## 4) **Alcance Funcional del MVP (Qué sí y qué no)**

### **Incluido**

| Área                    | Funciones esenciales del MVP                                                                 |
| ----------------------- | -------------------------------------------------------------------------------------------- |
| **Estructura Markdown** | Cargar archivo · Visualizar árbol · Navegar y seleccionar secciones                          |
| **Operaciones básicas** | Extraer, mover, insertar y fusionar secciones; insertar contenido antes/después de un título |
| **IA – Edición**        | Detección de redundancias · Propuestas de síntesis · Generación de transiciones              |
| **IA – RAG**            | Sugerencia de fuentes y citas según el contenido de una sección                              |
| **Control del autor**   | Vista previa de cambios · Aprobación manual antes de aplicar modificaciones                  |

### **Excluido en MVP (diferido)**

* Edición colaborativa en tiempo real
* Automatización de estilos de citación (APA, MLA…)
* Múltiples archivos simultáneos o proyectos complejos

---

## 5) **Arquitectura Propuesta (Simple, clara y centrada en el núcleo)**

### **Principio rector**

El **núcleo del producto es el Objeto Markdown**:
Debe modelar el documento como estructura editable y comprensible para IA y para el usuario.
Todo lo demás (UI, agente, RAG) **se conecta a ese núcleo**.

### **Componentes del MVP**

| Componente                           | Rol                                                                                   |
| ------------------------------------ | ------------------------------------------------------------------------------------- |
| **Core Markdown Object**             | Representa el documento como árbol de secciones; expone métodos para editarlo         |
| **Módulo de Análisis de Texto (IA)** | Identifica redundancias, propone síntesis, genera transiciones                        |
| **Módulo RAG**                       | Recupera fuentes relevantes para alimentar el texto                                   |
| **Capa de Herramientas para IA**     | Exposición de funciones del núcleo como “acciones” que un agente puede ejecutar       |
| **UI (Streamlit)**                   | Visualización del documento, acciones sobre secciones, y revisión de propuestas de IA |

### **Flujo conceptual**

1. Usuario carga documento → se convierte en Objeto Markdown estructurado.
2. Usuario navega, selecciona sección → solicita acción (humana o IA).
3. IA analiza/propone → usuario revisa → si aprueba, se actualiza el objeto.
4. Documento puede exportarse de nuevo a Markdown plano.