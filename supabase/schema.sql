-- ============================================
-- StochastiQdata - Schéma Supabase (PostgreSQL)
-- Plateforme de notation de datasets pour actuaires
-- ============================================

-- Extension pour UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- ENUM Types
-- ============================================

-- Sources de datasets
CREATE TYPE dataset_source AS ENUM ('kaggle', 'insee', 'opendata', 'other');

-- Tags métiers actuariels
CREATE TYPE business_tag AS ENUM ('iard', 'sante', 'vie', 'glm', 'pricing', 'reserving', 'fraude', 'machine_learning');

-- Types de modélisation
CREATE TYPE modeling_type AS ENUM ('classification', 'regression', 'time_series', 'clustering', 'survival', 'other');

-- Variables pivots actuarielles
CREATE TYPE pivot_variable AS ENUM ('occurrence_date', 'claim_amount', 'exposure', 'policy_id', 'claim_id');

-- Modèles actuariels suggérés (Best Fit Models)
CREATE TYPE model_type AS ENUM (
    'glm',
    'xgboost',
    'random_forest',
    'chain_ladder',
    'bornhuetter_ferguson',
    'mack',
    'cox',
    'kaplan_meier',
    'neural_network',
    'lightgbm',
    'catboost',
    'other'
);

-- Types de métriques de performance
CREATE TYPE metric_type AS ENUM (
    'gini',
    'rmse',
    'mae',
    'aic',
    'bic',
    'r2',
    'log_loss',
    'auc',
    'accuracy',
    'f1_score',
    'mape',
    'other'
);

-- ============================================
-- Table: datasets
-- ============================================
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    source dataset_source NOT NULL DEFAULT 'other',
    source_url VARCHAR(500),
    tags business_tag[] DEFAULT '{}',

    -- Métadonnées du dataset
    row_count INTEGER,
    column_count INTEGER,
    file_size_mb DECIMAL(10, 2),

    -- Data Freshness & Documentation
    data_updated_at TIMESTAMP WITH TIME ZONE, -- Dernière mise à jour des données source
    data_dictionary_url VARCHAR(500), -- Lien vers le dictionnaire des variables

    -- Modeling & Pivot Variables
    modeling_types modeling_type[] DEFAULT '{}', -- Types de modélisation supportés
    pivot_variables pivot_variable[] DEFAULT '{}', -- Variables pivots disponibles
    best_fit_models model_type[] DEFAULT '{}', -- Modèles suggérés pour ce dataset

    -- Scores agrégés (calculés via trigger)
    avg_utility_score DECIMAL(3, 1) DEFAULT 0,
    avg_cleanliness_score DECIMAL(3, 1) DEFAULT 0,
    avg_documentation_score DECIMAL(3, 1) DEFAULT 0,
    global_score DECIMAL(3, 1) DEFAULT 0,
    review_count INTEGER DEFAULT 0,

    -- Audit
    created_by VARCHAR(255), -- Clerk user_id
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherche et filtrage
CREATE INDEX idx_datasets_source ON datasets(source);
CREATE INDEX idx_datasets_tags ON datasets USING GIN(tags);
CREATE INDEX idx_datasets_modeling_types ON datasets USING GIN(modeling_types);
CREATE INDEX idx_datasets_pivot_variables ON datasets USING GIN(pivot_variables);
CREATE INDEX idx_datasets_best_fit_models ON datasets USING GIN(best_fit_models);
CREATE INDEX idx_datasets_global_score ON datasets(global_score DESC);
CREATE INDEX idx_datasets_created_at ON datasets(created_at DESC);

-- ============================================
-- Table: reviews (évaluations)
-- ============================================
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL, -- Clerk user_id

    -- Scores (0-10)
    utility_score INTEGER NOT NULL CHECK (utility_score >= 0 AND utility_score <= 10),
    cleanliness_score INTEGER NOT NULL CHECK (cleanliness_score >= 0 AND cleanliness_score <= 10),
    documentation_score INTEGER NOT NULL CHECK (documentation_score >= 0 AND documentation_score <= 10),

    -- Commentaire optionnel
    comment TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Contrainte: un user ne peut noter qu'une fois par dataset
    UNIQUE(dataset_id, user_id)
);

-- Index pour les reviews
CREATE INDEX idx_reviews_dataset_id ON reviews(dataset_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);

-- ============================================
-- Table: notebooks (scripts/analyses liés)
-- ============================================

-- Type de plateforme pour les notebooks
CREATE TYPE notebook_platform AS ENUM ('github', 'kaggle', 'colab', 'other');

CREATE TABLE notebooks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL, -- Clerk user_id

    -- Informations du notebook
    title VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    platform notebook_platform NOT NULL DEFAULT 'other',
    description TEXT,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les notebooks
