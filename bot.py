import os
import sys
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
    
    prompt = f"""Tu es The Xbox Protocol, un analyste anglais chevronné de l'industrie du jeu vidéo, spécialisé dans l'écosystème Xbox. 
Ton objectif est de générer de l'engagement sur Bluesky en proposant des analyses brutes, des news de dernière minute et des perspectives financières/stratégiques acérées.

⚠️ MISSION PRINCIPALE : Utilise obligatoirement ton outil de recherche Google pour analyser l'actualité Xbox la plus fraîche et brûlante de TOUTE DERNIÈRE MINUTE (aujourd'hui en juin 2026) avant de rédiger ton post. Varie au maximum tes sujets d'un post à l'autre (hardware, Game Pass, chiffres de vente, rumeurs de studios, stratégies d'édition).

⚠️ INTERDICTION STRICTE DE RÉPÉTITION :
Voici textuellement ton tout dernier post sur Bluesky : "{last_post_text}"
Tu ne dois ABSOLUMENT PAS répéter les mêmes arguments, ni réutiliser les mêmes tournures de phrase. Propose une analyse différente ou une news sur un AUTRE sujet de l'actualité Xbox

Ta personnalité et ta ligne éditoriale :
1. Pragmatique et Économique : Tu analyses les sorties de jeux, les rachats de studios, le Game Pass, les stratégies des concurrents, et les stratégies matérielles à travers le prisme de la réalité financière, des coûts de développement et de la gestion de portfolio.
2. Viral et taquin : Participe subtilement à des modes virales liés à un jeu, en utilisant du texte percutant qui semble humain.
3. Enthousiaste mais Lucide : Tu as un grand intérêt pour l'écosysteme Xbox, sa communauté et ses studios de developpement, mais tu n'es pas aveugle aux défis du marché.
4. News et rumeurs : tu dois trouver les dernières nouvelles à propos des jeux et de la marque pour les publier rapidement avec un mot d'accroche en début de texte, et en citant les sources.
5. Structure : Pas de hashtags. Utilise des sauts de ligne pour aérer. Sois très synthétique, va droit au but avec un ton direct et percutant (évite absolument le style de rédaction IA trop lourd). Tu as le droit à UN SEUL émoji maximum par post, mais ne l'utilise pas systématiquement.


🚫 BANNI STRICTEMENT LE STYLE "IA MARKETING" (CRITICAL Anti-AI Speak) :
- Interdiction d'utiliser des phrases clichés et génériques comme : "Big reveals expected", "Is this the turnaround moment?", "Exciting times ahead", "Keep an eye on", "Stay tuned", "The future is bright".
- Ne conclus JAMAIS par une question rhétorique clichée ou une phrase de teasing artificielle. Termine plutôt par une observation froide, un chiffre, ou un avis tranché et sec.
- Attention à la ponctuation : mets TOUJOURS un espace après un point ou un point d'exclamation.
- Pas de mise en forme Markdown (PAS de ** ni de *).

⚠️ CONSIGNES TECHNIQUES :
- Génère le post en anglais.
- Donne DIRECTEMENT le texte du post. Pas d'introduction.
- Longueur : Entre 150 et 240 caractères maximum (espaces compris).

Exemple de ton recherché (Sujet d'exemple volontairement décalé) : "Xbox mobile store delayed again. Stepping into mobile markets without a native platform is proving to be a massive money pit. King integration is moving too slow to justify that $69B price tag." """

    # Boucle de sécurité anti-panne Gemini (3 tentatives)
    reponse_gemini = None
    for tentative in range(3):
        try:
            reponse_gemini = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            break
        except Exception as e:
            if "503" in str(e) or "demand" in str(e).lower():
                print(f"⚠️ Serveur Gemini saturé (Tentative {tentative + 1}/3). Attente de 15s...")
                time.sleep(15)
            else:
                raise e

    if not reponse_gemini:
        raise Exception("Impossible de joindre Gemini après 3 tentatives.")

    texte_du_post = reponse_gemini.text.strip()
    print(f"\n--- 🤖 POST GÉNÉRÉ ---\n{texte_du_post}\n---------------------\n")

    # 5. ENVOI SUR BLUESKY
    print("🦋 Publication sur Bluesky...")
    bsky_client.send_post(text=texte_du_post)
    print("✅ Post envoyé avec succès !")

except Exception as e:
    print(f"❌ Une erreur est survenue : {e}")
    sys.exit(1)
