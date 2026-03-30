import pandas as pd
from SPARQLWrapper import SPARQLWrapper, JSON
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import time
import os

MAPPING_FILE = "kg_artifacts/mapping_table.csv"
OUTPUT_NT = "kg_artifacts/expanded.nt"

# Les Namespaces
EX = Namespace("http://cinema-controversy.org/entity/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

P_CAST_MEMBER = "wdt:P161"
P_DIRECTOR = "wdt:P57"
P_PRODUCER = "wdt:P162"

def expand_graph():
    print("Démarrage de l'expansion du graphe via SPARQL (Niveau 2: 2-Hop)...")
    
    try:
        df = pd.read_csv(MAPPING_FILE)
    except FileNotFoundError:
        print("Erreur: Lancez l'alignement d'abord.")
        return
        
    wd_ids = df['External URI'].str.replace('wd:', '').tolist()
    
    g = Graph()
    g.bind("ex", EX)
    g.bind("wd", WD)
    g.bind("wdt", WDT)
    
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)
    sparql.addCustomHttpHeader("User-Agent", "CinemaControversyGraphBot/2.0 (Student Project)")
    
    # ETAPE 1 : 1-Hop (Ce que vous venez de faire)
    print(f"\n--- ÉTAPE 1 : Extraction des films pour {len(wd_ids)} personnalités ---")
    films_found = set()
    
    batch_size = 10
    for i in range(0, len(wd_ids), batch_size):
        batch_ids = wd_ids[i:i+batch_size]
        values_clause = " ".join([f"wd:{wd_id}" for wd_id in batch_ids])
        
        query = f"""
        SELECT ?person ?personLabel ?film ?filmLabel ?roleType WHERE {{
          VALUES ?person {{ {values_clause} }}
          {{ ?film {P_CAST_MEMBER} ?person. BIND("actedIn" AS ?roleType) }}
          UNION
          {{ ?film {P_DIRECTOR} ?person. BIND("directed" AS ?roleType) }}
          UNION
          {{ ?film {P_PRODUCER} ?person. BIND("produced" AS ?roleType) }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        """
        sparql.setQuery(query)
        try:
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                person_uri = URIRef(result["person"]["value"])
                film_uri = URIRef(result["film"]["value"])
                
                # On sauvegarde l'ID du film pour l'étape 2
                film_id = result["film"]["value"].split('/')[-1]
                films_found.add(film_id)
                
                role_type = result["roleType"]["value"]
                relation = EX.actedIn if role_type == "actedIn" else (EX.directed if role_type == "directed" else EX.produced)
                
                g.add((person_uri, relation, film_uri))
                g.add((film_uri, RDF.type, EX.Film))
                g.add((film_uri, RDFS.label, Literal(result["filmLabel"]["value"])))
                g.add((person_uri, RDFS.label, Literal(result["personLabel"]["value"])))
        except Exception as e:
            print(f"Erreur Etape 1: {e}")
        time.sleep(1)

    print(f"=> {len(films_found)} films trouvés !")
    
    # ETAPE 2 : 2-Hop 
    films_list = list(films_found)
    batch_size_films = 60 #passage de 40 à 60 pour contourner les limites de l'API Wikidata 
    
    # On limite à 1500 films pour ne pas faire tourner le script pendant 2 heures
    # C'est largement suffisant pour dépasser les 50 000 triplets
    max_films = min(1500, len(films_list))
    films_to_query = films_list[:max_films]
    
    print(f"\n--- ÉTAPE 2 : Extraction du casting complet pour {len(films_to_query)} films ---")
    print("(Cela peut prendre 2 à 3 minutes...)")

    for i in range(0, len(films_to_query), batch_size_films):
        batch_films = films_to_query[i:i+batch_size_films]
        values_clause = " ".join([f"wd:{f_id}" for f_id in batch_films])
        
        print(f"  -> Aspiration casting des films {i} à {min(i+batch_size_films, len(films_to_query))}...")
        
        query2 = f"""
        SELECT ?film ?person ?personLabel ?roleType WHERE {{
          VALUES ?film {{ {values_clause} }}
          {{ ?film {P_CAST_MEMBER} ?person. BIND("actedIn" AS ?roleType) }}
          UNION
          {{ ?film {P_DIRECTOR} ?person. BIND("directed" AS ?roleType) }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        """
        sparql.setQuery(query2)
        try:
            results = sparql.query().convert()
            for result in results["results"]["bindings"]:
                film_uri = URIRef(result["film"]["value"])
                person_uri = URIRef(result["person"]["value"])
                role_type = result["roleType"]["value"]
                
                relation = EX.actedIn if role_type == "actedIn" else EX.directed
                
                g.add((person_uri, relation, film_uri))
                # On marque ces nouvelles personnes comme entités Person
                g.add((person_uri, RDF.type, EX.Person))
                g.add((person_uri, RDFS.label, Literal(result["personLabel"]["value"])))
        except Exception as e:
            print(f"Erreur Etape 2: {e}")
        time.sleep(1)

    triplets_count = len(g)
    entities_count = len(set(g.subjects()) | set(g.objects()))
    
    print("\n========== STATISTIQUES FINALES (2-HOP) ==========")
    print(f"Nombre de triplets : {triplets_count}")
    print(f"Nombre d'entités uniques : {entities_count}")
    print("==================================================")
    
    g.serialize(destination=OUTPUT_NT, format="nt", encoding="utf-8")
    print(f"\nGraphe géant sauvegardé dans : {OUTPUT_NT}")

if __name__ == "__main__":
    expand_graph()