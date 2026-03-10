require('dotenv').config();
const express = require('express');
const axios = require('axios');
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const compression = require('compression');
const winston = require('winston');
const validator = require('validator');
const multer = require('multer');
const FormData = require('form-data');

// Import security configuration
const { limiter, helmetConfig } = require('./config/security');

const app = express();
const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';
const NODE_ENV = process.env.NODE_ENV || 'development';
const IS_PRODUCTION = NODE_ENV === 'production';

// Configure Axios defaults
axios.defaults.timeout = 10000; // 10 seconds timeout

// ============================================
// LOGGER CONFIGURATION
// ============================================
const logger = winston.createLogger({
  level: IS_PRODUCTION ? 'info' : 'debug',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: []
});

// Add file transports only in development (Vercel filesystem is read-only)
if (!IS_PRODUCTION) {
  logger.add(new winston.transports.File({ filename: 'logs/error.log', level: 'error' }));
  logger.add(new winston.transports.File({ filename: 'logs/combined.log' }));
}

// Add console transport (works in both dev and production)
logger.add(new winston.transports.Console({
  format: winston.format.combine(
    winston.format.colorize(),
    winston.format.simple()
  )
}));

// Suppress console.log in production
if (IS_PRODUCTION) {
  console.log = () => {};
  console.debug = () => {};
  console.info = () => {};
}

// ============================================
// SECURITY MIDDLEWARES
// ============================================
// Helmet for security headers
app.use(helmetConfig);

// Compression
app.use(compression());

// HTTPS redirect in production
if (IS_PRODUCTION) {
  app.use((req, res, next) => {
    if (req.header('x-forwarded-proto') !== 'https') {
      res.redirect(`https://${req.header('host')}${req.url}`);
    } else {
      next();
    }
  });
}

// ============================================
// EJS CONFIGURATION
// ============================================
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(expressLayouts);
app.set('layout', 'layout');

// ============================================
// BASIC MIDDLEWARES
// ============================================
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Static files with cache headers
app.use(express.static(path.join(__dirname, 'public'), {
  maxAge: IS_PRODUCTION ? '1y' : 0,
  etag: true
}));

// Favicon.ico — sert le logo PNG comme favicon (pour Google Search)
app.get('/favicon.ico', (_req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'images', 'logo.png'));
});

// Common data middleware
const SITE_URL = process.env.SITE_URL || 'https://www.stochastiqdata.com';
app.use((req, res, next) => {
  res.locals.currentPath = req.path;
  res.locals.currentDate = new Date().toLocaleDateString('fr-FR', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  res.locals.currentTime = new Date().toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit'
  });
  // SEO defaults (overridable per route)
  res.locals.siteUrl = SITE_URL;
  res.locals.pageTitle = null;
  res.locals.pageDescription = null;
  res.locals.canonicalPath = null;
  res.locals.ogType = 'website';
  res.locals.noIndex = false;
  res.locals.jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'StochastiQdata',
    url: SITE_URL,
    description: 'Plateforme de référence pour les data scientists, data analysts, data engineers, ML engineers et BI analysts travaillant avec des données d\'assurance et de banque.',
    potentialAction: {
      '@type': 'SearchAction',
      target: { '@type': 'EntryPoint', urlTemplate: SITE_URL + '/?search={search_term_string}' },
      'query-input': 'required name=search_term_string'
    }
  };
  next();
});

// ============================================
// CONSTANTS
// ============================================
const TAG_LABELS = {
  iard: 'IARD',
  sante: 'Santé',
  vie: 'Vie',
  glm: 'GLM',
  pricing: 'Pricing',
  reserving: 'Reserving',
  fraude: 'Fraude',
  machine_learning: 'ML'
};

const SOURCE_LABELS = {
  kaggle: 'Kaggle',
  insee: 'INSEE',
  opendata: 'OpenData',
  other: 'Autre'
};

