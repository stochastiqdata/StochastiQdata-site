# 📦 Installation et Configuration - StochastiQdata

## ✅ Ce qui a été fait automatiquement

### 1. Fichiers créés
- ✅ `.gitignore` - Protection des fichiers sensibles
- ✅ `frontend/config/security.js` - Configuration de sécurité
- ✅ `frontend/views/pages/error.ejs` - Page d'erreur 404/500
- ✅ `SECURITY_FIXES.md` - Guide de sécurité complet
- ✅ `PRODUCTION_CHECKLIST.md` - Checklist complète

### 2. Code amélioré
- ✅ `frontend/package.json` - Dépendances de sécurité ajoutées
- ✅ `frontend/server.js` - Complètement sécurisé avec :
  - Helmet pour headers de sécurité
  - Rate limiting sur toutes les routes API
  - Logger Winston configuré
  - Validation des entrées utilisateur
  - Gestion d'erreurs complète
  - Console.log supprimés en production
  - Routes standardisées
- ✅ `frontend/public/js/auth.js` - Sauvegardé (Supabase Auth non utilisé)

---

## 🔧 À FAIRE MAINTENANT

### Étape 1 : Installer les nouvelles dépendances (5 min)

```bash
cd /home/kompany-konga/stochastiqdata_site/frontend

# Installer toutes les dépendances
npm install

# Vérifier qu'il n'y a pas d'erreurs
npm list helmet express-rate-limit validator winston compression
```

### Étape 2 : Régénérer les clés API (10 min) 🔴 CRITIQUE

#### Clerk
1. Aller sur https://dashboard.clerk.com
2. Sélectionner votre projet
3. **API Keys** → Cliquer sur **Regenerate** pour :
   - Publishable Key (pk_test_...)
   - Secret Key (sk_test_...)
4. Copier les nouvelles clés

#### Supabase
1. Aller sur https://supabase.com/dashboard
2. Sélectionner votre projet (mjqtthaypifkdlaneymx)
3. **Settings > API** → Régénérer :
   - Project URL (reste le même)
   - anon/public key
   - service_role key
4. **Settings > Database > Connection string** → JWT Secret

### Étape 3 : Créer les fichiers .env avec les NOUVELLES clés

#### Frontend

```bash
cd /home/kompany-konga/stochastiqdata_site/frontend

# Copier le template
cp .env.example .env

# Éditer avec vos NOUVELLES clés
nano .env
```

Contenu à mettre dans `frontend/.env` :
```env
# Clerk (NOUVELLES CLÉS)
CLERK_PUBLISHABLE_KEY=pk_test_VOTRE_NOUVELLE_CLE
CLERK_SECRET_KEY=sk_test_VOTRE_NOUVELLE_CLE

# API Backend URL
API_URL=http://localhost:8000/api/v1

# Server Port
PORT=3000

# Environment
NODE_ENV=development
```

#### Backend

```bash
cd /home/kompany-konga/stochastiqdata_site/backend

# Copier le template
cp .env.example .env

# Éditer avec vos NOUVELLES clés
nano .env
```

Contenu à mettre dans `backend/.env` :
```env
# Supabase (NOUVELLES CLÉS)
SUPABASE_URL=https://mjqtthaypifkdlaneymx.supabase.co
SUPABASE_KEY=VOTRE_NOUVELLE_ANON_KEY
SUPABASE_SERVICE_KEY=VOTRE_NOUVELLE_SERVICE_KEY
SUPABASE_JWT_SECRET=VOTRE_NOUVEAU_JWT_SECRET

# CORS
FRONTEND_URL=http://localhost:3000

# Environment
NODE_ENV=development
```

### Étape 4 : Compiler le CSS (2 min)

```bash
cd /home/kompany-konga/stochastiqdata_site/frontend

# Compiler le CSS minifié
npm run build
```

### Étape 5 : Tester en local (5 min)

```bash
# Terminal 1 - Backend
cd /home/kompany-konga/stochastiqdata_site/backend
# Démarrer votre backend (commande dépend de votre setup)
python -m uvicorn main:app --reload

# Terminal 2 - Frontend
cd /home/kompany-konga/stochastiqdata_site/frontend
npm run dev
```

Ouvrir http://localhost:3000 et vérifier :
- ✅ La page s'affiche
- ✅ La connexion Clerk fonctionne
- ✅ Les favoris fonctionnent
- ✅ Pas d'erreurs dans la console

---

## 🚀 Déploiement en Production

### Préparation

```bash
cd /home/kompany-konga/stochastiqdata_site/frontend

# 1. Compiler le CSS en mode production
npm run build

# 2. Tester en mode production localement
npm run test:prod

# 3. Vérifier qu'il n'y a pas de console.log
# Ouvrir le navigateur et vérifier la console → devrait être vide
```

