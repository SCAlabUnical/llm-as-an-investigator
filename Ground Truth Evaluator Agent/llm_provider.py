# llm_provider.py

import time
import random
from openai import OpenAI
from google import genai

print("Scegli il provider LLM:")
print("1 → Gemini")
print("2 → OpenAI")

scelta = input("> ").strip()

# ======================
# CONFIG
# ======================

if scelta == "2":

    provider = "openai"

    client = OpenAI(
        api_key="LA_TUA_OPENAI_KEY"
    )

    MODELLO = "gpt-4.1-mini"

else:

    provider = "gemini"

    client = genai.Client(
        api_key="LA_TUA_GEMINI_KEY"
    )

    MODELLO = "gemini-2.5-flash-lite"


MAX_RETRY = 15


# ======================
# CHIAMATA LLM
# ======================
def chiama_llm(prompt):

    for attempt in range(MAX_RETRY):

        try:

            if provider == "gemini":

                response = client.models.generate_content(
                    model=MODELLO,
                    contents=prompt
                )

                out = getattr(response, "text", None)

            else:

                response = client.responses.create(
                    model=MODELLO,
                    input=prompt
                )

                out = response.output_text

            if out and out.strip():

                return out.strip()

            print(f"⚠️ OUTPUT VUOTO (tentativo {attempt + 1})")

        except Exception as e:

            msg = str(e)

            print("\n====================")
            print("⚠️ ERRORE LLM")
            print("====================")
            print(msg)

            if "503" in msg or "UNAVAILABLE" in msg:

                wait = (2 ** attempt) + random.uniform(0, 1)

            else:

                wait = 1 + random.uniform(0, 1)

            print(f"Retry tra {wait:.2f}s")

            time.sleep(wait)

    print("\n❌ LLM FALLITO DEFINITIVAMENTE")

    return None