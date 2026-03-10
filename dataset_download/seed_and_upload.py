#!/usr/bin/env python3
"""
StochastiQdata — Seed + Upload datasets
========================================
1. Télécharge les datasets via kagglehub
2. Insère les métadonnées dans Supabase (table `datasets`)
3. Upload les fichiers CSV vers Supabase Storage (bucket `datasets-files`)
4. Met à jour les enregistrements avec file_url

Usage:
    cd /home/kompany-konga/stochastiqdata_site
    source backend/venv/bin/activate
    python3 dataset_download/seed_and_upload.py

Prérequis:
    - Compte Kaggle + kaggle.json dans ~/.kaggle/ (pour les datasets privés)
    - SUPABASE_URL et SUPABASE_SERVICE_KEY dans backend/.env
"""

import os
import sys
import hashlib
import uuid
import csv
import io
from pathlib import Path
from datetime import datetime, timezone

# ── Chargement .env ──────────────────────────────────────────
env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
BUCKET = "datasets-files"

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ SUPABASE_URL ou SUPABASE_SERVICE_KEY manquants dans backend/.env")
    sys.exit(1)

from supabase import create_client
import kagglehub

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ═══════════════════════════════════════════════════════════════
# CATALOGUE DES DATASETS
# ═══════════════════════════════════════════════════════════════
# Format:
#   kaggle_id   : "username/dataset-name" pour kagglehub.dataset_download()
#                 None si pas sur Kaggle (metadata only)
#   files       : liste des fichiers CSV à uploader depuis le dossier téléchargé
#                 None = tous les CSV du dossier
# ═══════════════════════════════════════════════════════════════

