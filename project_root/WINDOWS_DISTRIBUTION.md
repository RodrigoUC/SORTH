# Distribución de SORTH para Windows

## Objetivo y límites

El programa debe usarse con las protecciones de seguridad activas. Un cambio de empaquetado no demuestra que un archivo sea seguro ni garantiza que desaparezcan las alertas. Distinguir:

- **SmartScreen / aplicación no reconocida:** reputación del archivo y del editor.
- **Defender / amenaza detectada:** requiere investigar el nombre de la detección y el archivo exacto; puede ser una detección real o un falso positivo.
- **Smart App Control o política institucional:** puede bloquear una aplicación por sus propias reglas. El responsable de TI debe evaluar la distribución.

No recomendar desactivar antivirus, crear exclusiones ni omitir advertencias. Conservar el mensaje exacto, versión del producto de seguridad, versión de SORTH, origen de descarga y SHA-256 del archivo afectado.

## Preparación y compilación

Compilar en Windows desde un entorno virtual limpio, como usuario estándar. Revisar las versiones de Python, dependencias y PyInstaller antes de instalarlas. No reutilizar los ejecutables históricos del repositorio como resultado de una nueva compilación.

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\python.exe -m pip install -r requeriments.txt
# Seleccionar previamente una versión revisada y compatible de PyInstaller.
.\.venv-build\Scripts\python.exe -m pip install "pyinstaller==VERSION_REVISADA"
.\.venv-build\Scripts\python.exe -m pip freeze > build-environment.txt
```

`VERSION_REVISADA` es un marcador que debe sustituirse. Las dependencias actuales de `requeriments.txt` todavía no están fijadas: guardar el inventario ayuda a auditar una compilación, pero no hace reproducibles las instalaciones futuras. Un archivo de dependencias bloqueadas, validado en Windows, queda pendiente antes de una distribución estable.

```powershell
.\build_exe.ps1
# Alternativa opcional de archivo único:
.\build_exe.ps1 -OneFile
# Alternativa usando la especificación mantenida:
.\.venv-build\Scripts\python.exe -m PyInstaller --clean --noconfirm SORTH.spec
```

La salida predeterminada es `dist/SORTH/SORTH.exe`, acompañada de sus dependencias. Distribuir **toda** la carpeta `dist/SORTH` en un ZIP; extraerla completa antes de abrir el programa. El modo opcional de archivo único genera `dist/SORTH.exe`. Si existen ambos, no confundir el ejecutable antiguo con la salida de la compilación actual.

El script no instala ni actualiza paquetes automáticamente, detiene errores de los procesos de compilación y deshabilita UPX. Usa metadatos de `windows_version_info.txt`; actualizar la versión con cada publicación. Estos metadatos no sustituyen una firma digital. La salida local del script no está firmada automáticamente.

El modo de carpeta facilita inspeccionar las dependencias y evita la extracción temporal propia del modo de archivo único. Es una elección de empaquetado y diagnóstico; no una solución garantizada para alertas de antivirus.

## Lista de verificación de publicación

1. Ejecutar las pruebas en un entorno limpio. Guardar commit, versiones, arquitectura, registro de compilación y lista de dependencias. Revisar vulnerabilidades y licencias de las dependencias antes de redistribuir.
2. Generar desde código revisado. Excluir sesiones personales, datos privados, cachés y archivos de desarrollo del paquete. La configuración y ejemplos incluidos deben estar autorizados para distribución.
3. Probar la carpeta empaquetada como usuario estándar en Windows, sin Python instalado: abrir, importar un Excel, generar, exportar y cerrar/reabrir la sesión. Mantener Defender actualizado y activo.
4. Para publicación con editor verificado, el propietario debe obtener una identidad/certificado de firma confiable o un servicio de firma, completar su validación y aprobar cualquier coste. Firmar con Authenticode y sello de tiempo según el proveedor, usando SHA-256. Nunca guardar claves privadas o contraseñas en este repositorio. No modificar los binarios después de firmarlos.
5. Verificar la firma final con el SDK de Windows: `signtool verify /pa /all /v dist\SORTH\SORTH.exe`. Si se publica sin firma, indicarlo expresamente; no declarar editor verificado. Conservar las firmas de las dependencias de terceros.
6. Analizar la distribución final con Defender y registrar el resultado y las versiones. Descargar el paquete desde su ubicación de publicación prevista en un Windows limpio para verificar también la experiencia real de SmartScreen. Una prueba local no reproduce necesariamente la reputación de una descarga.
7. Generar el ZIP después de firmar; calcular y publicar SHA-256 del ZIP final junto con versión, notas y procedencia. Una suma de verificación comprueba integridad, no ausencia de malware. No cambiar los archivos tras calcularla.
8. Actualizar también los manuales PDF antes de publicar. Los PDF históricos y el EXE/ZIP ya presentes en el repositorio no se regeneran mediante estas correcciones y no validan esta versión.

## Si aparece una detección

Detener la publicación del archivo afectado. Revisar procedencia, entorno de compilación y dependencias antes de afirmar que es un falso positivo. Si la revisión indica una detección incorrecta, el propietario puede enviar el archivo exacto a [Microsoft Security Intelligence](https://www.microsoft.com/en-us/wdsi/filesubmission), como desarrollador, con nombre de detección, SHA-256, versión de Defender y explicación del comportamiento legítimo. El envío comparte el archivo con Microsoft y debe autorizarlo el propietario. Respetar los límites de tamaño que muestre el portal; no enviar datos de usuarios. Conservar el resultado del análisis y repetir la validación de la distribución final.

La revisión de una detección de malware no equivale a obtener reputación SmartScreen. Microsoft indica que una aplicación firmada nueva todavía puede mostrar advertencias y que los certificados EV ya no conceden reputación inmediata. Mantener una identidad de editor consistente ayuda; no existe una promesa de ausencia de alertas. La distribución mediante Microsoft Store es otra opción que requiere cuenta, preparación del paquete y revisión del propietario.

## Fuentes primarias

- [Reputación SmartScreen para desarrolladores](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/smartscreen-reputation)
- [SignTool y verificación Authenticode](https://learn.microsoft.com/en-us/windows/win32/seccrypto/signtool)
- [Envío de archivos a Microsoft](https://learn.microsoft.com/en-us/defender-xdr/submission-guide)
- [Funcionamiento de PyInstaller: carpeta y archivo único](https://pyinstaller.org/en/stable/operating-mode.html)
- [Opciones de PyInstaller, UPX y recursos de versión](https://pyinstaller.org/en/stable/usage.html)