const MODEL_LABELS = {
  xgboost: 'XGBoost',
  random_forest: 'Random Forest',
  glm: 'GLM',
  neural_network: 'Neural Network',
  gradient_boosting: 'Gradient Boosting',
  linear_regression: 'Linear Regression',
  logistic_regression: 'Logistic Regression',
  svm: 'SVM',
  decision_tree: 'Decision Tree',
  other: 'Other'
};

const MODELING_TYPE_LABELS = {
  classification: 'Classification',
  regression: 'Régression',
  time_series: 'Séries temporelles',
  clustering: 'Clustering',
  survival: 'Survie',
  other: 'Autre'
};

// ============================================
// PAGE ROUTES
// ============================================

// Dashboard
app.get('/', async (req, res, next) => {
  try {
    const { source, tags, search, sortBy = 'created_at', page = 1, modelingTypes } = req.query;

    const params = new URLSearchParams();
    params.append('page', page);
    params.append('page_size', '12');
    params.append('sort_by', sortBy);
    params.append('sort_order', 'desc');

    if (source) params.append('source', source);
    if (tags) params.append('tags', tags);
    if (search) params.append('search', search);
    if (modelingTypes) params.append('modeling_types', modelingTypes);

    const response = await axios.get(`${API_URL}/datasets?${params.toString()}`);

    res.render('pages/dashboard', {
      datasets: response.data.datasets || [],
      total: response.data.total || 0,
      page: parseInt(page),
      totalPages: Math.ceil((response.data.total || 0) / 12),
      filters: { source, tags, search, sortBy, modelingTypes },
      TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, MODELING_TYPE_LABELS,
      pageTitle: 'Datasets pour Data Scientists, Analysts & ML Engineers',
      pageDescription: 'Datasets qualifiés pour la data science en assurance et en banque : tarification, fraude, crédit, provisionnement, mortalité. Pour data scientists, analysts, ML engineers et BI.',
    });
  } catch (error) {
    logger.error('Dashboard error', { error: error.message, stack: error.stack });
    res.render('pages/dashboard', {
      datasets: [], total: 0, page: 1, totalPages: 0, filters: {},
      TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, MODELING_TYPE_LABELS,
      error: 'Impossible de charger les datasets',
      pageTitle: 'Datasets pour Data Scientists, Analysts & ML Engineers',
      pageDescription: 'Plateforme de datasets assurance et banque pour data scientists, analysts, ML engineers et BI analysts.',
    });
  }
});

// Modeling overview
app.get('/modeling', (req, res) => {
  res.render('pages/modelisation', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Modélisation & Machine Learning',
    pageDescription: 'Workflows de modélisation pour l\'assurance et la banque : GLM, XGBoost, réseaux de neurones, séries temporelles. Benchmarks et comparatifs pour data scientists, ML engineers et analystes.',
  });
});

// Alias français pour modeling
app.get('/modelisation', (req, res) => {
  res.render('pages/modelisation', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Modélisation & Machine Learning',
    pageDescription: 'Workflows de modélisation pour l\'assurance et la banque : GLM, XGBoost, réseaux de neurones, séries temporelles. Benchmarks et comparatifs pour data scientists, ML engineers et analystes.',
    canonicalPath: '/modeling',
  });
});

