# SORTH - Sistema de Organización de Horarios

## Repositorio de GITHUB
https://github.com/RodrigoUC/SORTH

## Descripción del Proyecto

SORTH es una aplicación de escritorio especializada en la generación automática de horarios académicos. El sistema resuelve el problema de asignación de cursos a aulas y bloques horarios utilizando técnicas avanzadas de optimización combinatoria, permitiendo automatizar un proceso que tradicionalmente requiere intervención manual y es propenso a conflictos de programación.

## Problema y Solución

### Desafío
La creación manual de horarios académicos es un problema complejo que implica:
- Asignación de cientos de grupos de cursos a aulas limitadas
- Respeto de disponibilidad de salas
- Minimización de conflictos de horario
- Cumplimiento de restricciones múltiples (aulas reservadas, horarios preferidos, etc.)

### Solución
SORTH implementa un **algoritmo Greedy con reintentos** y heurísticas inteligentes para resolver automáticamente estas asignaciones en tiempo real, garantizando soluciones válidas respetando todas las restricciones definidas.

## Características Técnicas Principales

- **Algoritmo Greedy con reintentos** — O(n) en lugar de backtracking exponencial. Ordena grupos por dominio más pequeño (MRV), asigna el mejor candidato disponible, y hace hasta 3 reintentos con preferencias relajadas para grupos sin asignar
- **Contadores incrementales** — scoring O(1) por lookup en lugar de O(n²) por iteración sobre asignaciones
- **Modelo de intervalos en minutos** — soporta horarios con cualquier granularidad (ej: 08:00–10:55)
- **Preferencias blandas** — día y hora preferidos son sugerencias, no restricciones duras. Si no hay espacio en el slot preferido, el grupo se asigna en otro horario
- **Sugerencias por grupo individual** — cada fila del Excel puede tener su propia aula/día/hora sugerida, preservada por grupo
- **Tipo de sala como preferencia** — LAB/REGULAR es preferencia de ordenamiento, no restricción dura. Si no hay aulas del tipo preferido disponibles, se usan las del otro tipo
- **Aulas con restricción de cursos** — un aula puede reservarse exclusivamente para ciertos cursos (bidireccional)
- **Horario máximo 22:00** — soporta cursos nocturnos que terminan después de las 21:00
- **Split automático de sesiones largas** — cursos > 270 min se dividen en bloques de 120 min con chunk mínimo de 60 min. El usuario puede forzar o desactivar el split por curso desde la GUI
- **Generación reproducible** — semilla configurable para resultados deterministas
- **Persistencia de sesión** — la sesión activa (cursos, aulas, restricciones y horario generado) se guarda automáticamente en SQLite (`data/sorth_session.db`) y se ofrece restaurar al abrir la aplicación
- **Exportación** en Excel (grilla visual por aula con colores por curso) y CSV

## Formato del Excel de Entrada

El sistema lee un único archivo Excel con dos hojas:

> **Importante**: el sistema busca las hojas **por nombre exacto** (`Aulas` y `Cursos`), respetando mayúsculas y minúsculas. El orden de las hojas dentro del archivo no importa.

### Hoja `Aulas`
| # DE AULA | DESCRIPCIÓN | CAMPUS | CAPACIDAD | CAPACIDAD 80% |
|-----------|-------------|--------|-----------|---------------|
| LBIOCOMP  | Lab Cómputo Biología | HO | 16 | 13 |
| 601       | Aula        | HO     | 60        | 48            |

- Aulas que comienzan con `L` → tipo LAB (por defecto, editable en GUI)
- Resto → tipo REGULAR
- Disponibilidad por defecto: **07:00 a 22:00**, todos los días (Lunes–Sábado)
- Aulas referenciadas en `Cursos` que no existen en esta hoja → ignoradas (tratadas como sin preferencia)

### Hoja `Cursos`
| Curso   | Nombre de Curso | Cantidad de Grupos | Horas       | Aula     | Días |
|---------|-----------------|--------------------|-------------|----------|------|
| BIJ400  | Biología General | —                 | 0800-1030   | 0604     | L    |
| BIJ400  | Biología General | —                 | 1000-1230   | 0601     | M    |
| BIJ400L | Bio General Lab  | —                 | 0700-0930   | LBIO3B   | I    |

- Cada fila representa **un grupo sugerido** del curso
- Múltiples filas con el mismo código → múltiples grupos, cada uno con su propia sugerencia de aula/día/hora
- `Horas`: formato `HHMM-HHMM`. Vacío o `-` = sin preferencia
- `Días`: `L`=Lunes, `I`=Martes, `M`=Miércoles, `J`=Jueves, `V`=Viernes, `S`=Sábado
- `Aula` y `Días` son opcionales

## Tecnologías Utilizadas

- **Python 3.13+**: Lenguaje principal
- **PyQt6**: Framework para interfaz gráfica de escritorio
- **pandas**: Procesamiento y manipulación de datos
- **openpyxl**: Lectura y escritura de archivos Excel
- **sqlite3** (stdlib): Persistencia de sesión
- **PyInstaller**: Empaquetado como ejecutable de Windows
- **pytest**: Framework de testing

## Arquitectura del Sistema

El proyecto sigue una arquitectura en capas:

- **Presentation Layer** (`src/gui/`): Interfaz gráfica PyQt6 con gestión de cursos y visualización de horarios
- **Application Layer** (`src/application/`): Servicios de orquestación y lógica de negocio
- **Domain Layer** (`src/scheduling/`): Algoritmo Greedy, modelo de intervalos, representación de cursos y aulas
- **Infrastructure Layer** (`src/infrastructure/`): Lectura de Excel, exportación de resultados, persistencia SQLite de sesión

