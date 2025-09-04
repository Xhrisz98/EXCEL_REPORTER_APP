# data_processor.py
import pandas as pd
from datetime import datetime

# --- Definiciones de Tipos de Reporte ---
REPORT_DEFINITIONS = {
    "Inventario": {
        "required_keywords_in_header": ["Categoría", "Subcategoría", "Código", "Nombre", "Stock", "Costo Prom"],
        "initial_excel_columns": [ 
            "Categoría",        # Con tilde
            "Subcategoría",     # SIN tilde
            "Código",           # Con tilde
            "Código Catálogo",  # SIN tilde en Catálogo
            "Nombre", 
            "Serie",            
            "Unidad",           
            "Costo Prom",      
            "Stock Mínimo",     # CON TILDE (Corregido)
            "Stock", 
            "Total"
        ],
        # Columnas que el DataFrame de Inventario tendrá DESPUÉS de load_and_validate_excel,
        # listas para ser pasadas a process_data_by_code_prefix o para la GUI
        "final_df_columns_for_processing": [
            "Código", "Código Catálogo", "Nombre", "Categoría", "Subcategoría", 
            "Stock", "Costo Prom", "Total" 
        ],
        # Columnas y orden que se mostrarán en la TABLA DE DETALLE de la GUI para Inventario
        "gui_detail_display_columns_ordered": [
            "Código", "Categoría", "Subcategoría", "Código Catálogo", "Nombre", 
            "Costo Prom", "Stock", "Total"
        ],
        # Mapeo para el ComboBox "Filtrar Columna por:" en la GUI para Inventario
        "filter_column_display_map": {
            "Categoría": "Categoría",
            "Subcategoría": "Subcategoría", # En GUI "Subcategoría", en Excel "Subcategoría"
            "Código": "Código",        
            "Código Catálogo": "Talla", # En GUI "Talla", en Excel "Código Catálogo"
            "Nombre": "Color"       # En GUI "Color", en Excel "Nombre"
        },
        # Columnas INTERNAS (del DataFrame después de cargar initial_excel_columns) 
        # que se ofrecerán para filtrar (usando los nombres de display del mapeo de arriba)
        "filterable_internal_columns": ["Categoría", "Subcategoría", "Código", "Código Catálogo", "Nombre"],

        "numeric_columns": ['Costo Prom', 'Stock Mínimo', 'Stock', 'Total'], # De initial_excel_columns
        "string_columns": ["Categoría", "Subcategoría", "Código", "Código Catálogo", "Nombre", "Serie", "Unidad"], # De initial_excel_columns
        "attrs_for_grouping": { 
            "total_col": "Total", 
            "main_code_col": "Código" # Columna usada para el prefijo en Inventario
        }
    },
    "Ventas": {
        "required_keywords_in_header": ["Mes Emisión", "Día Emisión", "Bodega", "Cantidad", "Total", "Código de Bien Servicio"],
        "initial_excel_columns": ["Tipo de Documento", "Mes Emisión", "Día Emisión", "Orden de Compra", "Bodega", "Categoría Producto", "Código de Bien Servicio", "Código Catalogo de Bien Servicio", "Nombre de Bien Servicio", "Cantidad", "Costo Venta", "Descripción", "% Descuento", "Total"],
        "final_df_columns": ["Fecha de emisión", "Orden de Compra", "Bodega", "Categoría Producto", "Codigo", "Cod. Catalogo", "Producto", "Cantidad", "Costo Venta", "Descripción", "% Descuento", "Total", "Unidad"],
        "numeric_columns": ['Cantidad', 'Costo Venta', '% Descuento', 'Total', 'Día Emisión'],
        "string_columns": ["Tipo de Documento", "Mes Emisión", "Orden de Compra", "Bodega", "Categoría Producto", "Código de Bien Servicio", "Código Catalogo de Bien Servicio", "Nombre de Bien Servicio", "Descripción"],
        "date_construction": {"year_source": "from_filename_or_current", "month_col": "Mes Emisión", "day_col": "Día Emisión", "target_col": "Fecha de emisión"},
        "column_renames": {'Código de Bien Servicio': 'Codigo', 'Código Catalogo de Bien Servicio': 'Cod. Catalogo', 'Nombre de Bien Servicio': 'Producto'},
        "attrs_for_grouping": {
            "month_cols": [], 
            "total_col": "Total", # Columna que representa la Venta por transacción
            "main_code_col": "Codigo" # Columna usada para el prefijo en Ventas (después de renombrar)
            }
    }
}

