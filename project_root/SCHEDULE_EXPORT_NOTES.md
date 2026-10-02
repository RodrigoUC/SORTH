# Consulta y exportación de horarios

## Consultar

- Buscar combina palabras y no distingue mayúsculas ni acentos. Aula, Día y Estado se aplican a las tres vistas.
- Las tablas son de solo lectura. Editar curso y Quitar del horario operan sobre la identidad seleccionada aunque se ordene la tabla.
- Las sesiones quitadas siguen visibles como Sin asignar. El resumen usa las asignaciones vigentes, no metadatos antiguos del grupo.
- La cuadrícula conserva minutos exactos, sesiones cortas y adyacentes, y muestra todos los participantes de un conflicto. Los colores por curso son estables y coinciden con Excel.

## Exportar

- **Exportar completo** conserva el comportamiento existente: exporta todas las asignaciones, sin aplicar los filtros. Ctrl+S mantiene esta acción.
- **Exportar filtrado (N)** es una acción adicional para Excel y CSV. N cuenta las sesiones asignadas que cumplen Buscar, Aula, Día y Estado. La pestaña activa y el selector local del aula de la cuadrícula no restringen esta exportación; use el filtro compartido Aula para exportar un aula.
- El diálogo de guardado y el mensaje final indican alcance y cantidad. Si no hay coincidencias asignadas, la acción filtrada está desactivada. Sin asignar no produce filas de horario ficticias.
- Generar o invalidar un horario desactiva ambas acciones. Cancelar el guardado no modifica filtros ni datos.

## Compatibilidad y seguridad

CSV conserva las siete columnas, orden, separador coma y UTF-8 con BOM. Las tablas Asignaciones y Por Aula mantienen el contrato, incluido Grupo sin sufijo de parte; la cuadrícula muestra el identificador completo de cada sesión.

Texto que pudiera interpretarse como fórmula recibe un apóstrofo inicial en ambos formatos. CR/CRLF se normalizan a LF y controles no admitidos por XML se convierten en espacios en ambos formatos. Los nombres de hojas se sanean y resuelven colisiones sin distinguir mayúsculas.

Excel incorpora encabezados repetidos al imprimir, filtros, paneles congelados, filas alternas, texto ajustado y orientación horizontal A4. Cada aula imprime solo su rango ocupado para evitar páginas iniciales vacías; no elimina sesiones ni modifica el horario. Las celdas combinadas reciben alturas explícitas.

## Verificación

Ejecutar desde project_root: `QT_QPA_PLATFORM=offscreen python -m pytest -q`.

Esta revisión se probó en Linux con Qt offscreen a 1200×800 y 960×640, con el Excel de ejemplo (249 asignaciones), nombres largos, acentos, saltos de línea, fórmulas, conflictos y sesiones de pocos minutos. La suite incluye paridad CSV/Excel, invariantes de intervalos, filtros, ordenación, selección, cancelación, eliminación, limpieza, exportación completa y filtrada, estado vacío y bloqueo por datos obsoletos/generación.

No se ha validado Microsoft Excel ni la aplicación nativa en Windows. No se reconstruyen ni publican ejecutables en este cambio.
