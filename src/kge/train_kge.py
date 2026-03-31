import os
import pykeen
from pykeen.pipeline import pipeline
import pandas as pd

DATA_DIR = "data/"
RESULTS_DIR = "reports/"

def train_with_early_stopping():
    print("--- ENTRAÎNEMENT KGE OPTIMISÉ (AVEC EARLY STOPPING) ---")
    
    train_path = os.path.join(DATA_DIR, "train.txt")
    valid_path = os.path.join(DATA_DIR, "valid.txt")
    test_path  = os.path.join(DATA_DIR, "test.txt")
    
    # On autorise un grand nombre d'époques, l'Early Stopper coupera avant si besoin
    training_kwargs = dict(
        num_epochs=150,  
        batch_size=256
    )
    
    # --- LA MAGIE EST ICI : Configuration de l'analyse de surapprentissage ---
    stopper_kwargs = dict(
        frequency=5,          # L'IA s'évalue toutes les 5 époques
        patience=3,           # Elle tolère 3 évaluations sans amélioration avant de couper
        relative_delta=0.005  # L'amélioration doit être d'au moins 0.5% pour être valide
    )

    results_list = []
    models = ['TransE', 'ComplEx']

    for model_name in models:
        print(f"\n Lancement de l'entraînement pour {model_name}...")
        print("L'IA s'arrêtera automatiquement dès qu'elle détectera un surapprentissage.")
        
        result = pipeline(
            training=train_path,
            testing=test_path,
            validation=valid_path,
            model=model_name,
            model_kwargs=dict(embedding_dim=50),
            training_kwargs=training_kwargs,
            stopper='early',               # Activation de l'Early Stopping
            stopper_kwargs=stopper_kwargs, # Paramètres de l'analyse
            device='cpu',
            random_seed=42,
        )

        mrr = result.get_metric('mrr')
        h1  = result.get_metric('hits@1')
        h10 = result.get_metric('hits@10')

        print(f"{model_name} terminé ! MRR: {mrr:.4f} | Hits@10: {h10:.4f}")

        results_list.append({
            'Model': model_name,
            'MRR': round(mrr, 4),
            'Hits@1': round(h1, 4),
            'Hits@10': round(h10, 4)
        })

    # --- AFFICHAGE ET SAUVEGARDE ---
    print("\n TABLEAU COMPARATIF FINAL (OPTIMISÉ) :")
    df_results = pd.DataFrame(results_list)
    print(df_results.to_string(index=False))
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    # On sauvegarde sous un nouveau nom pour garder la trace de votre amélioration
    df_results.to_csv(os.path.join(RESULTS_DIR, "kge_metrics_optimized.csv"), index=False)
    print(f"\nRésultats optimisés sauvegardés dans {RESULTS_DIR}kge_metrics_optimized.csv")

if __name__ == "__main__":
    train_with_early_stopping()