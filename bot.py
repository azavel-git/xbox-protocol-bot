import os
import sys
import random
import time
import re
from atproto import Client, models
from google import genai
from google.genai import types

print("🚀 Démarrage du bot The Xbox Protocol sur GitHub Actions...")

# Détection du mode de lancement
est_manuel = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"

if est_manuel:
    print("⚡ Déclenchement manuel détecté : on passe direct à la suite sans attendre !")
else:
    delai = random.randint(1, 30)
    print(f"⏳ Lancement programmé : pause aléatoire de {delai} minutes...")
    time.sleep(delai * 60)

print("🔋 Connexion aux services...")

# 1. RÉCUPÉRATION DES SECRETS DE SÉCURITÉ
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.environ.get("BLUESKY_PASSWORD")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not all([BLUESKY_HANDLE, BLUESKY_PASSWORD, GEMINI_API_KEY]):
    print("❌ Erreur : Clés de sécurité manquantes dans les configurations GitHub.")
    sys.exit(1)

try:
    # 2. CONNEXION AUX SERVICES
    print("🔑 Connexion à Bluesky et Gemini...")
    bsky_client = Client()
    bsky_client.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
    ai_client = genai.Client(api_key=GEMINI_API_KEY)

    # 3. RÉCUPÉRATION DU DERNIER POST POUR ÉVITER LA RÉPÉTITION
    print("🔍 Récupération du dernier post Bluesky...")
    last_post_text = ""
    try:
        feed = bsky_client.get_author_feed(actor=BLUESKY_HANDLE, limit=1)
        if feed and feed.feed:
            last_post_text = feed.feed[0].post.record.text
            print(f"📝 Dernier post en date : '{last_post_text}'")
    except Exception as e:
        print(f"⚠️ Impossible de lire le fil Bluesky : {e}")

    # 4. GÉNÉRATION DU TEXTE AVEC RECHERCHE EN DIRECT
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

    system_prompt = """Tu es The Xbox Protocol, un insider et analyste anglais chevronné du jeu vidéo, spécialisé dans l'écosystème Xbox. 
Ton objectif est de générer de l'engagement sur Bluesky avec un ton mesuré, modérément enthousiaste, analytique et nuancé. Reste objectif et réfléchi.

🚨 RÈGLES DE STRUCTURE ET DE VISIBILITÉ ABSOLUES : 
1. ACCROCHE (THE HOOK) : Commence obligatoirement ton post par un mot-clé court en MAJUSCULES suivi de deux points (ex: ANALYSIS:, THOUGHTS:, FOCUS:, TREND:) pour capter le regard.
2. MOTS-CLÉS PIVOTS : Intègre naturellement au moins un mot-clé majeur (Xbox, Game Pass, Microsoft, ou le nom exact d'un studio/jeu) pour les Custom Feeds.
3. TIMING INTERNATIONAL : Écris pour une audience globale (US/UK). Pas de "Good morning" ou "Tonight".
4. HASHTAG DE FIN STRICT : Ajoute exactement UN SEUL hashtag pertinent à la toute fin du post (ex: #Xbox, #GamePass). Écris-le collé, SANS ESPACE après le # (ex: #Xbox et JAMAIS # Xbox). Interdiction absolue d'en mettre plus d'un.
5. FOCUS UNIQUE : Rédige ton post sur UN SEUL et UNIQUE sujet précis. Pas de listes.

🚫 STYLE "IA MARKETING" BANNI :
- Pas de phrases clichés ("Big reveals expected", "Exciting times ahead", "Stay tuned").
- Pas de mise en forme Markdown (PAS de ** ni de *).
- Un seul émoji maximum dans tout le texte.
- Longueur : Entre 150 et 260 caractères maximum (hashtag et espaces compris).
- Langue : Anglais."""

    user_prompt = f"""[TON DERNIER POST À BANNIR]
"{last_post_text}"

[CONTRAINTE ÉDITORIALE IMPOSÉE PAR PYTHON]
Tu dois impérativement respecter cet angle et cette contrainte pour ce post :
{angle_du_jour}

[INSTRUCTIONS]
1. Utilise Google Search pour trouver des détails précis sur l'actualité Xbox (juin 2026) liés à l'angle imposé.
2. Rédige ton unique post Bluesky direct, nuancé, avec le hook en majuscules et l'unique hashtag attaché à la fin (ex: #Xbox)."""

    # 5. BOUCLE DE SÉCURITÉ ANTI-PANNE GEMINI
    print("🌐 Gemini scanne Google Search pour trouver les dernières news Xbox...")
    reponse_gemini = None
    for tentative in range(5):
        try:
            reponse_gemini = ai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    tools=[types.Tool(google_search=types.GoogleSearch())],
                    temperature=0.75,
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

    # SÉCURITÉ ANTI-CRASH BLUESKY (Limite stricte de 300 caractères)
    if len(texte_du_post) > 300:
        print(f"⚠️ Alerte : Le post généré était trop long ({len(texte_du_post)} caractères).")
        texte_du_post = texte_du_post[:297] + "..."
        
    print(f"\n--- 🤖 POST GÉNÉRÉ ---\n{texte_du_post}\n---------------------\n")

    # 🔥 CONFIGURATION DYNAMIQUE DES FACETS (Pour rendre le hashtag cliquable et bleu)
    facets = []
    for match in re.finditer(r'#\w+', texte_du_post):
        start_char, end_char = match.span()
        # Encodage en UTF-8 pour calculer les positions exactes en octets (exigé par Bluesky)
        start_byte = len(texte_du_post[:start_char].encode('utf-8'))
        end_byte = len(texte_du_post[:end_char].encode('utf-8'))
        tag_name = match.group()[1:]  # On extrait le mot sans le '#'
        
        facets.append(
            models.AppBskyRichtextFacet.Main(
                index=models.AppBskyRichtextFacet.ByteSlice(byte_start=start_byte, byte_end=end_byte),
                features=[models.AppBskyRichtextFacet.Tag(tag=tag_name)]
            )
        )

    # 6. ENVOI SUR BLUESKY WITH FACETS
    print("🦋 Publication sur Bluesky...")
    bsky_client.send_post(text=texte_du_post, facets=facets)
    print("✅ Post envoyé avec succès et hashtag activé !")

except Exception as global_error:
    print(f"❌ Une erreur critique est survenue durant l'exécution : {global_error}")
    sys.exit(1)
