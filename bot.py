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
        "ANGLE IMPOSÉ : HARDWARE & ACCESSOIRES. Règle : Analyse de manière brute les fuites de la manette Elite Series 3 ou du pad Cloud. Est-ce un gadget gadget ou un vrai game-changer pour l'écosystème ? Interdiction absolue de mentionner un jeu, le Game Pass ou le Showcase.",
        "ANGLE IMPOSÉ : COMPÉTITION & RIVALITÉ. Règle : Rebondis sur un mouvement de PlayStation (comme leur récent State of Play, Wolverine, etc.) ou de Nintendo. Compare la hype brute des exclus Sony face à la stratégie de volume d'Xbox. Sois piquant sur ce qui manque cruellement à Xbox pour créer l'événement.",
        "ANGLE IMPOSÉ : NOSTALGIE & REVIVAL. Règle : Attaque l'actu des rumeurs de retour de franchises cultes (Banjo-Kazooie, licences OG Xbox). Est-ce une vraie bonne idée pour les 25 ans ou juste du fan-service désespéré ? Pas de langue de bois.",
        "ANGLE IMPOSÉ : ZOOM INDÉ GAME PASS. Règle : Focus unique sur une pépite indé récente de juin (comme Solarpunk ou Beastro). Explique pourquoi ce micro-jeu a plus d'âme ou de potentiel de gameplay que les AAA standard de l'industrie. Sois court et percutant.",
        "ANGLE IMPOSÉ : ATTENTE STUDIO. Règle : Prends un projet lointain d'un studio Xbox (ex: Clockwork Revolution, State of Decay 3). Pose la vraie question : pourquoi le développement est si long et qu'est-ce que le studio joue sur ce titre ? Risque de bide ou chef-d'œuvre ?",
        "ANGLE IMPOSÉ : NEWS XBOX GÉNÉRALE. Règle : Utilise Google Search pour choper la news générale Xbox de la semaine (juin 2026). Donne ton avis critique immédiat, sans filtre, comme si tu parlais à un autre passionné sur un forum. Pas de résumé neutre.",
        "ANGLE IMPOSÉ : DÉCLARATIONS DES DIRIGEANTS. Règle : Analyse la dernière déclaration publique d'Asha Sharma (CEO Xbox) ou de Matt Booty. Décode le jargon corporate pour révéler ce que ça cache vraiment pour l'avenir de la marque."
    ]
    angle_du_jour = random.choice(angles_de_redaction)

    system_prompt = """Tu es The Xbox Protocol, un insider et analyste anglais de l'industrie du jeu vidéo. Tu as une forte audience car tu refuses la langue de bois, le politiquement correct et le blabla marketing. 

Ton style est incisif, direct, cynique mais passionné. Tu écris des "hot takes" (des avis tranchés et stimulants) qui font réagir, débattre et partager. Tu ne résumes pas l'actualité : tu la bouscules.

🚨 RÈGLES DE STYLE ET D'ENGAGEMENT :
1. INTERDICTION DES TRUISMES : Ne dis jamais de banalités évidentes (ex: "Xbox a besoin de bons jeux", "Il faut contrer Sony", "L'avenir nous le dira"). Va droit au cœur du problème, de la contradiction ou de la hype.
2. ACCROCHE VARIABLE ET ORGANIQUE : Commence par une phrase d'attaque percutante. Pas de formule figée, pas de structure robotique répétitive d'un post à l'autre. Entre directement dans le vif du sujet.
3. TON SANS FILTRE : Utilise le vocabulaire des joueurs et des analystes (hype, shadowdrop, corporate spin, first-party fatigue, system-seller). Sois court, percutant, presque provocateur mais toujours intelligent.
4. HASHTAG DE FIN STRICT : Ajoute exactement UN SEUL hashtag pertinent à la toute fin du post (ex: #Xbox, #GamePass), collé, sans espace après le #.
5. PAS DE TEXTE IA CLICHÉ : Supprime les mots de liaison inutiles, les phrases de conclusion bateau ("Exciting times ahead", "Let's see what happens").

🚫 STRATÉGIE DE TAILLE (ANTI-TRONCATURE) :
- Longueur : Entre 120 et 210 caractères MAXIMUM (hashtag compris). Le post doit se lire d'un seul coup d'œil. Supprime tout le gras, ne garde que l'impact."""

    user_prompt = f"""[TON DERNIER POST À BANNIR (Ne reprends pas ce style ni ce sujet)]
"{last_post_text}"

[CONTRAINTE ÉDITORIALE IMPOSÉE]
Respecte impérativement cet angle pour ton analyse d'aujourd'hui :
{angle_du_jour}

[INSTRUCTIONS DE RÉDACTION]
1. Utilise Google Search pour trouver un détail croustillant ou une actu Xbox (juin 2026) liée à cet angle.
2. Rédige un post en anglais ultra-percutant, sans langue de bois, de maximum 210 caractères, se terminant par un unique hashtag."""

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
                    temperature=0.9,  # Augmentée pour plus d'audace et de punch dans le ton
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

    # SÉCURITÉ ANTI-CRASH BLUESKY
    if len(texte_du_post) > 300:
        print(f"⚠️ Alerte : Le post généré était trop long ({len(texte_du_post)} caractères).")
        texte_du_post = texte_du_post[:297] + "..."
        
    print(f"\n--- 🤖 POST GÉNÉRÉ ---\n{texte_du_post}\n---------------------\n")

    # 🔥 CONFIGURATION DYNAMIQUE DES FACETS
    facets = []
    for match in re.finditer(r'#\w+', texte_du_post):
        start_char, end_char = match.span()
        start_byte = len(texte_du_post[:start_char].encode('utf-8'))
        end_byte = len(texte_du_post[:end_char].encode('utf-8'))
        tag_name = match.group()[1:]
        
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

       