CATALOG = [

    # ────────────────────────────────────────────────
    # IARD — TARIFICATION AUTO
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "karansarpal/fremtpl-french-motor-tpl-insurance-claims",
        "files": ["freMTPLfreq.csv"],
        "name": "French Motor MTPL Frequency (freMTPL2freq)",
        "description": "678 013 polices d'assurance auto française RC. Variables tarifaires (puissance, âge conducteur, bonus-malus, région) et sinistralité (ClaimNb, Exposure). Référence académique Charpentier, Denuit & Trufin (ArXiv:2103.03635). Dataset de référence pour GLM Poisson fréquence.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/karansarpal/fremtpl-french-motor-tpl-insurance-claims",
        "tags": ["iard", "pricing", "glm"],
        "row_count": 678013,
        "column_count": 12,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm", "xgboost", "neural_network"],
        "pivot_variables": ["exposure", "policy_id", "claim_id"],
        "target_variable": "ClaimNb",
        "exposure_variable": "Exposure",
        "license": "cc-by",
    },
    {
        "kaggle_id": "karansarpal/fremtpl-french-motor-tpl-insurance-claims",
        "files": ["freMTPLsev.csv"],
        "name": "French Motor MTPL Severity (freMTPL2sev)",
        "description": "26 639 sinistres auto RC française avec montant de coût individuel (ClaimAmount). Complément de freMTPL2freq pour la modélisation GLM Gamma du coût par sinistre. Tweedie possible sur la prime pure.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/karansarpal/fremtpl-french-motor-tpl-insurance-claims",
        "tags": ["iard", "pricing", "glm"],
        "row_count": 26639,
        "column_count": 3,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm", "xgboost", "lightgbm"],
        "pivot_variables": ["claim_amount", "claim_id", "policy_id"],
        "target_variable": "ClaimAmount",
        "license": "cc-by",
    },
    {
        "kaggle_id": "sagnik1511/car-insurance-data",
        "files": None,
        "name": "Car Insurance Claims",
        "description": "10 302 contrats d'assurance automobile avec variables sociodémographiques (âge, revenu, éducation, état civil) et historique de sinistres. Idéal pour la segmentation clientèle, la propension au sinistre et la détection de fraude.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/sagnik1511/car-insurance-data",
        "tags": ["iard", "pricing", "fraude"],
        "row_count": 10302,
        "column_count": 19,
        "modeling_types": ["classification", "regression"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "OUTCOME",
        "license": "cc0",
    },
    {
        "kaggle_id": "anmolkumar/health-insurance-cross-sell-prediction",
        "files": ["train.csv"],
        "name": "Vehicle Insurance Cross-Sell (Health → Auto)",
        "description": "381 109 clients avec historique assurance santé et indicateur d'intérêt pour l'assurance auto. Variables : âge, sexe, permis, véhicule, prime actuelle. Modèle de propension à l'achat / cross-sell.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/anmolkumar/health-insurance-cross-sell-prediction",
        "tags": ["iard", "pricing", "machine_learning"],
        "row_count": 381109,
        "column_count": 12,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": ["policy_id"],
        "target_variable": "Response",
        "license": "cc0",
    },
    {
        "kaggle_id": "buntyshah/auto-insurance-claims-data",
        "files": None,
        "name": "Auto Insurance Claims Fraud",
        "description": "15 420 déclarations de sinistres auto avec indicateur de fraude. Inclut type de police, lieu du sinistre, type de sinistre, véhicule et profil du conducteur. Référence pour la modélisation de détection de fraude IARD.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/buntyshah/auto-insurance-claims-data",
        "tags": ["iard", "fraude", "machine_learning"],
        "row_count": 15420,
        "column_count": 40,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": ["claim_amount", "occurrence_date", "claim_id"],
        "target_variable": "fraud_reported",
        "license": "cc0",
    },
    {
        "kaggle_id": "xiaomengsun/car-insurance-claim-prediction",
        "files": None,
        "name": "Car Insurance Claim Prediction",
        "description": "58 592 polices avec indicateur de sinistre (0/1). Variables démographiques et comportementales. Cas typique de déséquilibre de classes pour la modélisation de fréquence sinistre.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/xiaomengsun/car-insurance-claim-prediction",
        "tags": ["iard", "pricing"],
        "row_count": 58592,
        "column_count": 18,
        "modeling_types": ["classification"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
        "pivot_variables": ["policy_id"],
        "target_variable": "is_claim",
        "license": "cc0",
    },
    {
        "kaggle_id": "shivamb/vehicle-claim-fraud-detection",
        "files": None,
        "name": "Vehicle Claim Fraud Detection",
        "description": "15 000 déclarations de sinistres véhicule avec label de fraude. Variables : type de véhicule, ancienneté, type de sinistre, police et profil assuré. Benchmark de détection de fraude en assurance automobile.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/shivamb/vehicle-claim-fraud-detection",
        "tags": ["iard", "fraude"],
        "row_count": 15000,
        "column_count": 33,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": ["claim_id", "occurrence_date"],
        "target_variable": "FraudFound_P",
        "license": "cc0",
    },
    {
        "kaggle_id": "mhdzahier/travel-insurance",
        "files": None,
        "name": "Travel Insurance Claims",
        "description": "63 326 polices d'assurance voyage avec sinistres (Claim). Variables : destination, durée, âge assuré, agence, canal de distribution, type de voyage. Modélisation fréquence/sévérité assurance voyage.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/mhdzahier/travel-insurance",
        "tags": ["iard", "pricing"],
        "row_count": 63326,
        "column_count": 11,
        "modeling_types": ["classification", "regression"],
        "best_fit_models": ["glm", "xgboost"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "Claim",
        "license": "cc0",
    },
    {
        "kaggle_id": "yctulu/wisconsin-auto-insurance",
        "files": None,
        "name": "Wisconsin Auto Insurance",
        "description": "Données d'assurance auto du Wisconsin. Relation entre nombre de réclamations et coût total des sinistres. Dataset classique pour la régression simple et la modélisation de fréquence/coût.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/yctulu/wisconsin-auto-insurance",
        "tags": ["iard", "pricing", "glm"],
        "row_count": 67,
        "column_count": 2,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "y",
        "license": "cc0",
    },
    {
        "kaggle_id": "merishnasuwal/insurance-churn-dataset",
        "files": None,
        "name": "Insurance Customer Churn",
        "description": "Dataset de résiliation (churn) d'assurance. Variables client et indicateur de résiliation. Modélisation de la fidélisation client et anticipation des résiliations en assurance.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/merishnasuwal/insurance-churn-dataset",
        "tags": ["iard", "machine_learning"],
        "row_count": 10000,
        "column_count": 9,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": ["policy_id"],
        "target_variable": "churn",
        "license": "cc0",
    },

    # ────────────────────────────────────────────────
    # ASSURANCE SANTÉ
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "mirichoi0218/insurance",
        "files": None,
        "name": "Medical Cost Personal Dataset",
        "description": "1 338 assurés avec coût médical individuel annuel. Variables : âge, sexe, IMC, nombre d'enfants, tabagisme, région. Dataset de référence pour la régression des dépenses de santé et la tarification assurance santé.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/mirichoi0218/insurance",
        "tags": ["sante", "pricing", "glm"],
        "row_count": 1338,
        "column_count": 7,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "charges",
        "license": "cc0",
    },
    {
        "kaggle_id": "teertha/ushealthinsurancedataset",
        "files": None,
        "name": "US Health Insurance Dataset",
        "description": "1 338 enregistrements d'assurance santé américaine. Variables similaires au dataset Medical Cost mais avec profil de risque étendu. Idéal pour la régression des primes et l'analyse actuarielle santé.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/teertha/ushealthinsurancedataset",
        "tags": ["sante", "pricing"],
        "row_count": 1338,
        "column_count": 7,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm", "xgboost"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "charges",
        "license": "cc0",
    },
    {
        "kaggle_id": "willianoliveiragibin/healthcare-insurance",
        "files": None,
        "name": "Healthcare Insurance Premium Prediction",
        "description": "Dataset de tarification assurance santé avec variables de risque (âge, antécédents, conditions chroniques). Modélisation de la prime pure et segmentation des risques.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/willianoliveiragibin/healthcare-insurance",
        "tags": ["sante", "pricing"],
        "row_count": 50000,
        "column_count": 11,
        "modeling_types": ["regression", "classification"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "PremiumPrice",
        "license": "cc0",
    },
    {
        "kaggle_id": "alexteboul/diabetes-health-indicators-dataset",
        "files": ["diabetes_binary_health_indicators_BRFSS2015.csv"],
        "name": "Diabetes Health Indicators (CDC BRFSS)",
        "description": "253 680 réponses à l'enquête CDC BRFSS 2015 avec indicateur diabète et 21 variables de santé. Idéal pour la classification risque diabète, modélisation de prévalence et segmentation risque santé.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset",
        "tags": ["sante", "machine_learning"],
        "row_count": 253680,
        "column_count": 22,
        "modeling_types": ["classification"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
        "pivot_variables": [],
        "target_variable": "Diabetes_binary",
        "license": "cc0",
    },
    {
        "kaggle_id": "prasad22/health-insurance-dataset",
        "files": None,
        "name": "Health Insurance Customer Dataset",
        "description": "Données clients d'une compagnie d'assurance santé. Variables : âge, sexe, historique médical, type de couverture et montant de la prime. Analyse de la rentabilité et segmentation des assurés.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/prasad22/health-insurance-dataset",
        "tags": ["sante", "pricing"],
        "row_count": 50000,
        "column_count": 14,
        "modeling_types": ["regression", "classification"],
        "best_fit_models": ["xgboost", "random_forest"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "claim",
        "license": "cc0",
    },
    {
        "kaggle_id": "ravindrasinghrana/health-insurance-premium-dataset",
        "files": None,
        "name": "Health Insurance Premium — Smoking Impact",
        "description": "Dataset de primes d'assurance santé avec focus sur l'impact du tabagisme et de l'IMC. Modélisation actuarielle de la sinistralité santé et étude des facteurs de risque.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/ravindrasinghrana/health-insurance-premium-dataset",
        "tags": ["sante", "pricing", "glm"],
        "row_count": 50000,
        "column_count": 13,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm", "xgboost"],
        "pivot_variables": ["claim_amount"],
        "target_variable": "PremiumPrice",
        "license": "cc0",
    },

    # ────────────────────────────────────────────────
    # FRAUDE
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "mlg-ulb/creditcardfraud",
        "files": None,
        "name": "Credit Card Fraud Detection (ULB)",
        "description": "284 807 transactions bancaires européennes (sept. 2013) avec 492 fraudes (0.17%). 28 composantes PCA anonymisées + montant + temps. Dataset de référence mondial pour la détection de fraude avec données déséquilibrées.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud",
        "tags": ["fraude", "machine_learning"],
        "row_count": 284807,
        "column_count": 31,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "neural_network", "lightgbm"],
        "pivot_variables": ["claim_amount", "occurrence_date"],
        "target_variable": "Class",
        "license": "other",
    },
    {
        "kaggle_id": "sgpjesus/bank-account-fraud-dataset-neurips-2022",
        "files": ["Base.csv"],
        "name": "Bank Account Fraud Dataset — NeurIPS 2022",
        "description": "1 million de demandes d'ouverture de compte bancaire avec indicateur de fraude. Dataset NeurIPS 2022 conçu pour les benchmarks de détection de fraude équitable. 30 features caractéristiques socio-comportementales.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/sgpjesus/bank-account-fraud-dataset-neurips-2022",
        "tags": ["fraude", "machine_learning"],
        "row_count": 1000000,
        "column_count": 32,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "lightgbm", "neural_network"],
        "pivot_variables": [],
        "target_variable": "fraud_bool",
        "license": "cc-by",
    },
    {
        "kaggle_id": "ealaxi/paysim1",
        "files": None,
        "name": "PaySim Mobile Money Fraud Simulation",
        "description": "6.3 millions de transactions de mobile money simulées avec fraudes. Généré par simulation multi-agents calibrée sur données réelles africaines. Types de transactions : CASH-IN, CASH-OUT, DEBIT, PAYMENT, TRANSFER.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/ealaxi/paysim1",
        "tags": ["fraude", "machine_learning"],
        "row_count": 6362620,
        "column_count": 11,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": ["claim_amount", "occurrence_date"],
        "target_variable": "isFraud",
        "license": "cc-by",
    },
    {
        "kaggle_id": "mastmustu/insurance-claims-fraud-data",
        "files": None,
        "name": "Insurance Claims Fraud Detection",
        "description": "Données de déclarations de sinistres assurance avec label de fraude. Couvre plusieurs lignes : auto, incendie, habitation. Variables : profil assuré, circonstances sinistre, historique police.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/mastmustu/insurance-claims-fraud-data",
        "tags": ["iard", "fraude"],
        "row_count": 15420,
        "column_count": 40,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest"],
        "pivot_variables": ["claim_id", "occurrence_date", "claim_amount"],
        "target_variable": "fraud_reported",
        "license": "cc0",
    },
    {
        "kaggle_id": "rupakroy/online-payments-fraud-detection-dataset",
        "files": None,
        "name": "Online Payments Fraud Detection",
        "description": "6.3 millions de transactions de paiement en ligne avec indicateur de fraude. Incluant type de transaction, montant, soldes initiaux et finaux. Dataset synthétique haute fidélité pour la modélisation de fraude bancaire.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/rupakroy/online-payments-fraud-detection-dataset",
        "tags": ["fraude", "machine_learning"],
        "row_count": 6362620,
        "column_count": 10,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "lightgbm", "random_forest"],
        "pivot_variables": ["claim_amount", "occurrence_date"],
        "target_variable": "isFraud",
        "license": "cc0",
    },
    {
        "kaggle_id": "valakhorasani/bank-transaction-dataset-for-fraud-detection",
        "files": None,
        "name": "Bank Transaction Anomaly Detection",
        "description": "Transactions bancaires avec anomalies et fraudes. Analyse comportementale des clients, montants inhabituels, fréquence et localisation. Idéal pour les modèles non-supervisés et l'isolation forest.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/valakhorasani/bank-transaction-dataset-for-fraud-detection",
        "tags": ["fraude", "machine_learning"],
        "row_count": 2512,
        "column_count": 9,
        "modeling_types": ["classification", "clustering"],
        "best_fit_models": ["xgboost", "random_forest"],
        "pivot_variables": ["claim_amount", "occurrence_date"],
        "target_variable": "Is_Fraud",
        "license": "cc0",
    },
    {
        "kaggle_id": "jainilcoder/online-payment-fraud-detection",
        "files": None,
        "name": "Synthetic Online Payment Fraud",
        "description": "6.3 millions de paiements en ligne synthétiques. Transactions PAYMENT, TRANSFER, CASH-OUT avec indicateur de fraude. Déséquilibre de classes marqué (0.13% de fraudes). Dataset d'entraînement pour systèmes anti-fraude.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/jainilcoder/online-payment-fraud-detection",
        "tags": ["fraude", "machine_learning"],
        "row_count": 6362620,
        "column_count": 11,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "lightgbm"],
        "pivot_variables": ["claim_amount", "occurrence_date"],
        "target_variable": "isFraud",
        "license": "cc0",
    },

    # ────────────────────────────────────────────────
    # BANQUE — CRÉDIT & SCORING
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "laotse/credit-risk-dataset",
        "files": None,
        "name": "Credit Risk Dataset",
        "description": "32 581 emprunteurs avec statut de défaut de crédit. Variables : âge, revenus, emploi, motif du prêt, historique crédit, taux d'endettement. Dataset propre et bien documenté pour la modélisation PD (Probabilité de Défaut).",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/laotse/credit-risk-dataset",
        "tags": ["machine_learning", "pricing"],
        "row_count": 32581,
        "column_count": 11,
        "modeling_types": ["classification"],
        "best_fit_models": ["glm", "xgboost", "random_forest", "lightgbm"],
        "pivot_variables": [],
        "target_variable": "loan_status",
        "license": "cc0",
    },
    {
        "kaggle_id": "sakshigoyal7/credit-card-customers",
        "files": None,
        "name": "Credit Card Customers Churn",
        "description": "10 127 clients bancaires avec indicateur d'attrition (churn). 19 variables : solde, utilisation, transactions, contacts, historique. Modélisation de la fidélisation client et prédiction de l'attrition bancaire.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/sakshigoyal7/credit-card-customers",
        "tags": ["machine_learning"],
        "row_count": 10127,
        "column_count": 23,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": [],
        "target_variable": "Attrition_Flag",
        "license": "cc0",
    },
    {
        "kaggle_id": "altruistdelhite04/loan-prediction-problem-dataset",
        "files": ["train_u6lujuX_CVtuZ9i.csv"],
        "name": "Loan Approval Prediction",
        "description": "615 demandes de prêt avec statut d'approbation. Variables : genre, statut marital, éducation, revenus, montant prêt, historique crédit, zone géographique. Cas classique de credit scoring binaire.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/altruistdelhite04/loan-prediction-problem-dataset",
        "tags": ["machine_learning", "pricing"],
        "row_count": 615,
        "column_count": 13,
        "modeling_types": ["classification"],
        "best_fit_models": ["glm", "random_forest", "xgboost"],
        "pivot_variables": [],
        "target_variable": "Loan_Status",
        "license": "cc0",
    },
    {
        "kaggle_id": "zaurbegiev/my-dataset",
        "files": None,
        "name": "Bank Loan Status Dataset",
        "description": "100 000 demandes de prêt bancaire avec statut (accordé/refusé). Variables financières : score de crédit, revenu annuel, ratio d'endettement, ancienneté emploi, montant emprunté.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/zaurbegiev/my-dataset",
        "tags": ["machine_learning"],
        "row_count": 100000,
        "column_count": 19,
        "modeling_types": ["classification"],
        "best_fit_models": ["glm", "xgboost", "random_forest"],
        "pivot_variables": [],
        "target_variable": "Loan Status",
        "license": "cc0",
    },
    {
        "kaggle_id": "adammaus/predicting-churn-for-bank-customers",
        "files": None,
        "name": "Bank Customer Churn Prediction",
        "description": "10 000 clients bancaires avec indicateur de churn. Variables : score de crédit, pays, sexe, âge, ancienneté, solde, produits, carte de crédit, membre actif, salaire estimé. Benchmark churn bancaire.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/adammaus/predicting-churn-for-bank-customers",
        "tags": ["machine_learning"],
        "row_count": 10000,
        "column_count": 14,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "neural_network"],
        "pivot_variables": [],
        "target_variable": "Exited",
        "license": "cc0",
    },
    {
        "kaggle_id": "shivamb/bank-customer-segmentation",
        "files": None,
        "name": "Bank Customer Segmentation",
        "description": "1 million de transactions bancaires avec données clients. Permet la segmentation comportementale (RFM), le clustering de clients et l'analyse des patterns de dépenses. Base pour le ciblage marketing bancaire.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/shivamb/bank-customer-segmentation",
        "tags": ["machine_learning"],
        "row_count": 1000000,
        "column_count": 9,
        "modeling_types": ["clustering", "classification"],
        "best_fit_models": ["random_forest", "xgboost"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "target_variable": None,
        "license": "cc0",
    },
    {
        "kaggle_id": "mirbektoktogaraev/should-this-loan-be-approved-or-denied",
        "files": None,
        "name": "SBA Loan Approval (US Small Business)",
        "description": "899 164 prêts Small Business Administration (SBA) 1987-2014 avec statut de défaut. Variables : état, banque, secteur NAICS, emploi créé, montant garanti. Analyse de risque crédit PME et impact des garanties publiques.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/mirbektoktogaraev/should-this-loan-be-approved-or-denied",
        "tags": ["machine_learning", "pricing"],
        "row_count": 899164,
        "column_count": 27,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "glm"],
        "pivot_variables": ["occurrence_date"],
        "target_variable": "MIS_Status",
        "license": "cc0",
    },
    {
        "kaggle_id": "arashnic/the-ultimate-bank-dataset",
        "files": None,
        "name": "Bank Marketing & Financial Indicators",
        "description": "Données de campagne marketing bancaire avec taux d'acceptation d'un dépôt à terme. Combiné à des indicateurs économiques (taux emploi, euribor). Modélisation de la conversion client et ROI campagnes.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/arashnic/the-ultimate-bank-dataset",
        "tags": ["machine_learning"],
        "row_count": 41188,
        "column_count": 21,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "glm"],
        "pivot_variables": [],
        "target_variable": "y",
        "license": "cc0",
    },
    {
        "kaggle_id": "nupur1306/properloandata",
        "files": None,
        "name": "Prosper P2P Loan Data",
        "description": "113 937 prêts P2P Prosper Marketplace avec 81 variables. Taux d'intérêt, score de risque, historique de crédit, statut du prêt. Dataset de référence pour l'analyse du risque de crédit en lending alternatif.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/nupur1306/properloandata",
        "tags": ["machine_learning", "pricing"],
        "row_count": 113937,
        "column_count": 81,
        "modeling_types": ["classification", "regression"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": ["occurrence_date"],
        "target_variable": "LoanStatus",
        "license": "cc0",
    },
    {
        "kaggle_id": "rameshmehta/bank-default-prediction",
        "files": None,
        "name": "Bank Loan Default Prediction",
        "description": "Historique de prêts bancaires avec indicateur de défaut. Variables financières et comportementales : utilisation du crédit, paiements en retard, ratio d'endettement, montant renouvelable.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/rameshmehta/bank-default-prediction",
        "tags": ["machine_learning", "pricing"],
        "row_count": 150000,
        "column_count": 11,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "glm"],
        "pivot_variables": [],
        "target_variable": "SeriousDlqin2yrs",
        "license": "cc0",
    },
    {
        "kaggle_id": "arjunbhasin2013/ccdata",
        "files": None,
        "name": "Credit Card Spend Patterns",
        "description": "8 950 clients de carte de crédit avec 17 variables comportementales : solde, achats, avances de fonds, paiements, fréquence. Idéal pour la segmentation clientèle et le clustering de profils de dépenses.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/arjunbhasin2013/ccdata",
        "tags": ["machine_learning"],
        "row_count": 8950,
        "column_count": 18,
        "modeling_types": ["clustering"],
        "best_fit_models": ["random_forest", "neural_network"],
        "pivot_variables": [],
        "target_variable": None,
        "license": "cc0",
    },

    # ────────────────────────────────────────────────
    # RISQUE MARCHÉ
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "camnugent/sandp500",
        "files": None,
        "name": "S&P 500 Historical Stock Data",
        "description": "Prix historiques de toutes les actions du S&P 500 depuis 1966. Colonnes : date, ouverture, fermeture, plus haut, plus bas, volume. Calcul de VaR, CVaR, volatilité, corrélations et stress-tests.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/camnugent/sandp500",
        "tags": ["machine_learning"],
        "row_count": 619040,
        "column_count": 7,
        "modeling_types": ["time_series", "regression"],
        "best_fit_models": ["neural_network", "xgboost"],
        "pivot_variables": ["occurrence_date"],
        "target_variable": "close",
        "license": "cc0",
    },
    {
        "kaggle_id": "lp187q/vix-index-data",
        "files": None,
        "name": "VIX Volatility Index Historical",
        "description": "Historique de l'indice VIX (CBOE Volatility Index) depuis 1990. Mesure de la volatilité implicite du marché sur 30 jours. Indicateur de sentiment de marché utilisé dans les modèles de risque assurance et bancaire.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/lp187q/vix-index-data",
        "tags": ["machine_learning"],
        "row_count": 7340,
        "column_count": 5,
        "modeling_types": ["time_series"],
        "best_fit_models": ["neural_network", "xgboost"],
        "pivot_variables": ["occurrence_date"],
        "target_variable": "VIX Close",
        "license": "cc0",
    },
    {
        "kaggle_id": "apoorvwatsky/bank-transaction-data",
        "files": None,
        "name": "Banking Transaction Time Series",
        "description": "Transactions bancaires individuelles avec montants et dates. Analyse de séries temporelles de flux financiers, détection d'anomalies et modélisation de la fréquence des opérations.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/apoorvwatsky/bank-transaction-data",
        "tags": ["machine_learning"],
        "row_count": 1048575,
        "column_count": 8,
        "modeling_types": ["time_series", "clustering"],
        "best_fit_models": ["neural_network", "xgboost"],
        "pivot_variables": ["occurrence_date", "claim_amount"],
        "target_variable": None,
        "license": "cc0",
    },

    # ────────────────────────────────────────────────
    # ML BENCHMARK APPLIQUÉ
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "blastchar/telco-customer-churn",
        "files": None,
        "name": "Telco Customer Churn",
        "description": "7 043 clients télécom avec indicateur de résiliation. Variables : type de contrat, services souscrits, durée d'engagement, montant facturé. Benchmark de churn applicable à l'assurance et aux services financiers.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/blastchar/telco-customer-churn",
        "tags": ["machine_learning"],
        "row_count": 7043,
        "column_count": 21,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "neural_network"],
        "pivot_variables": [],
        "target_variable": "Churn",
        "license": "cc0",
    },
    {
        "kaggle_id": "pavansubhasht/ibm-hr-analytics-attrition-dataset",
        "files": None,
        "name": "IBM HR Analytics — Employee Attrition",
        "description": "1 470 employés avec indicateur d'attrition. 35 variables RH : satisfaction, performance, ancienneté, salaire, déplacement. Modèles de rétention applicables aux risques humains en assurance (turnover, mortalité RH).",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset",
        "tags": ["machine_learning", "vie"],
        "row_count": 1470,
        "column_count": 35,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest"],
        "pivot_variables": [],
        "target_variable": "Attrition",
        "license": "cc0",
    },
    {
        "kaggle_id": "camnugent/california-housing-prices",
        "files": None,
        "name": "California Housing Prices",
        "description": "20 640 blocs de recensement californiens avec valeur médiane des maisons. Variables : localisation, âge, revenus médians, occupation. Benchmark de régression utilisé pour la tarification en assurance habitation et crédit immobilier.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/camnugent/california-housing-prices",
        "tags": ["machine_learning", "pricing"],
        "row_count": 20640,
        "column_count": 10,
        "modeling_types": ["regression"],
        "best_fit_models": ["xgboost", "random_forest", "neural_network"],
        "pivot_variables": [],
        "target_variable": "median_house_value",
        "license": "cc0",
    },
    {
        "kaggle_id": "benpowis/customer-propensity-to-purchase-data",
        "files": None,
        "name": "Customer Propensity to Purchase",
        "description": "Sessions e-commerce avec indicateur d'achat. Données comportementales en ligne : pages visitées, temps, panier, device. Applicable à la modélisation de propension à la souscription en assurance digitale.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/benpowis/customer-propensity-to-purchase-data",
        "tags": ["machine_learning"],
        "row_count": 96510,
        "column_count": 30,
        "modeling_types": ["classification"],
        "best_fit_models": ["xgboost", "random_forest", "lightgbm"],
        "pivot_variables": [],
        "target_variable": "ordered",
        "license": "cc0",
    },
    {
        "kaggle_id": "hieree/ubi-telematics-data",
        "files": None,
        "name": "UBI Telematics Driving Data",
        "description": "Données de conduite télématiques pour l'assurance usage-based (UBI). Variables de conduite : accélérations, freinages, vitesse, trajets nocturnes. Modélisation du score de conduite et tarification comportementale.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/hieree/ubi-telematics-data",
        "tags": ["iard", "pricing", "machine_learning"],
        "row_count": 50000,
        "column_count": 20,
        "modeling_types": ["regression", "clustering"],
        "best_fit_models": ["xgboost", "random_forest", "neural_network"],
        "pivot_variables": [],
        "target_variable": "risk_score",
        "license": "cc0",
    },

    # ────────────────────────────────────────────────
    # VIE / SURVIE
    # ────────────────────────────────────────────────
    {
        "kaggle_id": "prashantk93/biological-age-features",
        "files": None,
        "name": "Biological Age & Health Features",
        "description": "Variables biométriques pour l'estimation de l'âge biologique vs chronologique. Applicable à la modélisation de mortalité, la tarification vie et l'analyse de longévité.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/prashantk93/biological-age-features",
        "tags": ["vie", "machine_learning"],
        "row_count": 5000,
        "column_count": 25,
        "modeling_types": ["regression", "survival"],
        "best_fit_models": ["cox", "xgboost", "random_forest"],
        "pivot_variables": [],
        "target_variable": "biological_age",
        "license": "cc0",
    },
    {
        "kaggle_id": "fedesoriano/body-fat-prediction-dataset",
        "files": None,
        "name": "Body Fat & Health Indicators",
        "description": "252 individus avec mesures corporelles et pourcentage de graisse. Variables morphologiques utilisées en modélisation actuarielle santé et vie : IMC, tour de taille, taille, poids.",
        "source": "kaggle",
        "source_url": "https://www.kaggle.com/datasets/fedesoriano/body-fat-prediction-dataset",
        "tags": ["sante", "vie"],
        "row_count": 252,
        "column_count": 15,
        "modeling_types": ["regression"],
        "best_fit_models": ["glm", "random_forest"],
        "pivot_variables": [],
        "target_variable": "BodyFat",
        "license": "cc0",
    },
]

