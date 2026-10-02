# Revisión de licencias antes de publicar

**Estado: GPL-3.0-only aprobada para el código propio; revisión de recursos y distribución pendiente.** La licencia está en [LICENSE](../LICENSE) y su alcance en [LICENSING.md](../LICENSING.md). No debe anunciarse que todos los materiales y binarios están listos para redistribuir hasta resolver lo siguiente.

## Decisión de licencia del proyecto

El mantenedor eligió **GNU GPL v3 únicamente (`GPL-3.0-only`)** para el código propio. [Riverbank](https://www.riverbankcomputing.com/software/pyqt) ofrece PyQt bajo GPLv3 o licencia comercial. No se presupone que SORTH tenga licencia comercial de PyQt. Una licencia permisiva del código propio no elimina las obligaciones de GPL de una distribución combinada con PyQt.

El mantenedor declara haber desarrollado SORTH con ayuda de agentes de IA y aprobó GPL-3.0-only para el código propio. Esto no acredita por sí mismo derechos sobre materiales incorporados: se debe revisar su procedencia y compatibilidad. No se ha añadido una cesión, CLA ni autorización automática sobre aportes ajenos.

Referencia: [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html). Esta revisión técnica identifica decisiones pendientes; no sustituye asesoría legal cuando haya dudas de titularidad o compatibilidad.

## Dependencias principales: inventario inicial

| Componente | Licencia/fuente oficial | Comprobación pendiente para la release |
| --- | --- | --- |
| PyQt6 | [GPLv3 o comercial](https://www.riverbankcomputing.com/software/pyqt) | Incluir textos/avisos del wheel exacto y satisfacer la modalidad elegida. |
| Qt incluido por PyQt6-Qt6 | [Licencias de Qt 6 y terceros](https://doc.qt.io/qt-6/licenses-used-in-qt.html) | Inventariar módulos/plugins y avisos realmente incluidos; no asumir una licencia única. |
| pandas | [BSD-3-Clause](https://pandas.pydata.org/docs/getting_started/overview.html#license) | Conservar avisos y licencias de la versión distribuida. |
| openpyxl | [MIT/Expat](https://openpyxl.readthedocs.io/en/stable/) | Conservar texto y copyright de la versión distribuida. |
| PyInstaller | [GPL con excepción de distribución y componentes Apache](https://pyinstaller.org/en/stable/license.html) | La excepción no elimina las obligaciones de las dependencias empaquetadas. |
| Python, NumPy, SIP y otras dependencias | Metadatos y archivos de licencia de cada distribución exacta | Inventariar todo `requirements-windows.lock`, incluyendo herramientas si se redistribuyen. |
| Generación PDF y pruebas | `requirements-docs.txt`, `requirements-dev.txt` | Revisar licencias, fuentes y avisos si se incluyen en un paquete o entregable. |

Este cuadro **no es un inventario completo ni una certificación de cumplimiento**. Las versiones exactas están en los requirements y el lock; al cambiar el lock debe repetirse la revisión. Antes de la release, recopilar textos de licencia y avisos de terceros en el paquete, además de preparar el código fuente correspondiente cuando corresponda. Los enlaces de esta guía no sustituyen los textos que deban acompañar la distribución.

## Recursos que requieren evidencia

- **Icono:** `CREDITS.md` atribuye “schedule board” a MQ Studio/IconScout; `project_root/schedule-board.png` y `project_root/assets/sorth.ico` deben asociarse a la licencia del recurso concreto. Un enlace genérico o atribución por sí solos no prueban derecho de redistribución del archivo fuente, derivados o icono empaquetado. Confirmar licencia/recibo y condiciones; si no permiten esa distribución, sustituir por un recurso original o compatible autorizado.
- **PDFs académicos:** los documentos de bachillerato incluidos en `project_root/` necesitan verificar titularidad y permiso de redistribución. Su disponibilidad pública o finalidad educativa no los convierte automáticamente en recursos con licencia abierta.
- **Datos de ejemplo:** revisar hojas de cálculo, JSON, capturas y fixtures para distinguir datos propios/sintéticos de información institucional o de terceros. No reetiquetar todo el repositorio con GPL sin separar estos recursos.

## Registro que debe completar el mantenedor

Para cada recurso externo: ruta, autor/titular, URL original, versión/fecha obtenida, licencia exacta, evidencia del permiso, obligaciones de atribución y destino en fuente/binario. Si un permiso no puede verificarse, mantenerlo como bloqueo de release y pedir autorización antes de retirarlo o sustituirlo.
