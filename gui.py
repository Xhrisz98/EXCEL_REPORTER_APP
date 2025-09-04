# gui.py
import customtkinter as ctk
from tkinter import filedialog, ttk 
import pandas as pd
from datetime import datetime

from data_processor import load_and_validate_excel, process_data_by_code_prefix, REPORT_DEFINITIONS
from report_generator import export_to_excel_multi_sheet_report, generate_bar_chart

CODIGO_PREFIX_LENGTH = 8
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

MONTH_INT_TO_NAME_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

class App(ctk.CTk):
    def __init__(self): # SIN CAMBIOS EN __INIT__ RESPECTO A V1.13
        super().__init__()
        self.title("Analizador de Reportes Múltiples v1.14 - Gráfico Inventario")
        self.geometry("1350x900") 
        self.loaded_data_frame = None; self.filtered_data_frame = None; self.processed_display_data = None
        self.report_types = ["Ventas", "Inventario"]; self.current_report_type_var = ctk.StringVar(value=self.report_types[0])
        self.filter_column_options_display = [] 
        self.current_filter_column_var = ctk.StringVar(); self.current_filter_value_var = ctk.StringVar()
        self.current_sort_order_var = ctk.StringVar(value="Descendente")
        self.ventas_filter_display_map = {"Fecha de emisión": "Fecha de emisión", "Bodega": "Bodega", "Categoría Producto": "Categoría Producto", "Codigo": "Codigo", "Cod. Catalogo": "Talla", "Producto": "Color"}
        self.ventas_internal_filter_cols = ["Fecha de emisión", "Bodega", "Categoría Producto", "Codigo", "Cod. Catalogo", "Producto"]
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(3, weight=1)
        self.report_type_frame = ctk.CTkFrame(self); self.report_type_frame.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")
        self.report_type_label = ctk.CTkLabel(self.report_type_frame, text="Seleccionar Tipo de Reporte:"); self.report_type_label.pack(side="left", padx=(0,10), pady=5)
        self.report_type_combobox = ctk.CTkComboBox(self.report_type_frame, values=self.report_types, variable=self.current_report_type_var, command=self.on_report_type_changed); self.report_type_combobox.pack(side="left", padx=5, pady=5)
        self.load_controls_frame = ctk.CTkFrame(self); self.load_controls_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.load_button = ctk.CTkButton(self.load_controls_frame, text="Cargar Archivo Excel", command=self.cargar_archivo); self.load_button.pack(side="left", padx=(0,10), pady=5)
        self.header_row_label = ctk.CTkLabel(self.load_controls_frame, text="Fila Encabezado (0 si auto):"); self.header_row_label.pack(side="left", padx=(10,0), pady=5)
        self.header_row_entry = ctk.CTkEntry(self.load_controls_frame, width=40); self.header_row_entry.insert(0, "0"); self.header_row_entry.pack(side="left", padx=5, pady=5)
        self.file_label = ctk.CTkLabel(self.load_controls_frame, text="Ningún archivo cargado", anchor="w"); self.file_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        self.filter_frame = ctk.CTkFrame(self); self.filter_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        self.filter_column_label = ctk.CTkLabel(self.filter_frame, text="Filtrar Columna:"); self.filter_column_label.pack(side="left", padx=(0,5), pady=5)
        self.filter_column_combobox = ctk.CTkComboBox(self.filter_frame, values=[], variable=self.current_filter_column_var, command=self.on_filter_column_selected, state="disabled"); self.filter_column_combobox.pack(side="left", padx=5, pady=5)
        self.filter_value_label = ctk.CTkLabel(self.filter_frame, text="Valor:"); self.filter_value_label.pack(side="left", padx=(10,5), pady=5)
        self.filter_value_combobox = ctk.CTkComboBox(self.filter_frame, values=[], variable=self.current_filter_value_var, command=self.apply_filters_and_display, state="disabled"); self.filter_value_combobox.pack(side="left", padx=5, pady=5)
        self.sort_segmented_button = ctk.CTkSegmentedButton(self.filter_frame, values=["Ascendente", "Descendente"], variable=self.current_sort_order_var, command=self.apply_filters_and_display); self.sort_segmented_button.pack(side="left", padx=(20,5), pady=5); self.sort_segmented_button.set("Descendente")
        self.data_display_frame = ctk.CTkFrame(self); self.data_display_frame.grid(row=3, column=0, padx=10, pady=5, sticky="nsew"); self.data_display_frame.grid_rowconfigure(0, weight=1); self.data_display_frame.grid_columnconfigure(0, weight=1)
        self.output_text = ctk.CTkTextbox(self.data_display_frame, wrap="none", state="disabled", font=("Consolas", 10)); self.output_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5) 
        self.export_frame = ctk.CTkFrame(self); self.export_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        self.export_excel_button = ctk.CTkButton(self.export_frame, text="Exportar a Excel", command=self.exportar_a_excel, state="disabled"); self.export_excel_button.pack(side="left", padx=5, pady=5)
        self.export_chart_button = ctk.CTkButton(self.export_frame, text="Exportar Gráfico", command=self.exportar_grafico, state="disabled"); # Se empaqueta en on_report_type_changed
        self.status_frame = ctk.CTkFrame(self, height=30); self.status_frame.grid(row=5, column=0, padx=10, pady=(5,10), sticky="ew")
        self.status_label = ctk.CTkLabel(self.status_frame, text="Listo. Seleccione tipo de reporte.", anchor="w"); self.status_label.pack(side="left", padx=5, pady=2, fill="x", expand=True)
        self.on_report_type_changed()

    def mostrar_mensaje_status(self, mensaje, es_error=False): # Sin cambios
        self.status_label.configure(text=mensaje, text_color="red" if es_error else ("#00A000" if ctk.get_appearance_mode().lower() == "light" else "#33FF33"))
    def limpiar_display_area(self): # Sin cambios
        self.output_text.configure(state="normal"); self.output_text.delete("1.0", "end"); self.output_text.configure(state="disabled")
    def reset_filters_and_sort(self): # Sin cambios
        self.filter_column_combobox.configure(values=[], state="disabled"); self.current_filter_column_var.set("")
        self.filter_value_combobox.configure(values=[], state="disabled"); self.current_filter_value_var.set("")
        self.export_excel_button.configure(state="disabled"); self.export_chart_button.configure(state="disabled")

    def on_report_type_changed(self, selected_report_type_gui=None):
        report_type = self.current_report_type_var.get()
        self.limpiar_display_area(); self.loaded_data_frame = None; self.filtered_data_frame = None; self.processed_display_data = None
        self.reset_filters_and_sort(); self.file_label.configure(text="Ningún archivo cargado")
        if hasattr(self, 'header_row_entry') and self.header_row_entry: self.header_row_entry.delete(0, "end"); self.header_row_entry.insert(0, "0")
        report_spec = REPORT_DEFINITIONS.get(report_type, {})
        
        # ***** CAMBIO: Mostrar/Ocultar botón de gráfico para AMBOS si es aplicable *****
        # La lógica de si es aplicable (si hay datos con Codigo_Prefijo) está en procesar_y_mostrar_reporte_final
        self.export_chart_button.pack(side="left", padx=5, pady=5) # Mostrar siempre, se deshabilita si no hay datos
        # ***** FIN CAMBIO *****

        current_filter_options_display = []
        if report_type == "Inventario":
            self.mostrar_mensaje_status("Modo Inventario. Cargue archivo.")
            inv_filter_map = report_spec.get("filter_column_display_map", {})
            inv_internal_cols = report_spec.get("filterable_internal_columns", [])
            display_options_inv = [inv_filter_map.get(col, col) for col in inv_internal_cols]
            current_filter_options_display = ["Todos"] + sorted(display_options_inv)
        elif report_type == "Ventas":
            self.mostrar_mensaje_status("Modo Ventas. Cargue archivo.")
            display_options_sales = [self.ventas_filter_display_map.get(col, col) for col in self.ventas_internal_filter_cols]
            current_filter_options_display = ["Total General"] + sorted(display_options_sales)
        else: current_filter_options_display = []
        
        self.filter_column_combobox.configure(values=current_filter_options_display)
        self.current_filter_column_var.set(current_filter_options_display[0] if current_filter_options_display else "")

    def cargar_archivo(self): # Sin cambios funcionales
        # ... (igual que v1.13)
        report_type = self.current_report_type_var.get(); self.mostrar_mensaje_status(f"Cargando para {report_type}..."); filepath = filedialog.askopenfilename(title=f"Seleccionar Excel de {report_type}", filetypes=(("Archivos Excel", "*.xlsx *.xls"),));
        if not filepath: self.mostrar_mensaje_status("Carga cancelada.", es_error=True); return
        try: header_row_input = int(self.header_row_entry.get())
        except ValueError: self.mostrar_mensaje_status("Fila encabezado no válida (0 auto).", es_error=True); return
        self.file_label.configure(text=filepath.split('/')[-1]); self.update_idletasks()
        df_cargado_temp, detected_header_row, error_msg_carga = load_and_validate_excel(filepath, report_type=report_type, user_header_row_input=header_row_input)
        self.reset_filters_and_sort()
        if error_msg_carga: self.mostrar_mensaje_status(f"Error al cargar: {error_msg_carga}", es_error=True); self.loaded_data_frame = None; self.limpiar_display_area(); return
        self.loaded_data_frame = df_cargado_temp
        if detected_header_row: self.header_row_entry.delete(0, "end"); self.header_row_entry.insert(0, str(detected_header_row))
        self.mostrar_mensaje_status(f"{report_type} cargado (enc. fila {detected_header_row if detected_header_row else 'auto'}).", es_error=False); self.update_idletasks()
        if self.loaded_data_frame is not None and not self.loaded_data_frame.empty:
            report_spec = REPORT_DEFINITIONS.get(report_type, {}); cols_for_filter_cb_display = []
            if report_type == "Inventario": inv_filter_map = report_spec.get("filter_column_display_map", {}); inv_internal_cols = report_spec.get("filterable_internal_columns", []); valid_internal_cols_inv = [col for col in inv_internal_cols if col in self.loaded_data_frame.columns]; display_options_inv = [inv_filter_map.get(col, col) for col in valid_internal_cols_inv]; cols_for_filter_cb_display = ["Todos"] + sorted(display_options_inv)
            elif report_type == "Ventas": valid_internal_cols_sales = [col for col in self.ventas_internal_filter_cols if col in self.loaded_data_frame.columns]; display_options_sales = [self.ventas_filter_display_map.get(col, col) for col in valid_internal_cols_sales]; cols_for_filter_cb_display = ["Total General"] + sorted(display_options_sales)
            else: cols_for_filter_cb_display = ["Todos"] + sorted(list(self.loaded_data_frame.columns))
            self.filter_column_combobox.configure(values=cols_for_filter_cb_display, state="normal"); self.current_filter_column_var.set(cols_for_filter_cb_display[0] if cols_for_filter_cb_display else "")
        else: self.filter_column_combobox.configure(values=[], state="disabled")
        self.on_filter_column_selected()

    def get_internal_col_name(self, display_name, report_type): # Sin cambios
        # ... (igual que v1.13)
        map_to_use = {};
        if report_type == 'Ventas': map_to_use = self.ventas_filter_display_map
        elif report_type == 'Inventario': map_to_use = REPORT_DEFINITIONS["Inventario"].get("filter_column_display_map", {})
        if display_name not in ["Total General", "Todos"]:
            for internal, disp in map_to_use.items():
                if disp == display_name: return internal
        return display_name 

    def on_filter_column_selected(self, selected_col_display_name_gui=None): # Sin cambios funcionales
        # ... (igual que v1.13)
        selected_display_name = self.current_filter_column_var.get(); self.current_filter_value_var.set(""); report_type = self.current_report_type_var.get(); internal_filter_col = self.get_internal_col_name(selected_display_name, report_type); self.filter_value_label.configure(text="Valor:") 
        if self.loaded_data_frame is None or not selected_display_name or selected_display_name in ["Todos", "Total General"]: self.filter_value_combobox.configure(values=[], state="disabled")
        elif internal_filter_col in self.loaded_data_frame.columns:
            try:
                if internal_filter_col == 'Fecha de emisión' and report_type == 'Ventas':
                    if pd.api.types.is_datetime64_any_dtype(self.loaded_data_frame[internal_filter_col]): unique_month_numbers = sorted(self.loaded_data_frame[internal_filter_col].dt.month.unique()); unique_month_names = ["Todos"] + [MONTH_INT_TO_NAME_ES.get(m, str(m)) for m in unique_month_numbers]; self.filter_value_combobox.configure(values=unique_month_names, state="normal"); self.filter_value_label.configure(text="Mes de Emisión:")
                    else: unique_values = ["Todos"] + sorted(self.loaded_data_frame[internal_filter_col].astype(str).unique().tolist()); self.filter_value_combobox.configure(values=unique_values, state="normal"); self.filter_value_label.configure(text=f"Valor de {selected_display_name}:")
                elif (internal_filter_col == 'Código' and report_type == 'Inventario') or (internal_filter_col == 'Codigo' and report_type == 'Ventas'): unique_prefixes = ["Todos"] + sorted(self.loaded_data_frame[internal_filter_col].astype(str).str[:CODIGO_PREFIX_LENGTH].unique().tolist()); self.filter_value_label.configure(text="Prefijo Código:"); self.filter_value_combobox.configure(values=unique_prefixes, state="normal")
                else: unique_values = ["Todos"] + sorted(self.loaded_data_frame[internal_filter_col].astype(str).unique().tolist()); self.filter_value_label.configure(text=f"Valor de {selected_display_name}:"); self.filter_value_combobox.configure(values=unique_values, state="normal")
                self.current_filter_value_var.set("Todos") 
            except Exception as e: self.mostrar_mensaje_status(f"Error al obtener valores para '{selected_display_name}': {e}", es_error=True); self.filter_value_combobox.configure(values=[], state="disabled")
        else: self.filter_value_combobox.configure(values=[], state="disabled")
        self.apply_filters_and_display()
        
    def apply_filters_and_display(self, event=None): # CAMBIO: Habilitar botón de gráfico para Inventario
        if self.loaded_data_frame is None: self.limpiar_display_area(); self.export_excel_button.configure(state="disabled"); self.export_chart_button.configure(state="disabled"); return
        df_to_filter = self.loaded_data_frame.copy(); report_type = self.current_report_type_var.get(); selected_display_name_filter = self.current_filter_column_var.get(); filter_val_str = self.current_filter_value_var.get()
        internal_filter_col = self.get_internal_col_name(selected_display_name_filter, report_type)
        if selected_display_name_filter and selected_display_name_filter not in ["Todos", "Total General"] and filter_val_str and filter_val_str != "Todos":
            if internal_filter_col in df_to_filter.columns:
                try:
                    if internal_filter_col == 'Fecha de emisión' and report_type == 'Ventas':
                        if pd.api.types.is_datetime64_any_dtype(df_to_filter[internal_filter_col]): selected_month_number = next((num for num, name in MONTH_INT_TO_NAME_ES.items() if name == filter_val_str), None)
                        if selected_month_number is not None: df_to_filter = df_to_filter[df_to_filter[internal_filter_col].dt.month == selected_month_number].copy()
                    elif (internal_filter_col == 'Código' and report_type == 'Inventario') or (internal_filter_col == 'Codigo' and report_type == 'Ventas'):
                        df_to_filter = df_to_filter[df_to_filter[internal_filter_col].astype(str).str.startswith(filter_val_str)].copy()
                    else: df_to_filter = df_to_filter[df_to_filter[internal_filter_col].astype(str) == filter_val_str].copy()
                except Exception as e: self.mostrar_mensaje_status(f"Error al aplicar filtro: {e}", es_error=True); df_to_filter = pd.DataFrame()
            else: df_to_filter = pd.DataFrame() 
        self.filtered_data_frame = df_to_filter; self.limpiar_display_area()
        if self.filtered_data_frame.empty: self.mostrar_mensaje_status(f"No hay datos de {report_type} (tras filtros).", es_error=False); self.processed_display_data = pd.DataFrame(); self.export_excel_button.configure(state="disabled"); self.export_chart_button.configure(state="disabled"); return
        sort_asc = (self.current_sort_order_var.get() == "Ascendente") 
        grouped_data = process_data_by_code_prefix(self.filtered_data_frame.copy(), prefix_length=CODIGO_PREFIX_LENGTH)
        if not grouped_data.empty:
            try: grouped_data = grouped_data.sort_values(by='Venta_Total_General', ascending=sort_asc, na_position='last')
            except Exception as e_sort_grouped: self.mostrar_mensaje_status(f"Error al ordenar datos agrupados: {e_sort_grouped}", es_error=True)
            self.processed_display_data = grouped_data; self.display_summary_in_textbox(self.processed_display_data, report_type)
            self.export_excel_button.configure(state="normal")
            # ***** CAMBIO: Habilitar botón de gráfico si hay datos agrupados para CUALQUIER tipo *****
            if 'Codigo_Prefijo' in grouped_data.columns and 'Venta_Total_General' in grouped_data.columns:
                self.export_chart_button.configure(state="normal")
            else:
                self.export_chart_button.configure(state="disabled")
            # ***** FIN CAMBIO *****
        else: self.mostrar_mensaje_status(f"No se generaron datos agrupados para {report_type}.", es_error=False); self.processed_display_data = pd.DataFrame(); self.export_excel_button.configure(state="disabled"); self.export_chart_button.configure(state="disabled")

    def display_summary_in_textbox(self, df_agrupado_por_prefijo, report_type): # Sin cambios funcionales
        # ... (igual que v1.13) ...
        self.limpiar_display_area(); self.output_text.configure(state="normal")
        if df_agrupado_por_prefijo is None or df_agrupado_por_prefijo.empty: self.output_text.insert("end", f"No hay datos de {report_type} procesados.")
        else:
            report_spec = REPORT_DEFINITIONS.get(report_type, {}); detalle_cols_data_names = []; detalle_cols_display_headers = []; detalle_cols_widths = []
            if report_type == "Ventas": detalle_cols_data_names = ["Fecha de emisión", "Bodega", "Codigo", "Categoría Producto", "Cod. Catalogo", "Producto", "Cantidad", "Costo Venta", "Descripción", "% Descuento", "Total"]; detalle_cols_display_headers = ["Fecha de emisión", "Bodega", "Codigo", "Categoría Producto", "Talla", "Color", "Cantidad", "Costo Venta", "Descripción", "% Descuento", "Total"]; detalle_cols_widths = [12, 15, 18, 20, 10, 20, 8, 12, 20, 10, 12] 
            elif report_type == "Inventario": detalle_cols_data_names = report_spec.get("gui_detail_display_columns_ordered", []); inv_display_map = report_spec.get("filter_column_display_map", {}); detalle_cols_display_headers = [inv_display_map.get(col, col) for col in detalle_cols_data_names]; detalle_cols_widths = [18, 15, 20, 10, 20, 12, 8, 12] 
            else:
                if not df_agrupado_por_prefijo.empty and df_agrupado_por_prefijo.iloc[0]['Detalles_Filas']: detalle_cols_data_names = list(df_agrupado_por_prefijo.iloc[0]['Detalles_Filas'][0].keys())
                if 'Codigo_Prefijo' in detalle_cols_data_names: detalle_cols_data_names.remove('Codigo_Prefijo'); detalle_cols_display_headers = detalle_cols_data_names; detalle_cols_widths = [15] * len(detalle_cols_data_names)
            for _, row_prefijo in df_agrupado_por_prefijo.iterrows():
                prefijo_codigo = row_prefijo['Codigo_Prefijo']; cant_total_gen = row_prefijo['Cantidad_Total_General']; venta_total_gen = row_prefijo['Venta_Total_General']; total_col_name_from_attrs = row_prefijo.get('total_col_name', 'Total')
                header_prefijo_text = f"Subcategoría (Prefijo Código): {prefijo_codigo}\n"; self.output_text.insert("end", header_prefijo_text)
                self.output_text.insert("end", f"  Cantidad Total Filas: {cant_total_gen}\n"); label_valor_total = "Venta Total" if report_type == "Ventas" else "Valor Total Inventario"; self.output_text.insert("end", f"  {label_valor_total} (Suma Col. '{total_col_name_from_attrs}'): {venta_total_gen:.2f}\n"); self.output_text.insert("end", "-" * (len(header_prefijo_text) + 30) + "\n")
                if row_prefijo['Detalles_Filas'] and detalle_cols_display_headers:
                    header_line = "  "; separator_line = "  "
                    for i, col_display_name in enumerate(detalle_cols_display_headers): width = detalle_cols_widths[i] if i < len(detalle_cols_widths) else 15; header_line += f"{col_display_name:<{width}} | "; separator_line += f"{'-'*width} | "
                    self.output_text.insert("end", header_line.rstrip(" | ") + "\n"); self.output_text.insert("end", separator_line.rstrip(" | ") + "\n")
                    for detalle_fila_dict in row_prefijo['Detalles_Filas']:
                        linea_vals = []
                        for i, col_data_name in enumerate(detalle_cols_data_names): 
                            width = detalle_cols_widths[i] if i < len(detalle_cols_widths) else 15; val = detalle_fila_dict.get(col_data_name, '')
                            if col_data_name == "Fecha de emisión" and isinstance(val, pd.Timestamp): val_str = val.strftime('%Y-%m-%d')
                            elif isinstance(val, (float, int)):
                                if col_data_name == "Cantidad" and report_type == "Ventas" and val == int(val): val_str = str(int(val))
                                elif col_data_name == "Stock" and report_type == "Inventario" and isinstance(val, (float,int)) and val == int(val): val_str = str(int(val))
                                elif col_data_name in ["% Descuento", "Costo Venta", "Total", "Costo Prom"]: val_str = f"{val:.2f}"
                                else: val_str = str(val)
                            else: val_str = str(val)
                            linea_vals.append(f"{val_str[:width]:<{width}}")
                        linea = "  " + " | ".join(linea_vals) + "\n"; self.output_text.insert("end", linea)
                self.output_text.insert("end", "="*max(100, sum(detalle_cols_widths) + len(detalle_cols_widths)*3 -1 if detalle_cols_widths else 100) + "\n\n")
        self.output_text.configure(state="disabled")

    def exportar_a_excel(self): # Sin cambios funcionales
        # ... (igual que v1.13)
        report_type = self.current_report_type_var.get(); df_to_export = self.processed_display_data
        if df_to_export is None or df_to_export.empty: self.mostrar_mensaje_status(f"No hay datos de {report_type} para exportar.", es_error=True); return
        filepath = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Archivos Excel", "*.xlsx")], title=f"Guardar Reporte {report_type}...");
        if not filepath: self.mostrar_mensaje_status("Exportación cancelada.", es_error=True); return
        self.mostrar_mensaje_status(f"Exportando {report_type}...", es_error=False); self.update_idletasks()
        try:
            report_spec = REPORT_DEFINITIONS.get(report_type, {}); report_title = f"REPORTE DE {report_type.upper()}"; filter_col_display = self.current_filter_column_var.get(); filter_val = self.current_filter_value_var.get()
            if filter_col_display and filter_col_display not in ["Todos", "Total General"] and filter_val and filter_val != "Todos": filter_col_internal = self.get_internal_col_name(filter_col_display,report_type) ; report_title += f" (Filtro: {filter_col_display} = {filter_val})"
            if report_type == "Ventas": success, message = export_to_excel_multi_sheet_report(df_to_export, filepath, report_type, report_title_prefix=report_title)
            elif report_type == "Inventario": inv_detail_cols = report_spec.get("gui_detail_display_columns_ordered", []); success, message = export_to_excel_multi_sheet_report(df_to_export, filepath, report_type, report_title_prefix=report_title, inventory_cols=inv_detail_cols)
            else: success, message = False, "Tipo de reporte no reconocido."
            if success: self.mostrar_mensaje_status(message, es_error=False)
            else: self.mostrar_mensaje_status(message, es_error=True)
        except Exception as e: self.mostrar_mensaje_status(f"Error al exportar: {e}", es_error=True); import traceback; traceback.print_exc()
    
    def exportar_grafico(self): # CAMBIO: Permitir gráfico para ambos si los datos son adecuados
        report_type = self.current_report_type_var.get() # Saber qué tipo de reporte es
        if self.processed_display_data is None or self.processed_display_data.empty or \
           'Codigo_Prefijo' not in self.processed_display_data.columns or \
           'Venta_Total_General' not in self.processed_display_data.columns:
            self.mostrar_mensaje_status("No hay datos agrupados por prefijo para generar el gráfico.", es_error=True)
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Imágenes PNG", "*.png"), ("Imágenes JPG", "*.jpg"), ("Todos los archivos", "*.*")],
            title=f"Guardar Gráfico {report_type} Como..." 
        )
        if not filepath:
            self.mostrar_mensaje_status("Exportación de gráfico cancelada.", es_error=True)
            return
        
        self.mostrar_mensaje_status(f"Generando gráfico para {report_type}...", es_error=False)
        self.update_idletasks()

        success, message = generate_bar_chart(
            self.processed_display_data, filepath
        )

        if success:
            self.mostrar_mensaje_status(message, es_error=False)
        else:
            self.mostrar_mensaje_status(message, es_error=True)

if __name__ == "__main__":
    app = App()
    app.mainloop()