MONTH_MAP_ES_TO_INT = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
    'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 
    'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
}

def clean_column_names(df):
    df.columns = df.columns.str.strip()
    return df

def auto_detect_header_row(filepath, report_type, max_rows_to_scan=30):
    if report_type not in REPORT_DEFINITIONS:
        print(f"Advertencia: Definición para '{report_type}' no en auto_detect.")
        return None
    keywords = REPORT_DEFINITIONS[report_type].get("required_keywords_in_header", [])
    if not keywords:
        print(f"Advertencia: No hay palabras clave para auto-detectar encabezado de '{report_type}'.")
        return None
    try:
        df_scan = pd.read_excel(filepath, header=None, nrows=max_rows_to_scan)
        for i, row in df_scan.iterrows():
            row_values_str = [str(val).strip().lower() for val in row.dropna().values]
            matches = sum(keyword.lower() in row_values_str for keyword in keywords)
            # Necesita un buen número de coincidencias para ser considerado encabezado
            if matches >= len(keywords) * 0.6 and matches > 1: # Al menos el 60% y más de una palabra clave
                print(f"Encabezado detectado en fila Excel {i + 1} para '{report_type}'.")
                return i 
    except Exception as e:
        print(f"Error en auto-detección de encabezado: {e}")
    print(f"No se pudo auto-detectar encabezado para '{report_type}'.")
    return None

