"""
Chatbot Interfaccia Utente per Santa Analysis.

Questo modulo implementa l'interfaccia chat basata su Chainlit.
Gestisce l'interazione con l'utente e orchestra le chiamate agli agenti appropriati:
- **Agent SQL**: per risposte testuali basate sui dati.
- **Agent Metabase**: per la creazione di dashboard e report visivi.

Caratteristiche principali:
- Riconoscimento automatico dell'intento (Domanda vs Dashboard).
- Visualizzazione delle query SQL eseguite (tramite Step espandibili).
- Mantenimento del contesto della conversazione.
"""

import chainlit as cl
import sys
import re
from pathlib import Path

# ===============================
# CONFIGURAZIONE PATH
# ===============================

# Aggiunge la cartella corrente al path per permettere l'importazione di moduli locali
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))  # Aggiunge anche la root del progetto

# Importazione degli agenti dal modulo agent.py
from agent import sql_agent, get_metabase_agent


# ===============================
# LOGICA DI ROUTING (INTENT DETECTION)
# ===============================

# Lista di parole chiave/pattern che indicano una richiesta di dashboard o grafici
DASHBOARD_KEYWORDS = [
    r"crea.*dashboard",
    r"crea.*report",
    r"genera.*dashboard",
    r"genera.*report",
    r"fai.*dashboard",
    r"fai.*report",
    r"prepara.*dashboard",
    r"prepara.*report",
    r"visualizza.*in metabase",
    r"aggiungi.*grafico",
    r"create.*dashboard",
    r"make.*dashboard",
]

def is_dashboard_request(text: str) -> bool:
    """
    Analizza il testo dell'utente per determinare se sta chiedendo una dashboard.
    
    Args:
        text (str): Il messaggio dell'utente.
        
    Returns:
        bool: True se è una richiesta di dashboard, False altrimenti.
    """
    text_lower = text.lower()
    for pattern in DASHBOARD_KEYWORDS:
        if re.search(pattern, text_lower):
            return True
    return False


# ===============================
# GESTORI EVENTI CHAINLIT
# ===============================

@cl.on_chat_start
async def start():
    """
    Eseguito all'avvio di una nuova sessione di chat.
    Inizializza la cronologia e invia il messaggio di benvenuto.
    """
    # Inizializzazione variabili di sessione
    cl.user_session.set("messages", [])
    # 'analysis_history' serve a dare contesto all'agente Metabase sulle query precedenti
    cl.user_session.set("analysis_history", [])
    
    # Messaggio di benvenuto
    await cl.Message(
        content="""🎅 **Oh oh oh! Benvenuto nell'ufficio analisi di Babbo Natale!**

Sono pronto ad aiutarti a capire chi è stato buono e chi no. 

**Cosa posso fare:**
- 📊 **Analizzare dati**: Fammi domande sul database delle letterine (es: "Quanti bambini Italiani?")
- 📈 **Creare dashboard**: Chiedi "crea una dashboard" o "genera un report" e creerò grafici su Metabase.

Cosa vuoi chiedermi?"""
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """
    Gestore principale dei messaggi dell'utente.
    Decide quale agente chiamare e gestisce la risposta.
    """
    # Recupero dati sessione
    messages = cl.user_session.get("messages") or []
    analysis_history = cl.user_session.get("analysis_history") or []
    
    user_text = message.content
    messages.append({"role": "user", "content": user_text})

    # Feedback immediato all'utente
    msg = cl.Message(content="🎄 *Babbo Natale sta consultando i suoi registri...*")
    await msg.send()

    try:
        # 1. Routing: Decide se è una dashboard o una domanda SQL
        if is_dashboard_request(user_text):
            # === RAMO METABASE AGENT ===
            msg.content = "📊 *Sto creando la dashboard in Metabase...*"
            await msg.update()
            
            # Recupero l'agente on-demand (gestisce errori di connessione)
            metabase_agent = get_metabase_agent()
            if metabase_agent is None:
                msg.content = "⚠️ **Metabase non è raggiungibile.** Assicurati che Docker sia attivo e Metabase sia avviato."
                await msg.update()
                return
            
            # Costruisco il prompt con il contesto delle ultime analisi
            context = "Contesto delle analisi precedenti:\n"
            for item in analysis_history[-5:]:  # Limita agli ultimi 5 elementi
                context += f"- Query: {item.get('query', 'N/A')}\n"
                context += f"  Risultato: {item.get('result', 'N/A')[:200]}...\n"
            
            full_prompt = f"{context}\n\nRichiesta utente: {user_text}"
            
            # Esecuzione agente
            result = metabase_agent.run(full_prompt)
            final_answer = getattr(result, "text", str(result))
            
            msg.content = f"📈 **Dashboard creata!**\n{final_answer}"
            await msg.update()
            
        else:
            # === RAMO SQL AGENT ===
            
            # Esecuzione agente
            result = sql_agent.run(user_text)
            full_response = getattr(result, "text", str(result))
            
            # Parsing della risposta per estrarre le query SQL (marcate dai tag speciali)
            sql_queries_text = ""
            final_text_answer = full_response
            
            if "---SQL_QUERIES---" in full_response:
                parts = full_response.split("---SQL_QUERIES---")
                final_text_answer = parts[0].strip()  # La parte discorsiva
                if len(parts) > 1:
                    # Estrae il blocco SQL
                    sql_part = parts[1].split("---END_SQL_QUERIES---")[0].strip()
                    sql_queries_text = sql_part
            
            # Salvataggio risultato in cronologia per contesto futuro
            analysis_history.append({
                "query": user_text,
                "result": final_text_answer
            })
            cl.user_session.set("analysis_history", analysis_history)
            
            # Invio della risposta testuale principale
            msg.content = f"🎅 **Risposta:**\n{final_text_answer}"
            await msg.update()
            
            # Se sono state trovate query SQL, le mostriamo in un elemento UI dedicato (Step)
            if sql_queries_text:
                async with cl.Step(name="🔍 Query SQL Eseguite", type="tool") as step:
                    # Formatta come blocco di codice SQL
                    step.output = f"```sql\n{sql_queries_text}\n```"
        
        # Aggiornamento cronologia chat
        messages.append({"role": "assistant", "content": final_answer if 'final_answer' in locals() else final_text_answer})
        cl.user_session.set("messages", messages)
        
    except Exception as e:
        # Gestione errori generica per non bloccare l'interfaccia
        msg.content = f"💥 **Accidenti! Un elfo ha inciampato nei cavi:**\n```\n{str(e)}\n```"
        await msg.update()

if __name__ == "__main__":
    pass