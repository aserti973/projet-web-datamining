import pandas as pd
import requests
import urllib.parse
import time
import os
import re
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import OWL

INPUT_CSV = "data/extracted_knowledge.csv"
OUTPUT_TTL = "kg_artifacts/alignment.ttl"
OUTPUT_MAPPING = "kg_artifacts/mapping_table.csv"

EX = Namespace("http://cinema-controversy.org/entity/")
WD = Namespace("http://www.wikidata.org/entity/")

def clean_entity_name(name):
    """Nettoie le bruit (comme les références Wikipédia [12] ou la ponctuation)"""
    # Enlève les crochets et les chiffres à l'intérieur
    name = re.sub(r'\[\d+\]?', '', name)
    # Enlève la ponctuation parasite à la fin
    name = name.replace("'", "").replace(";", "").replace(".", "").strip()
    return name

def align_with_wikidata():
    print("Démarrage de l'alignement avec Wikidata...")
    
    g = Graph()
    g.bind("ex", EX)
    g.bind("wd", WD)
    g.bind("owl", OWL)
    
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"Erreur: {INPUT_CSV} introuvable.")
        return
        
    persons = df[df["Type"] == "PERSON"]["Entity"].unique()
    mapping_data = []
    
    WIKIDATA_API_URL = "https://www.wikidata.org/w/api.php"
    
    
    headers = {
        'User-Agent': 'CinemaControversyGraphBot/1.0 (Student Project; contact@example.com)'
    }
    
    for person in persons:
        clean_person = clean_entity_name(person)
        
        # Ignorer si le nom est trop court après nettoyage
        if len(clean_person) < 2:
            continue
            
        print(f"Recherche de '{clean_person}' sur Wikidata...")
        
        params = {
            "action": "wbsearchentities",
            "search": clean_person,
            "language": "en",
            "format": "json"
        }
        
        try:
            # Ajout du paramètre "headers"
            response = requests.get(WIKIDATA_API_URL, params=params, headers=headers).json()
            
            if response.get('search') and len(response['search']) > 0:
                best_match = response['search'][0]
                wd_id = best_match['id']
                
                # Création des URIs
                safe_name = urllib.parse.quote(clean_person.replace(" ", "_"))
                private_uri = EX[safe_name]
                wikidata_uri = WD[wd_id]
                
                # Ajout du lien dans le graphe
                g.add((private_uri, OWL.sameAs, wikidata_uri))
                
                mapping_data.append({
                    "Private Entity": f"ex:{safe_name}",
                    "External URI": f"wd:{wd_id}",
                    "Confidence": 0.95
                })
                print(f"  -> rouvé ! ex:{safe_name} = wd:{wd_id}")
            else:
                print(f"  -> Aucun résultat")
                
        except Exception as e:
            print(f"  -> Erreur API pour {clean_person}: {e}")
            
        time.sleep(0.1) 

    g.serialize(destination=OUTPUT_TTL, format="turtle")
    
    mapping_df = pd.DataFrame(mapping_data)
    mapping_df.to_csv(OUTPUT_MAPPING, index=False)
    
    print(f"\nAlignement terminé !")

if __name__ == "__main__":
    align_with_wikidata()