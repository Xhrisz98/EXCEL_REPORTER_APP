=================================================
      Analizador de Reportes Múltiples (Python)
                 Versión 1.14
                  Por: Christian Ilbay
=================================================

Fecha: 23 de Mayo de 2025

¡Gracias por utilizar el Analizador de Reportes Múltiples! 
Esta guía te ayudará a comenzar.

-------------------------------------------------
1. ¿QUÉ HACE ESTA APLICACIÓN?
-------------------------------------------------
Esta aplicación te permite cargar archivos Excel de Inventario o Ventas,
procesar los datos, aplicar filtros, y visualizar la información de forma
agrupada. También puedes exportar los resultados a un nuevo archivo Excel
y generar un gráfico de resumen para los reportes de Ventas.

-------------------------------------------------
2. ¿QUÉ NECESITO PARA USARLA?
-------------------------------------------------
*   Computadora con Windows 10 o superior.
*   Microsoft Excel para ver los reportes exportados.

-------------------------------------------------
3. ¿CÓMO EJECUTO LA APLICACIÓN?
-------------------------------------------------
1.  Si recibiste un archivo `.zip`, primero haz clic derecho sobre él y selecciona "Extraer todo..."
    para descomprimirlo en una carpeta en tu computadora.
2.  Abre la carpeta donde está la aplicación.
3.  Busca el archivo llamado "AnalizadorReportes.exe"  y haz
    doble clic en él para iniciar la aplicación.

-------------------------------------------------
4. FORMATO IMPORTANTE DE LOS ARCHIVOS EXCEL
-------------------------------------------------
Para que la aplicación funcione correctamente, tus archivos Excel deben tener
un formato específico en la fila de encabezados.

**Importante - Fila de Encabezados:**
*   La aplicación intentará detectar automáticamente en qué fila comienzan los
    encabezados de tu tabla.
*   Si la detección automática no funciona, o si prefieres especificarla tú mismo,
    ingresa el número de la fila (contando desde 1, como lo ves en Excel) en el
    campo "Fila Encabezado (0 si auto):" antes de cargar el archivo.
    Si pones "0", se usará la detección automática.

**4.1. Para Reportes de INVENTARIO:**
   Tu archivo Excel debe tener los siguientes encabezados de columna (los nombres
   deben ser exactos, incluyendo tildes donde las haya):
    *   Categoría
    *   Subcategoria (Ejemplo: SIN tilde en la 'i')
    *   Código (Ejemplo: CON tilde)
    *   Código Catalogo (Ejemplo: SIN tilde en la 'a' de Catalogo)
    *   Nombre
    *   Serie (Si existe en tu archivo)
    *   Unidad (Si existe en tu archivo)
    *   Costo Prom
    *   Stock Mínimo (Ejemplo: CON tilde en la 'i' de Mínimo)
    *   Stock
    *   Total

**4.2. Para Reportes de VENTAS:**
   Tu archivo Excel debe tener los siguientes encabezados de columna:
    *   Tipo de Documento
    *   Mes Emisión (Ej: "Abril", "Mayo", "Ene". Se usará para construir la fecha)
    *   Día Emisión (Ej: 15, 20. Se usará para construir la fecha)
    *   Bodega
    *   Categoría Producto
    *   Código de Bien Servicio
    *   Código Catalogo de Bien Servicio
    *   Nombre de Bien Servicio
    *   Cantidad
    *   Costo Venta
    *   % Descuento
    *   Total

-------------------------------------------------
5. GUÍA RÁPIDA DE USO
-------------------------------------------------
1.  **Seleccionar Tipo de Reporte:** Elige "Inventario" o "Ventas" en el menú
    desplegable superior. Al cambiar, la "Fila Encabezado" se reseteará a "0".
2.  **Cargar Archivo:**
    *   Ingresa el número de la "Fila Encabezado" (o deja "0" para auto-detección).
    *   Haz clic en "Cargar Archivo Excel" y selecciona tu archivo.
    *   Los datos aparecerán en el área principal.
3.  **Filtrar Datos:**
    *   **Filtrar Columna:** Selecciona la columna por la que quieres filtrar.
        *   Para **Inventario**, las opciones incluyen: Todos, Categoría, Subcategoría, Código (Prefijo), Talla (antes Código Catálogo), Color (antes Nombre).
        *   Para **Ventas**, las opciones incluyen: Total General, Fecha de emisión (por Mes), Bodega, Categoría Producto, Codigo (Prefijo), Talla (antes Cod. Catalogo), Color (antes Producto).
    *   **Valor:** Selecciona el valor específico para tu filtro.
    *   La vista se actualiza automáticamente. Para quitar filtros, elige "Todos" o "Total General".
4.  **Visualización:**
    *   Los datos se muestran agrupados por un PREFIJO de código.
    *   Verás un resumen para cada prefijo y luego una tabla con los detalles.
    *   **Ordenamiento:** Usa los botones "Ascendente"/"Descendente" para ordenar la lista de PREFIJOS por su valor/venta total. Los detalles dentro de cada prefijo se ordenan automáticamente por Color/Nombre.
5.  **Exportar:**
    *   **Exportar a Excel:** Guarda el reporte actual en un archivo Excel con dos hojas (Resumen y Detalle Completo).
    *   **Exportar Gráfico:** Guarda un gráfico de barras del valor total por prefijo.

-------------------------------------------------
6. SI ALGO SALE MAL (SOLUCIÓN DE PROBLEMAS)
-------------------------------------------------
*   **Error "Columnas iniciales faltantes..."**:
    *   Verifica que el número en "Fila Encabezado" sea el correcto para tu archivo.
    *   Asegúrate de que los nombres de las columnas en tu Excel coincidan EXACTAMENTE con los listados en la sección 4 de esta guía.
*   **Error "No hay datos válidos tras la limpieza" o no se muestran datos**:
    *   Puede que las columnas clave (como "Código" o "Total") estén vacías o tengan datos incorrectos en muchas filas de tu Excel.
    *   Revisa que el formato del archivo sea el correcto.

-------------------------------------------------
7. SOPORTE
-------------------------------------------------
Si tienes preguntas o necesitas ayuda, por favor contacta a:
Ing.Christian Ilbay
Correo: ilbaychris01@gmail.com
Numero telefónico: 0998368526 
Sitio Web: https://xhrisz98.github.io/WebPortafolio---Christian-Ilbay/

¡Gracias por usar el Analizador de Reportes Múltiples!
=================================================