# ═══════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════

def count_csv_rows(filepath: str) -> int:
    """Compte les lignes d'un CSV (sans header)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            return sum(1 for _ in reader)
    except Exception:
        return 0


def get_csv_columns(filepath: str) -> int:
    """Retourne le nombre de colonnes."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            return len(header)
    except Exception:
        return 0


def file_size_mb(filepath: str) -> float:
    """Taille fichier en MB."""
    return round(os.path.getsize(filepath) / (1024 * 1024), 2)


def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def dataset_exists(name: str) -> bool:
    """Vérifie si un dataset avec ce nom existe déjà."""
    try:
        res = supabase.table("datasets").select("id").ilike("name", name).execute()
        return len(res.data) > 0
    except Exception:
        return False


def upload_to_storage(dataset_id: str, filepath: str) -> str | None:
    """Upload un fichier vers Supabase Storage, retourne l'URL publique."""
    filename = Path(filepath).name
    ext = Path(filepath).suffix.lower()
    storage_path = f"{dataset_id}/{uuid.uuid4()}{ext}"
    try:
        with open(filepath, "rb") as f:
            content = f.read()
        content_type = "text/csv" if ext == ".csv" else "application/octet-stream"
        supabase.storage.from_(BUCKET).upload(storage_path, content, {"content-type": content_type})
        public_url = supabase.storage.from_(BUCKET).get_public_url(storage_path)
        print(f"    ✅ Uploadé : {filename} → {storage_path}")
        return public_url
    except Exception as e:
        print(f"    ⚠️  Upload échoué ({filename}) : {e}")
        return None


