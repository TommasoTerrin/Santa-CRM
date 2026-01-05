"""
Modulo Agenti per Elf-ETL Santa Analysis.

Questo modulo definisce e configura gli agenti AI utilizzati per analizzare i dati di Babbo Natale.
Include:
1.  **SQL Agent**: Un agente capace di interrogare il database PostgreSQL per rispondere a domande sui dati.
2.  **Metabase Agent**: Un agente capace di interagire con Metabase (via MCP) per creare dashboard e grafici.

Configura anche la connessione al database e la gestione del client MCP per Metabase.
"""

import os
import json
import time
import requests
from dotenv import load_dotenv
from pathlib import Path

# DataPizza & Framework Imports
from datapizza.agents import Agent
from datapizza.clients.google import GoogleClient
from datapizza.tools.SQLDatabase import SQLDatabase
from datapizza.tools.mcp_client import MCPClient

# ===============================
# 1. CONFIGURAZIONE AMBIENTE
# ===============================

# Caricamento variabili d'ambiente dal file .env nella root del progetto
load_dotenv(Path(__file__).parent.parent / ".env")

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
DB_URI = os.getenv("SANTA_DB_URL")
METABASE_USERNAME = os.getenv("METABASE_USERNAME", "")
METABASE_PASSWORD = os.getenv("METABASE_PASSWORD", "")

# Fallback per sviluppo locale se DB_URI non è settato (uso SQLite di esempio)
if not DB_URI:
    DB_FILE_PATH = Path(__file__).parent.parent / "database" / "santa_data.sqlite"
    DB_URI = f"sqlite:///{DB_FILE_PATH}"

print(f"🔗 [INFO] Connessione al database: {DB_URI.split('@')[-1] if '@' in DB_URI else DB_URI}")


# ===============================
# 2. CONFIGURAZIONE CLIENT LLM
# ===============================

# Inizializzazione del client Gemini
client = GoogleClient(
    api_key=GOOGLE_API_KEY,
    model="gemini-2.0-flash"
)


# ===============================
# 3. AGENTE SQL (ANALISI DATI)
# ===============================

# Inizializzazione strumenti SQL
sql_tools = SQLDatabase(DB_URI)

# Prompt di sistema per l'Agente SQL
# Definisce il comportamento, il formato di risposta e le regole per le query.
SQL_SYSTEM_PROMPT = """
Sei l'assistente dati di Babbo Natale per Merry-CRM.
Il database contiene le tabelle 'child' (elenco dei bambini) e 'letter' (letterine inviate dai bambini).

FLUSSO DI LAVORO:
1. Usa `get_table_schema` se necessario per capire le colonne.
2. Costruisci ed ESEGUI la query SQL con `run_sql_query`.
3. Leggi i risultati e rispondi all'utente in italiano con tono gioioso (🎅).

FORMATO RISPOSTA OBBLIGATORIO:
- Prima rispondi in linguaggio naturale (es: "Ho trovato 16 bambini italiani! 🎄")
- ALLA FINE, aggiungi SEMPRE le query SQL eseguite nel seguente formato:

---SQL_QUERIES---
SELECT ...;
---END_SQL_QUERIES---

Regole SQL:
- Solo SELECT (PostgreSQL).
- Valori enum come 'country' sono in MAIUSCOLO (es: 'ITALY', 'USA', 'CHINA').
"""

# Creazione dell'Agente SQL
sql_agent = Agent(
    name="sql_analyst",
    client=client,
    system_prompt=SQL_SYSTEM_PROMPT,
    tools=[sql_tools.get_table_schema, sql_tools.run_sql_query],
    planning_interval=1,
)

# Alias per retrocompatibilità con vecchie importazioni
agent = sql_agent


# ===============================
# 4. AGENTE METABASE (DASHBOARD)
# ===============================

# URL di Metabase nella rete Docker interna (per comunicazione Agent -> MCP -> Docker Metabase)
METABASE_INTERNAL_URL = "http://metabase-datapizza-christmas:3000"
print(f"📊 [INFO] Metabase URL per MCP (Internal Docker): {METABASE_INTERNAL_URL}")

# Configurazione del Client MCP (Model Context Protocol)
# Questo client avvia un container Docker effimero che fa da ponte verso Metabase
metabase_mcp = MCPClient(
    command="docker",
    args=[
        "run", "-i", "--rm",
        "--network", "elf-etl_default",  # Rete condivisa con postgres e metabase
        "-e", f"METABASE_URL={METABASE_INTERNAL_URL}",
        "-e", f"METABASE_USERNAME={METABASE_USERNAME}",
        "-e", f"METABASE_PASSWORD={METABASE_PASSWORD}",
        "mcp/metabase"
    ],
    timeout=120  # Timeout esteso per gestire avvio container lento
)