CREATE INDEX idx_notebooks_dataset_id ON notebooks(dataset_id);
CREATE INDEX idx_notebooks_user_id ON notebooks(user_id);
CREATE INDEX idx_notebooks_platform ON notebooks(platform);

-- ============================================
-- Table: benchmarks (scores SOTA de la communauté)
-- ============================================
CREATE TABLE benchmarks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    dataset_id UUID NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL, -- Clerk user_id

    -- Informations du benchmark
    model_type model_type NOT NULL,
    model_name VARCHAR(255), -- Nom personnalisé du modèle (ex: "GLM Poisson avec interactions")
    metric_type metric_type NOT NULL,
    metric_value DECIMAL(10, 6) NOT NULL,

    -- Lien optionnel vers le notebook/code
    notebook_url VARCHAR(500),

    -- Description de la méthodologie
    methodology TEXT,

    -- Validation
    is_verified BOOLEAN DEFAULT FALSE, -- Vérifié par la communauté
    upvotes INTEGER DEFAULT 0,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour les benchmarks
CREATE INDEX idx_benchmarks_dataset_id ON benchmarks(dataset_id);
CREATE INDEX idx_benchmarks_model_type ON benchmarks(model_type);
CREATE INDEX idx_benchmarks_metric_type ON benchmarks(metric_type);
CREATE INDEX idx_benchmarks_metric_value ON benchmarks(metric_value);
CREATE INDEX idx_benchmarks_user_id ON benchmarks(user_id);

-- ============================================
-- Fonction: Calcul du score global
-- ============================================
CREATE OR REPLACE FUNCTION calculate_dataset_scores()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE datasets
    SET
        avg_utility_score = (
            SELECT COALESCE(AVG(utility_score), 0)
            FROM reviews WHERE dataset_id = COALESCE(NEW.dataset_id, OLD.dataset_id)
        ),
        avg_cleanliness_score = (
            SELECT COALESCE(AVG(cleanliness_score), 0)
            FROM reviews WHERE dataset_id = COALESCE(NEW.dataset_id, OLD.dataset_id)
        ),
        avg_documentation_score = (
            SELECT COALESCE(AVG(documentation_score), 0)
            FROM reviews WHERE dataset_id = COALESCE(NEW.dataset_id, OLD.dataset_id)
        ),
        global_score = (
            SELECT COALESCE(
                (AVG(utility_score) * 0.4 + AVG(cleanliness_score) * 0.35 + AVG(documentation_score) * 0.25),
                0
            )
            FROM reviews WHERE dataset_id = COALESCE(NEW.dataset_id, OLD.dataset_id)
        ),
        review_count = (
            SELECT COUNT(*)
            FROM reviews WHERE dataset_id = COALESCE(NEW.dataset_id, OLD.dataset_id)
        ),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.dataset_id, OLD.dataset_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger pour mise à jour automatique des scores
CREATE TRIGGER trigger_update_dataset_scores
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION calculate_dataset_scores();

-- ============================================
-- Row Level Security (RLS)
-- ============================================

-- Activer RLS
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;

-- Politique: Tout le monde peut lire les datasets
CREATE POLICY "Datasets are viewable by everyone"
ON datasets FOR SELECT
USING (true);

-- Politique: Seuls les utilisateurs authentifiés peuvent créer
CREATE POLICY "Authenticated users can create datasets"
ON datasets FOR INSERT
WITH CHECK (created_by IS NOT NULL);

-- Politique: Tout le monde peut lire les reviews
CREATE POLICY "Reviews are viewable by everyone"
ON reviews FOR SELECT
USING (true);

-- Politique: Utilisateurs authentifiés peuvent créer leurs reviews
CREATE POLICY "Users can create their own reviews"
ON reviews FOR INSERT
WITH CHECK (user_id IS NOT NULL);

-- Politique: Utilisateurs peuvent modifier leurs propres reviews
CREATE POLICY "Users can update their own reviews"
ON reviews FOR UPDATE
USING (user_id = current_setting('app.current_user_id', true))
WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- RLS pour notebooks
ALTER TABLE notebooks ENABLE ROW LEVEL SECURITY;

-- Politique: Tout le monde peut lire les notebooks
CREATE POLICY "Notebooks are viewable by everyone"
ON notebooks FOR SELECT
USING (true);

-- Politique: Utilisateurs authentifiés peuvent créer des notebooks
CREATE POLICY "Users can create notebooks"
ON notebooks FOR INSERT
WITH CHECK (user_id IS NOT NULL);

