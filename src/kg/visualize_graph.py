import networkx as nx
import matplotlib.pyplot as plt
from rdflib import Graph, URIRef
import os
import matplotlib.colors as mcolors
import collections

INPUT_NT = "kg_artifacts/expanded.nt"
OUTPUT_PNG = "reports/social_network_filtered.png"

# On définit les URI des "Graines" de la controverse (les accusés initiaux)
SEED_URIS = {
    URIRef("http://www.wikidata.org/entity/Q531599"): "Harvey Weinstein",
    URIRef("http://www.wikidata.org/entity/Q51552"): "Roman Polanski",
    URIRef("http://www.wikidata.org/entity/Q25144"): "Kevin Spacey",
    URIRef("http://www.wikidata.org/entity/Q25089"): "Woody Allen"
}

RDFS_LABEL = URIRef("http://www.w3.org/2000/01/rdf-schema#label")

def clean_label(uri):
    return str(uri).split('/')[-1]

def build_filtered_network():
    print("Chargement du graphe géant (patience)...")
    g = Graph()
    g.parse(INPUT_NT, format="nt")
    
    # 1. Récupération des Vrais Noms (Labels) depuis le graphe
    print("Extraction des vrais noms...")
    qid_to_name = {}
    for s, p, o in g:
        if p == RDFS_LABEL:
            qid_to_name[clean_label(s)] = str(o).strip('"')
            
    # Ajout forcé des graines au cas où
    for uri, name in SEED_URIS.items():
        qid_to_name[clean_label(uri)] = name

    # 2. Cartographie : Film -> Personnes
    film_to_people = collections.defaultdict(set)
    for s, p, o in g:
        p_label = clean_label(p)
        if p_label in ["actedIn", "directed", "produced"]:
            film_to_people[str(o)].add(str(s))
            
    # 3. Construction du Réseau Social (Personne -> Personne)
    print("Construction du Réseau Social...")
    G_social = nx.Graph() 
    
    for film, people in film_to_people.items():
        people_list = list(people)
        for i in range(len(people_list)):
            for j in range(i + 1, len(people_list)):
                G_social.add_edge(clean_label(people_list[i]), clean_label(people_list[j]))

    # 4. Extraction du Sous-ensemble autour des graines
    seed_qids = {clean_label(uri) for uri in SEED_URIS.keys()}
    present_seeds = seed_qids.intersection(set(G_social.nodes()))
    
    people_linked_to_seeds = set()
    for seed in present_seeds:
        people_linked_to_seeds.add(seed)
        people_linked_to_seeds.update(G_social.neighbors(seed))

    G_sub = G_social.subgraph(people_linked_to_seeds).copy()
    
    
    print(f"Avant filtrage : {G_sub.number_of_nodes()} personnes.")
    
    # On supprime les personnes qui ont strictement moins de 2 connexions 
    
    nodes_to_remove = [node for node, degree in G_sub.degree() if degree < 2]
    G_sub.remove_nodes_from(nodes_to_remove)
    
    print(f"Après filtrage (Degré >= 2) : {G_sub.number_of_nodes()} personnes restantes.")

    
    # On trie les nœuds par leur nombre de connexions
    sorted_by_degree = sorted(G_sub.degree(), key=lambda x: x[1], reverse=True)
    # On prend le Top 20
    top_20_nodes = {node for node, degree in sorted_by_degree[:20]}

    
    degrees = dict(G_sub.degree())
    node_colors = []
    node_sizes = []
    labels = {}
    
    cmap = plt.cm.plasma
    all_degrees = list(degrees.values())
    norm = mcolors.Normalize(vmin=min(all_degrees), vmax=max(all_degrees))

    for node in G_sub.nodes():
        if node in present_seeds:
            # Graines initiales (Rouge foncé)
            node_colors.append('#CC0000')
            node_sizes.append(3000)
            labels[node] = qid_to_name.get(node, node)
        elif node in top_20_nodes:
            # Top Collaborateurs (Orange / Jaune selon le colormap)
            node_colors.append(cmap(norm(degrees[node])))
            node_sizes.append(2000)
            labels[node] = qid_to_name.get(node, node) # On affiche le vrai nom !
        else:
            # Reste du réseau (plus petit, pas de nom)
            node_colors.append(cmap(norm(degrees[node])))
            node_sizes.append(500)
            labels[node] = "" 

   
    plt.figure(figsize=(24, 20))
    pos = nx.spring_layout(G_sub, k=0.6, iterations=100, seed=42) 
    
    nx.draw_networkx_nodes(G_sub, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9, edgecolors='white')
    nx.draw_networkx_edges(G_sub, pos, width=1.0, alpha=0.3, edge_color='gray')
    
    
    for node, (x, y) in pos.items():
        if labels.get(node):
            plt.text(x, y, labels[node], fontsize=11, fontweight='bold', ha='center', va='center', 
                     bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=1))
    
    plt.title("Réseau Social Filtré (Degré >= 2) - Focus sur les Top 20 Collaborateurs", fontsize=16)
    plt.axis('off')
    
    os.makedirs("reports", exist_ok=True)
    plt.savefig(OUTPUT_PNG, bbox_inches='tight', dpi=300) # dpi=300 pour une haute qualité
    print(f"\nVisualisation finale sauvegardée dans {OUTPUT_PNG}")

if __name__ == "__main__":
    build_filtered_network()