# ═══════════════════════════════════════════════════════════════
# SCRIPT PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'='*60}")
    print(f"  StochastiQdata — Seed {len(CATALOG)} datasets")
    print(f"{'='*60}\n")

    inserted = 0
    skipped = 0
    errors = 0

    for entry in CATALOG:
        name = entry["name"]
        print(f"\n📦 {name}")

        # ── 1. Vérifier doublon ──────────────────────────────
        if dataset_exists(name):
            print(f"   ⏭  Déjà en base — skip")
            skipped += 1
            continue

        # ── 2. Télécharger via kagglehub ────────────────────
        download_dir = None
        if entry.get("kaggle_id"):
            try:
                print(f"   ⬇  Download kagglehub : {entry['kaggle_id']}")
                download_dir = kagglehub.dataset_download(entry["kaggle_id"])
                print(f"   📁 Dossier : {download_dir}")
            except Exception as e:
                print(f"   ⚠️  Download échoué : {e}")
                # On continue quand même pour insérer la metadata seule

        # ── 3. Identifier les fichiers CSV ────────────────────
        csv_files = []
        if download_dir and Path(download_dir).exists():
            if entry.get("files"):
                for fname in entry["files"]:
                    p = Path(download_dir) / fname
                    if p.exists():
                        csv_files.append(str(p))
                    else:
                        # Chercher récursivement
                        found = list(Path(download_dir).rglob(fname))
                        if found:
                            csv_files.append(str(found[0]))
            else:
                # Prendre tous les CSV
                csv_files = [str(p) for p in Path(download_dir).rglob("*.csv")]

        # ── 4. Enrichir metadata depuis les fichiers ─────────
        row_count = entry.get("row_count")
        column_count = entry.get("column_count")
        fsize = None

        if csv_files:
            main_csv = csv_files[0]
            if not row_count:
                row_count = count_csv_rows(main_csv)
            if not column_count:
                column_count = get_csv_columns(main_csv)
            fsize = sum(file_size_mb(f) for f in csv_files)
            print(f"   📊 {row_count:,} lignes × {column_count} colonnes ({fsize:.1f} MB)")

        # ── 5. Insérer en base ────────────────────────────────
        record = {
            "name": name,
            "description": entry.get("description", ""),
            "source": entry.get("source", "other"),
            "source_url": entry.get("source_url"),
            "tags": entry.get("tags", []),
            "row_count": row_count,
            "column_count": column_count,
            "file_size_mb": fsize,
            "modeling_types": entry.get("modeling_types", []),
            "best_fit_models": entry.get("best_fit_models", []),
            "pivot_variables": entry.get("pivot_variables", []),
        }
        # Champs optionnels (si colonnes existent en DB)
        if entry.get("target_variable"):
            record["target_variable"] = entry["target_variable"]
        if entry.get("exposure_variable"):
            record["exposure_variable"] = entry["exposure_variable"]
        if entry.get("license"):
            record["license"] = entry["license"]

        try:
            res = supabase.table("datasets").insert(record).execute()
            dataset_id = res.data[0]["id"]
            print(f"   ✅ Inséré en base — id: {dataset_id}")
        except Exception as e:
            print(f"   ❌ Insertion échouée : {e}")
            errors += 1
            continue

        # ── 6. Uploader les fichiers CSV ──────────────────────
        if csv_files:
            file_urls = []
            for csv_path in csv_files:
                fsize_single = file_size_mb(csv_path)
                if fsize_single > 50:
                    print(f"   ⚠️  Fichier trop grand (>{50}MB) : {Path(csv_path).name} — skip upload")
                    continue
                url = upload_to_storage(dataset_id, csv_path)
                if url:
                    file_urls.append(url)

            # Mettre à jour le premier file_url + hash
            if file_urls:
                main_hash = sha256_file(csv_files[0])
                changelog_entry = {
                    "version": "v1.0",
                    "date": datetime.now(timezone.utc).isoformat(),
                    "description": f"Seed initial : {Path(csv_files[0]).name}",
                    "file_url": file_urls[0],
                    "hash": main_hash,
                    "size_mb": file_size_mb(csv_files[0]),
                }
                try:
                    supabase.table("datasets").update({
                        "file_url": file_urls[0],
                        "file_hash": main_hash,
                        "changelog": [changelog_entry],
                    }).eq("id", dataset_id).execute()
                except Exception as e:
                    print(f"   ⚠️  Mise à jour file_url échouée : {e}")

        inserted += 1

    print(f"\n{'='*60}")
    print(f"  ✅ Insérés   : {inserted}")
    print(f"  ⏭  Skippés   : {skipped}")
    print(f"  ❌ Erreurs   : {errors}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
