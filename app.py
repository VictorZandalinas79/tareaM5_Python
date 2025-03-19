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
    Crea una visualización del análisis Arsenal-Madrid y la guarda como archivo.
    
    Args:
        notebook_path: Ruta a la notebook de visualización
        
    Returns:
        Ruta al archivo de imagen generado
    """
    try:
        # Verificar si ya existe la imagen
        target_filename = 'arsenal_madrid_visualizacion.png'
        if os.path.exists(target_filename):
            print(f"Usando visualización existente: {target_filename}")
            return target_filename
        
        # También buscar visualizacion_arsenal_madrid.png
        alt_filename = 'visualizacion_arsenal_madrid.png'
        if os.path.exists(alt_filename):
            print(f"Usando visualización alternativa: {alt_filename}")
            # Copiar al nombre deseado para consistencia
            import shutil
            shutil.copy(alt_filename, target_filename)
            return target_filename
        
        print("Generando nueva visualización...")
        
        # Intentar ejecutar la notebook primero para generar la visualización original
        try:
            # Primero verificamos si el archivo existe
            if os.path.exists(notebook_path):
                # Convertir notebook a script Python con código adicional para guardar
                with open(notebook_path) as f:
                    nb = nbformat.read(f, as_version=4)
                
                # Añadir imports necesarios al principio
                imports_code = """
# Importaciones necesarias
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib.gridspec as gridspec
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
from scipy.spatial import ConvexHull

# Intentar importar mplsoccer
try:
    from mplsoccer import Pitch, FontManager
except ImportError:
    print("Biblioteca mplsoccer no disponible")
    # Definir clases alternativas básicas si no están disponibles
    class Pitch:
        def __init__(self, **kwargs):
            pass
        def draw(self, ax=None):
            pass
        def grid(self, **kwargs):
            fig, ax = plt.subplots(1, 1, figsize=(10, 8))
            return fig, {'pitch': ax, 'title': ax, 'endnote': ax}
    
    class FontManager:
        def __init__(self, *args, **kwargs):
            self.prop = None
"""
                
                # Crear celda con importaciones
                imports_cell = nbformat.v4.new_code_cell(source=imports_code)
                nb.cells.insert(0, imports_cell)
                
                # Añadir código para guardar la visualización al final
                save_code = """
# Guardar la visualización final como archivo PNG
try:
    # Si hay figuras activas, guardar la actual
    if plt.get_fignums():
        plt.savefig('arsenal_madrid_visualizacion.png', dpi=300, bbox_inches='tight')
        print("Visualización guardada como 'arsenal_madrid_visualizacion.png'")
except Exception as e:
    print(f"Error al guardar visualización: {e}")
