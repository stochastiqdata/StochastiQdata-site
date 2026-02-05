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
        "https://cdn.jsdelivr.net"
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
        "https://mjqtthaypifkdlaneymx.supabase.co"
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
