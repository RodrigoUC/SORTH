# SORTH - Sistema de Organización de Horarios

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
SORTH implementa un algoritmo de **Satisfacción de Restricciones (CSP)** con backtracking y heurísticas inteligentes para resolver automáticamente estas asignaciones, garantizando soluciones válidas respetando todas las restricciones definidas.

## Características Técnicas Principales

- Algoritmo CSP con backtracking, forward checking y restauración de dominios
- Heurísticas MRV (Minimum Remaining Values) y LCV (Least Constraining Value)
- **Modelo de intervalos en minutos** — soporta horarios con cualquier granularidad (ej: 08:00–10:55)
- Detección automática de tipo de sala (laboratorio vs regular) por sufijo del código del curso
- Soporte para restricciones opcionales (día preferido, hora preferida por curso)
- **Aulas con restricción de cursos** — un aula puede reservarse exclusivamente para ciertos cursos
- Generación de horarios reproducibles mediante semillas configurables
- Exportación en múltiples formatos (Excel con grillas visuales, CSV)
- Horario de almuerzo (12:00–13:00) excluido automáticamente del dominio

## Formato del Excel de Entrada

El sistema lee un único archivo Excel con dos hojas:

### Hoja `Aulas`
| # DE AULA | DESCRIPCIÓN | CAMPUS | CAPACIDAD | CAPACIDAD 80% |
|-----------|-------------|--------|-----------|---------------|
| LBIOCOMP  | Lab Cómputo Biología | HO | 16 | 13 |
| 601       | Aula        | HO     | 60        | 48            |

- Aulas que comienzan con `L` → tipo LAB
- Resto → tipo REGULAR
- Disponibilidad por defecto: **07:00 a 21:00**, todos los días (Lunes–Sábado)

### Hoja `Cursos`
| Curso   | Nombre de Curso | Cantidad de Grupos | Horas       | Aula     | Días |
|---------|-----------------|--------------------|-------------|----------|------|
| BIJ400  | Biología General | —                 | 0800-1030   | 0604     | L    |
| BIJ400L | Bio General Lab  | —                 | 0700-0930   | LBIO3B   | I    |

- Cada fila representa **un grupo sugerido** del curso
- Múltiples filas con el mismo código → múltiples grupos
- `Horas`: formato `HHMM-HHMM`. Vacío o `-` = sin preferencia
- `Días`: abreviatura `L`=Lunes, `I`=Martes, `M`=Miércoles, `J`=Jueves, `V`=Viernes, `S`=Sábado. Puede ser múltiple separado por coma (`L,M`)
- `Aula` y `Días` son opcionales

## Tecnologías Utilizadas

- **Python 3.13+**: Lenguaje principal
- **PyQt6**: Framework para interfaz gráfica de escritorio
- **pandas**: Procesamiento y manipulación de datos
- **openpyxl**: Lectura y escritura de archivos Excel
- **PyInstaller**: Empaquetado como ejecutable de Windows
- **pytest**: Framework de testing

## Arquitectura del Sistema

El proyecto sigue una arquitectura en capas:

- **Presentation Layer** (`src/gui/`): Interfaz gráfica PyQt6 con gestión de cursos y visualización de horarios
- **Application Layer** (`src/application/`): Servicios de orquestación y lógica de negocio
- **Domain Layer** (`src/scheduling/`): Algoritmo CSP, modelo de intervalos, representación de cursos y aulas
- **Infrastructure Layer** (`src/infrastructure/`): Lectura de Excel, exportación de resultados

## Flujo de Operación

1. Carga del archivo Excel (hojas `Aulas` y `Cursos`)
2. Revisión y edición de cursos importados en la GUI
3. Configuración opcional de aulas con restricciones
4. Ejecución del algoritmo de programación
5. Visualización de resultados en múltiples formatos
6. Exportación del horario finalizado

## Distribución

El sistema se empaqueta como ejecutable standalone (`SORTH.exe`) para Windows, incluyendo todas las dependencias necesarias en un único archivo sin requerimientos de instalación adicional en la máquina destino.

## Historial de Cambios

### v2.0 (en desarrollo)
- **Modelo de intervalos en minutos**: reemplaza el modelo de bloques horarios enteros. Soporta horarios con inicio/fin en cualquier minuto (ej: 08:00–10:55)
- **Nueva lectura de Excel**: hojas `Aulas` y `Cursos` con formato simplificado. Cada fila en `Cursos` = un grupo sugerido
- **Aulas con restricción de cursos**: soporte para reservar un aula exclusivamente para ciertos cursos (ej: `LBIOCOMP`)
- **Disponibilidad por defecto 07:00–21:00**: ya no se requiere hoja de disponibilidad horaria en el Excel
- **`SchedulingService` simplificado**: ya no depende de JSON de cursos, recibe cursos directamente desde la GUI o los carga del Excel

### v1.0
- Versión inicial con modelo de bloques de 1 hora
- Lectura de Excel con hojas `Capacidad aulas` y `Aulas` (disponibilidad)
- Configuración de cursos mediante JSON
- Algoritmo CSP con backtracking, MRV y LCV
- Exportación a Excel y CSV
