import trafilatura
import json
import os

# 1. Nos URLs de départ (Seed URLs) sur la thématique des controverses au cinéma
SEED_URLS = [
    "https://en.wikipedia.org/wiki/Harvey_Weinstein_sexual_abuse_cases",
    "https://fr.wikipedia.org/wiki/Violences_sexuelles_et_sexistes_dans_le_cin%C3%A9ma_fran%C3%A7ais#:~:text=En%20novembre%202024%2C%20l'acteur,le%20tournage%20du%20film%20Bonhomme.",
    "https://en.wikipedia.org/wiki/Kevin_Spacey_sexual_misconduct_allegations",
    "https://en.wikipedia.org/wiki/Woody_Allen_sexual_abuse_allegation",
    "https://en.wikipedia.org/wiki/Me_Too_movement",
    "https://www.bbc.com/news/entertainment-arts-41940680"
]

OUTPUT_FILE = "data/crawler_output.jsonl"

def crawl_and_clean(urls):
    """Télécharge, nettoie et sauvegarde les textes de plus de 500 mots."""
    valid_pages = 0
    
    # On s'assure que le dossier data/ existe
    os.makedirs("data", exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for url in urls:
            print(f"Téléchargement de : {url}...")
            # Téléchargement de la page HTML
            downloaded = trafilatura.fetch_url(url)
            
            if downloaded:
                # Extraction du texte principal (nettoyage du HTML)
                text = trafilatura.extract(downloaded)
                
                if text:
                    word_count = len(text.split())
                    # Le TD demande de vérifier si la page est "utile" (> 500 mots)
                    if word_count > 500:
                        print(f"  ->  Succès : {word_count} mots extraits.")
                        
                        # Création de l'objet JSON
                        data = {
                            "url": url,
                            "text": text
                        }
                        # Sauvegarde au format JSONL
                        f.write(json.dumps(data, ensure_ascii=False) + '\n')
                        valid_pages += 1
                    else:
                        print(f"  ->  Rejeté : Page trop courte ({word_count} mots).")
            else:
                print(f"  ->  Erreur de téléchargement pour {url}")
                
    print(f"\nTerminé ! {valid_pages} pages sauvegardées dans {OUTPUT_FILE}")

if __name__ == "__main__":
    crawl_and_clean(SEED_URLS)