def load_and_validate_excel(filepath, report_type, user_header_row_input=0):
    if report_type not in REPORT_DEFINITIONS:
        return None, None, f"Tipo de reporte '{report_type}' no definido."

    report_spec = REPORT_DEFINITIONS[report_type]
    detected_header_idx = None 

    if not user_header_row_input or user_header_row_input == 0:
        detected_header_idx = auto_detect_header_row(filepath, report_type)
        if detected_header_idx is None:
            return None, None, "No se pudo auto-detectar la fila de encabezado. Especifíquela manualmente."
    else:
        detected_header_idx = user_header_row_input - 1

    try:
        df = pd.read_excel(filepath, header=detected_header_idx)
        df = clean_column_names(df)
        print(f"Columnas leídas (para {report_type}, encabezado fila Excel {detected_header_idx + 1}): {df.columns.tolist()}")

        initial_cols_to_check = report_spec.get("initial_excel_columns", [])
        missing_cols = [col for col in initial_cols_to_check if col not in df.columns]
        if missing_cols:
            return None, detected_header_idx + 1, f"Columnas iniciales faltantes para '{report_type}': {', '.join(missing_cols)}. Columnas encontradas: {df.columns.tolist()}"
        
        df = df[initial_cols_to_check].copy() # Trabajar solo con las columnas iniciales definidas

        for col in report_spec.get("numeric_columns", []):
            if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
        for col in report_spec.get("string_columns", []):
            if col in df.columns: df[col] = df[col].fillna('').astype(str)
        
        # print(f"\n--- DataFrame DESPUÉS de conversiones de tipo y ANTES de dropna ({report_type}) ---")
        # print(df.head(10)); print("Tipos de datos:"); print(df.dtypes); print("Conteo de NaNs:"); print(df.isnull().sum())
        # print("--------------------------------------------------------------------")

        if report_type == "Ventas":
            date_spec = report_spec.get("date_construction")
            if date_spec:
                try:
                    file_name_year_match = pd.Series(filepath).str.extract(r'(20\d{2})'); year_val = int(file_name_year_match[0].iloc[0]) if not file_name_year_match.empty and pd.notna(file_name_year_match[0].iloc[0]) else datetime.now().year
                    df[date_spec["month_col"]] = df[date_spec["month_col"]].astype(str).str.lower().str.strip().map(MONTH_MAP_ES_TO_INT)
                    df[date_spec["month_col"]] = pd.to_numeric(df[date_spec["month_col"]], errors='coerce'); df[date_spec["day_col"]] = pd.to_numeric(df[date_spec["day_col"]], errors='coerce')
                    valid_dates_mask = df[date_spec["month_col"]].notna() & df[date_spec["day_col"]].notna()
                    date_components = pd.DataFrame({'year': year_val, 'month': df.loc[valid_dates_mask, date_spec["month_col"]], 'day': df.loc[valid_dates_mask, date_spec["day_col"]]})
                    df.loc[valid_dates_mask, date_spec["target_col"]] = pd.to_datetime(date_components, errors='coerce')
                    df.dropna(subset=[date_spec["month_col"], date_spec["day_col"], date_spec["target_col"]], inplace=True)
                except KeyError as ke: return None, detected_header_idx + 1, f"Ventas: Columna '{ke}' no encontrada para fecha."
                except Exception as e_date: return None, detected_header_idx + 1, f"Ventas: Error construyendo fecha: {e_date}."
            df.rename(columns=report_spec.get("column_renames", {}), inplace=True)
            if 'Unidad' not in df.columns: df['Unidad'] = 'Unidad' # Asegurar compatibilidad
            
            # Seleccionar y reordenar columnas finales para el DataFrame de Ventas que usará la GUI y process_data
            final_cols_for_df = report_spec.get("final_df_columns", [])
        
        elif report_type == "Inventario":
            # Para Inventario, el DataFrame para la GUI y para process_data usará 'final_df_columns_for_processing'
            final_cols_for_df = report_spec.get("final_df_columns_for_processing", [])
        else: # Fallback
            final_cols_for_df = list(df.columns)

        # Asegurar que todas las columnas finales existan, añadir las que falten con pd.NA
        for col_fc in final_cols_for_df:
            if col_fc not in df.columns: 
                print(f"Advertencia: La columna final '{col_fc}' no se encontró después del procesamiento inicial. Se añadirá como NA.")
                df[col_fc] = pd.NA
        
        df = df[final_cols_for_df].copy() # Seleccionar y reordenar a las columnas finales para este tipo de reporte
            
        # Establecer atributos para process_data_by_code_prefix
        attrs_grouping = report_spec.get("attrs_for_grouping", {});
        df.attrs['total_col'] = attrs_grouping.get('total_col', 'Total')
        df.attrs['main_code_col'] = attrs_grouping.get('main_code_col', 'Codigo' if report_type=="Ventas" else "Código")
        df.attrs['month_cols'] = attrs_grouping.get('month_cols', []) # Para Ventas era [], para Inventario también

        # Limpieza final de NaNs en columnas clave (usando los nombres de columna del df actual)
        key_cols_to_check_nan = []
        main_code_col_in_df = df.attrs['main_code_col'] # Nombre de la columna de código en el df actual
        total_col_in_df = df.attrs['total_col']       # Nombre de la columna total en el df actual

        if main_code_col_in_df in df.columns: key_cols_to_check_nan.append(main_code_col_in_df)
        if report_type == "Inventario" and "Stock" in df.columns: key_cols_to_check_nan.append("Stock") # Si Stock es crítico
        if total_col_in_df in df.columns: key_cols_to_check_nan.append(total_col_in_df) # Si el total es crítico
        
        # Quitar duplicados de key_cols_to_check_nan
        key_cols_to_check_nan = sorted(list(set(key_cols_to_check_nan)))


        cols_for_dropna = [col for col in key_cols_to_check_nan if col in df.columns]
        if cols_for_dropna:
            print(f"Aplicando dropna en columnas: {cols_for_dropna}")
            df.dropna(subset=cols_for_dropna, how='any', inplace=True)
        else: 
            print("No se aplicó dropna (no se definieron/encontraron columnas clave para ello).")
        
        # print(f"\n--- DataFrame DESPUÉS de dropna ({report_type}) ---"); print(f"Filas restantes: {len(df)}"); print(df.head())

        if df.empty: 
            return None, detected_header_idx + 1, "No hay datos válidos tras la limpieza."
        
        print(f"Reporte '{report_type}' cargado y validado. {len(df)} filas procesables.")
        return df, detected_header_idx + 1, None

    except FileNotFoundError: return None, None, f"Archivo no encontrado: {filepath}"
    except Exception as e: 
        import traceback
        print(f"Excepción en load_and_validate_excel: {type(e).__name__} - {e}")
        traceback.print_exc()
        return None, detected_header_idx + 1 if detected_header_idx is not None else None, f"Error procesando Excel: {str(e)}"

