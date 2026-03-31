# Manual de Usuario — SORTH v2.0

## 1. ¿Qué es SORTH?

SORTH genera horarios académicos automáticamente, asignando grupos de cursos a aulas y franjas horarias disponibles. El sistema respeta preferencias de aula, día y hora, y permite configurar restricciones exclusivas por aula.

---

## 2. Qué necesitas antes de comenzar

- El archivo `SORTH.exe`.
- Un archivo Excel (`.xlsx`) con dos hojas: **`Aulas`** y **`Cursos`**.

> Los nombres de las hojas deben ser exactamente `Aulas` y `Cursos` (con mayúscula inicial). El orden de las hojas dentro del archivo no importa.

---

## 3. Cómo abrir la aplicación

1. Haz doble clic en `SORTH.exe`.
2. Espera a que aparezca la ventana principal.

Si Windows muestra una advertencia de seguridad, selecciona **Más información** → **Ejecutar de todas formas**.

---

## 4. Flujo de uso paso a paso

### Paso 1 — Cargar el archivo Excel

1. Haz clic en **📂 Cargar Excel**.
2. Selecciona el archivo `.xlsx` con las hojas `Aulas` y `Cursos`.
3. El nombre del archivo aparecerá en verde junto al botón si la carga fue exitosa.

Los cursos se importan automáticamente a la pestaña **Gestión de Cursos**.

---

### Paso 2 — Revisar y editar cursos

En la pestaña **📚 Gestión de Cursos** verás todos los cursos importados.

**Buscar cursos**: usa la barra de búsqueda para filtrar por código o nombre en tiempo real.

**Editar un curso**: selecciona la fila y haz clic en **✏️ Editar**. Puedes modificar:
- Código y nombre del curso.
- Número de grupos.
- Duración (horas + minutos).
- Aula sugerida.
- Día preferido.
- Hora preferida — activa el checkbox y selecciona la hora con el selector `HH:mm`.
- **División en días** — controla si el curso se divide en múltiples sesiones:
  - **Automático** (por defecto): se divide solo si la duración supera 4.5 horas.
  - **Forzar división**: siempre se divide en bloques de 2 horas en días distintos, sin importar la duración.
  - **No dividir**: se asigna completo en un solo día, sin importar la duración.

> El tipo de sala (LAB / REGULAR) se detecta automáticamente por el código del curso (sufijo `L` o `P` → LAB). Es solo informativo.

**Agregar un curso manualmente**: haz clic en **➕ Agregar Curso** y completa el formulario.

**Eliminar un curso**: selecciona la fila y haz clic en **🗑️ Eliminar**.

**Limpiar todo**: elimina todos los cursos de la lista con **🧹 Limpiar Todo**.

---

### Paso 3 — Agregar aulas nuevas (opcional)

Si necesitas incluir aulas que no están en el Excel:

1. Haz clic en **🏫 Agregar Aula**.
2. Completa el código, descripción, campus y capacidad.
3. El tipo (LAB / REGULAR) se detecta automáticamente por el código, pero puedes cambiarlo manualmente.
4. Haz clic en **OK**.

---

### Paso 4 — Configurar restricciones de aulas (opcional)

Permite reservar un aula exclusivamente para ciertos cursos.

1. Haz clic en **🔒 Restricciones de Aulas**.
2. En el panel izquierdo, activa el checkbox del aula que deseas restringir.
3. En el panel derecho aparecen los cursos asociados a esa aula en el Excel. Marca solo los cursos que deben usar esa aula exclusivamente.
   - Usa **Marcar todos** / **Desmarcar todos** para agilizar la selección.
4. Haz clic en **OK**.

> Cuando un aula está restringida, los grupos de los cursos marcados **solo** pueden asignarse a esa aula, y esa aula **solo** acepta esos cursos.

---

### Paso 5 — Configurar semilla (opcional)

En la barra inferior:

- **Semilla fija** (por defecto): el resultado es idéntico en cada ejecución con el mismo valor. Útil para reproducir resultados.
- **Aleatoria**: cada ejecución puede generar una distribución distinta.

---

### Paso 6 — Generar el horario

1. Haz clic en **🚀 Generar Horario**.
2. Aparece una barra de progreso animada mientras el algoritmo trabaja. La aplicación no se congela.
3. Al terminar, un diálogo muestra el resumen: grupos asignados, aulas utilizadas y cursos programados.

> Si algunos grupos no pudieron asignarse por falta de aulas disponibles, se indica en el resumen y aparecen marcados en **rojo** en la Lista Detallada.

---

### Paso 7 — Revisar el horario generado

En la pestaña **📅 Horario Generado** tienes tres vistas:

#### 📋 Lista Detallada
- Muestra todos los grupos asignados con código, nombre, aula, día y horario.
- **Buscar**: filtra por código o nombre de curso en tiempo real.
- **Ordenar**: haz clic en cualquier encabezado de columna para ordenar ascendente o descendente. Los días se ordenan en orden de semana (Lunes → Sábado).
- **Editar curso**: selecciona una fila y haz clic en **✏️ Editar Curso** para modificar el curso en Gestión de Cursos.
- **Eliminar del horario**: selecciona una fila y haz clic en **🗑️ Eliminar del Horario** para quitar ese grupo. Las tres vistas se actualizan en tiempo real.
- También puedes hacer **clic derecho** sobre una fila para acceder a estas opciones.

#### 📅 Vista de Cuadrícula
- Muestra el horario del aula seleccionada en una grilla de 07:00 a 22:00 en franjas de 30 minutos.
- Cada bloque ocupa el espacio proporcional a su duración real.
- Los colores identifican cada curso (consistentes en todas las vistas y en el Excel exportado).
- Selecciona el aula con el selector desplegable en la parte superior.

#### 🏫 Por Aula
- Lista todos los grupos ordenados por aula, día y hora.
- **Buscar**: filtra por nombre de aula o código de grupo.
- **Ordenar**: clic en encabezado de columna.
- **Editar / Eliminar**: mismos botones que en Lista Detallada.

#### 📊 Ver Resumen
Haz clic en **📊 Ver Resumen** para ver:
- Tarjetas con grupos asignados (y porcentaje), sin asignar, aulas utilizadas y cursos programados.
- Tabla de grupos por día.
- Tabla de grupos por aula (ordenada de mayor a menor carga).
- Lista de grupos sin asignar (si los hay).

---

### Paso 8 — Exportar resultados

1. Haz clic en **💾 Exportar Resultados**.
2. Elige el formato y la ubicación:
   - **Excel (`.xlsx`)**: incluye una hoja por aula con grilla visual, más hojas de lista detallada y por aula. Los colores de los cursos son consistentes con la GUI.
   - **CSV (`.csv`)**: lista detallada en formato plano.
3. Haz clic en **Guardar**.

---

## 5. Formato del Excel de entrada

### Hoja `Aulas`

| # DE AULA | DESCRIPCIÓN | CAMPUS | CAPACIDAD | CAPACIDAD 80% |
|-----------|-------------|--------|-----------|---------------|
| LBIOCOMP  | Lab Cómputo Biología | HO | 16 | 13 |
| 601       | Aula General | HO | 60 | 48 |

- Aulas cuyo código comienza con `L` → tipo **LAB**.
- El resto → tipo **REGULAR**.
- La columna `CAPACIDAD 80%` es opcional e informativa.
- Aulas referenciadas en `Cursos` que no existen aquí se ignoran (el grupo queda sin preferencia de aula).

### Hoja `Cursos`

| Curso   | Nombre de Curso  | Cantidad de Grupos | Horas     | Aula   | Días |
|---------|------------------|--------------------|-----------|--------|------|
| BIJ400  | Biología General | —                  | 0800-1030 | 0604   | L    |
| BIJ400  | Biología General | —                  | 1000-1230 | 0601   | M    |
| BIJ400L | Bio General Lab  | —                  | 0700-0930 | LBIO3B | I    |

