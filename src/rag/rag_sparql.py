import ollama
import rdflib
import re
import time

FICHIER_GRAPHE = "kg_artifacts/expanded.nt"
MODELE_LLM = "llama3.2"

def charger_graphe(chemin_fichier):
    start_time = time.time()
    print(f"[1/4] Début du chargement du fichier {chemin_fichier}...")
    g = rdflib.Graph()
    try:
        
        g.parse(chemin_fichier, format="nt") 
        end_time = time.time()
        print(f"[2/4] Graphe chargé avec succès en {end_time - start_time:.2f} secondes.")
        print(f"[INFO] Taille actuelle : {len(g)} triplets.")
    except Exception as e:
        print(f"[ERREUR] Impossible de lire le fichier : {e}")
    return g

def construire_resume_schema(graph, max_predicats=30, max_classes=20):
    q_preds = f"SELECT DISTINCT ?p WHERE {{ ?s ?p ?o . }} LIMIT {max_predicats}"
    predicats = [str(row.p) for row in graph.query(q_preds)]

    q_classes = f"SELECT DISTINCT ?cls WHERE {{ ?s a ?cls . }} LIMIT {max_classes}"
    classes = [str(row.cls) for row in graph.query(q_classes)]

    prefixes = (
        "PREFIX ont: <http://cinema-controversy.org/ontology.owl#>\n"
        "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
        "PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>"
    )

    lignes_preds = "\n".join(f"- {p}" for p in predicats)
    lignes_classes = "\n".join(f"- {c}" for c in classes)

    resume = f"{prefixes}\n# Predicats disponibles:\n{lignes_preds}\n# Classes disponibles:\n{lignes_classes}"
    return resume.strip()

def extraire_nom(question):
    
    match = re.search(r"avec\s+(.*?)\s*\?", question)
    if match:
        return match.group(1).strip()
    return None

