# SORTH - Sistema de Organización de Horarios

## Descripción

SORTH es una aplicación de escritorio con interfaz gráfica para la generación automática de horarios académicos. Utiliza un algoritmo de Satisfacción de Restricciones (CSP) con backtracking para asignar grupos de cursos a aulas disponibles, respetando restricciones de capacidad, tipo de sala, horarios preferidos y aulas reservadas.

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
2. **Revisar cursos importados** — cada fila del Excel es un grupo sugerido
3. **Configurar aulas con restricciones** (opcional) — reservar un aula para ciertos cursos
4. **Generar horario** con el botón verde
5. **Ver resultados** en las pestañas: Lista Detallada, Vista de Cuadrícula, Por Aula
6. **Exportar** a Excel o CSV

### Línea de Comandos
```powershell
python main.py
```

---

## Formato del Excel de Entrada

El sistema lee un único archivo Excel con **dos hojas**:

### Hoja `Aulas`
| # DE AULA | DESCRIPCIÓN | CAMPUS | CAPACIDAD | CAPACIDAD 80% |
|-----------|-------------|--------|-----------|---------------|
| LBIOCOMP  | Lab Cómputo Biología | HO | 16 | 13 |
| 601       | Aula        | HO     | 60        | 48            |

- Nombre comienza con `L` → tipo **LAB**
- Resto → tipo **REGULAR**
- Disponibilidad por defecto: **07:00–21:00**, Lunes a Sábado

### Hoja `Cursos`
| Curso   | Nombre de Curso  | Cantidad de Grupos | Horas     | Aula   | Días |
|---------|------------------|--------------------|-----------|--------|------|
| BIJ400  | Biología General | —                  | 0800-1030 | 0604   | L    |
| BIJ400  | Biología General | —                  | 1000-1230 | 0601   | M    |
| BIJ400L | Bio General Lab  | —                  | 0700-0930 | LBIO3B | I    |

- **Cada fila = un grupo sugerido**. Dos filas con el mismo código → 2 grupos de ese curso
- `Horas`: formato `HHMM-HHMM` (ej: `0800-1055`). Vacío o `-` = sin preferencia
- `Días`: `L`=Lunes, `I`=Martes, `M`=Miércoles, `J`=Jueves, `V`=Viernes, `S`=Sábado. Puede ser múltiple: `L,M`
- `Aula` y `Días` son opcionales — vacío = sin preferencia

---

## Arquitectura

```
src/
├── scheduling/          # Dominio — algoritmo CSP
│   ├── time_model.py    # Modelo de tiempo en minutos (07:00–21:00)
│   ├── classroom.py     # Aula con ocupación por intervalos
│   ├── group.py         # Grupo de curso (unidad de asignación CSP)
│   ├── course.py        # Curso → genera grupos, split si duración > 180 min
│   ├── schedule_state.py# Estado del horario (assign/unassign)
│   ├── scheduler.py     # Algoritmo CSP: backtracking + MRV + LCV + forward checking
│   └── assignment.py    # Dataclass de asignación
├── application/
│   └── scheduling_service.py  # Orquestador: carga datos, ejecuta scheduler
├── infrastructure/
│   ├── excel_reader.py  # Lee hojas Aulas y Cursos del Excel
│   ├── schedule_exporter.py   # Exporta a Excel/CSV
│   └── course_config_reader.py # (legacy) Lee cursos desde JSON
└── gui/
    ├── main_window.py           # Ventana principal
    ├── course_manager_widget.py # Gestión de cursos
    └── schedule_viewer_widget.py# Visualización del horario
```

---

## Modelo de Tiempo

El sistema trabaja con **intervalos en minutos desde medianoche**:

| Concepto | Valor |
|----------|-------|
| Inicio del día | 420 (07:00) |
| Fin del día | 1260 (21:00) |
| Almuerzo excluido | 720–780 (12:00–13:00) |
| Paso sin preferencia | 30 min |
| Paso con preferencia | 5 min |

Conversiones:
```python
TimeModel.hhmm_to_minutes("0800")  # → 480
TimeModel.minutes_to_hhmm(655)     # → "10:55"
```

---

## Algoritmo CSP

### Flujo
1. `_initialize_domains`: genera candidatos `(aula, día, start_min)` por grupo
   - Con preferencia de hora → paso de 5 min
   - Sin preferencia → paso de 30 min
   - Filtra: tipo de sala, capacidad, solapamiento con almuerzo, restricción de aula