// Comparateur de datasets
app.get('/compare', async (req, res) => {
  const { a, b } = req.query;
  let datasetA = null, datasetB = null, allDatasets = [];
  try {
    const listResponse = await axios.get(`${API_URL}/datasets?limit=50`);
    allDatasets = listResponse.data.datasets || [];
    if (a) {
      const resA = await axios.get(`${API_URL}/datasets/${a}`);
      datasetA = resA.data;
    }
    if (b) {
      const resB = await axios.get(`${API_URL}/datasets/${b}`);
      datasetB = resB.data;
    }
  } catch (e) {
    logger.error('Compare fetch error', { error: e.message });
  }
  res.render('pages/compare', { datasetA, datasetB, allDatasets, TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Route de prévisualisation avec données mock (dev/test)
app.get('/modeling/preview/:type', (req, res) => {
  const type = req.params.type;
  const mockDatasets = {
    iard: { name: 'freMTPL2freq', description: 'French Motor Third-Party Liability — fréquence des sinistres auto.', global_score: 87, source: 'cas', tags: ['iard', 'pricing'], best_fit_models: ['glm_poisson', 'xgboost'], row_count: 678013, column_count: 12, file_size_mb: 45, review_count: 3, source_url: 'https://dutangc.github.io/CASdatasets/', data_dictionary_url: null },
    reserving: { name: 'CAS Loss Reserving DB', description: 'NAIC Schedule P — triangles de développement pour le provisionnement.', global_score: 82, source: 'cas', tags: ['reserving'], best_fit_models: ['chain_ladder', 'bornhuetter_ferguson'], row_count: 200, column_count: 8, file_size_mb: 2, review_count: 1, source_url: null, data_dictionary_url: null },
    vie: { name: 'HMD Human Mortality', description: 'Tables de mortalité historiques de 40+ pays depuis le 19ème siècle.', global_score: 95, source: 'insee', tags: ['vie'], best_fit_models: ['kaplan_meier', 'cox'], row_count: 50000, column_count: 6, file_size_mb: 12, review_count: 2, source_url: null, data_dictionary_url: null },
    fraude: { name: 'Vehicle Claim Fraud', description: 'Détection de fraude dans les sinistres automobiles.', global_score: 74, source: 'kaggle', tags: ['fraude', 'iard'], best_fit_models: ['xgboost', 'logistic'], row_count: 15420, column_count: 33, file_size_mb: 8, review_count: 5, source_url: null, data_dictionary_url: null },
    sante: { name: 'MEPS Health Expenditure', description: 'Dépenses de santé individuelles aux États-Unis — Medical Expenditure Panel Survey.', global_score: 79, source: 'soa', tags: ['sante'], best_fit_models: ['tweedie', 'xgboost'], row_count: 31880, column_count: 22, file_size_mb: 18, review_count: 0, source_url: null, data_dictionary_url: null }
  };
  const dataset = mockDatasets[type] || mockDatasets.iard;
  const mockNotebooks = {
    iard: [
      { title: 'GLM Poisson — Tarification fréquence freMTPL2freq', platform: 'Kaggle', author: 'floser', url: 'https://www.kaggle.com/code/floser/glm-neural-nets-and-xgboost-for-insurance-pricing' },
      { title: 'Tweedie Regression — Pure Premium Insurance Claims', platform: 'Kaggle', author: 'captcalculator', url: 'https://www.kaggle.com/code/captcalculator/tweedie-regression-insurance-claims' },
      { title: 'XGBoost vs GLM — French Motor Dataset Benchmark', platform: 'GitHub', author: 'actuarial-data-science', url: 'https://github.com/actuarial-data-science/Tutorials/tree/master/2%20-%20French%20Motor%20Third-Party%20Liability' }
    ],
    reserving: [
      { title: 'Chain-Ladder Reserving with CAS Triangle Data', platform: 'GitHub', author: 'mages', url: 'https://github.com/mages/ChainLadder' },
      { title: 'Bornhuetter-Ferguson — Loss Reserve Estimation', platform: 'Kaggle', author: 'reserving_actuaire', url: 'https://www.kaggle.com/code/stochastiqdata/bornhuetter-ferguson-reserve' }
    ],
    vie: [
      { title: 'Kaplan-Meier & Cox — Human Mortality Database', platform: 'GitHub', author: 'lifelines', url: 'https://github.com/CamDavidsonPilon/lifelines' },
      { title: 'Lee-Carter Mortality Forecast — HMD Data', platform: 'Kaggle', author: 'mortalitymodels', url: 'https://www.kaggle.com/code/stochastiqdata/lee-carter-mortality' }
    ],
    fraude: [
      { title: 'Fraud Detection — XGBoost + SHAP Explainability', platform: 'Kaggle', author: 'anokas', url: 'https://www.kaggle.com/code/anokas/fraud-detection-eda' },
      { title: 'Logistic Regression Baseline — Vehicle Claim Fraud', platform: 'Kaggle', author: 'fraud_detect', url: 'https://www.kaggle.com/code/stochastiqdata/logistic-fraud-baseline' }
    ],
    sante: [
      { title: 'Tweedie GLM — Health Expenditure Prediction (MEPS)', platform: 'GitHub', author: 'sklearn-examples', url: 'https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html' }
    ]
  };
  const notebooks = mockNotebooks[type] || mockNotebooks.iard;
  res.render('pages/modeling', { dataset, notebooks, TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Modeling specific dataset
app.get('/modeling/:id', async (req, res, next) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}`);
    const ds = response.data;
    const dsTitle = ds.name || 'Dataset';
    const dsTags = (ds.tags || []).join(', ');
    res.render('pages/modeling', {
      dataset: ds,
      notebooks: [],
      TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
      pageTitle: dsTitle,
      pageDescription: ds.description ? ds.description.slice(0, 160) : `Explorez et modélisez le dataset ${dsTitle} — ${dsTags}. Score qualité, aperçu des données, benchmarks et notebooks.`,
      ogType: 'article',
      jsonLd: {
        '@context': 'https://schema.org',
        '@type': 'Dataset',
        name: dsTitle,
        description: ds.description || '',
        url: `${SITE_URL}/modeling/${ds.id}`,
        keywords: dsTags,
        creator: { '@type': 'Organization', name: 'StochastiQdata', url: SITE_URL },
        ...(ds.row_count && { size: `${ds.row_count} lignes` }),
        ...(ds.license && { license: ds.license }),
      },
    });
  } catch (error) {
    logger.error('Dataset fetch error', { datasetId: req.params.id, error: error.message });
    next(error);
  }
});

// Dataset documentation page
app.get('/modeling/:id/docs', async (req, res, next) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}`);
    const ds = response.data;
    res.render('pages/dataset-docs', {
      dataset: ds,
      TAG_LABELS, SOURCE_LABELS,
      pageTitle: `Documentation — ${ds.name || 'Dataset'}`,
      pageDescription: `Documentation complète du dataset ${ds.name} : dictionnaire des variables, guide d'utilisation, citation et licence.`,
    });
  } catch (error) {
    next(error);
  }
});

// Model detail page
app.get('/models/:id', async (req, res, next) => {
  try {
    const modelRes = await axios.get(`${API_URL}/models/${req.params.id}`);
    const model = modelRes.data;

    let dataset = null;
    try {
      const dsRes = await axios.get(`${API_URL}/datasets/${model.dataset_id}`);
      dataset = dsRes.data;
    } catch {}

    let author = null;
    if (model.created_by && model.created_by !== 'anonymous') {
      try {
        const profileRes = await axios.get(`${API_URL}/profiles/${model.created_by}`);
        author = profileRes.data;
      } catch {}
    }

    res.render('pages/model', {
      model, dataset, author, TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
      pageTitle: model.name || 'Modèle',
      pageDescription: model.description ? model.description.slice(0, 160) : `Modèle ${model.name} — performances, métriques et code source.`,
      ogType: 'article',
    });
  } catch (error) {
    logger.error('Model fetch error', { modelId: req.params.id, error: error.message });
    next(error);
  }
});

// Public user profile page
app.get('/users/:id', async (req, res, next) => {
  try {
    const profileRes = await axios.get(`${API_URL}/profiles/${req.params.id}`);
    const profile = profileRes.data;
    res.render('pages/user-profile', { profile, TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
  } catch (error) {
    if (error.response?.status === 404) {
      return res.status(404).render('pages/error', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, statusCode: 404, message: 'Profil introuvable.' });
    }
    next(error);
  }
});

// Notebooks hub
app.get('/notebooks', async (req, res) => {
  let notebooks = [];
  try {
    const response = await axios.get(`${API_URL}/notebooks?limit=50`);
    notebooks = response.data || [];
  } catch (e) {
    logger.error('Notebooks fetch error', { error: e.message });
  }
  res.render('pages/notebooks', {
    notebooks, TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Notebooks & Tutoriels',
    pageDescription: 'Notebooks Jupyter et tutoriels de modélisation pour l\'assurance et la banque : tarification GLM, détection de fraude, provisionnement, machine learning.',
  });
});

// Profile
app.get('/profile', (req, res) => {
  res.render('pages/profile', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, noIndex: true });
});

// Settings
app.get('/settings', (req, res) => {
  res.render('pages/settings', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, noIndex: true });
});

// Add dataset
app.get('/add-dataset', (req, res) => {
  res.render('pages/add-dataset', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Proposer un Dataset',
    pageDescription: 'Partagez un dataset assurance ou bancaire avec la communauté des professionnels de la donnée.',
  });
});

// Guide
app.get('/guide', (req, res) => {
  res.render('pages/guide', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Guide d\'utilisation',
    pageDescription: 'Comment utiliser StochastiQdata : explorer les datasets, lire les scores qualité, télécharger et contribuer à la communauté.',
  });
});

// FAQ
app.get('/faq', (req, res) => {
  res.render('pages/faq', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'FAQ',
    pageDescription: 'Réponses aux questions fréquentes sur StochastiQdata : datasets disponibles, méthodologie de scoring, profils métier et contribution.',
  });
});