### Configuration des variables d'environnement

#### Sur Vercel

1. Dashboard → Votre projet → **Settings** → **Environment Variables**
2. Ajouter :

```
NODE_ENV = production
PORT = 3000
API_URL = https://api.votredomaine.com/api/v1
CLERK_PUBLISHABLE_KEY = pk_live_VOTRE_CLE_LIVE
CLERK_SECRET_KEY = sk_live_VOTRE_CLE_LIVE
```

#### Sur Railway

1. Projet → **Variables**
2. Même variables qu'au-dessus

#### Sur Netlify

1. Site settings → **Environment variables**
2. Même variables

### Commandes de déploiement

#### Vercel
```bash
npm install -g vercel
vercel login
vercel --prod
```

#### Railway
```bash
npm install -g railway
railway login
railway up
```

#### Netlify
```bash
npm install -g netlify-cli
netlify login
netlify deploy --prod
```

---

## 🧪 Tests avant production

### Checklist de tests

- [ ] Inscription/connexion fonctionne
- [ ] Déconnexion fonctionne
- [ ] Recherche fonctionne
- [ ] Favoris fonctionnent (ajouter/retirer)
- [ ] Page profil s'affiche
- [ ] Page 404 s'affiche si mauvaise URL
- [ ] Mode sombre fonctionne
- [ ] Toutes les pages se chargent
- [ ] Pas d'erreurs dans la console navigateur
- [ ] Pas d'erreurs dans les logs serveur

### Tester le rate limiting

```bash
# Faire 10 requêtes rapides pour vérifier le rate limiting
for i in {1..10}; do curl http://localhost:3000/api/search?q=test; done

# Devrait retourner "Too Many Requests" après 5-6 requêtes
```

---

## 📊 Monitoring après déploiement

### Vérifier les logs

```bash
# Logs d'erreurs
tail -f /home/kompany-konga/stochastiqdata_site/frontend/logs/error.log

# Tous les logs
tail -f /home/kompany-konga/stochastiqdata_site/frontend/logs/combined.log
```

### Sur les services cloud

- **Vercel** : Dashboard → Runtime Logs
- **Railway** : Deployments → View Logs
- **Netlify** : Functions → Function logs

---

## 🔒 Sécurité après déploiement

### Vérifier les headers de sécurité

Aller sur https://securityheaders.com et tester votre site.

Devrait avoir :
- ✅ Content-Security-Policy
- ✅ Strict-Transport-Security
- ✅ X-Content-Type-Options
- ✅ X-Frame-Options

### Vérifier SSL/HTTPS

```bash
curl -I https://votredomaine.com

# Devrait retourner 200 OK avec HTTPS
```

---

## 🆘 Dépannage

### Erreur: "Cannot find module './config/security'"

```bash
# Le fichier existe déjà mais vérifier :
ls -la /home/kompany-konga/stochastiqdata_site/frontend/config/security.js

# Si manquant, il a été créé automatiquement
```

### Erreur: ENOENT logs/error.log

```bash
# Créer le dossier logs
mkdir -p /home/kompany-konga/stochastiqdata_site/frontend/logs
```

### Erreur: Clerk keys invalid

1. Vérifier que vous avez bien régénéré les clés
2. Vérifier qu'il n'y a pas d'espaces avant/après les clés dans .env
3. Redémarrer le serveur après modification du .env

### Rate limiting trop strict

Modifier `frontend/config/security.js` ligne 6-9 :
```javascript
max: 200, // Augmenter de 100 à 200
```

---

## ✅ Checklist finale

Avant de dire "C'est en production" :

- [ ] Toutes les dépendances installées (`npm install`)
- [ ] Clés API régénérées (Clerk + Supabase)
- [ ] Fichiers .env créés avec nouvelles clés
- [ ] .gitignore en place et vérifié
- [ ] CSS compilé en mode minifié (`npm run build`)
- [ ] Tests locaux OK
- [ ] Variables d'environnement configurées sur le serveur
- [ ] Site déployé et accessible
- [ ] HTTPS fonctionne
- [ ] Tests en production OK
- [ ] Logs accessibles et pas d'erreurs

---

## 📞 Support

Si vous rencontrez des problèmes :

1. Vérifier les logs : `frontend/logs/error.log`
2. Vérifier la configuration : `frontend/config/security.js`
3. Vérifier les variables d'environnement
4. Redémarrer le serveur

**IMPORTANT :** Ne partagez JAMAIS vos clés API dans un chat, issue GitHub ou forum public.
