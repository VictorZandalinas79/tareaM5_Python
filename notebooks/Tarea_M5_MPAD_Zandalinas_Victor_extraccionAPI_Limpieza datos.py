#!/usr/bin/env python
# coding: utf-8

# # Tarea M5 MPAD de Zandalinas_Victor

# #### Importar pandas y las librerías utilizadas para resolver la tarea.

# In[1]:


# Importe todas las librerias que se usan en esta notebook
import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from IPython.display import display, HTML
import time
import matplotlib.pyplot as plt
from mplsoccer import Pitch, FontManager
import seaborn as sns
import numpy as np


# # 1. Cafecito API by Sports Data Campus
#  1.0.1 

#  
# [ Base URL: https://api-cafecito.onrender.com/ ]
# 

# In[2]:


# Cuente y describa que api eligió
# Configuración base para la API
BASE_URL = "https://api-cafecito.onrender.com"
AUTH_TOKEN = "EAAHlp1ycWFIBOzFZASIPjVtB1n30C8jUBKHo"

# Cabeceras para las peticiones
headers = {
    'Authorization': f'Bearer {AUTH_TOKEN}',
    'Content-Type': 'application/json'
}


# # 2. Realice las siguientes tareas, creando funciones para cada paso principal:

# ### a) Análisis y Planificación (10 puntos)

# * Analice la estructura y documentación de la API o conjunto de datos elegido.
# * Identifique los endpoints relevantes o los datos específicos a extraer.
# * Planifique la estrategia de adquisición de datos, considerando límites de tasa si es aplicable.
# * Documente las consideraciones éticas y legales del uso de la API o datos.

# In[3]:


##1.Función auxiliar para hacer peticiones a la API
def make_api_request(endpoint):
    """
    Realiza una petición GET a la API y devuelve los datos JSON.

    Args:
        endpoint (str): El endpoint de la API a consultar

    Returns:
        dict: Los datos recibidos de la API en formato JSON
    """
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=headers)

    # Verificar si la petición fue exitosa
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al realizar la petición: {response.status_code}")
        print(response.text)
        return None


# In[4]:


# Mostrar todos los endpoints disponibles en la API MPAD Cafecito y su propósito
api_structure = [
    {"endpoint": "/competitions", "descripción": "Devuelve todas las competiciones disponibles", "uso": "Obtener lista de competiciones"},
    {"endpoint": "/features/qualifiers", "descripción": "Devuelve la lista de qualifiers", "uso": "Obtener metadatos sobre qualifiers"},
    {"endpoint": "/features/typeId", "descripción": "Devuelve la lista de registros extraída de typeId", "uso": "Obtener metadatos sobre tipos de eventos"},
    {"endpoint": "/match/base/{match_id}", "descripción": "Devuelve la información base del partido", "uso": "Obtener datos básicos de un partido específico"},
    {"endpoint": "/match/events/{match_id}", "descripción": "Obtiene todos los eventos del partido", "uso": "Obtener eventos detallados de un partido específico"},
    {"endpoint": "/match/formationIdNameMappings/{match_id}", "descripción": "Devuelve la lista de formationIdNameMappings para el partido", "uso": "Obtener mapeos de formaciones"},
    {"endpoint": "/match/formations/{match_id}", "descripción": "Devuelve todas las formaciones del equipo local y del equipo visitante", "uso": "Obtener formaciones tácticas"},
    {"endpoint": "/match/incidentEvents/{match_id}", "descripción": "Devuelve los incidentEvents del partido", "uso": "Obtener eventos incidentales"},
    {"endpoint": "/match/matchCentreEventTypeJson/{match_id}", "descripción": "Devuelve la lista de matchCentreEventTypeJson para el partido", "uso": "Obtener tipos de eventos del centro de partido"},
    {"endpoint": "/match/players/{match_id}", "descripción": "Devuelve la lista de jugadores que participaron en el partido", "uso": "Obtener información de jugadores"},
    {"endpoint": "/match/stats/{match_id}", "descripción": "Devuelve los stats del equipo local y visitante", "uso": "Obtener estadísticas del partido"},
    {"endpoint": "/match/{match_id}", "descripción": "Devuelve el contenido completo del partido en crudo", "uso": "Obtener todos los datos del partido"},
    {"endpoint": "/matches", "descripción": "Trae todos los partidos disponibles", "uso": "Obtener lista de todos los partidos"},
    {"endpoint": "/matches/competition/{competition}", "descripción": "Devuelve los partidos filtrados por competición", "uso": "Obtener partidos de una competición específica"},
    {"endpoint": "/matches/competition/{competition}/season/{season}", "descripción": "Trae los partidos de una competición y una temporada específicas", "uso": "Filtrar partidos por competición y temporada"},
    {"endpoint": "/teams", "descripción": "Devuelve la lista de equipos", "uso": "Obtener información de equipos"}
]

