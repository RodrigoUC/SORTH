# SORTH - Sistema de Organización de Horarios

## Descripción

SORTH es una aplicación de escritorio con interfaz gráfica para la generación automática de horarios académicos. Utiliza un **algoritmo Greedy con reintentos** y contadores incrementales para asignar grupos de cursos a aulas disponibles en tiempo real, respetando restricciones de capacidad, tipo de sala, horarios preferidos y aulas reservadas.

---

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/RodrigoUC/SORTH.git
cd SORTH/project_root
```

### 2. Crear entorno virtual
```powershell
python -m venv venv
. venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias
```powershell
pip install -r requeriments.txt
```

---

## Uso

### Interfaz Gráfica
```powershell
python gui_app.py
```

#### Pasos:
1. **Cargar archivo Excel** con las hojas `Aulas` y `Cursos`
2. **Revisar cursos importados** — cada fila del Excel es un grupo sugerido. Filtrar por código o nombre con la barra de búsqueda
3. **Agregar aulas nuevas** (opcional) — desde el botón "Agregar Aula", con tipo auto-detectado pero editable
4. **Configurar restricciones de aulas** (opcional) — reservar un aula para ciertos cursos específicos con checkboxes individuales
5. **Generar horario** con el botón verde — corre en hilo separado, la GUI no se congela
6. **Ver resultados** en las pestañas: Lista Detallada, Vista de Cuadrícula, Por Aula
7. **Editar o eliminar grupos** desde el horario generado con los botones al pie de cada tabla
8. **Exportar** a Excel (con grilla visual por aula) o CSV

---

## Formato del Excel de Entrada

El sistema lee un único archivo Excel con **dos hojas**.

> **Importante**: el sistema busca las hojas **por nombre exacto** (`Aulas` y `Cursos`), respetando mayúsculas y minúsculas. El **orden de las hojas** dentro del archivo **no importa**.

### Hoja `Aulas`
| # DE AULA | DESCRIPCIÓN | CAMPUS | CAPACIDAD | CAPACIDAD 80% |
|-----------|-------------|--------|-----------|---------------|
| LBIOCOMP  | Lab Cómputo Biología | HO | 16 | 13 |
| 601       | Aula        | HO     | 60        | 48            |

- Nombre comienza con `L` → tipo **LAB** (editable desde GUI al agregar aulas manualmente)
- Resto → tipo **REGULAR**
- Disponibilidad por defecto: **07:00–22:00**, Lunes a Sábado
- Aulas referenciadas en `Cursos` que no existen aquí → ignoradas (sin preferencia de aula)

### Hoja `Cursos`
| Curso   | Nombre de Curso  | Cantidad de Grupos | Horas     | Aula   | Días |
|---------|------------------|--------------------|-----------|--------|------|
| BIJ400  | Biología General | —                  | 0800-1030 | 0604   | L    |
| BIJ400  | Biología General | —                  | 1000-1230 | 0601   | M    |
| BIJ400L | Bio General Lab  | —                  | 0700-0930 | LBIO3B | I    |

- **Cada fila = un grupo sugerido**. Dos filas con el mismo código → 2 grupos de ese curso, cada uno con su propia sugerencia de aula/día/hora
- `Horas`: formato `HHMM-HHMM` (ej: `0800-1055`). Vacío o `-` = sin preferencia
- `Días`: `L`=Lunes, `I`=Martes, `M`=Miércoles, `J`=Jueves, `V`=Viernes, `S`=Sábado. Puede ser múltiple: `L,M`
- `Aula` y `Días` son opcionales — vacío = sin preferencia

---

## Arquitectura

```
src/
├── scheduling/              # Dominio — algoritmo y modelo
│   ├── time_model.py        # Modelo de tiempo en minutos (07:00–22:00)
│   ├── classroom.py         # Aula con ocupación por intervalos y restricciones
│   ├── group.py             # Grupo de curso (unidad de asignación)
│   ├── course.py            # Curso → genera grupos, split si duración > 270 min
│   ├── schedule_state.py    # Estado del horario (assign/unassign)
│   └── scheduler.py         # Algoritmo Greedy con reintentos + contadores O(1)
├── application/
│   └── scheduling_service.py  # Orquestador: carga datos, ejecuta scheduler
├── infrastructure/
│   ├── excel_reader.py      # Lee hojas Aulas y Cursos del Excel
│   └── schedule_exporter.py # Exporta a Excel (grilla visual) / CSV
└── gui/
    ├── main_window.py           # Ventana principal + QThread worker
    ├── course_manager_widget.py # Gestión de cursos con búsqueda
    └── schedule_viewer_widget.py# Visualización: lista, cuadrícula, por aula
```

---

## Modelo de Tiempo

El sistema trabaja con **intervalos en minutos desde medianoche**:

| Concepto | Valor |
|----------|-------|
| Inicio del día | 420 (07:00) |
| Fin del día | 1320 (22:00) |
| Almuerzo excluido | 720–780 (12:00–13:00) |
| Paso sin preferencia | 30 min |
| Paso con preferencia | 5 min (±30 min alrededor de la preferencia) |
| Fallback si ±30 min vacío | día completo con paso de 30 min |

