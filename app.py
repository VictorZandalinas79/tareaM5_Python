import streamlit as st
import os
import subprocess
import pandas as pd
import base64
from pathlib import Path
import nbformat
from nbconvert import PythonExporter
from nbconvert.exporters import PDFExporter
import matplotlib.pyplot as plt
import time  # Necesario para las pausas en las barras de progreso
import sys 

# Configuración de la página
st.set_page_config(
    page_title="App Análisis Champions 24/25",
    page_icon="⚽",
    layout="wide"
)

# Función para convertir notebooks a scripts de Python
def convert_notebook_to_python(notebook_path, output_path):
    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)
    
    exporter = PythonExporter()
    python_code, _ = exporter.from_notebook_node(nb)
    
    with open(output_path, 'w') as f:
        f.write(python_code)
    
    return output_path

def run_notebook_and_get_pdf(notebook_path):
    """
    Ejecuta una notebook y devuelve la ruta del archivo PDF generado por la notebook.
    Instala automáticamente las dependencias necesarias.
    """
    # Asegurarnos de que las dependencias estén instaladas
    if not ensure_dependencies():
        st.error("No se pudieron instalar las dependencias necesarias")
        return None
    
    # Primero convertimos la notebook a un script Python
    script_path = notebook_path.replace('.ipynb', '.py')
    convert_notebook_to_python(notebook_path, script_path)
    
    # Obtenemos el directorio donde está la notebook
    notebook_dir = os.path.dirname(notebook_path)
    if not notebook_dir:
        notebook_dir = "."
    
    # Guardamos la lista de PDFs antes de ejecutar el script
    pdf_files_before = set(Path(notebook_dir).glob("*.pdf"))
    
    # Ejecutamos el script
    print("Ejecutando script para generar PDF...")
    result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        st.error(f"Error al ejecutar el script: {result.stderr}")
        return None
    
    # Buscamos PDFs nuevos después de ejecutar el script
    pdf_files_after = set(Path(notebook_dir).glob("*.pdf"))
    new_pdfs = pdf_files_after - pdf_files_before
    
    # Si hay algún PDF nuevo, devolvemos el primero
    if new_pdfs:
        print(f"PDF generado: {list(new_pdfs)[0]}")
        return str(list(new_pdfs)[0])
    
    # Si no hay PDFs nuevos, buscamos en diferentes ubicaciones
    expected_pdf = os.path.join(notebook_dir, "Arsenal_vs_RealMadrid_report.pdf")
    if os.path.exists(expected_pdf):
        return expected_pdf
    
    # Buscar en la carpeta raíz también
    root_pdf = "Arsenal_vs_RealMadrid_report.pdf"
    if os.path.exists(root_pdf):
        return root_pdf
    
    # Buscar cualquier PDF si no encontramos el específico
    all_pdfs = pdf_files_after
    if all_pdfs:
        return str(list(all_pdfs)[0])
    
    # Buscar en la carpeta raíz por cualquier PDF
    root_pdfs = list(Path(".").glob("*.pdf"))
    if root_pdfs:
        return str(root_pdfs[0])
    
    return None

# Función para ejecutar una notebook y obtener el resultado
def run_notebook(notebook_path, output_type='csv'):
    # Convertimos la notebook a un script Python
    script_path = notebook_path.replace('.ipynb', '.py')
    convert_notebook_to_python(notebook_path, script_path)
    
    # Ejecutamos el script
    result = subprocess.run(['python', script_path], capture_output=True, text=True)
    
    if result.returncode != 0:
        st.error(f"Error al ejecutar el script: {result.stderr}")
        return None
    
    if output_type == 'csv':
        # Asumimos que el script genera un archivo CSV en la misma carpeta
        csv_path = notebook_path.replace('.ipynb', '.csv')
        if os.path.exists(csv_path):
            return csv_path
    
    return True

def ensure_dependencies():
    """
    Asegura que todas las dependencias necesarias estén instaladas.
    Retorna True si la instalación fue exitosa, False en caso contrario.
    """
    try:
        # Lista de dependencias necesarias
        dependencies = ["fpdf"]
        
        # Verificar cuáles necesitan ser instaladas
        to_install = []
        for dep in dependencies:
            try:
                __import__(dep)
                print(f"✓ {dep} ya está instalado")
            except ImportError:
                to_install.append(dep)
        
        # Instalar las dependencias faltantes
        if to_install:
            print(f"Instalando dependencias faltantes: {', '.join(to_install)}")
            for dep in to_install:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
                print(f"✓ {dep} instalado correctamente")
        
        return True
    except Exception as e:
        print(f"Error al instalar dependencias: {str(e)}")
        return False
    