# Mostrar la estructura de la API en un DataFrame
api_structure_df = pd.DataFrame(api_structure)
print("Estructura de la API MPAD Cafecito:")
display(api_structure_df)


# In[5]:


# Explorar los metadatos disponibles de la API para entender mejor su estructura
print("\nExplorando los metadatos de la API para entender su estructura:")

# Explorar qualifiers
qualifiers = make_api_request("/features/qualifiers")
if qualifiers:
    print("\n1. Qualifiers:")
    if isinstance(qualifiers, list):
        print(f"   - {len(qualifiers)} qualifiers disponibles")
        if len(qualifiers) > 0:
            print("   - Ejemplo de qualifier:")
            print(f"     {json.dumps(qualifiers[0], indent=2)}")
    else:
        print("   - Estructura no es una lista como se esperaba")

# Explorar typeId
type_ids = make_api_request("/features/typeId")
if type_ids:
    print("\n2. TypeIds:")
    if isinstance(type_ids, list):
        print(f"   - {len(type_ids)} typeIds disponibles")
        if len(type_ids) > 0:
            print("   - Ejemplo de typeId:")
            print(f"     {json.dumps(type_ids[0], indent=2)}")
    else:
        print("   - Estructura no es una lista como se esperaba")


# In[6]:


## 2. Identificación de Endpoints Relevantes

# Mostrar los endpoints más relevantes para nuestro análisis de eventos
relevant_endpoints = [
    {"endpoint": "/competitions", "relevancia": "Alta", "propósito": "Identificar la competición disponible"},
    {"endpoint": "/matches/competition/{competition}", "relevancia": "Alta", "propósito": "Obtener todos los partidos de la competición"},
    {"endpoint": "/match/events/{match_id}", "relevancia": "Alta", "propósito": "Obtener eventos detallados de cada partido"},
    {"endpoint": "/match/base/{match_id}", "relevancia": "Media", "propósito": "Enriquecer los datos con información básica del partido"},
    {"endpoint": "/teams", "relevancia": "Media", "propósito": "Obtener nombres de equipos para enriquecer los datos"},
    {"endpoint": "/match/players/{match_id}", "relevancia": "Baja", "propósito": "Obtener datos de jugadores (no necesario para el objetivo inicial)"},
    {"endpoint": "/match/stats/{match_id}", "relevancia": "Baja", "propósito": "Obtener estadísticas agregadas (no necesario para el objetivo inicial)"}
]

relevant_endpoints_df = pd.DataFrame(relevant_endpoints)
print("Endpoints relevantes para nuestro análisis:")
display(relevant_endpoints_df)

# Realizar una comprobación rápida de los endpoints clave
print("\nComprobación de los endpoints clave:")

# Verificar competiciones
competitions = make_api_request("/competitions")
if competitions:
    print(f"- Competiciones: {len(competitions)} disponibles")

# Verificar equipos
teams = make_api_request("/teams")
if teams:
    print(f"- Equipos: {len(teams)} disponibles")

# Verificar partidos (sin filtrar por competición aún)
matches = make_api_request("/matches")
if matches:
    print(f"- Partidos totales: {len(matches)} disponibles")


# In[7]:


## 3. Planificación de la Estrategia de Adquisición de Datos

# Definir nuestra estrategia de adquisición
print("\nEstrategia de adquisición de datos:")
print("""
1. Obtener la lista de competiciones (/competitions) - Un solo llamado a la API
2. Obtener todos los partidos de la competición (/matches/competition/{competition}) - Un llamado por competición
3. Para cada partido:
   a. Obtener eventos (/match/events/{match_id}) - Un llamado por partido
   b. Obtener información básica (/match/base/{match_id}) - Un llamado por partido
4. Obtener información de equipos (/teams) - Un solo llamado a la API

Total de llamados a la API = 1 + 1 + (N × 2) + 1 = 3 + 2N
donde N es el número de partidos en la competición
""")

