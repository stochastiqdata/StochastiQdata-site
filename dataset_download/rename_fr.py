#!/usr/bin/env python3
"""Met à jour les noms des datasets en français dans Supabase."""
import os
from pathlib import Path

env_path = Path(__file__).parent.parent / "backend" / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())

from supabase import create_client
supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

RENAMES = {
    "French Motor MTPL Frequency (freMTPL2freq)":       "Fréquence Sinistres Auto RC France (freMTPL2freq)",
    "French Motor MTPL Severity (freMTPL2sev)":         "Sévérité Sinistres Auto RC France (freMTPL2sev)",
    "Car Insurance Claims":                              "Sinistres Assurance Auto",
    "Vehicle Insurance Cross-Sell (Health → Auto)":     "Vente Croisée Assurance Auto (Santé → Auto)",
    "Auto Insurance Claims Fraud":                      "Fraude Déclarations Sinistres Auto",
    "Car Insurance Claim Prediction":                   "Prédiction Sinistres Assurance Auto",
    "Vehicle Claim Fraud Detection":                    "Détection Fraude Sinistres Véhicule",
    "Travel Insurance Claims":                          "Sinistres Assurance Voyage",
    "Wisconsin Auto Insurance":                         "Assurance Auto Wisconsin",
    "Insurance Customer Churn":                         "Résiliation Clients Assurance",
    "Medical Cost Personal Dataset":                    "Coûts Médicaux Personnels",
    "US Health Insurance Dataset":                      "Assurance Santé USA",
    "Healthcare Insurance Premium Prediction":          "Prédiction Prime Assurance Santé",
    "Diabetes Health Indicators (CDC BRFSS)":           "Indicateurs Santé Diabète (CDC BRFSS)",
    "Health Insurance Customer Dataset":                "Données Clients Assurance Santé",
    "Health Insurance Premium — Smoking Impact":        "Prime Assurance Santé — Impact Tabagisme",
    "Credit Card Fraud Detection (ULB)":                "Détection Fraude Carte Bancaire (ULB)",
    "Bank Account Fraud Dataset — NeurIPS 2022":        "Fraude Ouverture Compte Bancaire — NeurIPS 2022",
    "PaySim Mobile Money Fraud Simulation":             "Simulation Fraude Mobile Money (PaySim)",
    "Insurance Claims Fraud Detection":                 "Détection Fraude Déclarations Assurance",
    "Online Payments Fraud Detection":                  "Détection Fraude Paiements en Ligne",
    "Bank Transaction Anomaly Detection":               "Détection Anomalies Transactions Bancaires",
    "Synthetic Online Payment Fraud":                   "Fraude Paiements en Ligne Synthétique",
    "Credit Risk Dataset":                              "Risque de Crédit",
    "Credit Card Customers Churn":                      "Résiliation Clients Carte de Crédit",
    "Loan Approval Prediction":                         "Prédiction Approbation Prêt",
    "Bank Loan Status Dataset":                         "Statut Prêts Bancaires",
    "Bank Customer Churn Prediction":                   "Prédiction Churn Clients Bancaires",
    "Bank Customer Segmentation":                       "Segmentation Clients Bancaires",
    "SBA Loan Approval (US Small Business)":            "Approbation Prêts PME (SBA USA)",
    "Bank Marketing & Financial Indicators":            "Marketing Bancaire & Indicateurs Financiers",
    "Prosper P2P Loan Data":                            "Données Prêts P2P Prosper",
    "Bank Loan Default Prediction":                     "Prédiction Défaut Prêts Bancaires",
    "Credit Card Spend Patterns":                       "Comportements Dépenses Carte de Crédit",
    "S&P 500 Historical Stock Data":                    "Données Historiques S&P 500",
    "VIX Volatility Index Historical":                  "Indice VIX — Volatilité Historique",
    "Banking Transaction Time Series":                  "Séries Temporelles Transactions Bancaires",
    "Telco Customer Churn":                             "Résiliation Clients Télécom",
    "IBM HR Analytics — Employee Attrition":            "Attrition Employés IBM HR Analytics",
    "California Housing Prices":                        "Prix Immobiliers Californie",
    "Customer Propensity to Purchase":                  "Propension à l'Achat Client",
    "UBI Telematics Driving Data":                      "Données Télématiques Conduite (UBI)",
    "Biological Age & Health Features":                 "Âge Biologique & Indicateurs Santé",
    "Body Fat & Health Indicators":                     "Masse Grasse & Indicateurs de Santé",
}

ok = 0
for old, new in RENAMES.items():
    res = supabase.table("datasets").update({"name": new}).eq("name", old).execute()
    if res.data:
        print(f"✅ {new}")
        ok += 1
    else:
        print(f"⏭  Non trouvé : {old}")

print(f"\n{ok}/{len(RENAMES)} datasets renommés.")
