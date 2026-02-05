"""
Script de peuplement de la base de données avec de vrais datasets actuariels.
Ces datasets sont des références vers des sources externes (Kaggle, CAS, UCI, etc.)
Aucune donnée n'est stockée - uniquement les métadonnées et liens.
"""

import os
import sys
from datetime import datetime, timezone

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis dans .env")
    sys.exit(1)

# Client Supabase avec service role (bypass RLS)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ============================================
# Vrais datasets actuariels publics
# ============================================

REAL_DATASETS = [
    # ========== KAGGLE DATASETS ==========
    {
        "name": "French Motor Third-Party Liability Claims (freMTPL2freq)",
        "description": "Dataset classique de l'assurance automobile française. Contient 678 013 polices avec les caractéristiques du véhicule, du conducteur et l'historique des sinistres. Idéal pour la modélisation de la fréquence des sinistres avec GLM Poisson.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/floser/french-motor-claims-datasets-fremtpl2freq",
        "tags": ["iard", "glm", "pricing"],
        "row_count": 678013,
        "column_count": 12,
        "file_size_mb": 45.2,
        "data_dictionary_url": "https://www.openml.org/search?type=data&sort=runs&id=41214&status=active",
        "modeling_types": ["regression", "classification"],
        "pivot_variables": ["exposure", "claim_amount", "policy_id"],
        "best_fit_models": ["glm", "xgboost", "lightgbm"],
    },
    {
        "name": "French Motor Third-Party Liability Severity (freMTPL2sev)",
        "description": "Dataset complémentaire au freMTPL2freq pour la modélisation du coût des sinistres. Contient les montants individuels des sinistres. Utilisé avec GLM Gamma ou Tweedie pour le pricing.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/floser/french-motor-claims-datasets-fremtpl2sev",
        "tags": ["iard", "glm", "pricing"],
        "row_count": 26639,
        "column_count": 2,
        "file_size_mb": 0.8,
        "data_dictionary_url": "https://www.openml.org/search?type=data&sort=runs&id=41215&status=active",
        "modeling_types": ["regression"],
        "pivot_variables": ["claim_amount", "claim_id"],
        "best_fit_models": ["glm", "xgboost", "lightgbm"],
    },
    {
        "name": "Health Insurance Cross Sell Prediction",
        "description": "Dataset pour prédire si un client d'assurance santé serait intéressé par une assurance véhicule. 381 109 clients avec caractéristiques démographiques et historique d'assurance. Excellent pour le cross-selling en assurance.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/anmolkumar/health-insurance-cross-sell-prediction",
        "tags": ["sante", "machine_learning"],
        "row_count": 381109,
        "column_count": 12,
        "file_size_mb": 25.3,
        "data_dictionary_url": "https://www.kaggle.com/datasets/anmolkumar/health-insurance-cross-sell-prediction",
        "modeling_types": ["classification"],
        "pivot_variables": ["policy_id"],
        "best_fit_models": ["xgboost", "lightgbm", "random_forest", "catboost"],
    },
    {
        "name": "Insurance Fraud Detection",
        "description": "Dataset de détection de fraude en assurance automobile. Contient des sinistres avec indicateur de fraude. Idéal pour développer des modèles de scoring anti-fraude.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/shivamb/vehicle-claim-fraud-detection",
        "tags": ["iard", "fraude", "machine_learning"],
        "row_count": 15420,
        "column_count": 33,
        "file_size_mb": 3.2,
        "data_dictionary_url": "https://www.kaggle.com/datasets/shivamb/vehicle-claim-fraud-detection",
        "modeling_types": ["classification"],
        "pivot_variables": ["claim_id", "claim_amount"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm", "neural_network"],
    },
    {
        "name": "Medical Cost Personal Dataset",
        "description": "Prédiction des coûts médicaux individuels basée sur l'âge, le sexe, l'IMC, le tabagisme et la région. Dataset simple mais très utilisé pour l'introduction au pricing santé.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/mirichoi0218/insurance",
        "tags": ["sante", "glm", "pricing"],
        "row_count": 1338,
        "column_count": 7,
        "file_size_mb": 0.05,
        "data_dictionary_url": "https://www.kaggle.com/datasets/mirichoi0218/insurance",
        "modeling_types": ["regression"],
        "pivot_variables": ["claim_amount"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
    },
    {
        "name": "Porto Seguro Safe Driver Prediction",
        "description": "Competition Kaggle de Porto Seguro (assureur brésilien). Prédiction de la probabilité qu'un conducteur soumette une réclamation. Dataset anonymisé avec variables catégorielles et continues.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/competitions/porto-seguro-safe-driver-prediction",
        "tags": ["iard", "machine_learning", "pricing"],
        "row_count": 595212,
        "column_count": 59,
        "file_size_mb": 150.0,
        "data_dictionary_url": "https://www.kaggle.com/competitions/porto-seguro-safe-driver-prediction/data",
        "modeling_types": ["classification"],
        "pivot_variables": ["policy_id"],
        "best_fit_models": ["xgboost", "lightgbm", "catboost", "neural_network"],
    },
    {
        "name": "Allstate Claims Severity",
        "description": "Competition Kaggle d'Allstate. Prédiction de la sévérité des sinistres (coût). Variables anonymisées catégorielles et continues. Dataset de référence pour le pricing severity.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/competitions/allstate-claims-severity",
        "tags": ["iard", "machine_learning", "pricing"],
        "row_count": 188318,
        "column_count": 132,
        "file_size_mb": 95.0,
        "data_dictionary_url": "https://www.kaggle.com/competitions/allstate-claims-severity/data",
        "modeling_types": ["regression"],
        "pivot_variables": ["claim_id", "claim_amount"],
        "best_fit_models": ["xgboost", "lightgbm", "catboost", "neural_network"],
    },
    {
        "name": "Life Insurance Assessment (Prudential)",
        "description": "Competition Kaggle de Prudential. Classification du niveau de risque pour l'assurance vie (8 classes). Variables médicales et démographiques anonymisées.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/competitions/prudential-life-insurance-assessment",
        "tags": ["vie", "machine_learning"],
        "row_count": 59381,
        "column_count": 128,
        "file_size_mb": 35.0,
        "data_dictionary_url": "https://www.kaggle.com/competitions/prudential-life-insurance-assessment/data",
        "modeling_types": ["classification"],
        "pivot_variables": ["policy_id"],
        "best_fit_models": ["xgboost", "lightgbm", "random_forest", "catboost"],
    },

    # ========== CAS (Casualty Actuarial Society) ==========
    {
        "name": "CAS Loss Reserving Database - Commercial Auto",
        "description": "Triangles de sinistres de la CAS pour l'assurance automobile commerciale. Données historiques de 1988-1997. Référence pour les méthodes de provisionnement (Chain-Ladder, Mack, BF).",
        "source": "other",
        "source_url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
        "tags": ["iard", "reserving"],
        "row_count": 200,
        "column_count": 15,
        "file_size_mb": 0.5,
        "data_dictionary_url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "best_fit_models": ["chain_ladder", "mack", "bornhuetter_ferguson"],
    },
    {
        "name": "CAS Loss Reserving Database - Workers Compensation",
        "description": "Triangles de sinistres Workers Compensation de la CAS. Idéal pour les études de développement long-tail et la comparaison des méthodes stochastiques de réserves.",
        "source": "other",
        "source_url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
        "tags": ["iard", "reserving"],
        "row_count": 200,
        "column_count": 15,
        "file_size_mb": 0.5,
        "data_dictionary_url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "best_fit_models": ["chain_ladder", "mack", "bornhuetter_ferguson"],
    },
    {
        "name": "CAS Loss Reserving Database - Medical Malpractice",
        "description": "Triangles de sinistres responsabilité médicale de la CAS. Branche à développement très long. Parfait pour étudier les incertitudes de provisionnement.",
        "source": "other",
        "source_url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
        "tags": ["sante", "reserving"],
        "row_count": 200,
        "column_count": 15,
        "file_size_mb": 0.5,
        "data_dictionary_url": "https://www.casact.org/publications-research/research/research-resources/loss-reserving-data-pulled-naic-schedule-p",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "best_fit_models": ["chain_ladder", "mack", "bornhuetter_ferguson"],
    },

    # ========== UCI MACHINE LEARNING REPOSITORY ==========
    {
        "name": "Statlog German Credit Data",
        "description": "Dataset classique de scoring crédit. 1000 demandeurs avec 20 attributs. Très utilisé en formation pour les modèles de classification binaire et l'interprétabilité.",
        "source": "other",
        "source_url": "https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
        "tags": ["machine_learning"],
        "row_count": 1000,
        "column_count": 21,
        "file_size_mb": 0.1,
        "data_dictionary_url": "https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
        "modeling_types": ["classification"],
        "pivot_variables": [],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
    },

    # ========== OPENDATA / INSEE ==========
    {
        "name": "INSEE - Données démographiques communales 2023",
        "description": "Statistiques démographiques par commune française. Population, âge moyen, répartition H/F. Utile pour la tarification géographique et les études de portefeuille.",
        "source": "insee",
        "source_url": "https://www.insee.fr/fr/statistiques/6683035",
        "tags": ["sante", "pricing"],
        "row_count": 35000,
        "column_count": 25,
        "file_size_mb": 8.0,
        "data_dictionary_url": "https://www.insee.fr/fr/statistiques/6683035",
        "modeling_types": ["classification", "clustering"],
        "pivot_variables": [],
        "best_fit_models": ["glm", "random_forest"],
    },
    {
        "name": "Data.gouv.fr - Accidents corporels de la circulation",
        "description": "Base de données des accidents corporels de la circulation routière en France. Détails sur les circonstances, véhicules et usagers impliqués. Excellent pour l'analyse des risques routiers.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2022/",
        "tags": ["iard", "machine_learning"],
        "row_count": 1500000,
        "column_count": 50,
        "file_size_mb": 200.0,
        "data_dictionary_url": "https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2022/",
        "modeling_types": ["classification", "regression"],
        "pivot_variables": ["occurrence_date", "claim_id"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
    },
    {
        "name": "INSEE - Tables de mortalité françaises",
        "description": "Tables de mortalité officielles françaises par âge et sexe. Données essentielles pour le calcul des provisions mathématiques en assurance vie et la tarification.",
        "source": "insee",
        "source_url": "https://www.insee.fr/fr/statistiques/6683035",
        "tags": ["vie", "pricing"],
        "row_count": 220,
        "column_count": 10,
        "file_size_mb": 0.1,
        "data_dictionary_url": "https://www.insee.fr/fr/statistiques/6683035",
        "modeling_types": ["survival", "time_series"],
        "pivot_variables": [],
        "best_fit_models": ["cox", "kaplan_meier"],
    },

    # ========== ACTUARIAL DATASETS CLASSIQUES ==========
    {
        "name": "Swedish Motor Insurance (LGPIF)",
        "description": "Dataset historique suédois de tarification automobile. Contient les zones géographiques, classes de véhicule et sinistralité. Référence pédagogique pour les GLM.",
        "source": "other",
        "source_url": "https://www.openml.org/search?type=data&id=574",
        "tags": ["iard", "glm", "pricing"],
        "row_count": 2182,
        "column_count": 7,
        "file_size_mb": 0.1,
        "data_dictionary_url": "https://www.openml.org/search?type=data&id=574",
        "modeling_types": ["regression"],
        "pivot_variables": ["exposure", "claim_amount"],
        "best_fit_models": ["glm"],
    },
    {
        "name": "Motorcycle Insurance Claims",
        "description": "Dataset de sinistres moto avec exposition et montants. Petit dataset pédagogique parfait pour l'introduction aux GLM Poisson et Gamma.",
        "source": "other",
        "source_url": "https://www.statsmodels.org/stable/datasets/generated/fair.html",
        "tags": ["iard", "glm", "pricing"],
        "row_count": 64,
        "column_count": 6,
        "file_size_mb": 0.01,
        "data_dictionary_url": "https://www.statsmodels.org/stable/datasets/generated/fair.html",
        "modeling_types": ["regression"],
        "pivot_variables": ["exposure", "claim_amount"],
        "best_fit_models": ["glm"],
    },
    {
        "name": "Wisconsin Breast Cancer Dataset",
        "description": "Classification de tumeurs malignes/bénignes. Dataset médical classique utilisé en actuariat santé pour démontrer les modèles de classification binaire.",
        "source": "other",
        "source_url": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        "tags": ["sante", "machine_learning"],
        "row_count": 569,
        "column_count": 32,
        "file_size_mb": 0.1,
        "data_dictionary_url": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        "modeling_types": ["classification"],
        "pivot_variables": [],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
    },
    {
        "name": "Telco Customer Churn",
        "description": "Prédiction du churn (résiliation) client. Applicable à l'assurance pour la rétention de portefeuille et l'analyse de la fidélité client.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/blastchar/telco-customer-churn",
        "tags": ["machine_learning"],
        "row_count": 7043,
        "column_count": 21,
        "file_size_mb": 0.5,
        "data_dictionary_url": "https://www.kaggle.com/datasets/blastchar/telco-customer-churn",
        "modeling_types": ["classification", "survival"],
        "pivot_variables": ["policy_id"],
        "best_fit_models": ["xgboost", "random_forest", "cox", "kaplan_meier"],
    },

    # ========== SURVIVAL / LIFE INSURANCE ==========
    {
        "name": "ROSSI Recidivism Dataset",
        "description": "Dataset de survie classique pour l'analyse du temps jusqu'à la récidive. Utilisé pour enseigner les modèles de Cox et Kaplan-Meier.",
        "source": "other",
        "source_url": "https://vincentarelbundock.github.io/Rdatasets/doc/carData/Rossi.html",
        "tags": ["vie", "machine_learning"],
        "row_count": 432,
        "column_count": 9,
        "file_size_mb": 0.02,
        "data_dictionary_url": "https://vincentarelbundock.github.io/Rdatasets/doc/carData/Rossi.html",
        "modeling_types": ["survival"],
        "pivot_variables": [],
        "best_fit_models": ["cox", "kaplan_meier"],
    },
    {
        "name": "Heart Failure Survival Dataset",
        "description": "Prédiction de la mortalité par insuffisance cardiaque. 299 patients avec variables cliniques. Parfait pour l'analyse de survie en santé.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/andrewmvd/heart-failure-clinical-data",
        "tags": ["sante", "machine_learning"],
        "row_count": 299,
        "column_count": 13,
        "file_size_mb": 0.02,
        "data_dictionary_url": "https://www.kaggle.com/datasets/andrewmvd/heart-failure-clinical-data",
        "modeling_types": ["survival", "classification"],
        "pivot_variables": [],
        "best_fit_models": ["cox", "kaplan_meier", "xgboost", "random_forest"],
    },

    # ========== REINSURANCE / CATASTROPHES ==========
    {
        "name": "EMDAT Natural Disasters Database",
        "description": "Base internationale des catastrophes naturelles depuis 1900. Décès, dommages économiques par événement. Essentiel pour la modélisation Cat et la réassurance.",
        "source": "other",
        "source_url": "https://www.emdat.be/",
        "tags": ["iard", "machine_learning"],
        "row_count": 25000,
        "column_count": 45,
        "file_size_mb": 15.0,
        "data_dictionary_url": "https://www.emdat.be/classification",
        "modeling_types": ["regression", "time_series"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "best_fit_models": ["glm", "xgboost"],
    },
]


def clear_existing_datasets():
    """Supprime tous les datasets existants pour un fresh start."""
    print("🗑️  Suppression des datasets existants...")
    try:
        # D'abord supprimer les reviews, notebooks et benchmarks (dépendances)
        supabase.table("benchmarks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("notebooks").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("reviews").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        supabase.table("datasets").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print("✅ Datasets existants supprimés")
    except Exception as e:
        print(f"⚠️  Avertissement lors de la suppression: {e}")


def insert_datasets():
    """Insère les vrais datasets dans Supabase."""
    print(f"\n📦 Insertion de {len(REAL_DATASETS)} datasets actuariels...")

    success_count = 0
    error_count = 0

    for i, dataset in enumerate(REAL_DATASETS, 1):
        try:
            # Préparer les données
            data = {
                "name": dataset["name"],
                "description": dataset["description"],
                "source": dataset["source"],
                "source_url": dataset["source_url"],
                "tags": dataset["tags"],
                "row_count": dataset.get("row_count"),
                "column_count": dataset.get("column_count"),
                "file_size_mb": dataset.get("file_size_mb"),
                "data_dictionary_url": dataset.get("data_dictionary_url"),
                "modeling_types": dataset.get("modeling_types", []),
                "pivot_variables": dataset.get("pivot_variables", []),
                "best_fit_models": dataset.get("best_fit_models", []),
                "created_by": "system",  # Datasets système
            }

            # Insérer dans Supabase
            result = supabase.table("datasets").insert(data).execute()

            if result.data:
                success_count += 1
                print(f"  ✅ [{i}/{len(REAL_DATASETS)}] {dataset['name'][:50]}...")
            else:
                error_count += 1
                print(f"  ❌ [{i}/{len(REAL_DATASETS)}] {dataset['name'][:50]} - Pas de données retournées")

        except Exception as e:
            error_count += 1
            print(f"  ❌ [{i}/{len(REAL_DATASETS)}] {dataset['name'][:50]} - Erreur: {e}")

    return success_count, error_count


def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("🚀 StochastiQdata - Peuplement avec vrais datasets actuariels")
    print("=" * 60)
    print(f"\n📊 {len(REAL_DATASETS)} datasets à insérer")
    print("📍 Sources: Kaggle, CAS, UCI, INSEE, OpenData, autres")
    print("-" * 60)

    # Option pour nettoyer d'abord
    if len(sys.argv) > 1 and sys.argv[1] == "--clean":
        clear_existing_datasets()

    # Insérer les datasets
    success, errors = insert_datasets()

    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"  ✅ Succès: {success}")
    print(f"  ❌ Erreurs: {errors}")
    print(f"  📦 Total: {len(REAL_DATASETS)}")
    print("=" * 60)

    if errors == 0:
        print("\n🎉 Tous les datasets ont été insérés avec succès!")
    else:
        print(f"\n⚠️  {errors} erreur(s) rencontrée(s). Vérifiez les logs ci-dessus.")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
