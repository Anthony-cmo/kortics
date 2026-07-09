from supabase import create_client, Client
import requests
import datetime

# =====================================================================
# CONFIGURATION DES ACCÈS
# =====================================================================
SUPABASE_URL = "https://otbonobfeyurkfuwavoa.supabase.co"
SUPABASE_KEY = "sb_publishable_8tjc55jb1aAqJGc_n3TCJQ_Twxl3q_P"
TENNIS_API_KEY = "a5fd614cf812554072fa03d63c679c296234a40ed3ce93f1fc10d5d8cf7ae7af"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
MISE_FICTIVE = 10.0 # On simule une mise de 10€ par match pour calculer le profit

def main():
    aujourdhui = datetime.date.today().strftime("%Y-%m-%d")
    print(f"🔍 Début de la vérification des résultats pour le {aujourdhui}...")

    # 1. On va chercher tous les matchs "En attente" et qui sont des "Value Bets" dans Supabase
    try:
        reponse_supa = supabase.table("historical_predictions").select("*").eq("match_date", aujourdhui).eq("match_status", "En attente").eq("is_value", True).execute()
        matchs_en_attente = reponse_supa.data
    except Exception as e:
        print(f"❌ Erreur de lecture Supabase : {e}")
        return

    if not matchs_en_attente:
        print("✅ Aucun match en attente à vérifier pour aujourd'hui.")
        return

    # 2. On appelle l'API Tennis pour avoir les résultats terminés du jour
    url_results = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={TENNIS_API_KEY}&date_start={aujourdhui}&date_stop={aujourdhui}"
    try:
        api_data = requests.get(url_results).json()
        matchs_termines = api_data.get("result", [])
    except:
        print("❌ Impossible de joindre l'API Tennis.")
        return

    # On crée un dictionnaire rapide pour trouver le vainqueur d'un match
    resultats_api = {}
    for m in matchs_termines:
        if m.get("event_status") == "Finished":
            # On stocke le nom du vainqueur
            vainqueur = m.get("event_home_team") if m.get("event_final_result") == "1" else m.get("event_away_team")
            # Astuce pour retrouver le match avec les noms de joueurs
            cle_match = f"{m.get('event_home_team')} vs {m.get('event_away_team')}"
            resultats_api[cle_match] = vainqueur

    # 3. On met à jour nos matchs dans Supabase
    compteur_maj = 0
    for pari in matchs_en_attente:
        joueur_1 = pari['player_a']
        joueur_2 = pari['player_b']
        cle_pari = f"{joueur_1} vs {joueur_2}"
        
        # Le robot a toujours parié sur le joueur qui avait la "value". 
        # Pour simplifier, dans notre code actuel, on vérifie si la Value était sur le J1 ou le J2 en fonction de la proba IA
        joueur_pari = joueur_1 if pari['proba_ia'] > 50 else joueur_2

        # Si le match est bien terminé dans l'API
        if cle_pari in resultats_api:
            vainqueur_reel = resultats_api[cle_pari]
            
            nouveau_statut = "Gagné" if vainqueur_reel == joueur_pari else "Perdu"
            
            if nouveau_statut == "Gagné":
                profit = round((MISE_FICTIVE * pari['odds_bookmaker']) - MISE_FICTIVE, 2)
            else:
                profit = -MISE_FICTIVE
                
            # Mise à jour dans Supabase
            try:
                supabase.table("historical_predictions").update({
                    "match_status": nouveau_statut,
                    "profit_loss": profit
                }).eq("id", pari['id']).execute()
                print(f"🎾 {cle_pari} -> {nouveau_statut} (Profit: {profit}€)")
                compteur_maj += 1
            except Exception as e:
                print(f"❌ Erreur Maj Supabase : {e}")

    print(f"🎉 Vérification terminée. {compteur_maj} matchs mis à jour dans le coffre-fort.")

if __name__ == "__main__":
    main()