// Mission
app.get('/mission', (req, res) => {
  res.render('pages/mission', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Notre Mission',
    pageDescription: 'StochastiQdata : rendre les données de l\'assurance et de la banque accessibles et utilisables par tous les professionnels de la donnée.',
  });
});

app.get('/docs', (_req, res) => {
  res.render('pages/docs', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Documentation',
    pageDescription: 'Documentation, guides techniques et ressources pour les professionnels de la donnée en assurance et en banque — modèles actuariels, machine learning, analyse de risque.',
  });
});

app.get('/communaute', (_req, res) => {
  res.render('pages/communaute', {
    TAG_LABELS, SOURCE_LABELS, MODEL_LABELS,
    pageTitle: 'Communauté',
    pageDescription: 'Articles, recherches, défis et ressources partagés par la communauté StochastiQdata — professionnels de la donnée en assurance et en banque.',
  });
});

// Legal pages
app.get('/mentions-legales', (req, res) => {
  res.render('pages/mentions-legales', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, pageTitle: 'Mentions Légales', noIndex: true });
});

app.get('/politique-confidentialite', (req, res) => {
  res.render('pages/politique-confidentialite', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, pageTitle: 'Politique de Confidentialité', noIndex: true });
});

app.get('/cgu', (req, res) => {
  res.render('pages/cgu', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS, pageTitle: 'Conditions Générales d\'Utilisation', noIndex: true });
});

