# 🔒 Corrections de Sécurité URGENTES

## ⚠️ ACTIONS IMMÉDIATES (À FAIRE MAINTENANT)

### 1. Régénérer TOUTES vos clés API 🔴 CRITIQUE

Vos clés actuelles ont été exposées dans ce chat et doivent être régénérées **IMMÉDIATEMENT**.

#### Clerk (Authentification)
1. Aller sur https://dashboard.clerk.com
2. Sélectionner votre projet
3. Aller dans **API Keys**
4. Cliquer sur **Regenerate** pour:
   - Publishable Key
   - Secret Key
5. Copier les nouvelles clés dans `.env` (PAS `.env.example`)

#### Supabase (Base de données)
1. Aller sur https://supabase.com/dashboard
2. Sélectionner votre projet
3. Aller dans **Settings > API**
4. Régénérer:
   - anon/public key
   - service_role key
5. Aller dans **Settings > Database**
6. Régénérer JWT Secret
7. Copier les nouvelles clés dans `.env`

### 2. Vérifier que .gitignore est en place ✅

Le fichier `.gitignore` a été créé à la racine du projet.

**SI vous avez déjà un repo Git:**
```bash
# Supprimer les fichiers .env du tracking Git
git rm --cached frontend/.env
git rm --cached backend/.env
git commit -m "Remove .env files from tracking"

# Vérifier qu'ils sont bien ignorés
git status
# Ne devrait PAS montrer les fichiers .env
```

### 3. Créer vos fichiers .env réels (NON COMMITÉES)

```bash
# Frontend
cp frontend/.env.example frontend/.env
# Puis éditer frontend/.env avec VOS clés

# Backend
cp backend/.env.example backend/.env
# Puis éditer backend/.env avec VOS clés
```

---

## 📦 Installation des dépendances de sécurité

```bash
cd frontend

# Installer les packages de sécurité
npm install --save helmet express-rate-limit validator winston compression

# Ou avec yarn
yarn add helmet express-rate-limit validator winston compression
```

---

## 🛡️ Fichier de configuration sécurité

Créer `frontend/config/security.js`:

```javascript
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');

// Rate limiting configuration
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requêtes max par IP
  message: 'Trop de requêtes depuis cette IP, veuillez réessayer plus tard.',
  standardHeaders: true,
  legacyHeaders: false,
});

// Rate limiting plus strict pour l'authentification
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 5 tentatives max
  skipSuccessfulRequests: true,
});

// Configuration Helmet (headers de sécurité)
const helmetConfig = helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: [
        "'self'",
        "'unsafe-inline'", // Nécessaire pour EJS inline scripts
        "https://cdn.jsdelivr.net",
        "https://*.clerk.accounts.dev",
        "https://*.clerk.com"
      ],
      styleSrc: [
        "'self'",
        "'unsafe-inline'",
        "https://fonts.googleapis.com"
      ],
      fontSrc: [
        "'self'",
        "https://fonts.gstatic.com"
      ],
      imgSrc: ["'self'", "data:", "https:", "blob:"],
      connectSrc: [
        "'self'",
        "https://mjqtthaypifkdlaneymx.supabase.co",
        "https://*.clerk.accounts.dev",
        "https://*.clerk.com"
      ],
      frameSrc: [
        "https://*.clerk.accounts.dev",
        "https://*.clerk.com"
      ]
    }
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  },
  noSniff: true,
  xssFilter: true,
  hidePoweredBy: true
});

module.exports = {
  limiter,
  authLimiter,
  helmetConfig
};
```

---

## 🔧 Modifications à apporter au server.js

### 1. Imports en haut du fichier

```javascript
require('dotenv').config();
const express = require('express');
const axios = require('axios');
const path = require('path');
const expressLayouts = require('express-ejs-layouts');
const { clerkMiddleware, getAuth } = require('@clerk/express');
const compression = require('compression');
const winston = require('winston');
const validator = require('validator');

// Importer la config de sécurité
const { limiter, authLimiter, helmetConfig } = require('./config/security');

const app = express();
```

### 2. Configuration du logger

```javascript
// Logger Winston
const logger = winston.createLogger({
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' })
  ]
});

// Ajouter console en développement
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.simple()
  }));
}

// Remplacer tous les console.log par logger
// console.error('Error:', error) → logger.error('Error', { error })
```

