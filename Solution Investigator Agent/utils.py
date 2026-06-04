# utils.py

import json
import re
from llm_provider import chiama_llm


# ======================
# ESTRAI JSON ROBUSTO
# ======================
def estrai_json(testo):

    if not testo:
        return "{}"

    testo = testo.strip()

    # rimuove markdown
    testo = testo.replace("```json", "")
    testo = testo.replace("```", "")

    # trova primo blocco JSON plausibile
    start = testo.find("{")
    end = testo.rfind("}")

    if start == -1 or end == -1:
        return "{}"

    return testo[start:end + 1]


# ======================
# EURISTICA SOLUZIONE
# ======================
def euristica_soluzione(risposta):

    risposta = risposta.lower()

    parole = [
        "era",
        "ho risolto",
        "il problema era",
        "si è scoperto",
        "era la",
        "era il"
    ]

    return any(p in risposta for p in parole)


# ======================
# SAFE JSON CALL
# ======================
def safe_json_call(prompt, default=None, debug_name=""):

    if default is None:
        default = {}

    full_prompt = f"""
    {prompt}

    REGOLE OBBLIGATORIE:
    - Rispondi SOLO JSON valido
    - NON usare markdown
    - NON aggiungere testo prima o dopo
    - JSON parsabile con json.loads
    """

    out = chiama_llm(full_prompt)

    if not out:

        print("\n❌ OUTPUT LLM VUOTO")

        if debug_name:
            print("DEBUG:", debug_name)

        return default

    try:

        raw_json = estrai_json(out)

        parsed = json.loads(raw_json)

        if not isinstance(parsed, dict):

            print("\n❌ JSON NON È DICT")

            if debug_name:
                print("DEBUG:", debug_name)

            print(raw_json)

            return default

        return parsed

    except Exception as e:

        print("\n====================")
        print("❌ ERRORE JSON")
        print("====================")

        if debug_name:
            print("DEBUG:", debug_name)

        print("\n--- OUTPUT LLM ---")
        print(out)

        print("\n--- JSON ESTRATTO ---")
        print(raw_json)

        print("\n--- ERRORE ---")
        print(e)

        return default