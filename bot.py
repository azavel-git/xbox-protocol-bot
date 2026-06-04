import os
import sys
import random
import time
from atproto import Client
from google import genai
from google.genai import types

print("🚀 Démarrage du bot The Xbox Protocol sur GitHub Actions...")
delai = random.randint(1, 30)  # Tire au sort entre 1 et 60 minutes (modifie 60 par 90 si tu veux plus)
print(f"⏳ Humanisation du post : pause aléatoire de {delai} minutes...")
time.sleep(delai * 60)
print("🔋 Fin de la pause ! Connexion aux services...")

# 1. RÉCUPÉRATION DES SECRETS DE SÉCURITÉ
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.environ.get("BLUESKY_PASSWORD")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not all([BLUESKY_HANDLE, BLUESKY_PASSWORD, GEMINI_API_KEY]):
    print("❌ Erreur : Clés de sécurité manquantes dans les configurations GitHub.")
    sys.exit(1)

try:
    # 2. CONNEXION AUX SERVICES
    bsky_client = Client()
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

    # 3. RÉCUPÉRATION DU DERNIER POST POUR ÉVITER LA RÉPÉTITION
    print("🔍 Récupération du dernier post Bluesky pour donner une mémoire au bot...")
    last_post_text = ""
    try:
        feed = bsky_client.get_author_feed(actor=BLUESKY_HANDLE, limit=1)
        if feed and feed.feed:
            last_post_text = feed.feed[0].post.record.text
            print(f"📝 Dernier post en date : '{last_post_text}'")
    except Exception as e:
        print(f"⚠️ Impossible de lire le fil Bluesky (première utilisation ou bug) : {e}")

    # 4. GÉNÉRATION DU TEXTE AVEC RECHERCHE EN DIRECT
    print("🌐 Gemini scanne Google Search pour trouver les dernières news Xbox...")

    system_prompt = f"""Tu es The Xbox Protocol, un analyste anglais chevronné de l'industrie du jeu vidéo, spécialisé dans l'écosystème Xbox. 
Ton objectif est de générer de l'engagement sur Bluesky avec un ton direct, pragmatique et tranché.

⚖️ STRATÉGIE D'ALTERNANCE OBLIGATOIRE :
Tu disposes de deux formats exclusifs. Tu dois impérativement ALTERNER entre eux d'un post à l'autre :
1. FORMAT [BREAKING NEWS] : Tu rapportes une seule actualité brûlante (Hardware, Jeu, Game Pass) dénichée via Google Search (juin 2026), accompagnée de ton avis critique immédiat.
2. FORMAT [STRATEGIC ANALYSIS] : Pas de news chaude ici. Tu prends du recul pour analyser la santé d'un studio Xbox, spéculer sur un projet en cours/lointain, ou analyser un mouvement de la concurrence (Sony/Nintendo) et son impact sur Xbox.

🚨 RÈGLE DE STRUCTURE CRITIQUE : 
Un SEUL sujet par post. Interdiction absolue de mélanger les deux formats, de faire des listes ou d'évoquer plusieurs thèmes/jeux différents. Pas de connecteurs de cumul (also, additionally, as well).

🚫 STYLE "IA MARKETING" BANNI :
- Pas de phrases clichés ("Big reveals expected", "Is this the turnaround moment?", "Exciting times ahead", "Stay tuned", "The future is bright").
- Pas de mise en forme Markdown (PAS de ** ni de *).
- Pas de hashtags. Un seul émoji maximum, sans automatisme.
- Longueur : Entre 150 et 240 caractères maximum (espaces compris).
- Langue : Anglais."""

    # 1. DEFINITION DU PROMPT UTILISATEUR (LOGIQUE D'ANALYSE D'ALTERNANCE)
    user_prompt = f"""[TON DERNIER POST SUR BLUESKY]
"{last_post_text}"

[CONSIGNES DE SÉLECTION DU FORMAT]
1. Analyse objectivement ton dernier post ci-dessus. 
2. Détermine son format : S'agissait-il d'une annonce de News/Date/Showcase, ou d'une Analyse de fond/Spéculation ?
3. Choisis obligatoirement le FORMAT OPPOSÉ pour ton nouveau post :
   - Si le dernier post était une News : Rédige une [STRATEGIC ANALYSIS] de fond (studio, projet en cours, concurrence) sans utiliser Google Search.
   - Si le dernier post était une Analyse : Utilise Google Search pour trouver une [BREAKING NEWS] de toute dernière minute (juin 2026) et balance l'info.

🚨 CONTRAINTE DE VARIÉTÉ : 
Interdiction absolue de parler du même jeu ou du même sujet que le post précédent. Change de cible à 100%. Rédige directement ton unique post Bluesky."""

    # 2. BOUCLE DE SÉCURITÉ ANTI-PANNE GEMINI (5 tentatives)
    reponse_gemini = None
    for tentative in range(5):
        try:
            reponse_gemini = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.8,
                    top_p=0.95
                )
            )
            break
        except Exception as e:
            if "503" in str(e) or "demand" in str(e).lower() or "quota" in str(e).lower():
                print(f"⚠️ Serveur Gemini saturé (Tentative {tentative + 1}/5). Attente de 30s...")
                time.sleep(30)
            else:
                raise e

    if not reponse_gemini:
        raise Exception("Impossible de joindre Gemini après 5 tentatives.")

    texte_du_post = reponse_gemini.text.strip()

    # 🚨 SÉCURITÉ ANTI-CRASH BLUESKY (Limite stricte de 300 caractères)
    if len(texte_du_post) > 300:
        print(f"⚠️ Alerte : Le post généré était trop long ({len(texte_du_post)} caractères).")
        texte_du_post = texte_du_post[:297] + "..."
        
    print(f"\n--- 🤖 POST GÉNÉRÉ ---\n{texte_du_post}\n---------------------\n")

    # 3. ENVOI SUR BLUESKY
    print("🦋 Publication sur Bluesky...")
    bsky_client.send_post(text=texte_du_post)
    print("✅ Post envoyé avec succès !")

    
