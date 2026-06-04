from llm_provider import *
from utils import *

cause_possibili = {}

contesto = {
    "sintomi": "",
    "storico": [],
    "domande_fatte": [],
    "vincoli": [],
    "storico_probabilità": [],
    "turni": 0  
}

# ======================
# PARAMETRI
# ======================
MIN_DOMANDE = 5
MAX_DOMANDE = 10
TURNI_DISAMBIGUA = 2
MIN_AMBIGUITA = 0
MAX_AMBIGUITA = 5 #standard: MAX_DOMANDE-MIN_DOMANDE
PROB_MAX=0.90

# ======================
# RILEVA SOLUZIONE
# ======================
def rileva_soluzione_esplicita(risposta):

    prompt = f"""
    Testo utente: "{risposta}"

    Sta indicando chiaramente la causa del problema?

    Rispondi JSON:
    {{
        "soluzione": true/false,
        "causa": "descrizione"
    }}
    """

    res = safe_json_call(prompt, {"soluzione": False, "causa": ""})

    if not isinstance(res, dict):
        return {"soluzione": False, "causa": ""}

    res.setdefault("soluzione", False)
    res.setdefault("causa", "")

    return res


# ======================
# CONTRADDIZIONI LIGHT
# ======================
def check_contraddizioni(nuova_risposta):

    prompt = f"""
    Storico: {contesto['storico']}
    Nuova risposta: {nuova_risposta}

    Regole:
    1. Contraddizione SOLO se negazione diretta.
    2. Se dubbio -> false

    JSON:
    {{
        "contraddizione": true/false,
        "messaggio": "breve"
    }}
    """

    res = safe_json_call(prompt, {"contraddizione": False, "messaggio": ""})

    if not isinstance(res, dict):
        return {"contraddizione": False, "messaggio": ""}

    res.setdefault("contraddizione", False)
    res.setdefault("messaggio", "")

    return res


# ======================
# CALCOLA BUDGET
# ======================
def calcola_budget():
    prompt = f"""
    Problema: {contesto['sintomi']}
    Quanto è ambiguo da {MIN_AMBIGUITA} a {MAX_AMBIGUITA}

    Valuta in questo modo:
    Livello 1 : se il problema è chiaro e specifico.
    Livello 2 : se hai dei leggeri dubbi o servono piccoli dettagli di contesto.
    Livello 3 : se non hai capito bene alcuni punti e ti servono dettagli essenziali.
    Livello 4 : se il sintomo è vago, hai dubbi seri sulla direzione da prendere.
    Livello 5 : se il problema è criptico o del tutto mancante (es. "Non funziona nulla").

    Rispondi solo con formato JSON, esempio:
    {{ "ambiguità": 3 }}
    """
    data = safe_json_call(prompt, {"ambiguità": 0.5})
    n_amb = int(data.get("ambiguità", 0.5))

    # Budget totale domande (investigazione)
    budget = min(MAX_DOMANDE, MIN_DOMANDE + n_amb)

    return budget


# ======================
# DISAMBIGUAZIONE
# ======================
def disambigua(get_risposta):

    print("\n--- Disambiguazione ---")

    for _ in range(TURNI_DISAMBIGUA):

        prompt = f"""
        Problema: {contesto['sintomi']}
        Storico: {contesto['storico']}

        Domande già fatte:
        {contesto['domande_fatte']}

        Serve davvero un chiarimento essenziale?

        Se NO:
        {{
            "serve": false,
            "domanda": ""
        }}

        Se SI:
        {{
            "serve": true,
            "domanda": "testo"
        }}
        """

        data = safe_json_call(prompt, {"serve": False, "domanda": ""})

        if not data.get("serve"):
            print("✅ Disambiguazione completata")
            return

        domanda = data.get("domanda", "").strip()

        if domanda == "" or domanda in contesto["domande_fatte"]:
            return

        contesto["domande_fatte"].append(domanda)

        print(f"\n🔍 {domanda}")

        risposta = get_risposta(domanda)
        contesto["turni"] += 1

        if not risposta:
            risposta = ""

        risposta = risposta.lower().strip()

        print(f"🧑 {risposta}")

        check = check_contraddizioni(risposta)

        if check.get("contraddizione"):
            print(f"⚠️ {check.get('messaggio')}")
            continue

        contesto["storico"].append(risposta)
        contesto["vincoli"].append(risposta)