### 3. Middlewares de sécurité (AVANT les routes)

```javascript
// Sécurité headers
app.use(helmetConfig);

// Compression
app.use(compression());

// Rate limiting général
app.use('/api/', limiter);

// HTTPS redirect en production
if (process.env.NODE_ENV === 'production') {
  app.use((req, res, next) => {
    if (req.header('x-forwarded-proto') !== 'https') {
      res.redirect(`https://${req.header('host')}${req.url}`);
    } else {
      next();
    }
  });
}

// Supprimer console.log en production
if (process.env.NODE_ENV === 'production') {
  console.log = () => {};
  console.debug = () => {};
  console.info = () => {};
}
```

### 4. Validation de la recherche

```javascript
// Route de recherche avec validation
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

    // Limite de longueur
    if (sanitizedQuery.length > 100) {
      return res.status(400).json({
        error: 'Requête trop longue (max 100 caractères)'
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
    logger.error('Search error', {
      error: error.message,
      query: req.query.q
    });
    res.status(500).json({ datasets: [], total: 0 });
  }
});
```

### 5. Gestion globale des erreurs (À LA FIN, après toutes les routes)

```javascript
// 404 Handler
app.use((req, res) => {
  res.status(404).render('pages/error', {
    TAG_LABELS,
    SOURCE_LABELS,
    MODEL_LABELS,
    statusCode: 404,
    message: 'Page non trouvée'
  });
});

// Global Error Handler
app.use((err, req, res, next) => {
  logger.error('Unhandled error', {
    error: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method
  });

  const statusCode = err.statusCode || 500;
  const message = process.env.NODE_ENV === 'production'
    ? 'Une erreur est survenue'
    : err.message;

  res.status(statusCode).render('pages/error', {
    TAG_LABELS,
    SOURCE_LABELS,
    MODEL_LABELS,
    statusCode,
    message
  });
});

// Unhandled Promise Rejections
process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled Rejection', { reason, promise });
});

// Unhandled Exceptions
process.on('uncaughtException', (error) => {
  logger.error('Uncaught Exception', { error: error.message, stack: error.stack });
  process.exit(1);
});
```

---

## 🚀 Configuration pour la production

### Variables d'environnement Vercel/Netlify/Railway

```env
NODE_ENV=production
PORT=3000
API_URL=https://api.votredomaine.com/api/v1
CLERK_PUBLISHABLE_KEY=pk_live_xxxxxxxxxx
CLERK_SECRET_KEY=sk_live_xxxxxxxxxx
SUPABASE_URL=https://mjqtthaypifkdlaneymx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI... (NOUVELLE CLÉ)
```

### Build commands

```json
{
  "scripts": {
    "dev": "concurrently \"nodemon server.js\" \"npx tailwindcss -i ./src/input.css -o ./public/css/output.css --watch\"",
    "build": "npx tailwindcss -i ./src/input.css -o ./public/css/output.css --minify",
    "start": "NODE_ENV=production node server.js",
    "prod": "npm run build && npm start"
  }
}
```

---

## ✅ Checklist de déploiement

Avant de déployer en production:

- [ ] Toutes les clés API ont été régénérées
- [ ] Les fichiers .env ne sont PAS dans Git
- [ ] .gitignore est configuré correctement
- [ ] helmet.js est installé et configuré
- [ ] Rate limiting est activé
- [ ] Logger Winston est configuré
- [ ] Validation des entrées implémentée
- [ ] Gestion d'erreurs globale ajoutée
- [ ] HTTPS est forcé
- [ ] Console.log supprimés en production
- [ ] CSS est compilé et minifié (`npm run build`)
- [ ] NODE_ENV=production est défini
- [ ] Toutes les URLs sont correctes (pas de localhost)
- [ ] Tests de bout en bout effectués

---

## 🆘 En cas de problème

Si vous avez besoin d'aide:
1. Vérifier les logs: `logs/error.log` et `logs/combined.log`
2. Activer le mode debug: `NODE_ENV=development`
3. Tester localement avant de déployer

**IMPORTANT:** Ne partagez JAMAIS vos vraies clés API dans un chat, forum ou repo public.