// Sitemap XML dynamique
app.get('/sitemap.xml', async (_req, res) => {
  const staticPages = [
    { path: '/', priority: '1.0', changefreq: 'daily' },
    { path: '/modeling', priority: '0.9', changefreq: 'weekly' },
    { path: '/notebooks', priority: '0.8', changefreq: 'weekly' },
    { path: '/compare', priority: '0.7', changefreq: 'monthly' },
    { path: '/guide', priority: '0.6', changefreq: 'monthly' },
    { path: '/faq', priority: '0.6', changefreq: 'monthly' },
    { path: '/mission', priority: '0.5', changefreq: 'monthly' },
  ];

  let datasetUrls = [];
  try {
    const response = await axios.get(`${API_URL}/datasets?page_size=200&sort_by=created_at`);
    const datasets = response.data.datasets || [];
    datasetUrls = datasets.map(ds => ({
      path: `/modeling/${ds.id}`,
      priority: '0.8',
      changefreq: 'weekly',
      lastmod: ds.updated_at ? ds.updated_at.slice(0, 10) : undefined,
    }));
  } catch (e) {
    logger.error('Sitemap datasets fetch error', { error: e.message });
  }

  const allUrls = [...staticPages, ...datasetUrls];
  const today = new Date().toISOString().slice(0, 10);

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${allUrls.map(u => `  <url>
    <loc>${SITE_URL}${u.path}</loc>
    <lastmod>${u.lastmod || today}</lastmod>
    <changefreq>${u.changefreq}</changefreq>
    <priority>${u.priority}</priority>
  </url>`).join('\n')}
</urlset>`;

  res.header('Content-Type', 'application/xml');
  res.send(xml);
});

// ============================================
// API ROUTES WITH VALIDATION
// ============================================

// Search with rate limiting and validation
app.get('/api/search', limiter, async (req, res) => {
  try {
    const { q } = req.query;

    // Validation
    if (!q || typeof q !== 'string') {
      return res.status(400).json({
        error: 'Requête de recherche invalide'
      });
    }

    // Sanitization
    const sanitizedQuery = validator.escape(q.trim());

    // Length limit
    if (sanitizedQuery.length > 100) {
      return res.status(400).json({
        error: 'Requête trop longue (max 100 caractères)'
      });
    }

    if (sanitizedQuery.length < 2) {
      return res.status(400).json({
        error: 'Requête trop courte (min 2 caractères)'
      });
    }

    const response = await axios.get(`${API_URL}/datasets`, {
      params: {
        search: sanitizedQuery,
        page_size: 5
      }
    });

    res.json(response.data);
  } catch (error) {
    logger.error('Search error', { error: error.message, query: req.query.q });
    res.status(500).json({ datasets: [], total: 0 });
  }
});

// Datasets similaires
app.get('/api/datasets/:id/similar', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}/similar`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors de la recherche de datasets similaires'
    });
  }
});