## Flujo de Operación

1. Carga del archivo Excel (hojas `Aulas` y `Cursos`)
2. Revisión y edición de cursos importados en la GUI
3. Configuración opcional de aulas con restricciones y/o agregar aulas nuevas
4. Ejecución del algoritmo de programación (en hilo separado, sin congelar la GUI)
5. Visualización de resultados en 3 vistas: Lista Detallada, Cuadrícula por Aula, Por Aula
6. Edición/eliminación de grupos directamente desde el horario generado
7. Exportación del horario finalizado

## Distribución

El sistema se empaqueta como ejecutable standalone (`SORTH.exe`) para Windows, incluyendo todas las dependencias necesarias en un único archivo sin requerimientos de instalación adicional en la máquina destino.

## Historial de Cambios

### v2.0

#### Algoritmo
- **Reemplazo de backtracking por Greedy con reintentos**: elimina el congelamiento de la GUI con datasets grandes (250+ grupos). Complejidad O(n) en lugar de O(n!)
- **Contadores incrementales**: `_day_load`, `_time_load`, `_classroom_uses`, `_course_slots` se actualizan en O(1) al asignar, eliminando el O(n²) oculto en el scoring
- **Preferencias blandas**: día y hora preferidos ya no son restricciones duras en `_build_domains`. Pass 1 respeta preferencias; reintentos las relajan para grupos sin asignar
- **Sugerencias por grupo individual**: cada grupo lleva su propia `suggested_classroom`, `preferred_day` y `preferred_start_min` desde el Excel, en lugar de compartir el valor más común del curso
- **Restricción bidireccional por grupo**: si un aula está restringida, solo aplica a los grupos cuya `suggested_classroom` coincide con esa aula, evitando forzar otros grupos del mismo curso
- **Tipo de sala como preferencia**: eliminado el filtro duro de `room_type` en `_initialize_domains` y `ScheduleState.assign`. LAB/REGULAR es ahora criterio de ordenamiento (`_type_score`)
- **Horario extendido a 22:00**: `DEFAULT_DAY_END = 22 * 60` para soportar cursos nocturnos
- **Umbral de split aumentado a 270 min**: sesiones de hasta 4.5h se asignan como bloque único. Chunk mínimo de 60 min para evitar fragmentos inútiles
- **Fallback en generación de candidatos**: si la ventana ±30 min alrededor de la preferencia no produce candidatos (ej: solapamiento con almuerzo), se usa el día completo con paso de 30 min

#### Infraestructura
- **Persistencia SQLite** (`src/infrastructure/session_repository.py`): reemplaza cualquier mecanismo anterior. La sesión completa (aulas, cursos con sugerencias por grupo, restricciones, asignaciones y metadatos) se guarda en `data/sorth_session.db`
- **Esquema relacional**: tablas `session`, `classrooms`, `courses`, `course_group_suggestions`, `restrictions`, `assignments`
- **Guardado automático**: se invoca tras cada acción relevante (cargar Excel, editar cursos, generar horario, eliminar grupo)
- **Restauración al inicio**: si existe sesión guardada con cursos, se ofrece restaurarla mediante diálogo al abrir la aplicación
- Aulas referenciadas en `Cursos` que no existen en la hoja `Aulas` se ignoran silenciosamente (tratadas como sin preferencia de aula)
- `load_course_classroom_map()` filtra correctamente con `known_classrooms`
- Sugerencias por grupo preservadas individualmente en `group_suggestions`

#### GUI
- **Hilo separado (`QThread`)**: el scheduler corre en `SchedulerWorker`, la GUI nunca se congela
- **Barra de progreso indeterminada** visible durante la generación
- **Diálogos personalizados** con header coloreado (azul/rojo) reemplazando `QMessageBox`
- **Pestañas con contraste visual**: pestaña activa en azul `#1967D2` con texto blanco en negrita
- **Fuente global 10pt** aplicada via stylesheet en `gui_app.py`
- **Agregar Aula**: tipo LAB/REGULAR se detecta automáticamente por el código pero es editable por el usuario
- **Hora preferida**: reemplazados spinners por `QTimeEdit` con formato `HH:mm`
- **Colores por curso** en vista de cuadrícula y Excel exportado (no por aula)
- **Ordenamiento por columnas** en Lista Detallada y Por Aula con `_SortableItem` para días (orden Lunes→Sábado) y horas (orden numérico)
- **Búsqueda en tiempo real**: por código/nombre en Lista Detallada; por aula/grupo en Por Aula
- **Botones Editar/Eliminar** en Lista Detallada y Por Aula + menú contextual (clic derecho)
- **Editar desde el horario**: abre `CourseDialog` del curso correspondiente en Gestión de Cursos
- **Eliminar grupo del horario**: actualiza lista, tabla por aula y cuadrícula en tiempo real
- **Resumen visual** con tarjetas KPI (grupos asignados, sin asignar, aulas, cursos), tabla por día, tabla por aula y lista de grupos sin asignar
- **Restricciones de aulas**: diálogo con panel izquierdo (aulas) y panel derecho (cursos individuales con checkbox), permite desmarcar cursos específicos

#### Exportador
- Reescrito completamente para el modelo de minutos
- Grilla visual con `merge_cells` proporcional a la duración del curso
- Colores por curso (no por aula) consistentes con la GUI

### v1.0
- Versión inicial con modelo de bloques de 1 hora
- Lectura de Excel con hojas `Capacidad aulas` y `Aulas` (disponibilidad)
- Configuración de cursos mediante JSON
- Algoritmo CSP con backtracking, MRV y LCV
- Exportación a Excel y CSV
