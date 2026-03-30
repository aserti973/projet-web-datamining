import pandas as pd
from rdflib import Graph
import os

INPUT_NT = "kg_artifacts/expanded.nt"
DATA_DIR = "data/"

def prepare_data():
    print("Chargement et nettoyage du graphe (cela peut prendre une minute avec 50k triplets)...")
    g = Graph()
    g.parse(INPUT_NT, format="nt")
    
    # Extraction des triplets en liste simple (Sujet, Prédicat, Objet)
    triplets = []
    for s, p, o in g:
        triplets.append([str(s), str(p), str(o)])
    
    # Transformation en DataFrame Pandas pour un nettoyage facile
    df = pd.DataFrame(triplets, columns=['s', 'p', 'o'])
    
    # Suppression des doublons (exigence stricte du TD pour l'IA)
    df = df.drop_duplicates()
    
    # Mélange aléatoire des données (Shuffle)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Découpage des données : 80% pour l'entraînement, 10% validation, 10% test
    n = len(df)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    
    train = df.iloc[:train_end]
    valid = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    
    # Création du dossier data/ s'il n'existe pas
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Sauvegarde au format .txt (séparé par des tabulations \t)
    train.to_csv(os.path.join(DATA_DIR, "train.txt"), sep='\t', header=False, index=False)
    valid.to_csv(os.path.join(DATA_DIR, "valid.txt"), sep='\t', header=False, index=False)
    test.to_csv(os.path.join(DATA_DIR, "test.txt"), sep='\t', header=False, index=False)
    
    print(f"\n✅ Préparation terminée ! {len(df)} triplets uniques ont été conservés.")
    print(f"Fichiers créés dans {DATA_DIR} : train.txt, valid.txt, test.txt")

if __name__ == "__main__":
    prepare_data()