// Matrice de corrélation (timeout long — calcul sur fichier complet + cache)
app.get('/api/datasets/:id/correlations', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}/correlations`, { timeout: 90000 });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors du calcul des corrélations'
    });
  }
});

// Track download + retourne file_url
app.post('/api/datasets/:id/download', async (req, res) => {
  try {
    const response = await axios.post(`${API_URL}/datasets/${req.params.id}/download`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors du téléchargement'
    });
  }
});

// Stats dataset (timeout long — calcul sur fichier complet + cache)
app.get('/api/datasets/:id/stats', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}/stats`, { timeout: 90000 });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors du calcul des statistiques'
    });
  }
});

// Preview dataset (Range request — rapide)
app.get('/api/datasets/:id/preview', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}/preview`, { timeout: 30000 });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors du chargement du preview'
    });
  }
});

// Models API proxies
app.get('/api/models', async (req, res) => {
  try {
    const params = new URLSearchParams();
    if (req.query.dataset_id) params.append('dataset_id', req.query.dataset_id);
    const response = await axios.get(`${API_URL}/models?${params.toString()}`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors du chargement des modèles'
    });
  }
});

app.get('/api/models/:id', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/models/${req.params.id}`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Modèle non trouvé'
    });
  }
});

app.post('/api/models', limiter, async (req, res) => {
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (req.headers.authorization) headers['Authorization'] = req.headers.authorization;
    const response = await axios.post(`${API_URL}/models`, req.body, { headers });
    res.status(201).json(response.data);
  } catch (error) {
    logger.error('Model creation error', { error: error.response?.data || error.message });
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors de la création du modèle'
    });
  }
});

app.delete('/api/models/:id', async (req, res) => {
  try {
    const headers = {};
    if (req.headers.authorization) headers['Authorization'] = req.headers.authorization;
    await axios.delete(`${API_URL}/models/${req.params.id}`, { headers });
    res.status(204).send();
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors de la suppression du modèle'
    });
  }
});

// Upload fichier modèle → proxy vers FastAPI (multipart)
const uploadModel = multer({ storage: multer.memoryStorage(), limits: { fileSize: 210 * 1024 * 1024 } });

