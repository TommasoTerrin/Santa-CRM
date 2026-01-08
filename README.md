# 🎅 Merry CRM: Il Sistema Gestionale di Babbo Natale

> *"Ogni anno, milioni di letterine arrivano al Polo Nord. Ma come fa Babbo Natale a gestire tutte quelle richieste, capire chi è stato buono e chi no, e soprattutto... decidere chi merita il carbone?"*

Benvenuto in **Merry CRM**, il sistema CRM (Customer Relationship Management) più *merry* del mondo! 🎄

Questo progetto nasce per risolvere un problema antico quanto il Natale stesso: trasformare montagne di letterine scritte a mano in **dati analizzabili**, e poi permettere a Babbo Natale di prendere decisioni basate sui dati... senza dover imparare SQL!

Il sistema è composto da **due moduli principali**, ciascuno pensato per alleggerire il carico di lavoro agli instancabili Elfi del Polo Nord.

---

## 🏗️ Architettura del Progetto

```
Merry-CRM/
├── 📂 Elf-ETL module/
│   ├── 📂 logs/              # 📝 Log della Pipeline
│   └── ...                   # 🔄 Pipeline ETL (Estrazione Letterine)
├── 📂 Fake-ETL-u-make-it/    # 🎭 Simulatore Dati (per sviluppo)
├── 📂 Santa-Analysis/        # 🤖 Data Analysis (Agenti AI)
├── 📄 docker-compose.yml     # 🐳 Orchestrazione servizi
├── 📄 requirements.txt       # 📦 Dipendenze Python
└── 📄 .env.example           # 🔐 Template variabili d'ambiente
```

---

## 📬 Modulo 1: Elf-ETL (Estrazione Letterine)

> **Stato**: 🚧 In Sviluppo (Attualmente simulato da "Fake-ETL-u-make-it")

### Il Problema

Immagina di essere un Elfo postino al Polo Nord. Ogni giorno arrivano **milioni e milioni** di letterine. E tu cosa devi fare?

1. **Leggere ogni singola letterina** scritta a mano (alcune illeggibili, altre con disegni di renne ovunque)
2. **Filtrare quelle false** — sì, perché il perfido **Grinch** 💚 invia ogni anno migliaia di letterine fasulle per sabotare il Natale!
3. **Estrarre le informazioni**: nome del bambino, età, paese, lista regali richiesti
4. **Valutare se il bambino è stato buono o cattivo** (e assegnare un punteggio di "buonità")
5. **Inserire tutto a mano** nel CRM

Questo lavoro richiede settimane di straordinari notturni per gli Elfi. E diciamocelo: anche un Elfo può stancarsi.

### La Soluzione: Una Pipeline ETL Intelligente

**Elf-ETL** automatizza l'intero processo con una pipeline che combina strumenti tradizionali e intelligenza artificiale:

| Step | Cosa fa | Tecnologia |
|------|---------|------------|
| 🛡️ **Filtro Anti-Grinch** | Identifica e scarta le letterine false | Regole deterministiche (no AI) |
| 📖 **Lettura & Estrazione** | Legge il contenuto e lo converte in dati strutturati | LLM (Google Gemini) |
| ⚖️ **Valutazione Buonità** | Assegna un punteggio basato su indicatori nel testo | LLM con Structured Output |
| 💾 **Caricamento CRM** | Inserisce tutto nel database PostgreSQL | SQLDatabase |

### Componenti DataPizza-AI utilizzate

| Componente | Perché è stata scelta |
|------------|----------------------|
| `Pipeline` | Orchestrazione del flusso ETL step-by-step, con gestione errori e retry automatici. |
| `GoogleClient` | Connessione a Google Gemini per l'estrazione intelligente del testo. |
| `StructuredOutput` | Parsing del testo libero in oggetti Pydantic/SQLModel con schema definito. |
| `SQLDatabase` | Persistenza diretta dei dati estratti su PostgreSQL. |

### Nota
Attualmente il modulo `Elf-ETL module` è in fase di sviluppo. Per permettere i test end-to-end, il suo funzionamento viene **simulato** dal modulo `Fake-ETL-u-make-it`, che genera dati sintetici realistici di bambini e letterine.

---

## 🤖 Modulo 2: Data-Analysis (Analisi Dati per Babbo Natale)

> **Stato**: ✅ Funzionante

### Il Problema

Ok, le letterine sono state processate. Ora Babbo Natale ha un bel database con **milioni di record**. Fantastico, no?

Beh, non proprio. Perché Babbo:
- Non sa scrivere query SQL
- Non ha idea di cosa sia un `JOIN`
- Per ogni minima domanda deve chiamare l'**Elfo Data Scientist** (che è già sommerso di lavoro)

*"Quanti bambini italiani hanno chiesto una bicicletta?"* — E l'Elfo deve mollare tutto, scrivere una query, eseguirla, e riportare il risultato. Per ogni. Singola. Domanda.

### La Soluzione: Intelligenza Artificiale al Servizio di Babbo Natale

Il modulo **Data-Analysis** offre a Babbo Natale due superpoteri:

---

#### 2.1 💬 Chat con il Database (SQL Agent)

Babbo apre la chat e scrive semplicemente: *"Quanti bambini italiani hanno scritto una letterina?"*

