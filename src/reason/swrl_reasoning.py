from owlready2 import *
import os

# Création du dossier pour sauvegarder l'ontologie finale
os.makedirs("kg_artifacts", exist_ok=True)

def run_cinema_reasoning():
    print("--- RAISONNEMENT SUR VOTRE KB CINEMA ---")
    
    onto = get_ontology("http://cinema-controversy.org/ontology.owl")
    
    with onto:
        # Définition des Classes
        class Person(Thing): pass
        class Film(Thing): pass
        
        # Définition des Relations (Propriétés)
        class actedIn(ObjectProperty):
            domain    = [Person]
            range     = [Film]
            
        class directed(ObjectProperty):
            domain    = [Person]
            range     = [Film]
            
        class workedWith(ObjectProperty):
            domain    = [Person]
            range     = [Person]

        #Ajout de quelques données d'exemple 
        quent = Person("Quentin_Tarantino")
        uma = Person("Uma_Thurman")
        pulp = Film("Pulp_Fiction")
        
        # Uma a joué dans Pulp Fiction, Quentin a réalisé Pulp Fiction
        uma.actedIn.append(pulp)
        quent.directed.append(pulp)

        print(f"Avant raisonnement : Uma Thurman a-t-elle travaillé avec Tarantino ? -> {quent in uma.workedWith}")

        
        rule = Imp()
        rule.set_as_rule("Person(?p1), actedIn(?p1, ?f), Person(?p2), directed(?p2, ?f) -> workedWith(?p1, ?p2)")
        
    
    print(" Lancement du moteur de raisonnement Pellet...")
    sync_reasoner_pellet(infer_property_values=True)
    
    print(f"Après raisonnement : Uma Thurman a-t-elle travaillé avec Tarantino ? -> {quent in uma.workedWith}")
    
    # Sauvegarde de l'ontologiie
    onto.save(file="kg_artifacts/ontology.owl", format="rdfxml")
    print("Ontologie et règles sauvegardées dans kg_artifacts/ontology.owl")


if __name__ == "__main__":
    run_cinema_reasoning()
    