```python
TimeModel.hhmm_to_minutes("0800")  # → 480
TimeModel.minutes_to_hhmm(655)     # → "10:55"
```

---

## Algoritmo Greedy con Reintentos

### Flujo
1. **`_build_domains`**: genera candidatos `(aula, día, start_min)` por grupo
   - Pass 1 (estricto): respeta `suggested_classroom`, `preferred_day` y `preferred_start_min`
   - Reintentos (relajado): ignora preferencias de día/hora para grupos sin asignar
   - Restricción bidireccional por grupo: si el aula sugerida del grupo está restringida, solo esa aula aplica; otros grupos del mismo curso no se ven afectados
2. **`_greedy_pass`**: ordena grupos por dominio más pequeño (MRV), asigna el mejor candidato según scoring
3. **Reintentos** (hasta 3): reconstruye dominios relajados para grupos sin asignar y repite

### Scoring de candidatos (menor = mejor)
| Prioridad | Criterio |
|-----------|----------|
| 1 | Tipo de sala coincide (LAB/REGULAR) |
| 2 | Aula sugerida del grupo coincide |
| 3 | Anti-copia: consecutivo mismo día > mismo horario > distinto día mismo horario |
| 4 | Preferencia de día y hora |
| 5 | Distribución equitativa por día (penaliza >2 grupos/día, sábado penalizado) |
| 6 | Distribución equitativa por hora (favorece ≤16:00) |
| 7 | Menor número de grupos en el aula |

### Restricciones de aula (bidireccional)
Un aula puede tener una lista de cursos permitidos (`allowed_courses`). Si está definida:
- Solo esos cursos pueden asignarse a esa aula
- Los grupos de esos cursos cuya `suggested_classroom` coincide con el aula restringida **solo** pueden ir a esa aula
- Grupos del mismo curso con distinta `suggested_classroom` no se ven afectados

---

## Detección de Tipo de Sala

| Código / Aula | Tipo | Regla |
|---------------|------|-------|
| BIJ400 | REGULAR | No termina en L ni P, sin aula sugerida LAB |
| BIJ400L | LAB | Termina en L |
| BIJ405P | LAB | Termina en P |
| BIJ405 con aula LBIOCOMP | LAB | Aula sugerida es LAB |
| LBIOCOMP (aula) | LAB | Nombre del aula comienza con L |

El tipo se infiere primero del aula sugerida en el Excel; si no hay aula sugerida, se usa el sufijo del código. El usuario puede sobreescribir el tipo al agregar aulas manualmente desde la GUI.

---

## Split de Cursos Largos

Cursos con duración > 270 min se dividen automáticamente en sesiones de 120 min:

| Duración total | Sesiones generadas |
|----------------|-------------------|
| 300 min | 120 + 120 + 60 |
| 360 min | 120 + 120 + 120 |
| 400 min | 120 + 160 (chunk mínimo 60 min) |

El usuario puede sobreescribir este comportamiento por curso desde el diálogo de edición:

| Opción | `force_split` | Comportamiento |
|--------|--------------|----------------|
| Automático (default) | `None` | Divide solo si duración > 270 min |
| Forzar división | `True` | Siempre divide en bloques de 2h |
| No dividir | `False` | Asigna completo en un solo día |

Las sesiones divididas deben cumplir:
- Días distintos entre sí
- Misma hora de inicio
- Preferentemente la misma aula

---

## GUI — Funcionalidades

### Gestión de Cursos
- Importación desde Excel con sugerencias por grupo preservadas
- Búsqueda en tiempo real por código o nombre
- Agregar/editar/eliminar cursos manualmente
- `QTimeEdit` para hora preferida (formato HH:mm, más intuitivo que spinners)
- Tipo de sala auto-detectado, editable al agregar aulas

### Horario Generado
- **Lista Detallada**: búsqueda por código/nombre, ordenamiento por cualquier columna (días en orden Lunes→Sábado, horas numéricamente), grupos sin asignar marcados en rojo
- **Vista de Cuadrícula**: grilla 07:00–22:00 en slots de 30 min, bloques con span proporcional a la duración, colores por curso
- **Por Aula**: búsqueda por aula o grupo, ordenamiento por columnas
- **Editar/Eliminar** desde cualquier tabla: botones al pie + menú contextual (clic derecho)
- Eliminar un grupo actualiza las 3 vistas en tiempo real
- **Resumen**: tarjetas KPI + tabla por día + tabla por aula + lista de sin asignar

### Restricciones de Aulas
- Diálogo con panel izquierdo (aulas checkables) y panel derecho (cursos con checkboxes individuales)
- Permite desmarcar cursos específicos (ej: excluir BIJ405 teórico, mantener solo BIJ405P)
- Botones "Marcar todos" / "Desmarcar todos"
- Restricciones persistentes entre reaperturas del diálogo

---

## Exportación

### Excel (`.xlsx`)
- Una hoja por aula con grilla visual 07:00–22:00
- Bloques de cursos con `merge_cells` proporcional a la duración
- Colores por curso (consistentes con la GUI)
- Hoja "Asignaciones": lista detallada con código, nombre, grupo, aula, día, hora inicio/fin
- Hoja "Por Aula": misma información ordenada por aula → día → hora

