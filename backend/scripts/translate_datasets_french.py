"""
Script pour traduire les noms des datasets en français.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Erreur: Variables Supabase non définies")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Mapping anglais -> français
TRANSLATIONS = {
    # Kaggle datasets
    "French Motor Third-Party Liability Claims (freMTPL2freq)": "Sinistres RC Auto France - Fréquence (freMTPL2freq)",
    "French Motor Third-Party Liability Severity (freMTPL2sev)": "Sinistres RC Auto France - Sévérité (freMTPL2sev)",
    "Health Insurance Cross Sell Prediction": "Prédiction de vente croisée Assurance Santé",
    "Insurance Fraud Detection": "Détection de fraude en Assurance",
    "Medical Cost Personal Dataset": "Coûts médicaux individuels",
    "Porto Seguro Safe Driver Prediction": "Prédiction conducteur prudent - Porto Seguro",
    "Allstate Claims Severity": "Sévérité des sinistres - Allstate",
    "Life Insurance Assessment (Prudential)": "Évaluation Assurance Vie - Prudential",

    # CAS datasets
    "CAS Loss Reserving Database - Commercial Auto": "Base de provisionnement CAS - Auto Commercial",
    "CAS Loss Reserving Database - Workers Compensation": "Base de provisionnement CAS - Accidents du Travail",
    "CAS Loss Reserving Database - Medical Malpractice": "Base de provisionnement CAS - Responsabilité Médicale",

    # UCI / Other
    "Statlog German Credit Data": "Données de crédit allemand - Statlog",
    "Swedish Motor Insurance (LGPIF)": "Assurance Auto Suède (LGPIF)",
    "Motorcycle Insurance Claims": "Sinistres Assurance Moto",
    "Wisconsin Breast Cancer Dataset": "Cancer du sein Wisconsin - Classification médicale",
    "Telco Customer Churn": "Prédiction de résiliation client (Churn)",

    # Survival / Life
    "ROSSI Recidivism Dataset": "Données de survie - Récidive (ROSSI)",
    "Heart Failure Survival Dataset": "Survie insuffisance cardiaque",

    # Catastrophes
    "EMDAT Natural Disasters Database": "Base de données catastrophes naturelles (EM-DAT)",
}

def main():
    print("=" * 60)
    print("🇫🇷 Traduction des noms de datasets en français")
    print("=" * 60)

    # Récupérer tous les datasets
    response = supabase.table("datasets").select("id, name").execute()
    datasets = response.data

    print(f"\n📊 {len(datasets)} datasets trouvés\n")

    updated = 0
    for dataset in datasets:
        old_name = dataset["name"]
        if old_name in TRANSLATIONS:
            new_name = TRANSLATIONS[old_name]
            supabase.table("datasets").update({"name": new_name}).eq("id", dataset["id"]).execute()
            print(f"  ✅ {old_name[:40]}... → {new_name[:40]}...")
            updated += 1

    print(f"\n{'=' * 60}")
    print(f"📊 RÉSUMÉ: {updated} datasets traduits")
    print("=" * 60)

if __name__ == "__main__":
    main()
