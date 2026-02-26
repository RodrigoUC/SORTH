# Configuración de Cursos

## Estado Actual: Archivo de Configuración Temporal

Actualmente, los cursos se definen manualmente en el archivo `data/input/courses_config.json`.
Este es un enfoque temporal mientras se desarrolla la interfaz gráfica.

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
      "suggested_classroom": null
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

### Ejemplos de códigos y detección automática:

- **BIJ400** → REGULAR (no termina en L o P)
- **BIJ400L** → LAB (termina en L)
- **BIJ405P** → LAB (termina en P)
- **MAT101** → REGULAR

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
