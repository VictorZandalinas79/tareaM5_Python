#!/usr/bin/env python
# coding: utf-8

# ### e) Implementación de Ollama para Análisis Generativo (20 puntos)

# * Instale Ollama y cargue un modelo apropiado para análisis de texto.
# * Desarrolle prompts efectivos para generar análisis deportivos basados en los datos procesados.
# * Implemente la integración entre sus datos procesados y Ollama.
# * Genere al menos 3 análisis diferentes utilizando Ollama (por ejemplo, resumen de rendimiento, predicciones, análisis táctico).

# In[24]:


# Importaciones necesarias
import pandas as pd
import requests
import json
import os
from fpdf import FPDF
from PIL import Image
import matplotlib.pyplot as plt
import datetime


# In[25]:


# Cargar el archivo CSV desde la misma carpeta de la notebook
df_arsenalmadrid = pd.read_csv('eventos.csv')

df_arsenalmadrid.head()


# In[26]:


def prepare_passes_stats(df):
    """Prepara estadísticas de pases para el prompt de Ollama"""
    # Filtrar sólo los pases
    df_pass = df[df['type'] == 'Pass'].copy()

    # Separar por equipos
    arsenal_passes = df_pass[df_pass['teamName'] == 'Arsenal']
    madrid_passes = df_pass[df_pass['teamName'] == 'Real Madrid']

    # Estadísticas de pases
    arsenal_total = len(arsenal_passes)
    madrid_total = len(madrid_passes)

    # Calcular pases completados
    arsenal_completed = len(arsenal_passes[arsenal_passes['outcomeType'] == 'Successful'])
    madrid_completed = len(madrid_passes[madrid_passes['outcomeType'] == 'Successful'])

    # Calcular porcentajes de éxito
    arsenal_success_rate = (arsenal_completed / arsenal_total * 100) if arsenal_total > 0 else 0
    madrid_success_rate = (madrid_completed / madrid_total * 100) if madrid_total > 0 else 0

    # Analizar zonas de pases dividiendo el campo en 9 zonas (3x3)
    def get_zone(x, y):
        zone_x = 1 if x < 33 else (2 if x < 66 else 3)
        zone_y = 1 if y < 33 else (2 if y < 66 else 3)
        return f"Zona {zone_x}-{zone_y}"

    # Añadir columnas de zona
    arsenal_passes['zone_start'] = arsenal_passes.apply(lambda row: get_zone(row['x'], row['y']), axis=1)
    arsenal_passes['zone_end'] = arsenal_passes.apply(lambda row: get_zone(row['endX'], row['endY']), axis=1)

    madrid_passes['zone_start'] = madrid_passes.apply(lambda row: get_zone(row['x'], row['y']), axis=1)
    madrid_passes['zone_end'] = madrid_passes.apply(lambda row: get_zone(row['endX'], row['endY']), axis=1)

    # Zonas más frecuentes
    arsenal_zones_start = arsenal_passes['zone_start'].value_counts().head(3).to_dict()
    arsenal_zones_end = arsenal_passes['zone_end'].value_counts().head(3).to_dict()

    madrid_zones_start = madrid_passes['zone_start'].value_counts().head(3).to_dict()
    madrid_zones_end = madrid_passes['zone_end'].value_counts().head(3).to_dict()

    # Formatear estadísticas para el prompt
    stats = f"""ESTADÍSTICAS DE PASES: ARSENAL VS REAL MADRID

Arsenal:
- Total de pases: {arsenal_total}
- Pases completados: {arsenal_completed} ({arsenal_success_rate:.1f}%)
- Zonas de origen más frecuentes:
  {', '.join([f"{zone}: {count}" for zone, count in arsenal_zones_start.items()])}
- Zonas de destino más frecuentes:
  {', '.join([f"{zone}: {count}" for zone, count in arsenal_zones_end.items()])}

Real Madrid:
- Total de pases: {madrid_total}
- Pases completados: {madrid_completed} ({madrid_success_rate:.1f}%)
- Zonas de origen más frecuentes:
  {', '.join([f"{zone}: {count}" for zone, count in madrid_zones_start.items()])}
- Zonas de destino más frecuentes:
  {', '.join([f"{zone}: {count}" for zone, count in madrid_zones_end.items()])}

Distribución de altura de pases (si disponible):
Arsenal: {arsenal_passes['height'].value_counts().to_dict() if 'height' in arsenal_passes.columns else 'No disponible'}
Real Madrid: {madrid_passes['height'].value_counts().to_dict() if 'height' in madrid_passes.columns else 'No disponible'}
"""
    return stats