- **Cada fila = un grupo sugerido**. Dos filas con el mismo código = 2 grupos distintos.
- `Horas`: formato `HHMM-HHMM` (ej: `0800-1055`). Vacío o `-` = sin preferencia de hora.
- `Días`: `L`=Lunes, `I`=Martes, `M`=Miércoles, `J`=Jueves, `V`=Viernes, `S`=Sábado.
- `Aula` y `Días` son opcionales.

---

## 6. Comportamiento del algoritmo

- El sistema intenta respetar las preferencias de aula, día y hora indicadas en el Excel.
- Si no hay espacio disponible en el slot preferido, el grupo se asigna en otro horario (preferencias blandas).
- El horario cubre de **07:00 a 22:00**, excluyendo el almuerzo (12:00–13:00).
- Cursos con duración mayor a 4.5 horas se dividen automáticamente en bloques de 2 horas en días distintos. Puedes cambiar este comportamiento por curso desde el campo **División en días** al editar el curso.
- El algoritmo es determinista con semilla fija: el mismo Excel + misma semilla = mismo resultado.

---

## 9. Persistencia de datos

SORTH guarda automáticamente la sesión activa en una base de datos local (`data/sorth_session.db`) cada vez que realizas una acción relevante: cargar un Excel, editar cursos, generar el horario o eliminar un grupo.

Al abrir la aplicación, si existe una sesión guardada, aparece un diálogo preguntando si deseas restaurarla. Al aceptar, se recuperan:
- Los cursos y sus configuraciones.
- Las aulas (incluyendo las agregadas manualmente).
- Las restricciones de aulas configuradas.
- El horario generado (si existía al cerrar).
- La ruta del Excel y el valor de semilla.

Si seleccionas **No**, la aplicación inicia con el estado vacío sin borrar la sesión guardada.

> La sesión se guarda localmente en el equipo. No se envía ningún dato a servicios externos.

---

## 10. Problemas frecuentes

### No se pudo generar un horario válido
**Causas posibles:**
- No hay aulas disponibles para algún tipo de curso.
- Restricciones de aula demasiado estrictas.

**Qué hacer:**
- Revisar que existan aulas suficientes en la hoja `Aulas`.
- Reducir o eliminar restricciones de aulas.
- Agregar aulas adicionales con el botón **🏫 Agregar Aula**.

### Algunos grupos quedan sin asignar
Aparecen en rojo en la Lista Detallada. Causas:
- No hay aulas disponibles en ningún horario para ese grupo.
- El aula restringida ya está completamente ocupada.

### Error al cargar Excel
**Qué hacer:**
- Verificar que las hojas se llamen exactamente `Aulas` y `Cursos` (con mayúscula inicial).
- Cerrar el archivo si está abierto en Excel.
- Verificar que el archivo no esté dañado.

### Error al exportar
**Qué hacer:**
- Cerrar el archivo de salida si ya estaba abierto en Excel.
- Guardar en otra carpeta con permisos de escritura.

---

## 11. Recomendaciones

- Cargar el Excel antes de agregar cursos manualmente para no perder los datos importados.
- Usar semilla fija para resultados reproducibles; cambiar la semilla si el resultado no es satisfactorio.
- Configurar las restricciones de aulas **antes** de generar el horario.
- Exportar el resultado si se necesita compartirlo o archivarlo — el Excel exportado es el formato definitivo.
- Mantener una copia de respaldo del Excel original.

---

## 12. Cierre

Para salir, cierra la ventana de la aplicación. La sesión se guarda automáticamente, por lo que podrás retomar el trabajo desde donde lo dejaste la próxima vez que abras SORTH.

---

## 13. Repositorio de GITHUB
https://github.com/RodrigoUC/SORTH