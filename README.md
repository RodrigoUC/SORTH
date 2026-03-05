# SORTH - Sistema de Organización de Horarios

## Descripción del Proyecto

SORTH es una aplicación de escritorio especializada en la generación automática de horarios académicos. El sistema resuelve el problema de asignación de cursos a aulas y bloques horarios utilizando técnicas avanzadas de optimización combinatoria, permitiendo automatizar un proceso que traditionally requiere intervención manual y es propenso a conflictos de programación.

## Problema y Solución

### Desafío
La creación manual de horarios académicos es un problema complejo que implica:
- Asignación de cientos de grupos de cursos a aulas limitadas
- Respeto de disponibilidad de salas y empleados
- Minimización de conflictos de horario
- Cumplimiento de restricciones múltiples

### Solución
SORTH implementa un algoritmo de **Satisfacción de Restricciones (CSP)** con backtracking y heurísticas inteligentes para resolver automáticamente estas asignaciones en segundos, garantizando soluciones válidas y óptimas.

## Características Técnicas Principales

- Algoritmo CSP con backtracking y forward checking
- Heurísticas MRV (Minimum Remaining Values) y LCV (Least Constraining Value)
- Detección automática de tipo de sala (laboratorio vs regular)
- Soporte para restricciones opcionales (día preferido, hora preferida)
- Generación de horarios reproducibles mediante semillas configurables
- Exportación en múltiples formatos (Excel, CSV)

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
- **Domain Layer** (`src/scheduling/`): Algoritmo CSP, modelo de tiempo, representación de cursos y aulas
- **Infrastructure Layer** (`src/infrastructure/`): Lectura de Excel, exportación de resultados

## Flujo de Operación

1. Carga de disponibilidad de aulas desde archivo Excel
2. Ingreso de cursos con parámetros (duración, número de grupos, restricciones)
3. Ejecución del algoritmo de programación
4. Visualización de resultados en múltiples formatos
5. Exportación de horario finalizado

## Distribución

El sistema se empaqueta como ejecutable standalone (`SORTH.exe`) para Windows, incluyendo todas las dependencias necesarias en un único archivo sin requerimientos de instalación adicional en la máquina destino.

