"""
=============================================================================
GUIDA ALL'USO DI AGENTETRAD (Problem-Solution Extractor Agent)
=============================================================================

Questo script automatizza l'estrazione strutturata di Problema, Contesto e 
Soluzione partendo da file di testo grezzi (es. discussioni/thread di forum).
Utilizza il modello LLM Gemini per effettuare il parsing del testo e 
restituire un file .ps formattato in formato JSON.

COME ESEGUIRE IL CODICE DA TERMINALE / PROMPT DEI COMANDI:
Lo script accetta come argomento il percorso della cartella che contiene i file 
di testo grezzi dei forum da elaborare.

Sintassi:
   python AgenteTrad.py <percorso_della_cartella_input>

Esempio pratico (Windows):
   python AgenteTrad.py C:\\Users\\NomeUtente\\Desktop\\Thread_Idraulici

Esempio pratico (Mac/Linux):
   python AgenteTrad.py ./Dataset/Thread_Idraulici

RISULTATO:
Lo script creerà in automatico una sotto-cartella chiamata "output_ps" all'interno 
della cartella di input inserita, salvando per ogni file processato un file 
corrispondente con estensione ".ps" contenente il JSON pulito.
=============================================================================
"""

import os
import sys
from google import genai

# 🔑 API KEY
client = genai.Client(api_key="AIzaSyBMBZ8rBWldZkujWglSCIAjnUyHJujF8r0")

def estrai_info(testo):
    prompt = f"""
    Analizza il seguente testo.

    IMPORTANTE:
    - Il testo può contenere conversazioni tra persone (chat, botta e risposta, opinioni).
    - Ignora completamente il formato conversazionale.
    - Estrai SOLO informazioni oggettive e rilevanti.

    Restituisci
    1) Problema: deve essere chiaro, sintetico e ben separato dalla soluzione, 
        ovvero non deve contenere le cause che l'hanno procovato
    2) Contesto del problema: senza dialoghi o frasi inutili, deve contenere 
        informazioni che possono utili per la risoluzione del problema 
        (come misurazioni, osservazioni effettuate dall'utente che ha esposto il problema)
    3) Soluzione al problema : deve essere concreta, precisa e sintetica

    Testo:
    {testo}

    Output:
    Rispondi SOLO JSON

                {{
                    "problema": "...",
                    "contesto": "...",
                    "soluzione": "..."
                }}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text


def main():
    if len(sys.argv) < 2:
        print("Uso: python script.py <percorso_cartella>")
        return

    input_folder = sys.argv[1]
    output_folder = os.path.join(input_folder, "output_ps")

    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        file_path = os.path.join(input_folder, filename)

        if os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    contenuto = f.read()

                risultato = estrai_info(contenuto)

                base_name = filename.split('.')[0] 
                output_filename = base_name + ".ps"

                #output_filename = os.path.splitext(filename)[0] + ".ps"
                output_path = os.path.join(output_folder, output_filename)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(risultato)

                print(f"Creato: {output_filename}")

            except Exception as e:
                print(f"Errore con {filename}: {e}")


if __name__ == "__main__":
    main()