def extract_last_subplot(notebook_path):
    """
    Extrae específicamente el último subplot de una notebook sin crear visualizaciones alternativas.
    """
    try:
        # Primero, intentamos usar la imagen que ya existe si la notebook se ejecutó manualmente
        if os.path.exists('visualizacion_arsenal_madrid.png'):
            return 'visualizacion_arsenal_madrid.png'
            
        # Convertimos la notebook a un script Python
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)
        
        # Crear un script temporal que solo ejecuta el notebook original sin modificaciones
        # Solo añadimos código al final para guardar la última figura
        script_path = notebook_path.replace('.ipynb', '_exact_plot.py')
        
        # Añadir código para guardar la figura final sin alterar nada más
        code_to_add = """
# Solo guardamos la figura actual, sin crear alternativas
import matplotlib.pyplot as plt

# Guardamos la figura con alta calidad
plt.savefig('exact_plot.png', dpi=300, bbox_inches='tight')
print("Figura original guardada como 'exact_plot.png'")
"""
        # Añadimos esta celda al final del notebook
        new_cell = nbformat.v4.new_code_cell(source=code_to_add)
        nb.cells.append(new_cell)
        
        # Exportamos el notebook a Python
        exporter = PythonExporter()
        python_code, _ = exporter.from_notebook_node(nb)
        
        with open(script_path, 'w') as f:
            f.write(python_code)
        
        # Ejecutamos el script completo - esto debería generar la misma visualización que en la notebook
        print("Ejecutando notebook original para extraer el último subplot...")
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        
        # Verificamos si se generó la imagen
        if os.path.exists('exact_plot.png'):
            return 'exact_plot.png'
            
        # Si no se generó la imagen, intentamos con el método original
        print("Intentando método alternativo...")
        
        # Método original modificado
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)
        
        # Crear otro script temporal
        script_path = notebook_path.replace('.ipynb', '_simple_plot.py')
        
        # Solo extraemos el código de las últimas celdas donde probablemente está la visualización
        # Nos quedamos con las últimas 5 celdas de código que podrían contener el gráfico
        code_cells = [cell for cell in nb.cells if cell.cell_type == 'code']
        last_cells = code_cells[-5:] if len(code_cells) > 5 else code_cells
        
        # Construimos un nuevo script con solo las importaciones necesarias y las últimas celdas
        script_content = """
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Intentamos ejecutar solo las últimas celdas de código que probablemente contienen la visualización
try:
"""
        
        # Añadimos el contenido de las últimas celdas con indentación
        for cell in last_cells:
            # Indentamos cada línea para que esté dentro del bloque try
            indented_code = '\n'.join('    ' + line for line in cell.source.split('\n'))
            script_content += indented_code + '\n\n'
        
        # Añadimos código para guardar la figura
        script_content += """
    # Guardamos la figura actual
    plt.savefig('last_plot.png', dpi=300, bbox_inches='tight')
    print("Última figura guardada como 'last_plot.png'")
except Exception as e:
    print(f"Error al ejecutar celdas: {str(e)}")
"""
        
        # Guardamos y ejecutamos este script simplificado
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        result = subprocess.run(['python', script_path], capture_output=True, text=True)
        print(f"Resultado de la ejecución: {result.stdout}")
        
        # Verificamos si se generó la imagen
        if os.path.exists('last_plot.png'):
            return 'last_plot.png'
            
        # Si todavía no funciona, dejamos un mensaje para el usuario
        print("No se pudo generar la visualización automáticamente.")
        print("Recomendación: ejecuta manualmente la notebook y guarda la última figura como 'visualizacion_arsenal_madrid.png'")
        
        return None
        
    except Exception as e:
        print(f"Error al extraer el subplot: {str(e)}")
        return None

