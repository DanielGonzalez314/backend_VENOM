import io
import base64
import logging
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, List, Dict, Any

logger = logging.getLogger("ChartService")

class ChartService:
    """Genera gráficos a partir de datos tabulares (CSV/Excel) con auto-detección de estructura"""
    
    @staticmethod
    async def generate_chart(
        file_bytes: bytes,
        filename: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        chart_type: str = "bar",
        title: str = "Gráfico generado por VENOM"
    ) -> Dict[str, Any]:
        """
        Genera un gráfico a partir de un archivo CSV o Excel.
        Si no se especifican columnas, intenta autodetectar las más adecuadas.
        """
        try:
            # Leer datos según extensión
            if filename.lower().endswith('.csv'):
                # Intentar detectar automáticamente si hay encabezado
                # Si la primera fila contiene solo números o fechas, probablemente no es encabezado
                sample = pd.read_csv(io.BytesIO(file_bytes), nrows=5)
                # Heurística simple: si la primera fila tiene menos de 3 cadenas no numéricas, asumir sin encabezado
                first_row = sample.iloc[0].astype(str)
                has_header = any(cell.isalpha() for cell in first_row)  # al menos una palabra
                if not has_header and len(first_row) > 1:
                    # Sin encabezado, asignar nombres de columnas automáticos
                    df = pd.read_csv(io.BytesIO(file_bytes), header=None)
                    df.columns = [f"Columna_{i+1}" for i in range(len(df.columns))]
                else:
                    df = pd.read_csv(io.BytesIO(file_bytes))
            elif filename.lower().endswith(('.xlsx', '.xls')):
                # Excel: leer con header automático, pero si no se detecta, usar None
                df = pd.read_excel(io.BytesIO(file_bytes))
                if df.columns[0] == 0:  # Si la primera columna es numérica, probablemente sin encabezado
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
                    df.columns = [f"Columna_{i+1}" for i in range(len(df.columns))]
            else:
                return {
                    "success": False,
                    "message": "Formato no soportado. Use CSV o Excel (.xlsx, .xls)."
                }
            
            # Si no hay suficientes filas
            if len(df) < 2:
                return {"success": False, "message": "El archivo tiene muy pocas filas (mínimo 2)."}
            
            # Auto-detectar columnas si no se proporcionaron
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Si no hay columnas numéricas, intentar convertir algunas strings a números
            if not numeric_cols:
                for col in df.columns:
                    try:
                        df[col] = pd.to_numeric(df[col], errors='raise')
                        numeric_cols.append(col)
                    except:
                        pass
                if not numeric_cols:
                    return {
                        "success": False,
                        "message": "No se encontraron columnas numéricas para graficar. Asegúrate de tener datos numéricos (números) en al menos una columna."
                    }
            
            # Si no se especificó columna X, elegir la primera columna categórica o la primera columna
            if not x_column:
                if categorical_cols:
                    x_column = categorical_cols[0]
                else:
                    x_column = df.columns[0]  # primera columna
            # Si no se especificó columna Y, elegir la primera columna numérica
            if not y_column:
                y_column = numeric_cols[0] if numeric_cols else df.columns[1] if len(df.columns) > 1 else df.columns[0]
            
            # Validar que las columnas existan en el DataFrame
            if x_column not in df.columns:
                # Intentar buscar columnas similares (ignorando mayúsculas/minúsculas)
                x_matches = [c for c in df.columns if c.lower() == x_column.lower()]
                if x_matches:
                    x_column = x_matches[0]
                else:
                    return {
                        "success": False,
                        "message": f"Columna '{x_column}' no encontrada. Columnas disponibles: {', '.join(df.columns)}. Si el archivo no tiene encabezados, usa los nombres 'Columna_1', 'Columna_2', etc."
                    }
            
            if y_column not in df.columns:
                y_matches = [c for c in df.columns if c.lower() == y_column.lower()]
                if y_matches:
                    y_column = y_matches[0]
                else:
                    return {
                        "success": False,
                        "message": f"Columna '{y_column}' no encontrada. Columnas disponibles: {', '.join(df.columns)}."
                    }
            
            # Preparar datos
            x_data = df[x_column].astype(str).tolist()
            y_data = pd.to_numeric(df[y_column], errors='coerce').fillna(0).tolist()
            
            # Si todos los valores de Y son cero, dar aviso
            if all(v == 0 for v in y_data):
                return {"success": False, "message": "La columna Y no contiene valores numéricos válidos (todos son cero o texto)."}
            
            # Crear gráfico
            plt.figure(figsize=(10, 6))
            
            if chart_type == "bar":
                plt.bar(x_data, y_data, color='purple', alpha=0.7)
            elif chart_type == "line":
                plt.plot(x_data, y_data, marker='o', color='purple', linewidth=2)
            elif chart_type == "pie":
                # Para gráficos de pastel, eliminar valores cero o negativos
                positive_data = [(x, y) for x, y in zip(x_data, y_data) if y > 0]
                if not positive_data:
                    return {"success": False, "message": "El gráfico de pastel requiere al menos un valor positivo."}
                x_data, y_data = zip(*positive_data)
                plt.pie(y_data, labels=x_data, autopct='%1.1f%%', startangle=90)
                plt.title(title)
            elif chart_type == "scatter":
                plt.scatter(x_data, y_data, color='purple', alpha=0.6)
            else:
                plt.bar(x_data, y_data, color='purple', alpha=0.7)
            
            if chart_type != "pie":
                plt.xlabel(x_column)
                plt.ylabel(y_column)
                plt.title(title)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()
            
            # Convertir a base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            
            logger.info(f"✅ Gráfico generado: {chart_type} de {x_column} vs {y_column} (auto={not bool(x_column or y_column)})")
            return {
                "success": True,
                "message": f"Gráfico {chart_type} generado exitosamente",
                "image_base64": img_base64,
                "data_points": len(x_data)
            }
            
        except Exception as e:
            logger.error(f"Error generando gráfico: {e}", exc_info=True)
            return {"success": False, "message": f"Error al procesar el archivo: {str(e)}. Verifica que sea un archivo válido con datos tabulares."}
    
    @staticmethod
    async def list_columns(file_bytes: bytes, filename: str) -> List[str]:
        """Devuelve los nombres de las columnas del archivo (útil para que la IA pregunte)"""
        try:
            if filename.lower().endswith('.csv'):
                df = pd.read_csv(io.BytesIO(file_bytes))
            else:
                df = pd.read_excel(io.BytesIO(file_bytes))
            return list(df.columns)
        except Exception as e:
            logger.warning(f"Error listando columnas: {e}")
            return []