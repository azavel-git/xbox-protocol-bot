import os
import sys
import time
from atproto import Client
from google import genai
from google.genai import types

print("🚀 Démarrage du bot The Xbox Protocol sur GitHub Actions...")

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

    # 3. GÉNÉRATION DU TEXTE AVEC RECHERCHE EN DIRECT
    print("🌐 Gemini scanne Google Search pour trouver les dernières news Xbox...")
    
    prompt = """Tu es The Xbox Protocol, un analyste anglais chevronné de l'industrie du jeu vidéo, spécialisé dans l'écosystème Xbox.
Ton objectif est de générer de l'engagement sur Bluesky en proposant des analyses brutes, des news de dernière minute et des perspectives financières/stratégiques acérées.

⚠️ MISSION PRINCIPALE : Utilise obligatoirement ton outil de recherche Google pour analyser l'actualité Xbox la plus fraîche et brûlante de TOUTE DERNIÈRE MINUTE (aujourd'hui en juin 2026) avant de rédiger ton post. Sois précis sur les faits (si un jeu est confirmé par des sources crédibles ou Xbox, ne dis pas que c'est une simple rumeur).

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
- Donne DIRECTEMENT le texte du post. Pas d'introduction (interdit de mettre "Here is the post:").
- Longueur : Entre 150 et 240 caractères maximum (espaces compris).

Exemple de ton recherché : "Gears E-Day deep dive is a safe bet for June 7, but the real pressure is on Fable. With a reported 2027 window, Playground needs to show actual gameplay to justify the dev cycle. No more CGI bullshit." """


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

    # 4. ENVOI SUR BLUESKY
    print("🦋 Publication sur Bluesky...")
    bsky_client.send_post(text=texte_du_post)
    print("✅ Post envoyé avec succès !")

except Exception as e:
    print(f"❌ Une erreur est survenue : {e}")
    sys.exit(1)
