import os
from dotenv import load_dotenv
from datapizza.clients.google import GoogleClient
from src.models import Child, Letter

load_dotenv()

# 1. Prendi testo da letterina (ci pensiamo dopo, magari in utils)
letter_path = "data/letters/letter_good_0.txt"
with open(letter_path, "r", encoding="utf-8") as f:
    letter_text = f.read()



# 2. Prompt per mappare testo -> Child
prompt = f"""Analizza la seguente letterina di Natale ed estrai le informazioni strutturate, creando uno o più oggetti (se dal testo totale rilevi più letterine di bambini diversi) strutturati Child.

Testo della letterina:
{letter_text}
"""

# Client Setup
# NOTA: Usiamo gemini-2.0-flash-exp per le migliori performance di estrazione
google_client = GoogleClient(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.0-flash-exp"
)



response = google_client.structured_response(
    input=prompt,
    output_cls=Child
)

structured_data = response.structured_data
person: Child = structured_data[0]

print(person, "\n\n\n\n")
print(structured_data)
