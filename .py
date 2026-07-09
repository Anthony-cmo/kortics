from supabase import create_client, Client
import requests
import datetime
import random
import time

# =====================================================================
# CONFIGURATION DES ACCÈS (On ne change rien ici)
# =====================================================================
SUPABASE_URL = "https://otbonobfeyurkfuwavoa.supabase.co"
SUPABASE_KEY = "sb_publishable_8tjc55jb1aAqJGc_n3TCJQ_Twxl3q_P"
TENNIS_API_KEY = "a5fd614cf812554072fa03d63c679c296234a40ed3ce93f1fc10d5d8cf7ae7af"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# =====================================================================
# LE CERVEAU MATHÉMATIQUE (On le garde, il est parfait)
# =====================================================================
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

# =====================================================================
# FONCTION : ALLER CHERCHER LES VRAIES STATS D'UN JOUEUR
# =====================================================================
def get_player_stats_api(player_key):
    """
    Récupère les statistiques réelles d'un joueur via l'API Tennis.
    Si une donnée manque, on met une valeur moyenne (Fail-safe).
    """
    # Si le joueur n'a pas de clé (pas d'ID API), on retourne des valeurs moyennes
    if not player_key:
        return {'classement': 100, 'pct_vic_carriere': 50, 'pct_vic_surface': 50, 'pct_sets_gagnes': 50, 'pct_vic_1an': 50, 'pct_vic_10_derniers': 50, 'matchs_dernier_mois': 4, 'defaites_favori_mois': 0, 'victoires_outsider_mois': 0, 'pct_1er_service': 65}

    # Appel à l'API pour les stats du joueur
    url_stats = f"https://api.api-tennis.com/tennis/?method=get_players_stats&APIkey={TENNIS_API_KEY}&player_key={player_key}"
    try:
        raw_reponse = requests.get(url_stats, headers=HEADERS, timeout=10)
        reponse = raw_reponse.json()
    except:
        # En cas d'erreur API, on retourne des valeurs moyennes
        return {'classement': 100, 'pct_vic_carriere': 50, 'pct_vic_surface': 50, 'pct_sets_gagnes': 50, 'pct_vic_1an': 50, 'pct_vic_10_derniers': 50, 'matchs_dernier_mois': 4, 'defaites_favori_mois': 0, 'victoires_outsider_mois': 0, 'pct_1er_service': 65}
        
    if "result" not in reponse:
        return {'classement': 100, 'pct_vic_carriere': 50, 'pct_vic_surface': 50, 'pct_sets_gagnes': 50, 'pct_vic_1an': 50, 'pct_vic_10_derniers': 50, 'matchs_dernier_mois': 4, 'defaites_favori_mois': 0, 'victoires_outsider_mois': 0, 'pct_1er_service': 65}

    # Extraction des données réelles
    data = reponse["result"]
    stats_reel = {
        'classement': int(data.get("ranking", 100)), # Si pas de classement, on met 100
        'pct_vic_carriere': float(data.get("win_percentage", 50)),
        'pct_vic_surface': float(data.get("surface_win_percentage", 50)),
        'pct_sets_gagnes': float(data.get("set_win_percentage", 50)),
        'pct_vic_1an': float(data.get("win_percentage_1y", 50)),
        'pct_vic_10_derniers': float(data.get("last_10_win_percentage", 50)),
        'matchs_dernier_mois': int(data.get("matches_played_1m", 4)),
        'defaites_favori_mois': int(data.get("matches_lost_as_favorite_1m", 0)),
        'victoires_outsider_mois': int(data.get("matches_won_as_outsider_1m", 0)),
        'pct_1er_service': float(data.get("first_serve_win_percentage", 65))
    }
    return stats_reel

# =====================================================================
# FONCTION PRINCIPALE : L'ASPIRATEUR AUTOMATIQUE
# =====================================================================
def main():
    aujourdhui = datetime.date.today().strftime("%Y-%m-%d")
    url_fixtures = f"https://api.api-tennis.com/tennis/?method=get_fixtures&APIkey={TENNIS_API_KEY}&date_start={aujourdhui}&date_stop={aujourdhui}"
    
    print(f"📡 Récupération des matchs du {aujourdhui}...")
    raw_reponse = requests.get(url_fixtures, headers=HEADERS)
    try:
        reponse = raw_reponse.json()
    except Exception as e:
        print("❌ Erreur critique de l'API (HTML reçu).")
        return
        
    if "result" not in reponse:
        print("⚠️ Pas de matchs reçus pour aujourd'hui.")
        return
        
    matchs = reponse["result"]
    print(f"🎾 {len(matchs)} matchs capturés ! Lancement de l'analyse réelle...")
    
    compteur = 0
    # Limite pour le test car les appels de stats sont longs
    limite_matchs = 5 
    
    for m in matchs:
        if compteur >= limite_matchs:
            break
            
        nom_tournoi = m.get("league_name") or "Tournoi International"
        
        # Récupération des clés uniques des joueurs (vital pour les stats)
        player_a_key = m.get("event_home_player_key") or m.get("event_first_player_key")
        player_b_key = m.get("event_away_player_key") or m.get("event_second_player_key")
        
        joueur_1 = m.get("event_home_team") or m.get("event_first_player") or "Joueur A"
        joueur_2 = m.get("event_away_team") or m.get("event_second_player") or "Joueur B"
        
        # 🧠 BRANCHEMENT DES VRAIES STATISTIQUES (Le cœur du changement)
        print(f"🧠 Analyse statistique réelle : {joueur_1} vs {joueur_2}...")
        stats_j1 = get_player_stats_api(player_a_key)
        stats_j2 = get_player_stats_api(player_b_key)
        
        # Petite pause pour ne pas surcharger l'API Tennis (Respect)
        time.sleep(0.5)
        
        # L'IA fait ses calculs sur ces vraies données
        proba_ia, cote_ia = calculer_cerveau_tennis(stats_j1, stats_j2)
        
        # Récupération des vraies cotes du bookmaker
        cote_bookmaker_1 = float(m.get("odds_first_player") or 0.0)
        cote_bookmaker_2 = float(m.get("odds_second_player") or 0.0)
        
        # Si pas de cotes bookmaker, on ne peut pas calculer de ValueBet
        if cote_bookmaker_1 == 0.0 or cote_bookmaker_2 == 0.0:
            continue

        # Comparaison pour le ValueBet (Pour le Joueur 1 uniquement ici)
        cote_bookmaker = cote_bookmaker_1
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
        except Exception as e:
            print(f"❌ Erreur lors de l'insertion Supabase : {e}")
            pass

    print(f"🎉 Analyse réelle terminée. {compteur} Value Bets détectées et envoyées dans Supabase.")

if __name__ == "__main__":
    main()