# In[27]:


def prepare_players_stats(df):
    """Prepara estadísticas de jugadores para el prompt de Ollama"""
    # Separar por equipos
    arsenal_df = df[df['teamName'] == 'Arsenal']
    madrid_df = df[df['teamName'] == 'Real Madrid']

    # Participación general (todas las acciones)
    arsenal_participation = arsenal_df.groupby('player_name')['type'].count().sort_values(ascending=False)
    madrid_participation = madrid_df.groupby('player_name')['type'].count().sort_values(ascending=False)

    # Métricas específicas - Definir categorías
    offensive_actions = ['Shot', 'Goal', 'TakeOn', 'KeyPass', 'Pass']
    defensive_actions = ['Tackle', 'Interception', 'BlockedPass', 'Clearance', 'BallRecovery']

    # Jugadores ofensivos
    arsenal_offensive = arsenal_df[arsenal_df['type'].isin(offensive_actions)].groupby('player_name')['type'].count().sort_values(ascending=False)
    madrid_offensive = madrid_df[madrid_df['type'].isin(offensive_actions)].groupby('player_name')['type'].count().sort_values(ascending=False)

    # Jugadores defensivos
    arsenal_defensive = arsenal_df[arsenal_df['type'].isin(defensive_actions)].groupby('player_name')['type'].count().sort_values(ascending=False)
    madrid_defensive = madrid_df[madrid_df['type'].isin(defensive_actions)].groupby('player_name')['type'].count().sort_values(ascending=False)

    # Formatear estadísticas para el prompt
    stats = f"""ESTADÍSTICAS DE JUGADORES: ARSENAL VS REAL MADRID

Top 5 jugadores de Arsenal por total de acciones:
{', '.join([f"{player}: {actions}" for player, actions in arsenal_participation.head(5).items()])}

Top 5 jugadores de Real Madrid por total de acciones:
{', '.join([f"{player}: {actions}" for player, actions in madrid_participation.head(5).items()])}

Top 3 jugadores ofensivos de Arsenal:
{', '.join([f"{player}: {actions}" for player, actions in arsenal_offensive.head(3).items()])}

Top 3 jugadores ofensivos de Real Madrid:
{', '.join([f"{player}: {actions}" for player, actions in madrid_offensive.head(3).items()])}

Top 3 jugadores defensivos de Arsenal:
{', '.join([f"{player}: {actions}" for player, actions in arsenal_defensive.head(3).items()])}

Top 3 jugadores defensivos de Real Madrid:
{', '.join([f"{player}: {actions}" for player, actions in madrid_defensive.head(3).items()])}

Goles Arsenal:
{arsenal_df[arsenal_df['type'] == 'Goal']['player_name'].value_counts().to_dict()}

Goles Real Madrid:
{madrid_df[madrid_df['type'] == 'Goal']['player_name'].value_counts().to_dict()}
"""
    return stats


# In[28]:


def prepare_prediction_stats(df):
    """Prepara estadísticas para predicción de futuros partidos"""
    # Separar por equipos
    arsenal_df = df[df['teamName'] == 'Arsenal']
    madrid_df = df[df['teamName'] == 'Real Madrid']

    # Estadísticas básicas
    arsenal_goals = len(arsenal_df[arsenal_df['type'] == 'Goal'])
    madrid_goals = len(madrid_df[madrid_df['type'] == 'Goal'])

    arsenal_shots = len(arsenal_df[arsenal_df['type'] == 'Shot'])
    madrid_shots = len(madrid_df[madrid_df['type'] == 'Shot'])

    arsenal_passes = len(arsenal_df[arsenal_df['type'] == 'Pass'])
    madrid_passes = len(madrid_df[madrid_df['type'] == 'Pass'])

    # Eficiencia de tiro
    arsenal_efficiency = (arsenal_goals / arsenal_shots * 100) if arsenal_shots > 0 else 0
    madrid_efficiency = (madrid_goals / madrid_shots * 100) if madrid_shots > 0 else 0

    # Calcular el rendimiento defensivo
    defensive_actions = ['Tackle', 'Interception', 'BlockedPass', 'Clearance']
    arsenal_defensive = len(arsenal_df[arsenal_df['type'].isin(defensive_actions)])
    madrid_defensive = len(madrid_df[madrid_df['type'].isin(defensive_actions)])

    # Formatear estadísticas para el prompt
    stats = f"""ESTADÍSTICAS PARA PREDICCIÓN: ARSENAL VS REAL MADRID

Resultado del partido analizado:
Arsenal {arsenal_goals} - {madrid_goals} Real Madrid

Estadísticas ofensivas:
- Arsenal: {arsenal_shots} tiros, {arsenal_goals} goles, eficiencia {arsenal_efficiency:.1f}%
- Real Madrid: {madrid_shots} tiros, {madrid_goals} goles, eficiencia {madrid_efficiency:.1f}%

Posesión (basada en pases):
- Arsenal: {arsenal_passes} pases
- Real Madrid: {madrid_passes} pases

Estadísticas defensivas:
- Arsenal: {arsenal_defensive} acciones defensivas
- Real Madrid: {madrid_defensive} acciones defensivas

Jugadores destacados:
Arsenal:
- Máximos goleadores: {arsenal_df[arsenal_df['type'] == 'Goal']['player_name'].value_counts().head(2).to_dict()}
- Máximos asistentes: {arsenal_df[arsenal_df['type'] == 'Pass']['player_name'].value_counts().head(2).to_dict()}

Real Madrid:
- Máximos goleadores: {madrid_df[madrid_df['type'] == 'Goal']['player_name'].value_counts().head(2).to_dict()}
- Máximos asistentes: {madrid_df[madrid_df['type'] == 'Pass']['player_name'].value_counts().head(2).to_dict()}
"""
    return stats


# In[29]:


def query_ollama(prompt, system_prompt, model="llama3.2:latest"):
    """Envía una consulta a Ollama y devuelve la respuesta"""
    url = "http://localhost:11434/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False
    }

    try:
        print(f"Consultando a Ollama (modelo: {model})...")
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            print("✅ Respuesta recibida correctamente de Ollama")
            return response.json().get("response", "")
        else:
            print(f"❌ Error de Ollama: Código {response.status_code}")
            print(f"Respuesta: {response.text[:500]}...")
            return None
    except Exception as e:
        print(f"❌ Error al comunicarse con Ollama: {e}")
        return None


# In[30]:


def generate_reports(df, model="llama3.2:latest"):
    """Genera los tres informes usando Ollama"""

    # 1. Informe de Pases
    print("\nPreparando estadísticas de pases...")
    passes_stats = prepare_passes_stats(df)

    passes_system_prompt = """
    Eres un analista táctico de fútbol especializado en análisis de pases. 
    Tu tarea es crear un informe detallado sobre el patrón de pases en un partido entre Arsenal y Real Madrid.
    Estructura tu análisis en secciones claras con títulos y subtítulos.
    Incluye interpretaciones tácticas de los datos proporcionados.
    """

    passes_prompt = f"""
    Con base en las siguientes estadísticas de pases del partido entre Arsenal y Real Madrid, 
    genera un análisis detallado sobre los patrones de pases, la altura de los pases, las zonas 
    de origen y destino más frecuentes, y las implicaciones tácticas de estos datos:

    {passes_stats}

    Tu informe debe incluir:
    1. Un análisis general del estilo de juego de cada equipo basado en sus patrones de pases
    2. Un análisis de las zonas del campo donde cada equipo fue más activo con sus pases
    3. Conclusiones sobre cómo estos patrones de pases influyeron en el desarrollo del partido

    Formato tu respuesta con títulos claros y secciones bien definidas.
    """

    print("Generando informe de pases con Ollama...")
    passes_report = query_ollama(passes_prompt, passes_system_prompt, model)
    if not passes_report:
        passes_report = "No se pudo generar el informe de pases debido a un error con Ollama."

    # 2. Informe de Jugadores
    print("\nPreparando estadísticas de jugadores...")
    players_stats = prepare_players_stats(df)

    players_system_prompt = """
    Eres un scout profesional de fútbol con experiencia evaluando el rendimiento individual de jugadores.
    Tu tarea es analizar el desempeño de los jugadores en un partido entre Arsenal y Real Madrid.
    Debes identificar a los jugadores destacados, evaluar sus contribuciones y crear rankings por diferentes métricas.
    """

    players_prompt = f"""
    Basándote en las siguientes estadísticas de los jugadores del partido entre Arsenal y Real Madrid,
    genera un análisis detallado sobre el rendimiento individual de los futbolistas más destacados:

    {players_stats}

    Tu informe debe incluir:
    1. Un ranking de los jugadores más influyentes de cada equipo
    2. Un análisis de los jugadores destacados en facetas ofensivas
    3. Un análisis de los jugadores destacados en facetas defensivas
    4. Conclusiones sobre qué jugadores fueron más determinantes para el resultado

    Asegúrate de contextualizar estos datos y explicar por qué estos jugadores destacaron, 
    no sólo enumerar las estadísticas.
    """

    print("Generando informe de jugadores con Ollama...")
    players_report = query_ollama(players_prompt, players_system_prompt, model)
    if not players_report:
        players_report = "No se pudo generar el informe de jugadores debido a un error con Ollama."

    # 3. Informe Predictivo
    print("\nPreparando estadísticas para predicción...")
    prediction_stats = prepare_prediction_stats(df)

    prediction_system_prompt = """
    Eres un analista predictivo especializado en fútbol con experiencia en modelado estadístico.
    Tu tarea es predecir cómo sería un futuro enfrentamiento entre Arsenal y Real Madrid basándote en datos históricos.
    Debes ser objetivo, analítico y considerar diferentes factores tácticos y estadísticos.
    """

    prediction_prompt = f"""
    Basándote en las siguientes estadísticas del partido entre Arsenal y Real Madrid,
    predice cómo sería un futuro enfrentamiento entre estos equipos:

    {prediction_stats}

    Tu análisis predictivo debe incluir:
    1. Factores clave que podrían influir en un futuro enfrentamiento
    2. Predicción de cómo cada equipo podría plantear tácticamente el partido
    3. Jugadores que podrían ser decisivos en el próximo encuentro
    4. Una predicción del posible resultado y por qué

    Considera aspectos como los estilos de juego, fortalezas y debilidades mostradas en los datos,
    y cómo podrían evolucionar en un próximo partido.
    """

    print("Generando análisis predictivo con Ollama...")
    prediction_report = query_ollama(prediction_prompt, prediction_system_prompt, model)
    if not prediction_report:
        prediction_report = "No se pudo generar el análisis predictivo debido a un error con Ollama."

    return {
        "passes": passes_report,
        "players": players_report,
        "prediction": prediction_report
    }


# In[31]:


def create_pdf_report(reports, output_file="analisis_arsenal_madrid.pdf"):
    """Crea un PDF con los tres informes y los escudos de los equipos"""
    print("\nCreando PDF con los informes...")

    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'Análisis: Arsenal vs Real Madrid', 0, 1, 'C')
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    # Crear PDF
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Función para procesar texto de los informes
    def add_report_text(pdf, text, title):
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(5)

        # Procesar el texto por párrafos
        pdf.set_font('Arial', '', 11)
        paragraphs = text.split('\n\n')

        for paragraph in paragraphs:
            # Detectar títulos y subtítulos
            if paragraph.strip().startswith('#'):
                lines = paragraph.strip().split('\n')
                for line in lines:
                    if line.startswith('# '):
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(0, 10, line[2:], 0, 1)
                    elif line.startswith('## '):
                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(0, 10, line[3:], 0, 1)
                    elif line.startswith('### '):
                        pdf.set_font('Arial', 'B', 11)
                        pdf.cell(0, 10, line[4:], 0, 1)
                    else:
                        pdf.set_font('Arial', '', 11)
                        pdf.multi_cell(0, 7, line)
            else:
                pdf.set_font('Arial', '', 11)
                pdf.multi_cell(0, 7, paragraph)

            pdf.ln(4)

    # Portada
    pdf.add_page()
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 20, 'ANÁLISIS TÁCTICO', 0, 1, 'C')
    pdf.cell(0, 20, 'ARSENAL vs REAL MADRID', 0, 1, 'C')

    # Fecha actual
    pdf.set_font('Arial', '', 12)
    current_date = datetime.datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 10, f'Fecha: {current_date}', 0, 1, 'C')

    # Añadir escudos
    try:
        # Escudo del Arsenal
        if os.path.exists('logos/escudo_arsenal.png'):
            pdf.image('logos/escudo_arsenal.png', x=30, y=100, w=60)

        # Escudo del Real Madrid
        if os.path.exists('logos/escudo_realmadrid.png'):
            pdf.image('logos/escudo_realmadrid.png', x=120, y=100, w=60)
    except Exception as e:
        print(f"Error al cargar escudos: {e}")
        pdf.ln(50)
        pdf.cell(0, 10, 'Error al cargar escudos', 0, 1, 'C')

    # Añadir los informes
    add_report_text(pdf, reports["passes"], "INFORME DE PASES")
    add_report_text(pdf, reports["players"], "INFORME DE JUGADORES")
    add_report_text(pdf, reports["prediction"], "ANÁLISIS PREDICTIVO")

    # Guardar el PDF
    pdf.output(output_file)
    print(f"PDF generado: {output_file}")
    return output_file


# In[32]:


def check_ollama_models():
    """Verifica qué modelos están disponibles en Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get('models', [])
            model_names = [m.get('name') for m in models]
            print(f"Modelos disponibles en Ollama: {model_names}")
            return model_names
        else:
            print(f"Error al consultar Ollama: código {response.status_code}")
            return []
    except Exception as e:
        print(f"Error al conectar con Ollama: {e}")
        return []


# In[33]:


def main(df):
    """Función principal"""
    print("Iniciando generación de informes para Arsenal vs Real Madrid")

    # Comprobar que Ollama está funcionando y qué modelos hay disponibles
    available_models = check_ollama_models()

    if not available_models:
        print("❌ No se pudo conectar con Ollama o no hay modelos disponibles.")
        print("Asegúrate de que Ollama está en ejecución con 'ollama serve'")
        return

    # Elegir el modelo preferido si está disponible
    preferred_models = ["llama3.2:latest", "llama3.2", "llama3", "qwen2.5:14b-instruct-q4_K_M", "qwen2.5", "mistral:7b"]

    model = None
    for preferred in preferred_models:
        for available in available_models:
            if preferred in available:
                model = available
                break
        if model:
            break

    if not model and available_models:
        model = available_models[0]  # Usar el primer modelo disponible

    if not model:
        print("❌ No se encontraron modelos adecuados en Ollama.")
        return

    print(f"Usando modelo: {model}")

    # Generar los informes
    reports = generate_reports(df, model)

    # Crear el PDF
    pdf_file = create_pdf_report(reports)

    print("\nProceso completado con éxito.")
    print(f"El informe completo ha sido guardado en: {pdf_file}")

# Ejemplo de uso:
main(df_arsenalmadrid)