# Estimar el número de llamados a la API
if 'matches' in locals() and matches:
    # Obtener el número aproximado de partidos por competición
    if competitions and len(competitions) > 0:
        comp_id = competitions[0].get('id') or competitions[0].get('competitionId')
        comp_matches = make_api_request(f"/matches/competition/{comp_id}")
        if comp_matches:
            n_matches = len(comp_matches)
            total_calls = 3 + (2 * n_matches)
            print(f"Para {n_matches} partidos en la competición, estimamos aproximadamente {total_calls} llamados a la API")

# Consideraciones sobre límites de tasa
print("\nConsideraciones sobre límites de tasa:")
print("""
La API MPAD Cafecito no especifica explícitamente límites de tasa. Sin embargo, como buena práctica:

1. Implementaremos un control de errores robusto para manejar posibles fallos en las peticiones
2. Podríamos implementar retrasos entre llamadas consecutivas para evitar sobrecargar el servidor
3. Si fuera necesario, podríamos implementar reintentos automáticos con espera exponencial

Al ser una API principalmente para uso educativo, no esperamos límites de tasa estrictos.
""")

# Implementar una función con manejo de errores y reintentos
print("\nFunción mejorada para peticiones a la API con manejo de errores:")

def make_api_request_robust(endpoint, max_retries=3, initial_delay=1):
    """
    Realiza una petición GET a la API con manejo de errores y reintentos.

    Args:
        endpoint (str): El endpoint de la API a consultar
        max_retries (int): Número máximo de reintentos
        initial_delay (float): Retraso inicial entre reintentos (segundos)

    Returns:
        dict: Los datos recibidos de la API en formato JSON
    """
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=headers, timeout=10)

            # Verificar si la petición fue exitosa
            if response.status_code == 200:
                return response.json()

            # Si el error es por límite de tasa, esperar más tiempo
            if response.status_code == 429:
                wait_time = initial_delay * (2 ** attempt)
                print(f"Límite de tasa alcanzado. Esperando {wait_time:.2f} segundos...")
                time.sleep(wait_time)
                continue

            # Otros errores
            print(f"Error en la petición (intento {attempt+1}/{max_retries+1}): {response.status_code}")
            print(response.text)

            # Si no es el último intento, esperar antes de reintentar
            if attempt < max_retries:
                wait_time = initial_delay * (2 ** attempt)
                print(f"Reintentando en {wait_time:.2f} segundos...")
                time.sleep(wait_time)

        except Exception as e:
            print(f"Excepción al realizar la petición (intento {attempt+1}/{max_retries+1}): {str(e)}")

            # Si no es el último intento, esperar antes de reintentar
            if attempt < max_retries:
                wait_time = initial_delay * (2 ** attempt)
                print(f"Reintentando en {wait_time:.2f} segundos...")
                time.sleep(wait_time)

    # Si llegamos aquí, todos los intentos fallaron
    print(f"Todos los intentos fallaron para el endpoint: {endpoint}")
    return None


# In[8]:


## 4. Consideraciones Éticas y Legales del Uso de la API

# Descargo de responsabilidad y aviso legal de la API
legal_disclaimer = """
Descargo de responsabilidad y Aviso Legal
La información y los datos presentados a través de esta API han sido obtenidos de fuentes disponibles públicamente en Internet. 
Esta aplicación se ha desarrollado únicamente con fines educativos, en el marco de los programas de Maestría de 
Sports Data Campus (SDC) y no tiene ningún propósito comercial. Se pone a disposición de los usuarios **tal cual**, 
sin ninguna garantía expresa o implícita de ningún tipo, incluyendo pero no limitándose a garantías de idoneidad 
para un propósito particular, exactitud, integridad o disponibilidad. Los derechos de autor, marcas y demás derechos 
de propiedad intelectual pertenecen a sus respectivos titulares. El uso de la información contenida en esta API se 
realiza bajo el principio del **uso justo** y para fines de enseñanza, investigación y análisis académico.

**IMPORTANTE:**
* El usuario es responsable de cumplir con todas las leyes y regulaciones aplicables en su jurisdicción en relación con el uso de los datos.
* Se recomienda que, en caso de querer utilizar estos datos para otros fines (por ejemplo, publicaciones, proyectos comerciales 
  o difusión pública), se consulte primero con los titulares de los derechos de la información original y se obtengan las 
  autorizaciones correspondientes.
* La administración de este proyecto no asume responsabilidad alguna por daños o perjuicios derivados del uso de la 
  información aquí dispuesta.
"""