-- Politique: Utilisateurs peuvent modifier leurs propres notebooks
CREATE POLICY "Users can update their own notebooks"
ON notebooks FOR UPDATE
USING (user_id = current_setting('app.current_user_id', true))
WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- Politique: Utilisateurs peuvent supprimer leurs propres notebooks
CREATE POLICY "Users can delete their own notebooks"
ON notebooks FOR DELETE
USING (user_id = current_setting('app.current_user_id', true));

-- RLS pour benchmarks
ALTER TABLE benchmarks ENABLE ROW LEVEL SECURITY;

-- Politique: Tout le monde peut lire les benchmarks
CREATE POLICY "Benchmarks are viewable by everyone"
ON benchmarks FOR SELECT
USING (true);

-- Politique: Utilisateurs authentifiés peuvent créer des benchmarks
CREATE POLICY "Users can create benchmarks"
ON benchmarks FOR INSERT
WITH CHECK (user_id IS NOT NULL);

-- Politique: Utilisateurs peuvent modifier leurs propres benchmarks
CREATE POLICY "Users can update their own benchmarks"
ON benchmarks FOR UPDATE
USING (user_id = current_setting('app.current_user_id', true))
WITH CHECK (user_id = current_setting('app.current_user_id', true));

-- Politique: Utilisateurs peuvent supprimer leurs propres benchmarks
CREATE POLICY "Users can delete their own benchmarks"
ON benchmarks FOR DELETE
USING (user_id = current_setting('app.current_user_id', true));

-- ============================================
-- Données de démonstration
-- ============================================

INSERT INTO datasets (name, description, source, source_url, tags, row_count, column_count, file_size_mb, data_updated_at, data_dictionary_url, modeling_types, pivot_variables, best_fit_models, created_by) VALUES
(
    'French Motor Claims Dataset',
    'Dataset de sinistres automobiles français pour modélisation GLM. Contient les fréquences et coûts moyens par profil.',
    'kaggle',
    'https://www.kaggle.com/datasets/floser/french-motor-claims-datasets',
    ARRAY['iard', 'glm', 'pricing']::business_tag[],
    678013,
    12,
    45.2,
    '2024-06-15T00:00:00Z',
    'https://www.kaggle.com/datasets/floser/french-motor-claims-datasets/data',
    ARRAY['regression']::modeling_type[],
    ARRAY['claim_amount', 'exposure', 'policy_id']::pivot_variable[],
    ARRAY['glm', 'xgboost', 'lightgbm']::model_type[],
    'system'
),
(
    'Données démographiques INSEE 2023',
    'Statistiques démographiques par commune pour segmentation et tarification santé.',
    'insee',
    'https://www.insee.fr/fr/statistiques',
    ARRAY['sante', 'pricing']::business_tag[],
    35000,
    48,
    12.8,
    '2023-12-01T00:00:00Z',
    'https://www.insee.fr/fr/metadonnees/source/serie/s1321',
    ARRAY['classification', 'clustering']::modeling_type[],
    ARRAY[]::pivot_variable[],
    ARRAY['random_forest', 'xgboost']::model_type[],
    'system'
),
(
    'Claims Reserving Triangle Dataset',
    'Triangles de développement pour provisionnement IARD. Méthode Chain-Ladder applicable.',
    'opendata',
    NULL,
    ARRAY['iard', 'reserving']::business_tag[],
    120,
    10,
    0.5,
    '2022-03-10T00:00:00Z',
    NULL,
    ARRAY['time_series', 'regression']::modeling_type[],
    ARRAY['occurrence_date', 'claim_amount']::pivot_variable[],
    ARRAY['chain_ladder', 'bornhuetter_ferguson', 'mack']::model_type[],
    'system'
),
(
    'Health Insurance Cross Sell',
    'Dataset pour prédiction de cross-sell assurance santé vers auto. Idéal pour ML.',
    'kaggle',
    'https://www.kaggle.com/datasets/anmolkumar/health-insurance-cross-sell-prediction',
    ARRAY['sante', 'machine_learning']::business_tag[],
    381109,
    12,
    28.4,
    '2025-01-10T00:00:00Z',
    'https://www.kaggle.com/datasets/anmolkumar/health-insurance-cross-sell-prediction/data',
    ARRAY['classification']::modeling_type[],
    ARRAY['policy_id']::pivot_variable[],
    ARRAY['xgboost', 'lightgbm', 'catboost', 'neural_network']::model_type[],
    'system'
),
(
    'Fraud Detection Insurance Claims',
    'Dataset labellisé pour détection de fraude en assurance auto.',
    'kaggle',
    'https://www.kaggle.com/datasets/buntyshah/auto-insurance-claims-data',
    ARRAY['iard', 'fraude', 'machine_learning']::business_tag[],
    15420,
    33,
    8.2,
    '2024-11-20T00:00:00Z',
    'https://www.kaggle.com/datasets/buntyshah/auto-insurance-claims-data/data',
    ARRAY['classification']::modeling_type[],
    ARRAY['occurrence_date', 'claim_amount', 'claim_id']::pivot_variable[],
    ARRAY['xgboost', 'random_forest', 'neural_network']::model_type[],
    'system'
);

