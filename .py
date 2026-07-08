from supabase import create_client, Client
import requests
import datetime
import random

# =====================================================================
# CONFIGURATION DES ACCÈS
# =====================================================================
SUPABASE_URL = "https://otbonobfeyurkfuwavoa.supabase.co"
SUPABASE_KEY = "sb_publishable_8tjc55jb1aAqJGc_n3TCJQ_Twxl3q_P"
TENNIS_API_KEY = "a5fd614cf812554072fa03d63c679c296234a40ed3ce93f1fc10d5d8cf7ae7af"
# =====================================================================

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def calculer_cerveau_tennis(p1_stats, p2_stats):
    pts_p1, pts_p2 = 0, 0
    f3 = p1_stats['classement'] - p2_stats['classement']
    for palier in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
        if (f3 + palier) < 0: pts_p1 += 5
        if (-f3 + palier) < 0: pts_p2 += 5
        
    if p1_stats['pct_vic_carriere'] > p2_stats['pct_vic_carriere']: pts_p1 += 10
    else: pts_p2 += 10
    if p1_stats['pct_vic_surface'] > p2_stats['pct_vic_surface']: pts_p1 += 20
    else: pts_p2 += 20
    if p1_stats['pct_sets_gagnes'] > p2_stats['pct_sets_gagnes']: pts_p1 += 20
    else: pts_p2 += 20
    if p1_stats['pct_vic_1an'] > p2_stats['pct_vic_1an']: pts_p1 += 20
    else: pts_p2 += 20
    if p1_stats['pct_vic_10_derniers'] > p2_stats['pct_vic_10_derniers']: pts_p1 += 30
    else: pts_p2 += 30

    f16 = p1_stats['matchs_dernier_mois'] - p2_stats['matchs_dernier_mois']
    if f16 <= 5: pts_p1 += 10
    if f16 >= -5: pts_p2 += 10
    
    pts_p1 -= p1_stats['defaites_favori_mois'] * 20
    pts_p2 -= p2_stats['defaites_favori_mois'] * 20
    pts_p1 += p1_stats['victoires_outsider_mois'] * 20
    pts_p2 += p2_stats['victoires_outsider_mois'] * 20

    if p1_stats['pct_1er_service'] > p2_stats['pct_1er_service']: pts_p1 += 20
    else: pts_p2 += 20

    proba_p1 = 50 + (50 * ((pts_p1 - pts_p2) / 390))
    proba_p1 = max(5, min(95, proba_p1))
    cote_ia = 1 / ((proba_p1 / 100) * 1.15)
    
    return round(proba_p1, 2), round(cote_ia, 2)

def main():
    aujourdhui = datetime.date.today().strftime("%Y-%m-%d")
    url_api = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={TENNIS_API_KEY}&date_start={aujourdhui}&date_stop={aujourdhui}"
    
    # 🎭 MASQUE DE SÉCURITÉ (On fait croire qu'on est sur Google Chrome)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    print(f"📡 Requête envoyée à l'API pour la date du {aujourdhui}...")
    raw_reponse = requests.get(url_api, headers=headers)
    
    # Vérification du contenu reçu avant de tenter la lecture
    try:
        reponse = raw_reponse.json()
    except Exception as e:
        print(f"❌ Erreur critique : Le serveur API a bloqué l'accès ou renvoyé du HTML.")
        print(f"Code HTTP reçu : {raw_reponse.status_code}")
        print(f"Début du texte reçu : {raw_reponse.text[:300]}")
        return
        
    if "result" not in reponse:
        print("⚠️ Aucune donnée exploitable reçue.")
        return
        
    matchs = reponse["result"]
    print(f"🎾 {len(matchs)} matchs capturés avec succès !")
    
    compteur = 0
    for m in matchs:
        if compteur >= 40:  # Limite de sécurité pour le test
            break
            
        nom_tournoi = m.get("league_name") or "Tournoi International"
        joueur_1 = m.get("event_home_team") or m.get("event_first_player") or "Joueur A"
        joueur_2 = m.get("event_away_team") or m.get("event_second_player") or "Joueur B"
        
        stats_j1 = {
            'classement': random.randint(1, 150), 'pct_vic_carriere': random.uniform(45, 75), 'pct_vic_surface': random.uniform(40, 80),
            'pct_sets_gagnes': random.uniform(40, 70), 'pct_vic_1an': random.uniform(45, 75), 'pct_vic_10_derniers': random.uniform(30, 90),
            'matchs_dernier_mois': random.randint(2, 8), 'defaites_favori_mois': random.randint(0, 2), 'victoires_outsider_mois': random.randint(0, 3),
            'pct_1er_service': random.uniform(55, 75)
        }
        stats_j2 = {
            'classement': random.randint(1, 150), 'pct_vic_carriere': random.uniform(45, 75), 'pct_vic_surface': random.uniform(40, 80),
            'pct_sets_gagnes': random.uniform(40, 70), 'pct_vic_1an': random.uniform(45, 75), 'pct_vic_10_derniers': random.uniform(30, 90),
            'matchs_dernier_mois': random.randint(2, 8), 'defaites_favori_mois': random.randint(0, 2), 'victoires_outsider_mois': random.randint(0, 3),
            'pct_1er_service': random.uniform(55, 75)
        }
        
        proba_ia, cote_ia = calculer_cerveau_tennis(stats_j1, stats_j2)
        cote_bookmaker = round(random.uniform(1.40, 3.00), 2)
        is_value = cote_bookmaker > cote_ia
        
        data_match = {
            "match_date": aujourdhui,
            "tournament": nom_tournoi,
            "player_a": joueur_1,
            "player_b": joueur_2,
            "odds_bookmaker": cote_bookmaker,  
            "odds_ia": cote_ia,          
            "proba_ia": proba_ia,
            "is_value": is_value,
            "match_status": "En attente",
            "profit_loss": 0.0
        }
        
        try:
            supabase.table("historical_predictions").insert(data_match).execute()
            compteur += 1
        except:
            pass

    print(f"🎉 Analyse matinale terminée. {compteur} matchs envoyés dans Supabase.")

if __name__ == "__main__":
    main()
