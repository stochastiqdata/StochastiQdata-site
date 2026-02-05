require('dotenv').config();
const express = require('express');
const axios = require('axios');
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const compression = require('compression');
const winston = require('winston');
const validator = require('validator');

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

// Common data middleware
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
      TAG_LABELS,
      SOURCE_LABELS,
      MODEL_LABELS,
      MODELING_TYPE_LABELS
    });
  } catch (error) {
    logger.error('Dashboard error', { error: error.message, stack: error.stack });
    res.render('pages/dashboard', {
      datasets: [],
      total: 0,
      page: 1,
      totalPages: 0,
      filters: {},
      TAG_LABELS,
      SOURCE_LABELS,
      MODEL_LABELS,
      MODELING_TYPE_LABELS,
      error: 'Impossible de charger les datasets'
    });
  }
});

// Modeling overview
app.get('/modeling', (req, res) => {
  res.render('pages/modelisation', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Alias français pour modeling
app.get('/modelisation', (req, res) => {
  res.render('pages/modelisation', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Modeling specific dataset
app.get('/modeling/:id', async (req, res, next) => {
  try {
    const response = await axios.get(`${API_URL}/datasets/${req.params.id}`);
    res.render('pages/modeling', {
      dataset: response.data,
      TAG_LABELS,
      SOURCE_LABELS,
      MODEL_LABELS
    });
  } catch (error) {
    logger.error('Dataset fetch error', {
      datasetId: req.params.id,
      error: error.message
    });
    next(error);
  }
});

// Profile
app.get('/profile', (req, res) => {
  res.render('pages/profile', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Settings
app.get('/settings', (req, res) => {
  res.render('pages/settings', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Add dataset
app.get('/add-dataset', (req, res) => {
  res.render('pages/add-dataset', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Guide
app.get('/guide', (req, res) => {
  res.render('pages/guide', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// FAQ
app.get('/faq', (req, res) => {
  res.render('pages/faq', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Mission
app.get('/mission', (req, res) => {
  res.render('pages/mission', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

// Legal pages
app.get('/mentions-legales', (req, res) => {
  res.render('pages/mentions-legales', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

app.get('/politique-confidentialite', (req, res) => {
  res.render('pages/politique-confidentialite', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
});

app.get('/cgu', (req, res) => {
  res.render('pages/cgu', { TAG_LABELS, SOURCE_LABELS, MODEL_LABELS });
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

// Create dataset
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