-- Ajouter quelques reviews de démonstration
INSERT INTO reviews (dataset_id, user_id, utility_score, cleanliness_score, documentation_score, comment)
SELECT
    d.id,
    'demo_user_1',
    8,
    7,
    9,
    'Excellent dataset pour débuter avec les GLM. Documentation très complète.'
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

INSERT INTO reviews (dataset_id, user_id, utility_score, cleanliness_score, documentation_score, comment)
SELECT
    d.id,
    'demo_user_2',
    9,
    8,
    7,
    'Très utile pour les modèles de pricing. Quelques valeurs manquantes à traiter.'
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

-- Ajouter quelques notebooks de démonstration
INSERT INTO notebooks (dataset_id, user_id, title, url, platform, description)
SELECT
    d.id,
    'demo_user_1',
    'GLM Pricing avec French Motor Claims',
    'https://www.kaggle.com/code/floser/glm-pricing-french-motor',
    'kaggle',
    'Notebook complet montrant le nettoyage des données et la construction d''un modèle GLM pour le pricing auto.'
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

INSERT INTO notebooks (dataset_id, user_id, title, url, platform, description)
SELECT
    d.id,
    'demo_user_2',
    'Data Cleaning Pipeline',
    'https://github.com/actuary/french-motor-cleaning',
    'github',
    'Script Python pour nettoyer et préparer le dataset French Motor Claims.'
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

-- Ajouter quelques benchmarks de démonstration
INSERT INTO benchmarks (dataset_id, user_id, model_type, model_name, metric_type, metric_value, notebook_url, methodology, is_verified)
SELECT
    d.id,
    'demo_user_1',
    'glm',
    'GLM Poisson avec offset log(exposure)',
    'gini',
    0.3245,
    'https://www.kaggle.com/code/floser/glm-pricing-french-motor',
    'Modèle Poisson pour fréquence avec variables tarifaires classiques. Validation croisée 5-fold.',
    TRUE
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

INSERT INTO benchmarks (dataset_id, user_id, model_type, model_name, metric_type, metric_value, notebook_url, methodology)
SELECT
    d.id,
    'demo_user_2',
    'xgboost',
    'XGBoost Tweedie',
    'gini',
    0.3512,
    'https://github.com/actuary/french-motor-xgb',
    'XGBoost avec loss Tweedie (p=1.5). Hyperparamètres optimisés par Optuna.'
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

INSERT INTO benchmarks (dataset_id, user_id, model_type, model_name, metric_type, metric_value, notebook_url, methodology)
SELECT
    d.id,
    'demo_user_1',
    'glm',
    'GLM Gamma pour coût moyen',
    'rmse',
    1247.32,
    NULL,
    'Modèle Gamma avec link log pour prédiction du coût moyen.'
FROM datasets d WHERE d.name = 'French Motor Claims Dataset';

INSERT INTO benchmarks (dataset_id, user_id, model_type, model_name, metric_type, metric_value, methodology, is_verified)
SELECT
    d.id,
    'demo_user_1',
    'chain_ladder',
    'Chain-Ladder standard',
    'mape',
    4.25,
    'Méthode Chain-Ladder avec facteurs de développement moyens.',
    TRUE
FROM datasets d WHERE d.name = 'Claims Reserving Triangle Dataset';

INSERT INTO benchmarks (dataset_id, user_id, model_type, model_name, metric_type, metric_value, notebook_url, methodology)
SELECT
    d.id,
    'demo_user_2',
    'xgboost',
    'XGBoost Classifier',
    'auc',
    0.8934,
    'https://www.kaggle.com/code/demo/health-crosssell-xgb',
    'Classification binaire avec SMOTE pour équilibrage. AUC calculé sur test set.'
FROM datasets d WHERE d.name = 'Health Insurance Cross Sell';

INSERT INTO benchmarks (dataset_id, user_id, model_type, model_name, metric_type, metric_value, methodology, is_verified)
SELECT
    d.id,
    'demo_user_1',
    'random_forest',
    'Random Forest Fraud Detection',
    'f1_score',
    0.7621,
    'Random Forest avec 500 arbres. Class weight balancé pour gérer le déséquilibre.',
    TRUE
FROM datasets d WHERE d.name = 'Fraud Detection Insurance Claims';
