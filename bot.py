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

    import random

    # Sélection aléatoire par Python pour saboter la tendance de l'IA à répéter les mêmes news
    angles_de_redaction = [
        "ANGLE IMPOSÉ : HARDWARE & ACCESSOIRES. Règle : Parle uniquement des fuites de la manette Elite Series 3 ou du pad dédié au Cloud. Interdiction absolue de mentionner un jeu, le Game Pass ou le Showcase de dimanche.",
        "ANGLE IMPOSÉ : COMPÉTITION & RIVALITÉ. Règle : Analyse un mouvement de PlayStation (comme leur récent State of Play ou leurs exclusivités) ou de Nintendo, et comment Xbox doit contrer de manière agressive. Interdiction d'évoquer l'actu interne d'Xbox.",
        "ANGLE IMPOSÉ : NOSTALGIE & REVIVAL. Règle : Parle des rumeurs de retour de franchises cultes (pitchs pour Banjo-Kazooie, licences de l'ère OG Xbox) pour les 25 ans de la marque. Interdiction de parler de Fable, de Gears ou du Showcase.",
        "ANGLE IMPOSÉ : ZOOM INDÉ GAME PASS. Règle : Focus unique sur une pépite indé récente de la vague de juin (comme Solarpunk ou Beastro). Décris brièvement l'ambiance, le genre ou le gameplay du jeu (ex: jeu de gestion cozy, action exigeante, direction artistique pixel-art) pour donner du contexte. Interdiction d'évoquer les gros AAA comme Persona 5 ou Fable.",
        "ANGLE IMPOSÉ : ATTENTE STUDIO. Règle : Spécule sur un projet précis et lointain d'un studio Xbox (ex: Clockwork Revolution de chez inXile, ou State of Decay 3). Interdiction de faire un résumé global ou de parler d'un autre sujet.",
        "ANGLE IMPOSÉ : NEWS XBOX GÉNÉRALE. Règle : Utilise Google Search pour trouver la news générale Xbox la plus fraîche et incontournable de la semaine (juin 2026). Donne l'info brute de manière percutante avec ton avis critique immédiat. Reste à 100% sur ce fait unique.",
        "ANGLE IMPOSÉ : DÉCLARATIONS DES DIRIGEANTS. Règle : Rebondis sur les dernières déclarations publiques, interviews ou mémos d'Asha Sharma (CEO Xbox) ou de Matt Booty. Décortique ce que leurs propos impliquent pour l'avenir de la marque ou des studios. Focus exclusif sur cette déclaration."
    ]
    angle_du_jour = random.choice(angles_de_redaction)

    system_prompt = f"""Tu es The Xbox Protocol, un insider et analyste anglais chevronné du jeu vidéo, spécialisé dans l'écosystème Xbox. 
Ton objectif est de générer de l'engagement sur Bluesky avec un ton direct, tranché et passionné.

🚨 RÈGLE DE STRUCTURE ABSOLUE : 
Rédige ton post sur UN SEUL et UNIQUE sujet précis (une seule idée, une seule news ou une seule spéculation).
Interdiction absolue de faire des listes, de faire des résumés d'actualités croisées ou de citer plus d'un jeu. Pas de connecteurs de cumul (also, additionally, as well). Focus 100% sur un seul angle incisif.

🚫 STYLE "IA MARKETING" BANNI :
- Pas de phrases clichés ("Big reveals expected", "Is this the turnaround moment?", "Exciting times ahead", "Keep an eye on", "Stay tuned", "The future is bright").
- Pas de mise en forme Markdown (PAS de ** ni de *).
- Pas de hashtags. Un seul émoji maximum, sans automatisme.
- Longueur : Entre 150 et 240 caractères maximum (espaces compris).
- Langue : Anglais."""

    # 1. DEFINITION DU PROMPT UTILISATEUR
    user_prompt = f"""[TON DERNIER POST À BANNIR]
"{last_post_text}"

[CONTRAINTE ÉDITORIALE IMPOSÉE PAR PYTHON]
Tu dois impérativement respecter cet angle et cette contrainte pour ce post :
{angle_du_jour}

[INSTRUCTIONS]
1. Utilise Google Search pour trouver des détails précis sur l'actualité Xbox (juin 2026) liés à l'angle imposé ci-dessus, si nécessaire.
2. Rédige ton unique post Bluesky direct et percutant en respectant strictement l'angle imposé. N'évoque rien d'autre et ne te répète jamais par rapport au post à bannir."""

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
                    temperature=0.85,
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
