"""
Script de peuplement avec les datasets français récents (2024-2025).
Focus sur les données longue période pour actuaires : accidents, météo, santé, mortalité.
Sources : data.gouv.fr, INSEE, Météo-France, DREES, CCR
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erreur: SUPABASE_URL et SUPABASE_SERVICE_KEY doivent être définis")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ============================================
# Datasets français récents (2024-2025)
# ============================================

FRENCH_DATASETS_2024 = [
    # ========== ACCIDENTS DE LA ROUTE (2005-2024) ==========
    {
        "name": "Accidents corporels de la circulation routière (2005-2024)",
        "description": "Base BAAC complète des accidents corporels en France métropolitaine et DOM-TOM. 20 ans de données avec localisation GPS, circonstances, véhicules impliqués et victimes. Mise à jour annuelle par l'ONISR. Idéal pour la tarification auto et l'analyse des risques routiers.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/",
        "tags": ["iard", "machine_learning", "pricing"],
        "row_count": 1800000,
        "column_count": 50,
        "file_size_mb": 250.0,
        "data_dictionary_url": "https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/",
        "modeling_types": ["classification", "regression", "time_series"],
        "pivot_variables": ["occurrence_date", "claim_id"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm", "glm"],
    },
    {
        "name": "Fichier BAAC - Caractéristiques des accidents 2024",
        "description": "Caractéristiques détaillées des accidents 2024 : conditions atmosphériques, luminosité, type de collision, intersection. Données extraites du fichier national BAAC administré par l'ONISR.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2024/",
        "tags": ["iard", "pricing"],
        "row_count": 55000,
        "column_count": 15,
        "file_size_mb": 8.0,
        "data_dictionary_url": "https://static.data.gouv.fr/resources/bases-de-donnees-annuelles-des-accidents-corporels-de-la-circulation-routiere-annees-de-2005-a-2023/20241023-153042/description-des-bases-de-donnees-annuelles.pdf",
        "modeling_types": ["classification", "regression"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["glm", "xgboost"],
    },

    # ========== MÉTÉO FRANCE (Historique complet) ==========
    {
        "name": "Données climatologiques quotidiennes - Météo-France",
        "description": "Données météo quotidiennes de toutes les stations françaises depuis leur ouverture. Température, précipitations, vent, humidité. Accès gratuit depuis janvier 2024. Essentiel pour la modélisation Cat et la corrélation sinistres/météo.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/donnees-climatologiques-de-base-quotidiennes/",
        "tags": ["iard", "machine_learning"],
        "row_count": 50000000,
        "column_count": 30,
        "file_size_mb": 2000.0,
        "data_dictionary_url": "https://donneespubliques.meteofrance.fr/",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["xgboost", "lightgbm", "neural_network"],
    },
    {
        "name": "Archives climatiques mensuelles France (depuis 1855)",
        "description": "Tableaux climatologiques mensuels numérisés depuis 1855. Observations quotidiennes historiques de France métropolitaine. Source unique pour les études climatiques longue période.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/documents-darchives-du-climat-numerises-tableaux-climatologiques-mensuels-resumant-les-observations-meteorologiques-quotidiennes-de-france-metropolitaine/",
        "tags": ["iard", "machine_learning"],
        "row_count": 2000000,
        "column_count": 20,
        "file_size_mb": 500.0,
        "data_dictionary_url": "https://donneespubliques.meteofrance.fr/",
        "modeling_types": ["time_series"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["chain_ladder", "neural_network"],
    },
    {
        "name": "Portail Météo Open Data - Données temps réel",
        "description": "Accès aux données d'observation temps réel de plus de 2000 stations météo françaises. API gratuite depuis 2024. Températures, précipitations, vent, pression.",
        "source": "opendata",
        "source_url": "https://meteo.data.gouv.fr/",
        "tags": ["iard", "machine_learning"],
        "row_count": 10000000,
        "column_count": 25,
        "file_size_mb": 1000.0,
        "data_dictionary_url": "https://donneespubliques.meteofrance.fr/",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["xgboost", "lightgbm"],
    },

    # ========== CATASTROPHES NATURELLES ==========
    {
        "name": "Bilan Catastrophes Naturelles France 1982-2024 (CCR)",
        "description": "Bilan complet du régime Cat Nat français par la CCR. 51,5 milliards d'euros de sinistres sur 1982-2023. Inondations et sécheresses = 90% des coûts. Données essentielles pour la réassurance et le pricing Cat.",
        "source": "other",
        "source_url": "https://www.ccr.fr/wp-content/uploads/2025/07/20250610_BILAN_CAT_NAT_2024-3.pdf",
        "tags": ["iard", "reserving", "pricing"],
        "row_count": 250000,
        "column_count": 20,
        "file_size_mb": 15.0,
        "data_dictionary_url": "https://www.ccr.fr/",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "best_fit_models": ["glm", "chain_ladder", "mack"],
    },
    {
        "name": "Arrêtés Cat Nat par commune - Georisques",
        "description": "Base des arrêtés de reconnaissance de catastrophe naturelle par commune française depuis 1982. Inondations, mouvements de terrain, sécheresse. Indispensable pour la tarification géographique.",
        "source": "opendata",
        "source_url": "https://www.georisques.gouv.fr/risques/catastrophes-naturelles/donnees",
        "tags": ["iard", "pricing"],
        "row_count": 300000,
        "column_count": 15,
        "file_size_mb": 50.0,
        "data_dictionary_url": "https://www.georisques.gouv.fr/",
        "modeling_types": ["classification", "time_series"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
    },

    # ========== SANTÉ / HOSPITALISATION ==========
    {
        "name": "Établissements de santé France 2023-2024 (DREES)",
        "description": "Panorama complet des hôpitaux et cliniques français. 13,2 millions de patients hospitalisés en 2023, 19 millions d'hospitalisations court séjour. Capacités, activité, personnel, urgences.",
        "source": "other",
        "source_url": "https://drees.solidarites-sante.gouv.fr/publications-communique-de-presse/panoramas-de-la-drees/250522_Panorama_etablissements-de-sante2025",
        "tags": ["sante", "machine_learning"],
        "row_count": 3000000,
        "column_count": 50,
        "file_size_mb": 200.0,
        "data_dictionary_url": "https://data.drees.solidarites-sante.gouv.fr/",
        "modeling_types": ["classification", "regression", "time_series"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
    },
    {
        "name": "Morbidité hospitalière 2010-2023 (PMSI)",
        "description": "Données d'hospitalisation en court séjour de 2010 à 2023. Source PMSI MCO via l'ATIH. Diagnostics, durées de séjour, actes. Base de référence pour le pricing santé.",
        "source": "other",
        "source_url": "https://data.drees.solidarites-sante.gouv.fr/explore/dataset/morbidite-hospitaliere/information/",
        "tags": ["sante", "pricing", "machine_learning"],
        "row_count": 200000000,
        "column_count": 40,
        "file_size_mb": 5000.0,
        "data_dictionary_url": "https://data.drees.solidarites-sante.gouv.fr/",
        "modeling_types": ["classification", "regression"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "best_fit_models": ["glm", "xgboost", "lightgbm"],
    },
    {
        "name": "Données COVID-19 hospitalières France (2020-2023)",
        "description": "Données hospitalières COVID-19 : hospitalisations, réanimations, décès par département et région. Historique complet 2020-2023. Arrêt des données au 1er juillet 2023.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/",
        "tags": ["sante", "machine_learning"],
        "row_count": 500000,
        "column_count": 15,
        "file_size_mb": 50.0,
        "data_dictionary_url": "https://www.data.gouv.fr/fr/datasets/donnees-hospitalieres-relatives-a-lepidemie-de-covid-19/",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["xgboost", "neural_network"],
    },

    # ========== MORTALITÉ / DÉMOGRAPHIE ==========
    {
        "name": "Décès quotidiens et mensuels France 2024 (INSEE)",
        "description": "643 168 décès en France en 2024. Données définitives au niveau national, régional et départemental. Âge moyen au décès : 79,4 ans. Mise à jour quotidienne.",
        "source": "insee",
        "source_url": "https://www.insee.fr/fr/statistiques/7764286",
        "tags": ["vie", "sante"],
        "row_count": 650000,
        "column_count": 10,
        "file_size_mb": 30.0,
        "data_dictionary_url": "https://www.insee.fr/fr/statistiques/7764286",
        "modeling_types": ["time_series", "survival"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["cox", "kaplan_meier", "glm"],
    },
    {
        "name": "Tables de mortalité France - Séries longues INSEE",
        "description": "Tables de mortalité françaises en séries longues. Espérance de vie, quotients de mortalité par âge et sexe. Données historiques depuis 1946. Indispensable pour le provisionnement vie.",
        "source": "insee",
        "source_url": "https://www.insee.fr/fr/statistiques/8638348",
        "tags": ["vie", "pricing", "reserving"],
        "row_count": 10000,
        "column_count": 15,
        "file_size_mb": 5.0,
        "data_dictionary_url": "https://www.insee.fr/fr/statistiques/8638348",
        "modeling_types": ["survival", "time_series"],
        "pivot_variables": [],
        "best_fit_models": ["cox", "kaplan_meier"],
    },
    {
        "name": "Bilan démographique France 2024 (INSEE)",
        "description": "Bilan démographique complet 2024 : naissances, décès, mariages, espérance de vie. Vieillissement du baby-boom et impact sur la mortalité. Données officielles INSEE.",
        "source": "insee",
        "source_url": "https://www.insee.fr/fr/statistiques/8327319",
        "tags": ["vie", "sante"],
        "row_count": 5000,
        "column_count": 20,
        "file_size_mb": 2.0,
        "data_dictionary_url": "https://www.insee.fr/fr/statistiques/8327319",
        "modeling_types": ["time_series"],
        "pivot_variables": [],
        "best_fit_models": ["glm", "neural_network"],
    },

    # ========== ASSURANCE / SINISTRALITÉ ==========
    {
        "name": "Assurance des événements naturels 2024 (France Assureurs)",
        "description": "Rapport annuel France Assureurs sur la sinistralité Cat Nat. 113,1 millions de risques assurés, 2,17 Md€ de primes. Charge totale 2024 : 1,58 Md€. Données marché assurance.",
        "source": "other",
        "source_url": "https://www.franceassureurs.fr/wp-content/uploads/lassurance-des-evenements-naturels-en-2024.pdf",
        "tags": ["iard", "pricing", "reserving"],
        "row_count": 1000,
        "column_count": 30,
        "file_size_mb": 5.0,
        "data_dictionary_url": "https://www.franceassureurs.fr/",
        "modeling_types": ["time_series", "regression"],
        "pivot_variables": ["claim_amount"],
        "best_fit_models": ["glm", "chain_ladder"],
    },

    # ========== DONNÉES GÉOGRAPHIQUES ==========
    {
        "name": "Base Adresse Nationale (BAN) France",
        "description": "Base officielle des adresses françaises. 26 millions d'adresses géolocalisées. Indispensable pour la tarification géographique et le géocodage des sinistres.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/base-adresse-nationale/",
        "tags": ["iard", "pricing"],
        "row_count": 26000000,
        "column_count": 15,
        "file_size_mb": 3000.0,
        "data_dictionary_url": "https://adresse.data.gouv.fr/",
        "modeling_types": ["clustering"],
        "pivot_variables": [],
        "best_fit_models": ["random_forest", "xgboost"],
    },
    {
        "name": "Zonage inondation - Plans de Prévention des Risques",
        "description": "Cartographie des zones inondables en France. PPRi par commune. Essentiel pour la tarification MRH et la souscription en zones à risques.",
        "source": "opendata",
        "source_url": "https://www.georisques.gouv.fr/risques/inondations",
        "tags": ["iard", "pricing"],
        "row_count": 500000,
        "column_count": 20,
        "file_size_mb": 500.0,
        "data_dictionary_url": "https://www.georisques.gouv.fr/",
        "modeling_types": ["classification"],
        "pivot_variables": [],
        "best_fit_models": ["glm", "random_forest"],
    },

    # ========== CRIMINALITÉ / SÉCURITÉ ==========
    {
        "name": "Crimes et délits enregistrés France (2016-2024)",
        "description": "Statistiques de la délinquance par département. Vols, cambriolages, violences. Utile pour la tarification MRH et la modélisation du vol.",
        "source": "opendata",
        "source_url": "https://www.data.gouv.fr/fr/datasets/bases-statistiques-communale-et-departementale-de-la-delinquance-enregistree-par-la-police-et-la-gendarmerie-nationales/",
        "tags": ["iard", "pricing", "machine_learning"],
        "row_count": 100000,
        "column_count": 25,
        "file_size_mb": 50.0,
        "data_dictionary_url": "https://www.interieur.gouv.fr/",
        "modeling_types": ["classification", "regression"],
        "pivot_variables": ["occurrence_date"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
    },
]


def insert_datasets():
    """Insère les nouveaux datasets français dans Supabase."""
    print(f"\n📦 Insertion de {len(FRENCH_DATASETS_2024)} datasets français récents...")

    success_count = 0
    error_count = 0

    for i, dataset in enumerate(FRENCH_DATASETS_2024, 1):
        try:
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
                "created_by": "system",
            }

            result = supabase.table("datasets").insert(data).execute()

            if result.data:
                success_count += 1
                print(f"  ✅ [{i}/{len(FRENCH_DATASETS_2024)}] {dataset['name'][:50]}...")
            else:
                error_count += 1
                print(f"  ❌ [{i}/{len(FRENCH_DATASETS_2024)}] {dataset['name'][:50]}")

        except Exception as e:
            error_count += 1
            print(f"  ❌ [{i}/{len(FRENCH_DATASETS_2024)}] {dataset['name'][:50]} - {e}")

    return success_count, error_count


def main():
    print("=" * 60)
    print("🇫🇷 StochastiQdata - Datasets français récents 2024-2025")
    print("=" * 60)
    print(f"\n📊 {len(FRENCH_DATASETS_2024)} datasets à insérer")
    print("📍 Sources : data.gouv.fr, INSEE, Météo-France, DREES, CCR")
    print("-" * 60)

    success, errors = insert_datasets()

    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"  ✅ Succès: {success}")
    print(f"  ❌ Erreurs: {errors}")
    print("=" * 60)

    if errors == 0:
        print("\n🎉 Tous les datasets ont été ajoutés!")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