def convert_notebook_to_html_or_pdf(notebook_path):
    """
    Convertir notebook a HTML (preferido) o PDF (si XeLaTeX está disponible).
    Esta función primero intenta exportar a HTML, que no requiere LaTeX.
    Si falla, intenta exportar a PDF y muestra instrucciones si faltan dependencias.
    """
    try:
        # Primero intentamos exportar a HTML (más confiable)
        from nbconvert import HTMLExporter
        
        with open(notebook_path) as f:
            nb = nbformat.read(f, as_version=4)
        
        # Usar el exportador HTML
        html_exporter = HTMLExporter()
        html_data, _ = html_exporter.from_notebook_node(nb)
        
        # Guardar como HTML
        html_path = notebook_path.replace('.ipynb', '.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_data)
        
        print(f"Notebook convertido a HTML: {html_path}")
        return html_path
        
    except Exception as e:
        print(f"Error al exportar a HTML: {str(e)}")
        
        try:
            # Intentar exportar a PDF como respaldo
            from nbconvert.exporters import PDFExporter
            
            with open(notebook_path) as f:
                nb = nbformat.read(f, as_version=4)
            
            exporter = PDFExporter()
            pdf_data, _ = exporter.from_notebook_node(nb)
            
            output_path = notebook_path.replace('.ipynb', '.pdf')
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            
            return output_path
            
        except OSError as latex_error:
            # Error específico si falta XeLatex
            print("Error: XeLatex no está instalado. Se requiere para generar PDFs.")
            
            # Crear un archivo de texto con instrucciones
            instructions_path = notebook_path.replace('.ipynb', '_instrucciones.txt')
            
            with open(instructions_path, 'w') as f:
                f.write("""
INSTRUCCIONES PARA EXPORTAR NOTEBOOKS A PDF

Para exportar notebooks a PDF, necesitas instalar LaTeX:

1. En macOS:
   - Instalar MacTex: https://tug.org/mactex/
   - O usar Homebrew: brew install --cask mactex-no-gui

2. En Windows:
   - Instalar MikTex: https://miktex.org/download

3. En Linux:
   - Instalar TexLive: sudo apt-get install texlive-xetex texlive-fonts-recommended texlive-plain-generic

Después de instalar LaTeX, reinicia la aplicación.

Alternativa:
1. Abre la notebook en Jupyter Notebook o JupyterLab
2. Usa la opción "Exportar como PDF" desde el menú
                """)
            
            return instructions_path
            
        except Exception as general_error:
            print(f"Error al exportar a PDF: {str(general_error)}")
            return None

# Función para mostrar la imagen del banner
def display_banner():
    banner_path = "assets/banner.png"
    if os.path.exists(banner_path):
        st.image(banner_path, use_column_width=True)
    else:
        st.warning("No se encontró el archivo del banner en 'assets/banner.png'")

# Función para descargar archivos
def get_binary_file_downloader_html(bin_file, file_label='Archivo'):
    with open(bin_file, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{os.path.basename(bin_file)}">{file_label}</a>'
    return href

# Sistema de login
def login():
    st.title("Acceso a la Aplicación")
    
    st.markdown("*Utilize usuario: 'admin' y contraseña: 'admin' para ingresar*")
    
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Ingresar"):
        if username == "admin" and password == "admin":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos")

# Página principal después del login
def main_page():
    display_banner()
    
    st.title("Análisis Champions League 24/25")
    
    # Estilo CSS personalizado para botones grandes con iconos
    st.markdown("""
    <style>
    div.stButton > button {
        font-size: 20px !important;
        height: auto !important;
        padding: 15px !important;
        margin: 10px 0px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Botón 1 con ícono
        if st.button("📊 Extracción API Cafesito\nDatos Champions 24/25\nExtraccion csv eventos"):
            # Crear un área para la barra de progreso
            progress_area = st.empty()
            progress_bar = progress_area.progress(0)
            
            # Mostrar mensaje de procesamiento
            status_area = st.empty()
            status_area.info("Iniciando extracción de datos...")
            
            # Simulación de progreso y ejecución real
            for i in range(101):
                # Actualizar barra de progreso
                progress_bar.progress(i)
                
                # Cambiar mensajes según el progreso
                if i == 10:
                    status_area.info("Conectando con API Cafesito...")
                elif i == 30:
                    status_area.info("Descargando datos de la Champions...")
                elif i == 60:
                    status_area.info("Procesando eventos del partido...")
                elif i == 80:
                    status_area.info("Preparando archivo CSV...")
                
                # Si estamos cerca del final, ejecutar realmente la notebook
                if i == 85:
                    csv_path = run_notebook("notebooks/Tarea_M5_MPAD_Zandalinas_Victor_extraccionAPI_Limpieza datos.ipynb", output_type='csv')
                
                time.sleep(0.05)  # Pequeña pausa para visualizar el progreso
            
            # Mostrar resultado final
            if csv_path:
                status_area.success("Extracción completada con éxito")
                st.markdown(
                    get_binary_file_downloader_html(csv_path, "📥 Descargar CSV"),
                    unsafe_allow_html=True
                )
            else:
                status_area.error("Error en la extracción de datos")
    
    with col2:
        # Botón 2 con ícono
        if st.button("📈 Visualización datos\nArsenal - Madrid"):
            # Crear un área para la barra de progreso
            progress_area = st.empty()
            progress_bar = progress_area.progress(0)
            
            # Mostrar mensaje de procesamiento
            status_area = st.empty()
            status_area.info("Iniciando generación de visualizaciones...")
            
            # Simulación de progreso y ejecución real
            for i in range(101):
                # Actualizar barra de progreso
                progress_bar.progress(i)
                
                # Cambiar mensajes según el progreso
                if i == 20:
                    status_area.info("Cargando datos del partido...")
                elif i == 40:
                    status_area.info("Analizando estadísticas...")
                elif i == 60:
                    status_area.info("Generando gráficos...")
                elif i == 80:
                    status_area.info("Finalizando visualización...")
                
                # Si estamos cerca del final, ejecutar realmente la notebook
                if i == 85:
                    plot_path = extract_last_subplot("notebooks/Tarea_M5_MPAD_Zandalinas_Victor_visualizaciones_arsenal_madrid.ipynb")
                
                time.sleep(0.05)  # Pequeña pausa para visualizar el progreso
            
            # Mostrar resultado final
            if plot_path:
                status_area.success("Visualización generada con éxito")
                st.image(plot_path)
            else:
                status_area.error("Error al generar la visualización")
    
    with col3:
        # Botón 3 mejorado con manejo de errores
        if st.button("📝 Informe Ollama\nArsenal-Madrid\nExtraccion PDF"):
            # Crear un área para la barra de progreso
            progress_area = st.empty()
            progress_bar = progress_area.progress(0)
            
            # Mostrar mensaje de procesamiento
            status_area = st.empty()
            status_area.info("Iniciando generación del informe...")
            
            try:
                # Simulación de progreso y ejecución real
                pdf_path = None
                for i in range(101):
                    # Actualizar barra de progreso
                    progress_bar.progress(i)
                    
                    # Cambiar mensajes según el progreso
                    if i == 10:
                        status_area.info("Verificando dependencias...")
                    elif i == 20:
                        status_area.info("Preparando datos para análisis...")
                    elif i == 40:
                        status_area.info("Procesando con Ollama...")
                    elif i == 60:
                        status_area.info("Generando insights del partido...")
                    elif i == 80:
                        status_area.info("Preparando documento PDF...")
                    
                    # Si estamos cerca del final, ejecutar realmente la notebook
                    if i == 85:
                        # Ejecutar la notebook y obtener directamente la ruta del PDF generado
                        pdf_path = run_notebook_and_get_pdf("notebooks/Tarea_M5_MPAD_Zandalinas_Victor_analisis_con_Ollama.ipynb")
                    
                    time.sleep(0.05)  # Pequeña pausa para visualizar el progreso
                
                # Mostrar resultado final
                if pdf_path and os.path.exists(pdf_path):
                    status_area.success("Informe PDF generado con éxito")
                    st.markdown(
                        get_binary_file_downloader_html(pdf_path, "📥 Descargar PDF"),
                        unsafe_allow_html=True
                    )
                else:
                    # Intento alternativo con la función original para generar al menos un HTML
                    status_area.warning("No se pudo generar el PDF directamente. Intentando método alternativo...")
                    
                    # Usar la función original para generar al menos un HTML
                    output_path = convert_notebook_to_html_or_pdf("notebooks/Tarea_M5_MPAD_Zandalinas_Victor_analisis_con_Ollama.ipynb")
                    
                    if output_path and os.path.exists(output_path):
                        status_area.success(f"Se ha generado un {os.path.splitext(output_path)[1][1:].upper()} como alternativa")
                        st.markdown(
                            get_binary_file_downloader_html(output_path, f"📥 Descargar {os.path.splitext(output_path)[1][1:].upper()}"),
                            unsafe_allow_html=True
                        )
                    else:
                        status_area.error("No se pudo generar el informe. Verifica las dependencias manualmente.")
                        st.error("""
                        Para resolver este problema:
                        1. Instala manualmente la biblioteca fpdf: `pip install fpdf`
                        2. Ejecuta la notebook manualmente desde Jupyter
                        3. Verifica que se genere el archivo PDF correctamente
                        """)
            except Exception as e:
                status_area.error(f"Error inesperado: {str(e)}")
                st.error(f"Detalles del error: {str(e)}")

# Inicialización de la sesión
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Mostrar la página correspondiente
if st.session_state['logged_in']:
    main_page()
else:
    login()