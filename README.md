# Elf-ETL & Santa Analysis 🎅📊

Benvenuto nel sistema di gestione dati avanzato per l'ufficio di Babbo Natale!
Questo progetto combina una pipeline ETL per processare le letterine dei bambini con un sistema di analisi basato su AI (Agentic) per interrogare i dati e creare dashboard automatiche.

## 📁 Struttura del Progetto

Il progetto è diviso in tre componenti principali:

1.  **Fake-ETL-u-make-it**:
    *   Sostituisce temporaneamente il modulo `Elf-ETL module`.
    *   Genera dati sintetici (bambini e letterine) e popola il database.
    
2.  **Elf-ETL module** (Legacy/In Sviluppo):
    *   Il modulo ETL originale (attualmente mantenuto ma non attivo in produzione).
    
3.  **Santa-Analysis (Il Cuore AI)**:
    *   Contiene gli Agenti AI basati su Google Gemini.
    *   **SQL Agent**: Traduce domande in linguaggio naturale in query SQL su PostgreSQL.
    *   **Metabase Agent**: Usa il protocollo MCP (Model Context Protocol) per pilotare Metabase e creare dashboard su richiesta.
    *   Interfaccia Chatbot realizzata con **Chainlit**.

## 🚀 Requisiti

*   **Python 3.10+**
*   **Docker & Docker Compose** (per Database e Metabase)
*   Account Google Cloud (per API Key Gemini) o altro LLM supportato da DataPizza.

## 🛠️ Installazione e Setup

### 1. Configurazione Ambiente
Crea un file `.env` nella root del progetto (copia da `.env.example` se presente) e imposta le variabili:

```env
# Database
SANTA_DB_URL=postgresql://santa:santa_password@localhost:5432/elf_db
POSTGRES_USER=santa
POSTGRES_PASSWORD=santa_password
POSTGRES_DB=elf_db

# Metabase
METABASE_URL=http://localhost:3000
METABASE_USERNAME=tuo_admin@email.com
METABASE_PASSWORD=tua_password_sicura

# AI (Google Gemini)
GEMINI_API_KEY=la_tua_chiave_api_qui
```

### 2. Avvio Servizi (Docker)
Avvia PostgreSQL e Metabase:

```bash
docker-compose up -d
```

### 3. Setup Python
Crea e attiva il virtual environment:

```bash
python -m venv venv
# Windows
.\venv\Scripts\Activate
# Mac/Linux
source venv/bin/activate
```

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

## 🎮 Utilizzo

### Avvio dell'Assistente AI
Per lanciare l'interfaccia di chat:

```bash
chainlit run Santa-Analysis/bot.py -w
```
L'applicazione sarà disponibile su `http://localhost:8000`.

### Cosa puoi chiedere?
*   **Analisi Dati**: "Quanti bambini italiani hanno scritto quest'anno?", "Qual è l'età media dei bambini buoni?".
*   **Dashboard**: "Crea una dashboard con un grafico a torta per l'età e una mappa per i paesi".

## 🔧 Note Tecniche
*   **Agenti**: Utilizzano la libreria `datapizza` per l'orchestrazione.
*   **Database**: I dati persistono nel volume Docker `postgres_data`.
*   **Metabase MCP**: L'agente comunica con Metabase avviando un container Docker effimero che funge da bridge API.

---
*Progetto sviluppato per rendere felici gli Elfi Analisti.* 🎄