app.post('/api/models/:id/upload-file', uploadModel.single('file'), async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ detail: 'Aucun fichier fourni.' });
    const form = new FormData();
    form.append('file', new Blob([req.file.buffer], { type: req.file.mimetype }), req.file.originalname);
    const headers = { ...form.headers };
    if (req.headers.authorization) headers['Authorization'] = req.headers.authorization;
    const response = await axios.post(`${API_URL}/models/${req.params.id}/upload-file`, form, { headers });
    res.json(response.data);
  } catch (error) {
    logger.error('Model file upload error', { error: error.response?.data || error.message });
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur upload fichier modèle'
    });
  }
});

// Profiles API proxies
app.get('/api/profiles/:id', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/profiles/${req.params.id}`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Profil non trouvé'
    });
  }
});

app.get('/api/profiles/:id/models', async (req, res) => {
  try {
    const response = await axios.get(`${API_URL}/profiles/${req.params.id}/models`);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json([]);
  }
});

app.put('/api/profiles/me', async (req, res) => {
  try {
    const headers = { 'Content-Type': 'application/json' };
    if (req.headers.authorization) headers['Authorization'] = req.headers.authorization;
    const response = await axios.put(`${API_URL}/profiles/me`, req.body, { headers });
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur mise à jour profil'
    });
  }
});

// Create dataset
// Upload fichier dataset → proxy vers FastAPI (multipart)
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 52 * 1024 * 1024 } });

app.post('/api/datasets/:id/upload-file', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ detail: 'Aucun fichier fourni.' });
    }

    const form = new FormData();
    form.append('file', req.file.buffer, {
      filename: req.file.originalname,
      contentType: req.file.mimetype,
    });

    const headers = { ...form.getHeaders() };
    if (req.headers.authorization) {
      headers['Authorization'] = req.headers.authorization;
    }

    const response = await axios.post(
      `${API_URL}/datasets/${req.params.id}/upload-file`,
      form,
      { headers, maxBodyLength: Infinity }
    );
    res.json(response.data);
  } catch (error) {
    logger.error('Dataset file upload error', { error: error.response?.data || error.message });
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || "Erreur lors de l'upload du fichier"
    });
  }
});

app.post('/api/datasets', limiter, async (req, res) => {
  try {
    const headers = {
      'Content-Type': 'application/json'
    };

    if (req.headers.authorization) {
      headers['Authorization'] = req.headers.authorization;
    }

    const response = await axios.post(`${API_URL}/datasets`, req.body, { headers });
    res.status(201).json(response.data);
  } catch (error) {
    logger.error('Dataset creation error', {
      error: error.response?.data || error.message
    });
    res.status(error.response?.status || 500).json({
      detail: error.response?.data?.detail || 'Erreur lors de la création du dataset'
    });
  }
});

// ============================================
// ERROR HANDLERS
// ============================================

// 404 Handler
app.use((req, res) => {
  res.status(404).render('pages/error', {
    TAG_LABELS,
    SOURCE_LABELS,
    MODEL_LABELS,
    statusCode: 404,
    message: 'La page que vous recherchez n\'existe pas.'
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  const statusCode = err.statusCode || 500;

  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    statusCode
  });

  const message = IS_PRODUCTION
    ? 'Une erreur est survenue. Notre équipe a été notifiée.'
    : err.message;

  res.status(statusCode).render('pages/error', {
    TAG_LABELS,
    SOURCE_LABELS,
    MODEL_LABELS,
    statusCode,
    message
  });
});

// ============================================
// PROCESS ERROR HANDLERS
// ============================================

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', {
    reason: reason instanceof Error ? reason.message : reason,
    stack: reason instanceof Error ? reason.stack : undefined
  });
});

process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', {
    error: error.message,
    stack: error.stack
  });

  // Give time for logging before exit
  setTimeout(() => {
    process.exit(1);
  }, 1000);
});

// ============================================
// START SERVER
// ============================================

app.listen(PORT, () => {
  logger.info(`Frontend server started`, {
    port: PORT,
    environment: NODE_ENV,
    apiUrl: API_URL
  });

  if (!IS_PRODUCTION) {
    console.log(`\n🚀 Frontend running on http://localhost:${PORT}`);
    console.log(`📡 API URL: ${API_URL}\n`);
  }
});