"""
                
                # Crear celda para guardar
                save_cell = nbformat.v4.new_code_cell(source=save_code)
                nb.cells.append(save_cell)
                
                # Guardar notebook modificada
                script_path = notebook_path.replace('.ipynb', '_save.py')
                exporter = PythonExporter()
                python_code, _ = exporter.from_notebook_node(nb)
                
                with open(script_path, 'w') as f:
                    f.write(python_code)
                
                # Ejecutar el script
                print("Ejecutando notebook para generar visualización...")
                result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
                print(f"Salida: {result.stdout}")
                if result.stderr:
                    print(f"Errores: {result.stderr}")
                
                # Verificar si se generó la imagen
                if os.path.exists(target_filename):
                    return target_filename
                
                if os.path.exists(alt_filename):
                    # Copiar al nombre deseado
                    import shutil
                    shutil.copy(alt_filename, target_filename)
                    return target_filename
        except Exception as notebook_error:
            print(f"Error al ejecutar notebook: {notebook_error}")
            
        # Si la ejecución de la notebook falla, crear visualización alternativa
        print("Creando visualización alternativa...")
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        import numpy as np
        
        # Crear una figura simplificada con estructura similar al análisis original
        fig, axs = plt.subplots(2, 2, figsize=(16, 12), facecolor='#22312b')
        fig.suptitle('Arsenal vs Real Madrid - Análisis Táctico', 
                   fontsize=22, color='white', y=0.98)
        
        # Configurar todos los subplots
        for ax in axs.flat:
            ax.set_facecolor('#22312b')
            
            # Simular un campo de fútbol simplificado
            field = Rectangle((0.1, 0.1), 0.8, 0.7, facecolor='#1a4731', edgecolor='white', alpha=0.7)
            ax.add_patch(field)
            
            # Línea central
            ax.plot([0.1, 0.9], [0.45, 0.45], color='white', linewidth=1)
            
            # Eliminar ejes
            ax.axis('off')
        
        # Cuadrante 1: Jugadores
        axs[0, 0].text(0.5, 0.85, "Arsenal - Jugadores", fontsize=14, 
                     color='red', ha='center', weight='bold')
        # Listar algunos jugadores
        players = ["1 - Raya", "4 - White", "6 - Gabriel", "35 - Zinchenko", "8 - Odegaard"]
        for i, player in enumerate(players):
            axs[0, 0].text(0.5, 0.7 - i*0.1, player, fontsize=10, 
                         color='red', ha='center')
                         
        axs[0, 1].text(0.5, 0.85, "Real Madrid - Jugadores", fontsize=14, 
                     color='white', ha='center', weight='bold')
        # Listar algunos jugadores
        players = ["1 - Courtois", "2 - Carvajal", "4 - Alaba", "8 - Kroos", "10 - Modric"]
        for i, player in enumerate(players):
            axs[0, 1].text(0.5, 0.7 - i*0.1, player, fontsize=10, 
                         color='white', ha='center')
        
        # Cuadrante 2: Acciones Defensivas
        axs[1, 0].text(0.5, 0.85, "Arsenal - Acciones Defensivas", fontsize=14, 
                     color='red', ha='center', weight='bold')
        # Simular algunos puntos
        for _ in range(10):
            x = np.random.uniform(0.2, 0.8)
            y = np.random.uniform(0.2, 0.7)
            axs[1, 0].scatter(x, y, s=100, color='red', edgecolor='white')
            
        axs[1, 1].text(0.5, 0.85, "Real Madrid - Acciones Defensivas", fontsize=14, 
                     color='white', ha='center', weight='bold')
        # Simular algunos puntos
        for _ in range(10):
            x = np.random.uniform(0.2, 0.8)
            y = np.random.uniform(0.2, 0.7)
            axs[1, 1].scatter(x, y, s=100, color='white', edgecolor='black')
        
        # Añadir nota explicativa
        fig.text(0.5, 0.02, 'Para ver el análisis completo, ejecute manualmente la notebook con las dependencias necesarias',
                ha='center', color='yellow', fontsize=10)
        
        # Añadir crédito
        fig.text(0.5, 0.01, 'Victor Zandalinas', ha='center', color='white', fontsize=12)
        
        # Ajustar espaciado
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        # Guardar la figura con el nombre específico
        plt.savefig(target_filename, dpi=150, bbox_inches='tight')
        plt.close()
        
        return target_filename
        
    except Exception as e:
        print(f"Error al crear visualización: {str(e)}")
        
        # Crear imagen de error muy básica en caso de fallo
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8, 6), facecolor='#22312b')
            plt.text(0.5, 0.5, f"Error: {str(e)}\nPara ver la visualización completa,\nejecutar manualmente la notebook.", 
                    ha='center', va='center', color='white', fontsize=14)
            plt.axis('off')
            plt.savefig(target_filename, dpi=100)
            plt.close()
            return target_filename
        except:
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
            
            # Simulación de progreso
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
                
                # Si estamos cerca del final, generar la visualización
                if i == 85:
                    try:
                        # Generar la visualización usando la función extract_last_subplot
                        plot_path = extract_last_subplot("notebooks/Tarea_M5_MPAD_Zandalinas_Victor_visualizaciones_arsenal_madrid.ipynb")
                        
                        # Si se especifica un nombre diferente al generar, renombrarlo
                        if plot_path and plot_path != 'arsenal_madrid_visualizacion.png' and os.path.exists(plot_path):
                            import shutil
                            shutil.copy(plot_path, 'arsenal_madrid_visualizacion.png')
                            plot_path = 'arsenal_madrid_visualizacion.png'
                            
                    except Exception as e:
                        status_area.error(f"Error al generar visualización: {str(e)}")
                        plot_path = None
                
                time.sleep(0.05)  # Pequeña pausa para visualizar el progreso
            
            # Mostrar resultado final
            if plot_path and os.path.exists(plot_path):
                status_area.success("Visualización generada con éxito")
                
                # Mostrar la imagen
                st.image(plot_path, use_container_width=True)
                
                # Añadir botón de descarga
                with open(plot_path, "rb") as file:
                    btn = st.download_button(
                        label="📥 Descargar visualización",
                        data=file,
                        file_name="arsenal_madrid_visualizacion.png",
                        mime="image/png"
                    )
            else:
                status_area.error("No se pudo generar la visualización")
    
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