print("Descargo de responsabilidad y aviso legal de la API:")
print(legal_disclaimer)

# Nuestras consideraciones éticas y legales
ethical_considerations = """
Consideraciones éticas y legales para nuestro uso de la API:

1. Uso educativo: Estamos utilizando estos datos únicamente con fines educativos y de investigación académica.

2. Privacidad de datos: Aunque los datos parecen ser públicos, debemos tener cuidado con cualquier información personal 
   que pueda estar presente. No publicaremos ni compartiremos ningún dato que pueda comprometer la privacidad.

3. Atribución: Reconocemos que los datos originales pertenecen a sus respectivos propietarios. En cualquier publicación 
   o presentación que utilice estos datos, debemos atribuir adecuadamente la fuente.

4. Uso justo: Nuestro uso se limita al análisis educativo y no comercial, lo que se alinea con el principio de "uso justo".

5. Respeto a los límites de la API: Implementamos una estrategia de adquisición de datos que respeta los recursos del servidor,
   evitando sobrecargarlo con demasiadas peticiones simultáneas.

6. No redistribución: No redistribuiremos los datos crudos obtenidos de la API sin permiso explícito.

7. Almacenamiento seguro: Almacenaremos los datos de manera segura y solo durante el tiempo necesario para nuestro análisis.

8. Interpretación responsable: Nos comprometemos a hacer interpretaciones responsables de los datos, reconociendo sus 
   limitaciones y evitando conclusiones injustificadas.
"""

print("\nNuestras consideraciones éticas y legales:")
print(ethical_considerations)


# ### b) Implementación de la Adquisición de Datos (30 puntos)

# * Desarrolle scripts para interactuar con la API o cargar los datos utilizando las bibliotecas apropiadas (requests, pandas, etc.).
# * Implemente manejo de autenticación si es necesario.
# * Incluya manejo de errores y reintentos.
# * Asegúrese de respetar los límites de tasa y políticas de uso de la API.

# # Competiciones

# In[9]:


# base_url = "https://api-cafecito.onrender.com"
# base_url = "http://127.0.0.1:5000"
headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}

# Obtener la lista completa de competiciones (sin parámetros)
url = f"{BASE_URL}/competitions"
response = requests.get(url, headers=headers)
print("Lista completa de competiciones:")
print(response.json())


# # Partidos Champions League 24/25

# In[10]:


# 1. Obtener partidos de una competición específica
competition = "Europe-Champions-League-2024-2025"
response = requests.get(f"{BASE_URL}/matches/competition/{competition}", headers=headers)

# 2. Convertir la respuesta JSON a un DataFrame
df_partidos = pd.DataFrame(response.json())

# 3. Verificar si la columna match_id existe en el DataFrame
if "match_id" not in df_partidos.columns:
    raise ValueError("La columna 'match_id' no está presente en los datos.")

# 4. Filtrar partidos sin match_id
df_partidos = df_partidos.dropna(subset=["match_id"])

# 5. Convertir match_id a enteros
df_partidos["match_id"] = df_partidos["match_id"].astype(int)

# 6. Mostrar las primeras filas del DataFrame filtrado
df_partidos.head(100)


# # Jugadores

# In[11]:


# 4. Extraer todos los match_id únicos y válidos
valid_match_ids = df_partidos["match_id"].dropna().unique()

# 5. Mostrar la cantidad de partidos válidos
print(f"Se encontraron {len(valid_match_ids)} partidos válidos con match_id.")

# 6. Lista para almacenar los jugadores de cada partido
players_data = []

