# Refinamiento de SORTH

## Interfaz y seguridad de la sesión

- Encabezado compacto, guía desplegable, resumen de cursos/sesiones/aulas y un estilo compartido en `src/gui/theme.py`.
- Tablas con filas alternas, búsqueda limpiable y selección estable al ordenar. Editar o eliminar usa la identidad del curso/grupo, no la posición visual de la fila.
- El horario muestra también las sesiones entre las 21:00 y 22:00.
- Generar bloquea temporalmente la edición y la importación. El trabajador recibe copias de los datos y no modifica las aulas de la interfaz.
- Cambiar cursos, aulas o restricciones invalida el horario anterior y desactiva su exportación. Una importación fallida conserva la sesión anterior.
- Los datos guardados permiten generar sin el Excel original. La semilla aleatoria se restaura y eliminar un grupo actualiza SQLite.
- La ventana espera la finalización del trabajador antes de permitir el cierre; no se cancela forzosamente un hilo.

## Organización

`main_window.py` coordina la sesión; los diálogos están en `dialogs.py`, el adaptador QThread en `scheduler_worker.py` y el estilo en `theme.py`. El servicio de aplicación aísla las aulas recibidas mediante copia profunda. Las pruebas de GUI usan una base temporal y Qt offscreen.

## Compatibilidad

Se conservan PyQt6, las hojas `Aulas`/`Cursos`, los formatos Excel/CSV y SQLite. La base recibe una migración aditiva para conservar el tamaño del curso; una base anterior sigue siendo legible y sus tamaños desconocidos permanecen en cero. No se cambia la política documentada de 07:00–22:00, umbral de división de 270 minutos o preferencia flexible de tipo de aula.

## Verificación local

Desde `project_root`, instale `requeriments.txt` en un entorno virtual y ejecute:

```bash
python -m pytest -q
python benchmark.py
python gui_app.py
```

La comparación de rendimiento excluye lectura de Excel y renderizado de Qt. Los tiempos varían según equipo y datos; la reducción medida no garantiza la misma mejora en cada caso.

## Distribución Windows

Consulte `WINDOWS_DISTRIBUTION.md`. Los EXE, ZIP y PDF históricos del repositorio no se reconstruyeron en Linux y no representan esta versión. No se debe desactivar el antivirus ni añadir exclusiones. Falta compilar, probar y, si corresponde, firmar la nueva distribución en Windows antes de publicarla como ejecutable.

### Resultado de esta revisión

- Base `07476f2`: 27 pruebas aprobadas, 10 fallidas (pruebas de APIs/fixtures antiguas y expectativas desactualizadas).
- Revisión: 113 pruebas aprobadas; compilación de módulos y `git diff --check` correctos.
- Comparación alternada, 8 ejecuciones por versión, mismo Excel y semilla: mediana de planificación 0,2512 s → 0,1870 s (25,6 % menos tiempo). Las 249 asignaciones son idénticas y se verificaron las restricciones.
- GUI comprobada con Qt offscreen en Linux a 1200×800 y 960×640, incluyendo generación real en QThread, bloqueo de edición, restauración de controles, selección tras ordenar, estado vacío y conservación de datos ante fallo de importación.
- No se ejecutó el empaquetado ni una prueba de Defender/SmartScreen en Windows; tampoco se creó una firma de código.
