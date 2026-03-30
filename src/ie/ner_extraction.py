import json
import spacy
import pandas as pd
import os

INPUT_FILE = "data/crawler_output.jsonl"
OUTPUT_FILE = "data/extracted_knowledge.csv"

def extract_entities():
    print("Chargement du modèle d'Intelligence Artificielle")
    
    nlp = spacy.load("en_core_web_trf")
    
    entities_list = []
    
    print("Analyse des textes en cours...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            url = data['url']
            text = data['text']
            
            print(f"  -> Extraction sur : {url}")
            
            # Pour éviter de surcharger la mémoire on analyse les 4000 premiers caractères de chaque page
            
            doc = nlp(text[:4000])
            
            
            target_labels = ["PERSON", "ORG", "GPE", "DATE"]
            
            for ent in doc.ents:
                if ent.label_ in target_labels:
                    # Nettoyage de base (enlever les retours à la ligne, etc.)
                    clean_text = ent.text.replace('\n', ' ').strip()
                    if len(clean_text) > 2: # Ignorer les bruits trop courts
                        entities_list.append({
                            "Entity": clean_text,
                            "Type": ent.label_,
                            "Source_URL": url
                        })
                        
    # Création d'un tableau de données (DataFrame) avec Pandas
    df = pd.DataFrame(entities_list)
    
    # Nettoyage : suppression des doublons exacts
    df = df.drop_duplicates()
    
    # Sauvegarde au format CSV 
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"\nTerminé ! {len(df)} entités uniques ont été extraites et sauvegardées dans {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_entities()