# Prompt di sistema per l'Agente Metabase
# Istruisce l'agente su come creare card e dashboard, con focus specifico sul mapping degli assi per i grafici.
METABASE_SYSTEM_PROMPT = """
Sei l'assistente di Babbo Natale per la creazione di report e dashboard in Metabase.
Il tuo compito è aiutare a creare visualizzazioni dei dati delle letterine.

DATABASE SCHEMA:
- Table `child`: id, name, age, city, country, gender
- Table `letter`: id, child_id (foreign key to child.id), goodness_score (0.0-1.0), gift_request (json/text), is_spam (boolean), spam_reason, received_at

Strumenti disponibili:
- list_databases: elenca i database collegati a Metabase
- list_dashboards: elenca le dashboard esistenti
- create_dashboard: crea una nuova dashboard (restituisce ID)
- create_card: crea un nuovo grafico/card (dataset_query è una query SQL nativa)
- add_card_to_dashboard: aggiunge un grafico a una dashboard
- execute_query: esegue una query SQL

IMPORTANTE - CONFIGURAZIONE GRAFICI:
Quando usi `create_card`, DEVI specificare `visualization_settings` per far capire a Metabase come disegnare il grafico.
Il solo risultato SQL non basta. Devi dire quali colonne sono l'asse X (dimensioni) e Y (metriche).

FORMATO visualization_settings (JSON):
{
    "display": "bar",  // o "line", "pie", "row", "map"
    "graph.dimensions": ["nome_colonna_x"],
    "graph.metrics": ["nome_colonna_y"]
}

Esempi:
1. Distribuzione per Paese (Bar Chart):
   - Query: `SELECT country, count(*) as conteggio FROM child GROUP BY country`
   - Settings: `{"display": "bar", "graph.dimensions": ["country"], "graph.metrics": ["conteggio"]}`

2. Andamento Temporale (Line Chart):
   - Query: `SELECT date_trunc('day', received_at) as data, count(*) as num_lettere FROM letter GROUP BY 1 ORDER BY 1`
   - Settings: `{"display": "line", "graph.dimensions": ["data"], "graph.metrics": ["num_lettere"]}`

3. Torta Età (Pie Chart):
   - Query: `SELECT age, count(*) as c FROM child GROUP BY age`
   - Settings: `{"display": "pie", "graph.dimensions": ["age"], "graph.metrics": ["c"]}`

FLUSSO DI LAVORO:
1. list_databases -> trovi elf_db (id=2 di solito).
2. create_dashboard -> "Dashboard Natale 2026".
3. create_card -> Query SQL + Visualization Settings CORRETTI.
4. add_card_to_dashboard.
5. Restituisci il link: http://localhost:3000/dashboard/{id}

Rispondi sempre con il tono gioioso di Babbo Natale 🎅.
"""

def ensure_metabase_connection():
    """
    Verifica e configura la connessione tra Metabase e il database PostgreSQL ('elf_db').
    
    Questa funzione chiama le API di Metabase per:
    1. Effettuare il login e ottenere un token di sessione.
    2. Controllare se il database 'elf_db' è già configurato.
    3. Se manca, aggiungerlo con le credenziali corrette (collegandosi via rete Docker interna).
    """
    try:
        # URL API locale (accessibile dall'host dove gira questo script)
        api_url = "http://localhost:3000/api"
        
        # 1. Login
        session = requests.Session()
        login_payload = {
            "username": METABASE_USERNAME,
            "password": METABASE_PASSWORD
        }
        res = session.post(f"{api_url}/session", json=login_payload)
        if not res.ok:
            print(f"⚠️ [METABASE] Login fallito: {res.text}")
            return
        
        token = res.json().get("id")
        headers = {"X-Metabase-Session": token}
        
        # 2. Lista Database
        res = session.get(f"{api_url}/database", headers=headers)
        if not res.ok:
            print(f"⚠️ [METABASE] Impossibile listare DB: {res.text}")
            return
            
        data = res.json()
        
        # Gestione flessibile della risposta (list o dict)
        if isinstance(data, list):
            databases = data
        elif isinstance(data, dict):
            databases = data.get("data", data.get("databases", []))
        else:
            databases = []

        db_names = [db.get("name") for db in databases if isinstance(db, dict)]
        
        if "elf_db" in db_names:
            print("✅ [METABASE] Database 'elf_db' già configurato.")
            return

        print("🔄 [METABASE] Configurazione 'elf_db' in corso...")
        
        # 3. Aggiunta Database (Parametri Docker interni)
        db_details = {
            "name": "elf_db",
            "engine": "postgres",
            "details": {
                "host": "postgres", # Nome del servizio docker-compose
                "port": 5432,
                "dbname": "elf_db",
                "user": "santa",
                "password": "santa_password",
                "ssl": False
            }
        }
        
        res = session.post(f"{api_url}/database", json=db_details, headers=headers)
        if res.ok:
            print("✅ [METABASE] Database 'elf_db' configurato con successo!")
        else:
            print(f"❌ [METABASE] Errore configurazione DB: {res.text}")
            
    except Exception as e:
        print(f"⚠️ [METABASE] Errore durante l'auto-configurazione: {e}")


def get_metabase_agent():
    """
    Inizializza e restituisce l'agente Metabase on-demand.
    
    Tenta prima di auto-configurare la connessione al database.
    Se il server MCP o Metabase non sono disponibili, gestisce l'errore e restituisce None.
    
    Returns:
        Agent: L'istanza dell'agente o None in caso di errore.
    """
    try:
        # Assicura che Metabase abbia il DB configurato prima di iniziare
        ensure_metabase_connection()
        
        # Carica i tool disponibili dal server MCP
        mcp_tools = metabase_mcp.list_tools()
        
        return Agent(
            name="metabase_dashboard_creator",
            client=client,
            system_prompt=METABASE_SYSTEM_PROMPT,
            tools=mcp_tools,
            planning_interval=1,
        )
    except Exception as e:
        print(f"⚠️ Errore caricamento Agente Metabase (Docker/MCP issue): {e}")
        return None