2. `_backtrack`: selecciona grupo con menor dominio (MRV), ordena candidatos por heurísticas, asigna, hace forward checking, retrocede si falla
3. `_forward_check`: elimina del dominio de otros grupos las opciones que ya no son válidas tras una asignación
4. `_restore_domains`: restaura dominios al hacer backtrack

### Heurísticas de ordenamiento (menor = mejor)
| Prioridad | Criterio |
|-----------|----------|
| 0 | Coincide con día Y hora preferidos del curso |
| 1 | Coincide solo con día preferido |
| 2 | Coincide solo con hora preferida |
| 3 | Sin preferencia o sin coincidencia |
| + | Distribución equitativa por día (penaliza >2 grupos/día, sábado penalizado) |
| + | Distribución equitativa por hora (favorece ≤16:00) |
| + | Menor carga total de minutos en el aula |
| + | Menor número de grupos en el aula |
| + | Mayor factibilidad restante (LCV) |

### Restricciones de aula
Un aula puede tener una lista de cursos permitidos (`allowed_courses`). Si está definida:
- Solo esos cursos pueden asignarse a esa aula
- Esos cursos **solo** pueden ir a esa aula (restricción bidireccional)

---

## Detección de Tipo de Sala

| Código | Tipo | Regla |
|--------|------|-------|
| BIJ400 | REGULAR | No termina en L ni P |
| BIJ400L | LAB | Termina en L |
| BIJ405P | LAB | Termina en P |
| LBIOCOMP | LAB | Nombre del aula comienza con L |

---

## Split de Cursos Largos

Cursos con duración > 180 min se dividen automáticamente en sesiones de 120 min:

| Duración total | Sesiones generadas |
|----------------|--------------------|
| 240 min | 120 + 120 |
| 300 min | 120 + 120 + 60 |
| 360 min | 120 + 120 + 120 |

Las sesiones (subgrupos) deben cumplir:
- Días distintos entre sí
- Misma hora de inicio
- Preferentemente la misma aula

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
├── gui_app.py           # Punto de entrada GUI
└── requeriments.txt
```

---

## Historial de Cambios

### v2.0 (en desarrollo)

#### Dominio (`src/scheduling/`)
- **`TimeModel`**: reescrito para trabajar con minutos desde medianoche en lugar de bloques de 1 hora. Soporta cualquier granularidad de horario. Genera candidatos con paso de 5 min (con preferencia) o 30 min (sin preferencia). Excluye almuerzo 12:00–13:00 automáticamente
- **`Classroom`**: ocupación cambia de `{(day, block): bool}` a `{day: [(start_min, end_min)]}`. Agrega soporte para `allowed_courses` (restricción de cursos permitidos)
- **`Group`**: `duration` en bloques → `duration_min` en minutos. `preferred_hour` → `preferred_start_min`
- **`Course`**: `duration` → `duration_min`. Umbral de split cambia de 3 bloques a 180 min. Chunks de split: 120 min
- **`ScheduleState`**: `assignments` ahora almacena `(classroom, day, start_min, end_min)`. Valida solapamiento de intervalos, almuerzo y restricciones de aula
- **`Scheduler`**: toda la lógica CSP adaptada a intervalos de minutos. Heurísticas mantenidas y adaptadas

#### Infraestructura (`src/infrastructure/`)
- **`ExcelReader`**: reescrito completamente. Lee hoja `Aulas` (reemplaza `Capacidad aulas`) y hoja `Cursos` (cada fila = un grupo sugerido). Parsea `Horas` en formato `HHMM-HHMM`. Traduce abreviaturas de días (`L`, `I`, `M`, `J`, `V`, `S`). Nuevo método `load_course_classroom_map()` para restricciones de aula

#### Aplicación (`src/application/`)
- **`SchedulingService`**: ya no depende de JSON de cursos. Recibe `courses` y `classroom_restrictions` como parámetros opcionales. Usa `TimeModel.default()` (07:00–21:00)

#### Tests
- Todos los tests de `test_scheduling/` reescritos para el nuevo modelo de intervalos (26 tests, todos pasando)

### v1.0
- Versión inicial con modelo de bloques de 1 hora
- Lectura de Excel con hojas `Capacidad aulas` y `Aulas` (disponibilidad horaria)
- Configuración de cursos mediante JSON (`courses_config.json`)
- Algoritmo CSP con backtracking, MRV y LCV
- Exportación a Excel (con grillas visuales por aula) y CSV
- GUI con gestión de cursos y visualización en 3 vistas

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
