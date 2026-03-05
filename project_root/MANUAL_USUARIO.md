# Manual de Usuario - SORTH (Uso del Ejecutable)

## 1. Objetivo

SORTH permite generar horarios académicos automáticamente, asignando cursos a aulas y bloques disponibles.

## 2. Qué necesitas antes de comenzar

- El archivo `SORTH.exe`.
- Un archivo Excel con la disponibilidad de aulas.

## 3. Cómo abrir la aplicación

1. Haz doble clic en `SORTH.exe`.
2. Espera a que aparezca la ventana principal.

Si Windows muestra una advertencia de seguridad, selecciona **Más información** y luego **Ejecutar de todas formas**.

## 4. Flujo de uso paso a paso

### Paso 1: Cargar Excel

1. Haz clic en **Cargar Excel**.
2. Selecciona el archivo con aulas y disponibilidad.
3. Confirma que el nombre del archivo quede visible en la parte inferior.

### Paso 2: Registrar cursos

1. En la pestaña **Gestión de Cursos**, agrega cada curso.
2. Completa los campos principales:
   - Código del curso.
   - Nombre del curso (opcional).
   - Número de grupos.
   - Duración en bloques.
   - Aula sugerida (opcional).
   - Día preferido (opcional).
   - Hora preferida (opcional).
3. Repite el proceso para todos los cursos.

Notas:

- La aplicación puede autocompletar datos desde su configuración interna.
- El tipo de sala se detecta automáticamente según el código del curso.

### Paso 3: Configurar semilla

En la parte inferior:

- Si **Aleatorio** está desactivado, el resultado es reproducible con la misma semilla.
- Si **Aleatorio** está activado, cada ejecución puede generar una solución distinta.

### Paso 4: Generar horario

1. Haz clic en **Generar Horario**.
2. Espera el resultado.

Si se encuentra solución, se habilita la visualización y la exportación.

### Paso 5: Revisar el horario

En la pestaña **Horario Generado** tienes tres vistas:

- **Lista Detallada**.
- **Vista de Cuadrícula**.
- **Por Aula**.

También puedes usar **Ver Resumen** para ver métricas generales.

### Paso 6: Exportar resultados

1. Haz clic en **Exportar Resultados**.
2. Elige formato:
   - Excel (`.xlsx`)
   - CSV (`.csv`)
3. Guarda el archivo en la carpeta deseada.

## 5. Formato esperado del Excel

El Excel debe incluir:

1. Hoja **Capacidad aulas**
   - Código de aula y capacidad.
2. Hoja de disponibilidad
   - Bloques ocupados por aula.

Si faltan hojas o columnas, la carga puede fallar.

## 6. Problemas frecuentes

### No se pudo generar un horario válido

Posibles causas:

- Disponibilidad insuficiente de aulas.
- Muchas restricciones de día y hora.
- Bloques ocupados excesivos en el Excel.

Qué hacer:

- Reducir restricciones opcionales.
- Revisar y corregir la disponibilidad en el Excel.
- Probar otra semilla.

### Error al cargar Excel

Qué hacer:

- Verificar que el archivo no esté dañado.
- Confirmar hojas y columnas requeridas.
- Cerrar el archivo si está abierto en Excel.

### Error al exportar

Qué hacer:

- Guardar en otra carpeta.
- Cerrar el archivo de salida si ya estaba abierto.
- Verificar permisos de escritura.

## 7. Recomendaciones

- Cargar primero el Excel y luego registrar cursos.
- Mantener copia de respaldo del Excel original.
- Usar semilla fija para resultados repetibles.
- Exportar en Excel para revisión visual y en CSV para análisis.

## 8. Cierre

Para salir, cierra la ventana de la aplicación. Se recomienda exportar antes de cerrar para no perder el resultado generado.