def process_data_by_code_prefix(df_loaded, prefix_length=8):
    if df_loaded is None or df_loaded.empty: return pd.DataFrame()
    
    total_col_attrs = df_loaded.attrs.get('total_col', 'Total') 
    main_code_col_attrs = df_loaded.attrs.get('main_code_col', 'Codigo') 
    
    report_type_col_for_detail_sort = 'Producto' # Default, usado por Ventas
    if main_code_col_attrs == 'Código': # Si el main_code_col es 'Código', asumimos Inventario
        report_type_col_for_detail_sort = 'Nombre' # En Inventario, ordenamos por 'Nombre'

    if main_code_col_attrs not in df_loaded.columns:
        print(f"Error en process_data_by_code_prefix: Falta la columna de código principal '{main_code_col_attrs}'.")
        return pd.DataFrame()
        
    df_loaded[main_code_col_attrs] = df_loaded[main_code_col_attrs].astype(str)
    df_loaded['Codigo_Prefijo'] = df_loaded[main_code_col_attrs].str[:prefix_length]

    processed_list = []
    for prefijo, group in df_loaded.groupby('Codigo_Prefijo'):
        venta_total_general_prefijo = group[total_col_attrs].sum() if total_col_attrs in group.columns else 0.0
        cantidad_total_general_prefijo = len(group) 
        detalles_filas = []
        group_to_iterate = group
        if report_type_col_for_detail_sort in group.columns:
            try: group_to_iterate = group.sort_values(by=report_type_col_for_detail_sort, ascending=True, na_position='last')
            except Exception as e_sort: print(f"Advertencia: No se pudo ordenar por '{report_type_col_for_detail_sort}' para prefijo {prefijo}: {e_sort}")
        
        for _, row in group_to_iterate.iterrows():
            fila_detalle = row.to_dict() 
            detalles_filas.append(fila_detalle)
        
        processed_list.append({
            'Codigo_Prefijo': prefijo, 
            'Cantidad_Total_General': cantidad_total_general_prefijo,
            'Venta_Total_General': venta_total_general_prefijo, 
            'Detalles_Filas': detalles_filas, 
            'month_cols_names': df_loaded.attrs.get('month_cols', []), 
            'total_col_name': total_col_attrs    
        })
    return pd.DataFrame(processed_list).copy()

if __name__ == '__main__':
    def create_test_excel(filepath, data_dict, header_fila_excel=7):
        df_test = pd.DataFrame(data_dict); writer = pd.ExcelWriter(filepath, engine='xlsxwriter')
        workbook  = writer.book; worksheet = writer.book.add_worksheet('Sheet1')
        for i in range(header_fila_excel - 1): worksheet.write(i, 0, f"Encabezado Fila {i+1}")
        df_test.to_excel(writer, sheet_name='Sheet1', startrow=(header_fila_excel - 1), index=False)
        writer.close(); print(f"Archivo de prueba '{filepath}' creado.")

    inventario_data_excel = {
        "Categoría": ["CAT_A", "CAT_B", "CAT_A"], "Subcategoria": ["SUB_A1", "SUB_B1", "SUB_A1"],
        "Código": ["INV001XYZ", "INV002ABC", "INV001DEF"], 
        "Código Catalogo": ["CC001", "CC002", "CC003"],
        "Nombre": ["Alpha Product", "Beta Product", "Gamma Product"], 
        "Serie": ["S1", "S2", "S3"], "Unidad": ["PZA", "CAJA", "PZA"],
        "Costo Prom": [100.0, 200.0, 150.0], "Stock Mínimo": [10, 5, 8],
        "Stock": [50, 0, 60], "Total": [5000.0, 0.0, 9000.0]} # Probar con Stock y Total 0
    create_test_excel('test_inventario_dp_final_v3.xlsx', inventario_data_excel, header_fila_excel=6)

    print("\n--- Probando Reporte de Inventario (fila 6) ---")
    df_inv, head_row_inv, err_inv = load_and_validate_excel('test_inventario_dp_final_v3.xlsx', report_type="Inventario", user_header_row_input=6)
    if err_inv: print(f"Error Inventario: {err_inv}")
    elif df_inv is not None: 
        print(f"Inventario Cargado (enc. fila {head_row_inv}):\n", df_inv.head())
        print(f"Columnas del DataFrame de Inventario (para process_data): {df_inv.columns.tolist()}")
        
        df_inv_grouped = process_data_by_code_prefix(df_inv.copy())
        if not df_inv_grouped.empty:
            print("\n--- Inventario Agrupado por Prefijo ---")
            for _, row_g in df_inv_grouped.iterrows():
                print(f"  Prefijo: {row_g['Codigo_Prefijo']}, Valor Total: {row_g['Venta_Total_General']:.2f}, Filas: {row_g['Cantidad_Total_General']}")
        else: print("No se generaron datos agrupados para inventario.")