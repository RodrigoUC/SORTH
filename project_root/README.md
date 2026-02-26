# SORTH - Sistema de Organización de Horarios

## Descripción

SORTH es una aplicación de escritorio con interfaz gráfica para la generación automática de horarios académicos. Utiliza un algoritmo de satisfacción de restricciones (CSP) con backtracking para asignar grupos de cursos a aulas disponibles.

## Características

✅ **Interfaz Gráfica Intuitiva** (PyQt6)
- Gestión visual de cursos
- Visualización del horario en múltiples formatos
  - 📋 Lista detallada con todos los datos
  - 📅 Vista de cuadrícula (timetable visual)
  - 🏫 Agrupado por aula
- Leyenda de colores para diferenciar aulas
- Exportación de resultados

✅ **Detección Automática de Tipo de Sala**
- Cursos terminados en 'L' o 'P' → Laboratorio
- Resto de cursos → Sala Regular

✅ **Orden de Días Garantizado**
- Los días siempre se muestran en orden: Lunes → Sábado
- Independientemente del orden en el archivo Excel

✅ **Diferenciación Visual**
- Cada aula tiene un color único en el horario
- Formato claro que muestra: Código-Grupo (Aula)
- Leyenda interactiva con colores de aulas
- Contraste optimizado para legibilidad

✅ **Exportación de Resultados**
- Excel con múltiples hojas:
  - 📅 Horario Visual (cuadrícula con colores)
  - 📋 Asignaciones detalladas
  - 🏫 Agrupado por aula
- Colores consistentes entre GUI y Excel
- Cada aula diferenciada con color único
- CSV para análisis de datos

✅ **Algoritmo CSP Optimizado**
- Backtracking con forward checking
- Heurísticas MRV (Minimum Remaining Values) y LCV (Least Constraining Value)

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
python -m pip install -r requeriments.txt
```

## Uso

### Opción 1: Interfaz Gráfica (Recomendado)

```powershell
python gui_app.py
```

#### Pasos en la GUI:

1. **Cargar archivo Excel** con capacidad y disponibilidad de aulas
   - Mensaje descriptivo indicará qué información debe contener
   
2. **Agregar cursos** en la pestaña "Gestión de Cursos":
   - Código del curso (Ej: BIJ400, BIJ400L, MAT101)
   - Nombre (opcional)
   - Número de grupos
   - Duración en bloques
   - Aula sugerida (opcional)
   
3. **Generar horario** presionando el botón verde
   
4. **Ver resultados** en la pestaña "Horario Generado":
   - 📋 **Lista Detallada**: Tabla con todos los datos
   - 📅 **Vista de Cuadrícula**: Timetable visual con colores por aula
     - Leyenda: Muestra cada aula con su color asignado
     - Orden garantizado: Lunes → Sábado
     - Cada celda muestra: Código-Grupo (Aula)
   - 🏫 **Por Aula**: Agrupado por aula y día
   
5. **Exportar** a Excel o CSV
   - Excel contiene las mismas vistas con colores
   - Listo para imprimir o compartir

### Opción 2: Línea de Comandos

```powershell
python main.py
```

Requiere:
- `data/input/test_small.xlsx` (aulas y disponibilidad)
- `data/input/courses_config.json` (configuración de cursos)

Los resultados se guardan automáticamente en `data/output/`.

## Estructura de Archivos

### Entrada

#### Excel de Aulas (`data/input/test_small.xlsx`)
Debe contener dos hojas:

1. **"Capacidad aulas"**: Información de las aulas
   - Columnas: `# DE AULA`, `CAPACIDAD`
   
2. **Hoja de disponibilidad**: Horario de disponibilidad por aula
   - Primera columna: Códigos de aula
   - Filas merged: Bloques ocupados

#### JSON de Cursos (`data/input/courses_config.json`) - Solo para CLI
```json
{
  "courses": [
    {
      "code": "BIJ400L",
      "name": "Laboratorio de Biología",
      "number_of_groups": 2,
      "duration": 3,
      "suggested_classroom": null
    }
  ]
}
```

### Salida

- **Excel**: Archivo con 3 hojas (Asignaciones, Horario Visual, Por Aula)
- **CSV**: Lista detallada de asignaciones

## Detección Automática de Tipo de Sala

El sistema detecta automáticamente el tipo de sala requerida:

| Código Curso | Tipo de Sala | Explicación |
|--------------|--------------|-------------|
| BIJ400       | REGULAR      | No termina en L o P |
| BIJ400L      | LAB          | Termina en L (Laboratorio) |
| BIJ405P      | LAB          | Termina en P (Práctica) |
| MAT101       | REGULAR      | No termina en L o P |

## Pruebas

```powershell
pytest
```

Para tests específicos:
```powershell
pytest tests/test_integration_real_excel.py -v
```

## Tecnologías

- **Python 3.13+**
- **PyQt6**: Interfaz gráfica
- **pandas**: Procesamiento de datos
- **openpyxl**: Lectura/escritura de Excel
- **pytest**: Testing

## Estructura del Proyecto

```
project_root/
├── src/
│   ├── application/         # Servicios de aplicación
│   ├── scheduling/          # Lógica de scheduling (CSP)
│   ├── infrastructure/      # Lectores y exportadores
│   └── gui/                 # Interfaz gráfica PyQt6
├── tests/                   # Pruebas unitarias
├── data/
│   ├── input/              # Archivos de entrada
│   └── output/             # Resultados generados
├── main.py                 # CLI principal
├── gui_app.py              # GUI principal
└── requeriments.txt        # Dependencias

```

## Próximas Mejoras

- [ ] Validaciones adicionales de restricciones
- [ ] Optimización del algoritmo CSP
- [ ] Importación de cursos desde Excel
- [ ] Restricciones de horario por curso
- [ ] Modo de edición manual del horario

## Licencia

[Incluir licencia aquí]

## Autor

RodrigoUC

## Soporte

Para reportar problemas o sugerencias, crear un issue en el repositorio de GitHub.