def extraire_sparql(texte: str) -> str:
    if not texte: return ""
    
    t = chr(96)
    balise = t + t + t
    motif = balise + r"(?:sparql)?\s*(.*?)" + balise
    match = re.search(motif, texte, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return texte.strip()

def requete_collaboration_fallback(nom_personne: str) -> str:
    nom_propre = nom_personne.lower()
    
    return f"""
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?collaborator_name (COUNT(DISTINCT ?film) AS ?nbFilms)
WHERE {{
  # 1. On trouve la cible (ex: Tarantino)
  ?target rdfs:label ?target_label .
  FILTER(CONTAINS(LCASE(STR(?target_label)), "{nom_propre}"))

  # 2. On récupère ses films via n'importe quelle relation contenant 'actedIn' ou 'directed'
  ?target ?p1 ?film .
  FILTER(CONTAINS(STR(?p1), "actedIn") || CONTAINS(STR(?p1), "directed"))

  # 3. On récupère les collaborateurs liés au même film
  ?collaborator ?p2 ?film .
  FILTER(CONTAINS(STR(?p2), "actedIn") || CONTAINS(STR(?p2), "directed"))
  FILTER(?collaborator != ?target)

  # 4. On récupère le nom lisible du collaborateur
  ?collaborator rdfs:label ?collaborator_name .
}}
GROUP BY ?collaborator_name
ORDER BY DESC(?nbFilms)
LIMIT 5
"""

def generer_sparql(question: str, schema_summary: str) -> str:
    t = chr(96)
    balise = t + t + t

    prompt = f"""
Tu es un expert SPARQL.

Règles STRICTES :
- Utilise UNIQUEMENT les prédicats du schéma
- Une collaboration = personnes liées à un même film
- Utilise ont:actedIn et ont:directed
- Ajoute toujours une ligne avec rdfs:label pour identifier la personne de la question.

Exemple :
Question: Qui a collaboré avec Harvey Weinstein ?
Requête:
SELECT ?collaborator (COUNT(?film) AS ?nbFilms)
WHERE {{
  ?target rdfs:label "Harvey Weinstein" .
  ?target ont:directed|ont:actedIn ?film .
  ?collaborator ont:directed|ont:actedIn ?film .
  FILTER(?collaborator != ?target)
}}
GROUP BY ?collaborator
ORDER BY DESC(?nbFilms)
LIMIT 5

RESUME DU SCHEMA:
{schema_summary}

QUESTION:
{question}

Renvoie SEULEMENT la requete SPARQL entre {balise}sparql et {balise}.
"""
    try:
        response = ollama.chat(model=MODELE_LLM, messages=[{'role': 'user', 'content': prompt}])
        contenu = response['message']['content']
        code_sparql = extraire_sparql(contenu)
        
        # On s'assure de renvoyer une chaîne, jamais None
        return f"PREFIX ont: <http://cinema-controversy.org/ontology.owl#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n{code_sparql}"
    except Exception as e:
        print(f"[ERREUR LLM] : {e}")
        return "" # Renvoie une chaîne vide au lieu de None


def nettoyer_requete(requete: str) -> str:
    if not requete:
        return ""
    return requete.strip()

def interroger_graphe(graph, question, schema_summary):
    nom_cible = extraire_nom(question).lower()
    print(f"[INFO] Recherche Turbo-Python pour : {nom_cible}")
    start = time.time()

    # 1. Trouver l'URI de la personne cible 
    target_uri = None
    for s, p, o in graph.triples((None, rdflib.RDFS.label, None)):
        if nom_cible in str(o).lower():
            target_uri = s
            break
    
    if not target_uri:
        print("Cible non trouvée dans le graphe.")
        return None

    # 2. Trouver ses films
    films = set()
    for s, p, o in graph.triples((target_uri, None, None)):
        # On élargit les mots-clés pour capter Weinstein
        if any(mot in str(p).lower() for mot in ["actedin", "directed", "produced", "producer"]):
            films.add(o)

    # 3. Compter les co-acteurs/réalisateurs/producteurs dans ces films
    compteur_collab = {}
    for film in films:
        for s, p, o in graph.triples((None, None, film)):
            if s != target_uri and any(mot in str(p).lower() for mot in ["actedin", "directed", "produced", "producer"]):
                compteur_collab[s] = compteur_collab.get(s, 0) + 1

    # 4. Prendre les 5 meilleurs et chercher leurs noms
    top_collabs = sorted(compteur_collab.items(), key=lambda x: x[1], reverse=True)[:5]
    
    contexte_brut = ""
    for uri, nb in top_collabs:
        name = uri.split('/')[-1]
        for s, p, o in graph.triples((uri, rdflib.RDFS.label, None)):
            name = str(o)
            break
        print(f"[TROUVÉ] {name} ({nb} collaborations)")
        
        contexte_brut += f"- {name} a collaboré sur {nb} projets avec {nom_cible.title()}.\n"

    print(f"[OK] Terminé en {time.time() - start:.2f}s")
    return contexte_brut

def generer_reponse_finale(question, contexte_brut):
    if not contexte_brut or not contexte_brut.strip() or "None" in contexte_brut:
        return "Aucune collaboration fiable trouvée dans le graphe."

    prompt = f"""
Tu es un assistant factuel.

Règles :
- Réponds UNIQUEMENT en utilisant les données fournies ci-dessous.
- Pour déterminer "qui a le plus collaboré", base-toi EXCLUSIVEMENT sur le nombre de projets/collaborations indiqué. Celui qui a le plus grand nombre est la bonne réponse.
- Rédige une réponse naturelle et directe. 
- N'invente aucune autre information.

DONNEES:
{contexte_brut}

QUESTION:
{question}
"""

    response = ollama.chat(
        model=MODELE_LLM,
        messages=[{'role': 'user', 'content': prompt}]
    )

    return response['message']['content']

if __name__ == "__main__":
    print("\n--- DÉMARRAGE DU PIPELINE RAG ---")
    
    # 1. Chargement
    graphe = charger_graphe(FICHIER_GRAPHE)
    
    # 2. Résumé
    print("[3/4] Extraction du schéma de l'ontologie...")
    resume = construire_resume_schema(graphe)
    print("[OK] Schéma extrait.")
    
    # 3. Question
    question_test = "Qui a le plus collaboré avec Harvey Weinstein ?"
    print(f"\n========================================")
    print(f"QUESTION UTILISATEUR : {question_test}")
    print(f"========================================\n")
    
    # 4. LLM
    print("[4/4] Appel à Ollama (Génération SPARQL)...")
    contexte = interroger_graphe(graphe, question_test, resume)
    
    # 5. Réponse
    if contexte:
        print("\n[INFO] Données trouvées dans le graphe. Synthèse finale...")
        reponse = generer_reponse_finale(question_test, contexte)
        print("\n========================================")
        print(f"RÉPONSE FINALE (RAG) :\n{reponse}")
        print("========================================\n")