### CSV
- Lista detallada en formato plano, codificación UTF-8 con BOM

---

## Pruebas

```powershell
# Todos los tests
pytest

# Solo dominio scheduling
pytest tests/test_scheduling/ -v

# Con detalle de fallos
pytest --tb=short
```

---

## Generar `.exe` para Windows

```powershell
.\build_exe.ps1
```

Salida: `dist/SORTH.exe`

---

## Estructura de Archivos

```
project_root/
├── src/
│   ├── application/
│   ├── scheduling/
│   ├── infrastructure/
│   └── gui/
├── tests/
│   └── test_scheduling/
├── data/
│   ├── input/           # Excel de entrada
│   └── output/          # Resultados exportados
├── assets/              # Icono de la aplicación
├── main.py              # Punto de entrada CLI
├── gui_app.py           # Punto de entrada GUI (con stylesheet global 10pt)
└── requeriments.txt
```

---

## Historial de Cambios

### v2.0

#### Algoritmo (`src/scheduling/scheduler.py`)
- **Reemplazo de backtracking por Greedy con reintentos**: O(n) en lugar de O(n!). Elimina congelamiento con 250+ grupos
- **Contadores incrementales**: `_day_load`, `_time_load`, `_classroom_uses`, `_course_slots` actualizados en O(1) al asignar
- **Preferencias blandas**: pass 1 estricto + hasta 3 reintentos relajados para grupos sin asignar
- **Sugerencias por grupo individual**: cada grupo lleva su propia `suggested_classroom`, `preferred_day` y `preferred_start_min`
- **Restricción bidireccional por grupo**: evalúa `suggested_classroom` del grupo, no solo el `course_code`
- **Tipo de sala como preferencia de ordenamiento**: eliminado filtro duro, LAB/REGULAR es `_type_score`
- **Horario extendido a 22:00**
- **Umbral de split a 270 min**, chunk mínimo de 60 min
- **Control de split por curso**: `force_split=True` fuerza división, `force_split=False` la desactiva, `None` usa el umbral automático
- **Fallback de candidatos**: si ±30 min produce dominio vacío, usa día completo con paso 30 min

#### Lectura de Excel (`src/infrastructure/excel_reader.py`)
- Aulas inexistentes en `Cursos` ignoradas silenciosamente
- `load_courses()` acepta `known_classrooms` para filtrar referencias inválidas
- `load_course_classroom_map()` filtra con `known_classrooms`
- `group_suggestions` preserva sugerencia individual de cada fila
- Tipo de sala inferido desde el aula sugerida real, no solo del sufijo del código

#### Exportador (`src/infrastructure/schedule_exporter.py`)
- Reescrito completamente para modelo de minutos
- Grilla con `merge_cells` proporcional a duración
- Colores por curso (no por aula)
- Hojas: una por aula + "Asignaciones" + "Por Aula"

#### Aplicación (`src/application/scheduling_service.py`)
- Acepta `classrooms` externo para incluir aulas agregadas desde GUI
- Resetea `occupancy` y `allowed_courses` al inicio de cada run
- `TimeModel` con `DAY_END = 22 * 60`

#### GUI
- **`QThread` worker**: scheduler en hilo separado, barra de progreso indeterminada
- **Diálogos con header coloreado**: reemplazan `QMessageBox` en toda la app
- **Pestañas con contraste**: activa en azul `#1967D2` texto blanco, inactiva gris
- **Fuente global 10pt** via stylesheet en `gui_app.py`
- **`QTimeEdit`** para hora preferida en `CourseDialog`
- **Control de split por curso** en `CourseDialog`: combo con tres opciones (Automático / Forzar división / No dividir)
- **Tipo de aula editable** en `AddClassroomDialog` (auto-detectado pero modificable)
- **Colores por curso** en cuadrícula y Excel exportado
- **`_SortableItem`**: ordenamiento correcto de días (Lunes→Sábado) y horas (numérico)
- **Búsqueda en tiempo real**: código/nombre en Gestión de Cursos y Lista Detallada; aula/grupo en Por Aula
- **Botones Editar/Eliminar** al pie de Lista Detallada y Por Aula + menú contextual
- **Eliminar grupo**: actualiza lista, por aula y cuadrícula en tiempo real
- **Resumen**: tarjetas KPI + tablas por día/aula + grupos sin asignar
- **Restricciones**: panel con checkboxes individuales por curso por aula

### v1.0
- Versión inicial con modelo de bloques de 1 hora
- Lectura de Excel con hojas `Capacidad aulas` y `Aulas`
- Configuración de cursos mediante JSON
- Algoritmo CSP con backtracking, MRV y LCV
- Exportación a Excel y CSV

---

## Tecnologías

- **Python 3.13+**
- **PyQt6**: Interfaz gráfica
- **pandas**: Procesamiento de datos
- **openpyxl**: Lectura/escritura de Excel
- **PyInstaller**: Empaquetado como `.exe`
- **pytest**: Testing

---

## Autor

RodrigoUC
