from investigatore_core import *

class InvestigatoreAgent:

    def __init__(self, agente_utente):
        self.A = agente_utente

    def get_risposta(self, domanda):
        return self.A.rispondi(domanda)

    def set_problema(self, problema):
        contesto["sintomi"] = problema

    def init(self):

        budget = calcola_budget()

        disambigua(self.get_risposta)

        iniziali = genera_cause()

        for c, p in iniziali.items():
            try:
                p = float(p)
            except:
                p = 0.0

            cause_possibili[c] = {
                "descrizione": c,
                "probabilità": p
            }

        return budget

    def step(self):

        disambigua(self.get_risposta)

        domanda = genera_domanda()

        print(f"\n🤖 {domanda}")

        contesto["turni"] += 1  
        risposta = self.get_risposta(domanda) or ""
        risposta = risposta.strip()

        print(f"🧑 {risposta}")

        contesto["storico"].append(risposta)
        contesto["vincoli"].append(risposta)

        aggiorna_cause()

        
        if not isinstance(cause_possibili, dict) or len(cause_possibili) == 0:
            return {"stop": True}

        if len(cause_possibili) == 0:
            return {"stop": True}

        salva_snapshot()
        stampa_debug()

        best = max(
            cause_possibili,
            key=lambda x: cause_possibili[x]["probabilità"]
        )

        prob = cause_possibili.get(best, {}).get("probabilità", 0)


        return {
            "stop": False,
            "best": best,
            "prob": prob
        }