# 7. Iterar sobre los match_id válidos
for match_id in valid_match_ids:
    url = f"{BASE_URL}/match/players/{match_id}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        players = response.json()

        # Procesar jugadores del equipo local
        for player in players.get("homePlayers", []):
            players_data.append({
                "match_id": match_id,
                "team": "home",
                "player_id": player.get("playerId"),
                "player_name": player.get("playerName"),
                "jersey_number": player.get("jerseyNumber"),
                "formation_slot": player.get("formationSlot"),
                "match_start": player.get("matchStart"),
                "team_id": player.get("teamId"),
                # Agrega más campos si es necesario
            })

        # Procesar jugadores del equipo visitante
        for player in players.get("awayPlayers", []):
            players_data.append({
                "match_id": match_id,
                "team": "away",
                "player_id": player.get("playerId"),
                "player_name": player.get("playerName"),
                "jersey_number": player.get("jerseyNumber"),
                "formation_slot": player.get("formationSlot"),
                "match_start": player.get("matchStart"),
                "team_id": player.get("teamId"),
                # Agrega más campos si es necesario
            })
    else:
        print(f"Error {response.status_code} para el partido {match_id}: {response.text}")

# 8. Convertir la lista de jugadores a un DataFrame
df_jugadores = pd.DataFrame(players_data)

# 9. Mostrar las primeras filas del DataFrame
df_jugadores.head(100)


# # Equipos
# 

# In[12]:


# 3. Obtener teams.csv
url_teams = f"{BASE_URL}/teams"
response = requests.get(url_teams, headers=headers)

# Verificar si la solicitud fue exitosa
if response.status_code == 200:
    # Convertir directamente la respuesta JSON a un DataFrame
    df_equipos = pd.DataFrame(response.json())

else:
    print("Error:", response.status_code, response.json())

df_equipos.head()


# # Eventos
# 

# In[13]:


# Lista para almacenar todos los eventos
events_data = []

# Iterar sobre los match_ids válidos
for match_id in valid_match_ids:
    try:
        # URL para obtener eventos del partido
        url = f"{BASE_URL}/match/events/{match_id}"

        # Realizar la solicitud
        response = requests.get(url, headers=headers)

        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            result = response.json()

            # Procesar cada evento del partido
            for event in result.get("events", []):
                # Crear un diccionario con la información del evento
                event_info = event.copy()
                event_info['match_id'] = match_id
                events_data.append(event_info)

            print(f"Eventos obtenidos para el partido {match_id}")
        else:
            print(f"Error al obtener eventos para el partido {match_id}: {response.status_code}")

        # Añadir un pequeño retraso para evitar sobrecargar la API
        time.sleep(0.5)

    except Exception as e:
        print(f"Excepción al procesar el partido {match_id}: {e}")

# Crear DataFrame de eventos
df_events = pd.DataFrame(events_data)

df_events.head()


# In[14]:


df_events.head(100)


# In[15]:


# Función para procesar los qualifiers
def parse_qualifiers(event):
    # Extraer el eventId del evento
    event_id = event.get('id')

    # Lista para almacenar los qualifiers parseados
    parsed_qualifiers = []

    # Procesar cada qualifier
    for qualifier in event.get('qualifiers', []):
        # Crear un diccionario con la información del qualifier
        parsed_qualifier = {
            'id': event_id,
            'qualifier_name': qualifier['type']['displayName'],
            'qualifier_type_value': qualifier['type']['value'],
            'qualifier_value': qualifier.get('value')
        }
        parsed_qualifiers.append(parsed_qualifier)

    return parsed_qualifiers

# Procesar qualifiers de todos los eventos
qualifiers_data = []
for _, evento in df_events.iterrows():
    # Parsear los qualifiers del evento
    qualifiers_parseados = parse_qualifiers(evento)
    qualifiers_data.extend(qualifiers_parseados)

# Crear DataFrame de qualifiers
df_qualifiers = pd.DataFrame(qualifiers_data)

df_qualifiers.head(100)


# ### c) Limpieza y Preprocesamiento de Datos (10 puntos)

# * Limpie los datos adquiridos (manejo de valores faltantes, corrección de formatos, etc.).
# * Realice transformaciones necesarias para el análisis (creación de nuevas columnas, agregaciones, etc.).
# * Guarde los datos procesados en un formato estructurado (CSV, JSON, etc.).

# In[16]:


# Método para agregar qualifiers a df_events
def add_qualifiers_to_events(df_events, df_qualifiers):
    # Crear una copia del DataFrame original
    df_events = df_events.copy()

    # Crear columna de características
    df_events['características'] = ''

    # Diccionarios para manejar diferentes tipos de qualifiers
    caracteristicas = {}
    numeros = {}

    # Iterar sobre los eventos y procesar los qualifiers correspondientes
    for index, evento in df_events.iterrows():
        # Filtrar qualifiers para este evento específico
        qualifiers_evento = df_qualifiers[df_qualifiers['id'] == evento['id']]

        # Separar qualifiers en características y números
        for _, qualifier in qualifiers_evento.iterrows():
            nombre = qualifier.qualifier_name
            valor = qualifier.qualifier_value

            # Clasificar qualifiers
            if valor in ['0', None]:
                # Características textuales o booleanas
                if nombre not in caracteristicas:
                    caracteristicas[nombre] = set()
                caracteristicas[nombre].add(str(valor))
            else:
                # Valores numéricos
                numeros[nombre] = valor

        # Añadir características
        caract_texto = ', '.join([f"{k}" for k, v in caracteristicas.items() if v != {'0'}])
        df_events.at[index, 'características'] = caract_texto

        # Añadir columnas numéricas
        for nombre, valor in numeros.items():
            df_events.at[index, nombre] = valor

        # Limpiar diccionarios para el siguiente evento
        caracteristicas.clear()
        numeros.clear()

    return df_events

# Aplicar la función
df_events = add_qualifiers_to_events(df_events, df_qualifiers)

df_events.head(100)


# In[17]:


# Función para limpiar el DataFrame de eventos
def limpiar_df_events(df_events):
    # Crear una copia del DataFrame
    df_limpio = df_events.copy()

    # Columnas a eliminar
    columnas_eliminar = [
        col for col in df_limpio.columns 
        if any(substring in col for substring in [
            'relatedEventId', 
            'relatedPlayerId', 
            'qualifiers', 
            'GoalMouthY', 
            'GoalMouthZ', 
            'satisfiedEventsTypes', 
            'PassEndX', 
            'PassEndY'
        ])
    ]

    # Eliminar columnas
    df_limpio = df_limpio.drop(columns=columnas_eliminar)

    # Función para extraer displayName de diccionarios
    def extraer_display_name(valor):
        if isinstance(valor, dict) and 'displayName' in valor:
            return valor['displayName']
        return valor

    # Columnas a procesar
    columnas_a_procesar = ['outcomeType', 'period', 'type']

    # Aplicar extracción de displayName
    for col in columnas_a_procesar:
        if col in df_limpio.columns:
            df_limpio[col] = df_limpio[col].apply(extraer_display_name)

    return df_limpio

# Aplicar la limpieza
df_events = limpiar_df_events(df_events)

df_events.head()


# In[18]:


# Asegurar que los IDs sean numéricos
# Conversión de IDs en df_events
df_events['playerId'] = pd.to_numeric(df_events['playerId'], errors='coerce')
df_events['teamId'] = pd.to_numeric(df_events['teamId'], errors='coerce')

# Conversión de IDs en df_jugadores
df_jugadores['player_id'] = pd.to_numeric(df_jugadores['player_id'], errors='coerce')

# Conversión de IDs en df_equipos
df_equipos['teamId'] = pd.to_numeric(df_equipos['teamId'], errors='coerce')

# Merge para añadir columna de jugador
df_events = df_events.merge(
    df_jugadores[['player_id', 'player_name', 'formation_slot', 'jersey_number']], 
    left_on='playerId', 
    right_on='player_id', 
    how='left'
)

# Merge para añadir columna de equipo
df_events = df_events.merge(
    df_equipos[['teamId', 'teamName']], 
    left_on='teamId', 
    right_on='teamId', 
    how='left'
)
df_events.head(100)


# In[30]:


# Convertir match_id a numérico para asegurar consistencia
df_events['match_id'] = pd.to_numeric(df_events['match_id'], errors='coerce')
df_partidos['match_id'] = pd.to_numeric(df_partidos['match_id'], errors='coerce')

# Crear la columna de partido con el formato especificado
df_events = df_events.merge(
    df_partidos[['match_id', 'home_team', 'away_team', 'home_score', 'away_score']], 
    left_on='match_id', 
    right_on='match_id', 
    how='left'
)

# Formatear la columna 'match'
df_events['match'] = (
    df_events['home_team'] + ' ' + 
    df_events['home_score'].astype(str) + 
    ' - ' + 
    df_events['away_score'].astype(str) + ' ' + 
    df_events['away_team']
)

# Eliminar columnas intermedias
df_events = df_events.drop(columns=['home_team', 'away_team', 'home_score', 'away_score'])
df_events.to_csv('eventos.csv', index=False)


df_events.head(100)

