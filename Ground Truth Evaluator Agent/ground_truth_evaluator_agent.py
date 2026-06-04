# =====================================================================
# AGENTE VALUTATORE (Ground Truth Evaluation Agent)
# =====================================================================
import os
import sys
from utils import safe_json_call

class AgenteValutatore:
    def __init__(self, soluzione_reale=""):
        # Memorizza la soluzione reale (ground truth) estratta originariamente dal file .ps
        self.soluzione = soluzione_reale

    def valuta(self, proposta):
        """
        Esegue la valutazione comparativa tra la diagnosi dell'investigatore
        e la soluzione reale basandosi prima su un match testuale e poi su LLM.
        """
        def normalizza(t):
            # Ottimizza le stringhe rimuovendo maiuscole, articoli comuni ed accenti
            return t.lower().replace("è", "").replace("la ", "").replace("il ", "").strip()

        sol = normalizza(self.soluzione)
        prop = normalizza(proposta)

        # 1. TENTATIVO DI MATCH DIRETTO (Ottimizzazione algoritmica)
        if prop in sol or sol in prop:
            return {
                "analisi_passo_passo": "Rilevato match testuale diretto o inclusione perfetta tra le due stringhe normalizzate.",
                "score": 100, 
                "ok": True
            }

        # 2. FALLBACK TRAMITE AGENTE LLM (Analisi semantica)
        prompt = f"""
        Sei un valutatore esperto e imparziale. Il tuo compito è confrontare una "Soluzione Proposta" da un agente software con la "Soluzione Reale" (ground truth) e assegnare un punteggio di accuratezza concettuale.

        Soluzione Reale: "{self.soluzione}"
        Soluzione Proposta: "{proposta}"

        ### Linee Guida per la Valutazione:
        1. Focus sul Concetto: Non valutare la forma sintattica o la lunghezza. Se la proposta è più sintetica ma coglie la causa principale corretta, deve ricevere un punteggio alto.
        2. Identificazione della Causa: Verifica se la causa scatenante individuata nella soluzione proposta coincide (o è strettamente correlata) con quella della soluzione reale.

        ### Scala di Punteggio (Rubric):
        - 100: La soluzione proposta identifica esattamente la stessa causa principale della soluzione reale.
        - 75: La causa principale è corretta, ma mancano alcuni dettagli secondari importanti o sfumature del contesto.
        - 50: La soluzione proposta è parzialmente corretta: coglie l'ambito del problema o una causa secondaria, ma manca il punto centrale.
        - 25: La soluzione contiene solo pochissimi elementi corretti o menziona la causa corretta in modo confuso/errato.
        - 0: La soluzione proposta è completamente sbagliata, inventata o identifica una causa logicamente incompatibile.

        ### Output Richiesto:
        Restituisci ESCLUSIVAMENTE un oggetto JSON valido con la struttura indicata sotto. È fondamentale che il campo "analisi_passo_passo" venga compilato prima del punteggio, descrivendo le somiglianze e le differenze riscontrate.

        JSON:
        {{
            "analisi_passo_passo": "Inserisci qui una dettagliata analisi comparativa, spiegando cosa coincide e cosa manca rispetto alla soluzione reale",
            "score": numero_intero_tra_0_e_100,
            "ok": true_se_score_maggiore_o_uguale_a_50_altrimenti_false
        }}
        """

        # Invocazione robusta dell'LLM delegato alla validazione dei risultati finali
        return safe_json_call(prompt, {"analisi_passo_passo": "Fallimento nel parsing del JSON di valutazione.", "score": 0, "ok": False})


# =====================================================================
# INTERFACCIA DI VALUTAZIONE AUTONOMA DA TERMINALE
# =====================================================================
def main():
    print("==================================================")
    print("              AVVIO AGENTE VALUTATORE             ")
    print("==================================================")

    # Richiesta manuale interattiva dei dati di test se lanciato in autonomia
    print("\n[INPUT] Inserisci la Soluzione Reale (Ground Truth):")
    sol_reale = input("> ").strip()
    
    print("\n[INPUT] Inserisci la Soluzione Proposta dall'Investigatore:")
    sol_proposta = input("> ").strip()

    if not sol_reale or not sol_proposta:
        print("❌ Errore: Entrambi i campi stringa devono essere compilati.")
        return

    # Inizializzazione dell'agente con la soluzione reale ed esecuzione del metodo richiesto
    valutatore = AgenteValutatore(soluzione_reale=sol_reale)
    
    print("\n[ELABORAZIONE] Avvio del processo decisionale dell'agente...")
    risultato = valutatore.valuta(sol_proposta)
    
    # Stampa a schermo strutturata dei risultati emessi dall'agente
    print("\n================ ESITO VALUTAZIONE ================")
    print(f"Analisi: {risultato.get('analisi_passo_passo')}")
    print(f"Score Assegnato: {risultato.get('score')}/100")
    print(f"Esito Approvato (OK): {risultato.get('ok')}")
    print("====================================================")

if __name__ == "__main__":
    main()
