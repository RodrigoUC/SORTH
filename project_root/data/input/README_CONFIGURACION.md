# Configuración de Cursos

## Estado Actual: Interfaz Gráfica + Archivo de Configuración

Los cursos se pueden gestionar de dos formas:
1. **Interfaz Gráfica (Recomendado)**: Usando la aplicación GUI donde puedes agregar cursos, establecer preferencias de día y hora, y visualizar el horario.
2. **Archivo JSON (Alternativo)**: Editando manualmente el archivo `data/input/courses_config.json` para casos especiales o automatización.

## Estructura del archivo JSON

```json
{
  "courses": [
    {
      "code": "MAT101",
      "name": "Matemáticas I",
      "number_of_groups": 2,
      "duration": 2,
      "room_type": "REGULAR",
      "suggested_classroom": null,
      "preferred_day": "Lunes",
      "preferred_hour": 10
    }
  ]
}
```

### Campos:

- **code** (requerido): Código único del curso (ej: "BIJ400", "BIJ400L", "MAT101")
  - Si termina en **L** o **P** → se asigna automáticamente a LAB
  - De lo contrario → sala REGULAR
- **name** (opcional): Nombre descriptivo del curso, solo para documentación
- **number_of_groups** (requerido): Cantidad de grupos/paralelos que necesita el curso
- **duration** (requerido): Duración en bloques horarios (ej: 2 = 2 bloques consecutivos)
- **room_type** (opcional): Tipo de sala requerida
  - `"REGULAR"`: Sala normal
  - `"LAB"`: Laboratorio
  - Si no se especifica, se detecta automáticamente del código
- **suggested_classroom** (opcional): Código de aula sugerida (ej: "601", "L301")
  - Usar `null` si no hay preferencia
- **preferred_day** (opcional): Día preferido de la semana para este curso
  - Valores válidos: `"Lunes"`, `"Martes"`, `"Miércoles"`, `"Jueves"`, `"Viernes"`, `"Sábado"`
  - Usar `null` o omitir si no hay preferencia
  - El scheduler intentará asignar el curso en este día (sin garantía)
- **preferred_hour** (opcional): Hora preferida de inicio (ej: 8, 10, 14)
  - Debe ser una hora válida según la disponibilidad configurada
  - Usar `null` o omitir si no hay preferencia
  - El scheduler intentará asignar el curso a esta hora (sin garantía)

### Ejemplos de códigos y detección automática:

- **BIJ400** → REGULAR (no termina en L o P)
- **BIJ400L** → LAB (termina en L)
- **BIJ405P** → LAB (termina en P)
- **MAT101** → REGULAR

## Ejemplos de Uso con Preferencias:

### Ejemplo 1: Curso sin preferencias
```json
{
  "code": "MAT101",
  "number_of_groups": 2,
  "duration": 2,
  "suggested_classroom": null
}
```
El scheduler asignará este curso según la disponibilidad general.

### Ejemplo 2: Preferencia de día solamente
```json
{
  "code": "FIS201",
  "number_of_groups": 1,
  "duration": 3,
  "preferred_day": "Miércoles"
}
```
El scheduler intentará programar este curso el miércoles, en cualquier hora disponible.

### Ejemplo 3: Preferencia de hora solamente
```json
{
  "code": "QUI301",
  "number_of_groups": 2,
  "duration": 2,
  "preferred_hour": 10
}
```
El scheduler intentará programar este curso a las 10:00, en cualquier día disponible.

### Ejemplo 4: Preferencia de día Y hora
```json
{
  "code": "BIO400L",
  "number_of_groups": 1,
  "duration": 4,
  "room_type": "LAB",
  "preferred_day": "Viernes",
  "preferred_hour": 14
}
```
El scheduler dará máxima prioridad al Viernes a las 14:00 para este laboratorio.

## Cómo usar:

1. Edita `data/input/courses_config.json`
2. Agrega/modifica los cursos según tus necesidades
3. Ejecuta el programa: `python main.py`

## Generación de Grupos:

Si defines un curso con `number_of_groups: 3`, el sistema generará automáticamente:
- MAT101-G1
- MAT101-G2
- MAT101-G3

Cada grupo se intentará asignar independientemente en el horario.

## Próximos Pasos: GUI con PyQt

En el futuro, este sistema será reemplazado por una interfaz gráfica donde podrás:
- Agregar cursos visualmente
- Editar cantidad de grupos
- Seleccionar aulas sugeridas de una lista
- Ver el horario generado en tiempo real
- Exportar resultados

---

**Nota importante**: El archivo Excel (`test_small.xlsx`) solo contiene:
- Capacidad de aulas
- Disponibilidad horaria de las aulas

**NO contiene** información de cursos. Los cursos se definen exclusivamente en el JSON.