# ======================
# GENERA CAUSE
# ======================
def genera_cause():

    prompt = f"""
    Problema:
    {contesto['sintomi']}

    Vincoli:
    {contesto['vincoli']}

    Genera ESATTAMENTE 4 possibili cause tecniche plausibili.

    REGOLE:
    - cause brevi
    - niente spiegazioni
    - niente testo extra
    - probabilità tra 0 e 1
    - somma circa 1

    ESEMPIO:

    {{
        "batteria scarica": 0.40,
        "relè difettoso": 0.30,
        "motorino avviamento": 0.20,
        "fusibile bruciato": 0.10
    }}
    """

    res = safe_json_call(
        prompt,
        default=None,
        debug_name="GENERA_CAUSE"
    )

    # fallback SOLO se veramente necessario
    if not res or not isinstance(res, dict):

        print("\n⚠️ FALLBACK CAUSE")

        return {
            "causa sconosciuta": 1.0
        }

    nuove = {}

    for k, v in res.items():

        try:

            prob = float(v)

            if prob > 0:

                nuove[k.strip().lower()] = prob

        except:
            continue

    if len(nuove) == 0:

        print("\n⚠️ CAUSE VUOTE DOPO FILTRO")

        return {
            "causa sconosciuta": 1.0
        }

    totale = sum(nuove.values())

    return {
        k: v / totale
        for k, v in nuove.items()
    }


# ======================
# AGGIORNA CAUSE
# ======================
def aggiorna_cause():

    prompt = f"""
    Problema:
    {contesto['sintomi']}

    Storico:
    {contesto['storico']}

    Cause attuali:
    {cause_possibili}

    Aggiorna SOLO le probabilità.

    Mantieni gli stessi nomi delle cause.

    JSON:
    {{
        "batteria scarica": 0.50,
        "relè difettoso": 0.30,
        "motorino avviamento": 0.20
    }}
    """

    nuove = safe_json_call(
        prompt,
        default=None,
        debug_name="AGGIORNA_CAUSE"
    )

    if not nuove:

        print("\n⚠️ UPDATE FALLITO → mantengo precedenti")

        return

    filtrate = {}

    for c, p in nuove.items():

        try:

            p = float(p)

            if p > 0:
                filtrate[c] = p

        except:
            continue

    if len(filtrate) == 0:

        print("\n⚠️ UPDATE VUOTO → mantengo precedenti")

        return

    totale = sum(filtrate.values())

    cause_possibili.clear()

    for c, p in filtrate.items():

        cause_possibili[c] = {
            "descrizione": c,
            "probabilità": p / totale
        }


# ======================
# DOMANDA
# ======================
def genera_domanda():

    prompt = f"""
    Problema: {contesto['sintomi']}
    Cause: {cause_possibili}

    Domande già fatte:
    {contesto['domande_fatte']}

    Fai UNA domanda nuova utile a distinguere
    le due cause più probabili.
    """

    try:
        testo = chiama_llm(prompt)

        if not testo:
            raise Exception("vuoto")

        testo = testo.strip()

    except:
        testo = ""

    if testo == "" or testo in contesto["domande_fatte"]:
        testo = "Puoi descrivere meglio quando succede il problema?"

    contesto["domande_fatte"].append(testo)

    return testo


# ======================
# DEBUG
# ======================
def stampa_debug():

    print("\n[CAUSE ATTUALI]")

    ordinate = sorted(
        cause_possibili.items(),
        key=lambda x: x[1]["probabilità"],
        reverse=True
    )

    for nome, info in ordinate:
        print(f"- {info['descrizione']} → {info['probabilità']:.2f}")
    
    print("\n[STORICO]")
    print(contesto["storico"])

    print("\n[VINCOLI]")
    print(contesto["vincoli"])


# ======================
# SNAPSHOT
# ======================
def salva_snapshot():

    ordinate = sorted(
        cause_possibili.items(),
        key=lambda x: x[1]["probabilità"],
        reverse=True
    )

    top2 = []

    for item in ordinate[:2]:
        top2.append((item[0], item[1]["probabilità"]))

    contesto["storico_probabilità"].append(top2)


# ======================
# CONVERGENZA
# ======================
'''
def stabilizzato():

    storico = contesto["storico_probabilità"]

    if len(storico) < TURNI_STABILI:
        return False

    ultimi = storico[-TURNI_STABILI:]

    nomi = []

    for turno in ultimi:
        if len(turno) == 0:
            return False
        nomi.append(turno[0][0])

    if len(set(nomi)) != 1:
        return False

    valori = [turno[0][1] for turno in ultimi]

    delta = max(valori) - min(valori)

    return delta <= SOGLIA_STABILITÀ
'''

# ======================
# RESET
# ======================
def reset_stato():
    global contesto, cause_possibili

    cause_possibili.clear()

    contesto["sintomi"] = ""
    contesto["storico"].clear()
    contesto["domande_fatte"].clear()
    contesto["vincoli"].clear()
    contesto["storico_probabilità"].clear()
    contesto["turni"] = 0