Dietro le quinte, un **Agente AI** converte la domanda in una query SQL, la esegue sul database, e restituisce la risposta in linguaggio naturale.

**Ma ehi, non è una black-box!** Per trasparenza, la query SQL eseguita viene mostrata in un **menu a tendina espandibile**. Così se qualcosa nella risposta non convince Babbo, può sempre chiamare l'Elfo Data Scientist per un controllo manuale.

| Componente DataPizza-AI | Perché è stata scelta |
|-------------------------|----------------------|
| `Agent` | Orchestrazione del ragionamento multi-step con planning automatico. |
| `GoogleClient` | LLM Gemini per la comprensione del linguaggio naturale e generazione SQL. |
| `SQLDatabase` | Tool `get_table_schema` e `run_sql_query` per interagire con il DB in modo sicuro (solo SELECT). |

---

#### 2.2 📊 Creazione Report & Dashboard (Metabase Agent)

Quando Babbo ha bisogno di qualcosa di più elaborato — un **report**, un **grafico**, una **dashboard** — gli basta chiedere:

*"Crea una dashboard con la distribuzione geografica dei bambini buoni"*

E boom! Un secondo agente si connette tramite **MCP (Model Context Protocol)** a [Metabase](https://www.metabase.com/), una piattaforma di Business Intelligence, e crea il report grafico richiesto in **pochi secondi**.

Non è incredibile? ✨

**Perché Metabase?**
- È **open source** — nessun vendor lock-in
- È incluso direttamente in questo progetto via **Docker**
- Se un domani Babbo volesse passare a Power BI, Looker, o altro? Basta connettere l'agente a un diverso server MCP. Più semplice di così...

| Componente DataPizza-AI | Perché è stata scelta |
|-------------------------|----------------------|
| `Agent` | Gestione autonoma del workflow: listare database, creare dashboard, creare card, aggiungere card alla dashboard. |
| `GoogleClient` | LLM per interpretare la richiesta e decidere tipo di grafico e query SQL appropriate. |
| `MCPClient` | Connessione al server MCP `mcp/metabase` che espone le API di Metabase come tool invocabili dall'agente. |

---

### Interfaccia Utente

L'interfaccia chat è realizzata con **Chainlit**, che fornisce:
- 💬 Chat in tempo reale con feedback visivo
- 📋 Step espandibili per mostrare le query SQL eseguite
- 🔗 Supporto per elementi multimediali (link alle dashboard)

---

## 🎭 Bonus: Fake-ETL-u-make-it (Simulatore Dati)

Genera dati fittizi ma realistici per popolare il database durante lo sviluppo e i test:
- `child`: Anagrafica bambini (nome, età, città, paese, genere)
- `letter`: Letterine con punteggio di buonità, richieste regali, data ricezione

Permette di sviluppare e testare `Data-Analysis` senza attendere il completamento della pipeline ETL reale.

---

## 🚀 Guida Rapida

### Requisiti
- **Python 3.10+**
- **Docker & Docker Compose**
- **API Key Google Gemini** (o altro LLM supportato)

### 1. Configurazione Ambiente

Copia il file `.env.example` in `.env` e compila con i tuoi valori:

```bash
cp .env.example .env
```

Vedi il file [.env.example](.env.example) per la lista completa delle variabili richieste.

### 2. Avvio Servizi Docker
```bash
docker-compose up -d
```

### 3. Installazione Dipendenze
```bash
python -m venv venv
.\venv\Scripts\Activate  # Windows
pip install -r requirements.txt
```

### 4. Avvio Chatbot
```bash
chainlit run Santa-Analysis/bot.py -w
```
Apri il browser su `http://localhost:8000` e inizia a chattare con Babbo Natale! 🎅

---

## 🎄 Esempi di Utilizzo

### Domande Dati (SQL Agent)
- *"Quanti bambini hanno scritto quest'anno?"*
- *"Qual è l'età media dei bambini buoni?"*
- *"Elenca i 5 paesi con più letterine"*

### Richieste Dashboard (Metabase Agent)
- *"Crea una dashboard con un grafico a torta per l'età dei bambini"*
- *"Genera un report con la distribuzione geografica"*
- *"Fai un grafico a barre del punteggio medio per paese"*

---

## 🔧 Stack Tecnologico

| Tecnologia | Utilizzo |
|------------|----------|
| **DataPizza-AI** | Framework per agenti AI e orchestrazione LLM |
| **Google Gemini** | Modello linguistico per comprensione e generazione |
| **PostgreSQL** | Database relazionale per i dati strutturati |
| **Metabase** | Business Intelligence e visualizzazione dati |
| **MCP (Model Context Protocol)** | Protocollo per esporre API esterne come tool per agenti |
| **Chainlit** | Framework per interfacce chat conversazionali |
| **Docker** | Containerizzazione dei servizi |

---

## 📝 Note per gli Sviluppatori

- Il modulo `Elf-ETL module` è mantenuto nel repository ma attualmente non attivo. Sarà completato in una fase successiva per sostituire il simulatore.
- L'agente Metabase si connette tramite un container Docker effimero che funge da bridge MCP.
- Le credenziali del database nel `.env` devono corrispondere a quelle nel `docker-compose.yml`.

---

*Progetto sviluppato con ❤️ per rendere il Natale più data-driven.*
*~ Gli Elfi della Divisione Analisi Dati, Polo Nord 🎄*
