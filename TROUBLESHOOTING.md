# 🔧 Guide de Dépannage - StochastiQdata

## 🚨 Problèmes Courants et Solutions

### 1. ❌ Le bouton "Ajouter un dataset" ne fonctionne pas

**Symptôme:** Cliquer sur "Ajouter un dataset" ne fait rien ou renvoie une 404

**Cause:** Route non définie ou page manquante

**Solution:**
```bash
# Vérifier que la page existe
ls -la /home/kompany-konga/stochastiqdata_site/frontend/views/pages/add-dataset.ejs

# Si elle existe, vérifier le server.js ligne 225
# La route devrait être : app.get('/add-dataset', ...)

# Redémarrer le serveur
cd /home/kompany-konga/stochastiqdata_site/frontend
npm run dev
```

**✅ Status:** CORRIGÉ - La route existe dans le nouveau server.js

---

### 2. ❌ Les favoris renvoient une erreur

**Symptôme:** Cliquer sur le coeur des favoris affiche "Erreur lors de la mise à jour des favoris"

**Causes possibles:**
1. Backend pas démarré
2. Routes proxy manquantes
3. Pas d'authentification Clerk

**Solution:**

#### A. Vérifier que le backend est démarré
```bash
# Terminal 1 - Démarrer le backend
cd /home/kompany-konga/stochastiqdata_site/backend
python -m uvicorn main:app --reload --port 8000

# Tester que le backend répond
curl http://localhost:8000/api/v1/datasets
# Devrait retourner du JSON avec les datasets
```

#### B. Vérifier que le frontend est démarré
```bash
# Terminal 2
cd /home/kompany-konga/stochastiqdata_site/frontend
npm run dev
```

#### C. Vérifier l'authentification
1. Ouvrir http://localhost:3000
2. Se connecter avec Clerk
3. Ouvrir la console navigateur (F12)
4. Essayer d'ajouter un favori
5. Vérifier la requête réseau :
   - Devrait aller vers `/api/v1/favorites/DATASET_ID/toggle`
   - Devrait avoir un header `Authorization: Bearer ...`

**✅ Status:** CORRIGÉ - Routes proxy ajoutées dans server.js (lignes 348-421)

---

### 3. ❌ Mon Profil redirige vers Dashboard

**Symptôme:** Cliquer sur "Mon Profil" charge puis redirige vers l'accueil

**Causes:**
1. Clerk pas chargé assez vite
2. Utilisateur pas connecté
3. Timeout trop court

**Solution:**

#### A. Si vous n'êtes PAS connecté
C'est normal ! La page profil nécessite une connexion.
1. Cliquer sur "Se connecter"
2. Se connecter avec Clerk
3. Retourner sur "Mon Profil"

#### B. Si vous ÊTES connecté et ça redirige quand même

Vérifier la console navigateur (F12) :
```javascript
// Dans la console, taper :
window.clerk
// Devrait retourner un objet Clerk

window.clerk.user
// Devrait retourner vos informations utilisateur

window.isUserLoggedIn()
// Devrait retourner true
```

Si `window.clerk` est `undefined` :
- Vérifier que `CLERK_PUBLISHABLE_KEY` est dans votre `.env`
- Vérifier qu'il n'y a pas d'erreur de chargement du script Clerk dans la console

**✅ Status:** CORRIGÉ - Timeout augmenté à 5s et logique améliorée dans profile.ejs

---

### 4. ❌ La page Modélisation ne montre aucun dataset

**Symptôme:** Page `/modeling` vide ou dit "Aucun dataset trouvé"

**Cause:** Le BACKEND n'a PAS DE DONNÉES dans la base Supabase

**Solution:**

#### A. Vérifier que le backend a des datasets
```bash
# Tester l'API backend directement
curl http://localhost:8000/api/v1/datasets

# Devrait retourner quelque chose comme :
# {"datasets": [...], "total": 10}

# Si retourne {"datasets": [], "total": 0} ou une erreur :
# → Le backend n'a pas de données
```

#### B. Ajouter des données de test

**Option 1 : Via l'interface**
1. Se connecter sur http://localhost:3000
2. Cliquer sur "Ajouter un dataset"
3. Remplir le formulaire
4. Soumettre

**Option 2 : Via l'API directement**
```bash
# Créer un dataset de test
curl -X POST http://localhost:8000/api/v1/datasets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tarification Auto - Dataset Test",
    "description": "Dataset pour la tarification automobile",
    "source": "kaggle",
    "source_url": "https://www.kaggle.com/test",
    "tags": ["iard", "pricing"],
    "modeling_types": ["regression"],
    "best_fit_models": ["glm", "random_forest"]
  }'
```

**Option 3 : Vérifier Supabase**
1. Aller sur https://supabase.com/dashboard
2. Sélectionner votre projet
3. Aller dans **Table Editor** → Table `datasets`
4. Vérifier qu'il y a des lignes

---

### 5. ❌ La barre de recherche ne montre aucun résultat

**Symptôme:** Taper dans la recherche ne montre rien

**Causes:**
1. Backend pas démarré
2. Backend n'a pas de datasets
3. Erreur JavaScript

**Solution:**

#### A. Ouvrir la console navigateur (F12)
Taper quelque chose dans la recherche et regarder :
- S'il y a des erreurs en rouge
- Les requêtes réseau (onglet Network)

#### B. Vérifier que la requête part correctement
1. F12 → Network
2. Taper dans la recherche
3. Vous devriez voir une requête vers `/api/search?q=...`
4. Cliquer dessus pour voir la réponse

**Réponse attendue :**
```json
{
  "datasets": [
    {"id": "...", "name": "...", "description": "...", "global_score": 85}
  ],
  "total": 10
}
```

**Si erreur 400 :**
```json
{"error": "Requête de recherche invalide"}
```
→ La query est invalide (trop courte, vide, etc.)

**Si erreur 500 ou timeout :**
→ Le backend ne répond pas

#### C. Tester le backend directement
```bash
# Tester la recherche backend
curl "http://localhost:8000/api/v1/datasets?search=test"

# Devrait retourner des datasets correspondant à "test"
```

#### D. Si le backend retourne des datasets mais le frontend ne les affiche pas

Vérifier dans la console navigateur :
```javascript
// Dans la console
fetch('/api/search?q=test')
  .then(r => r.json())
  .then(data => console.log(data))

// Devrait afficher les datasets
```

---

## 🔍 Diagnostic Complet

### Script de Diagnostic Automatique

Créer un fichier `test-connection.js` dans le dossier frontend :

```javascript
const axios = require('axios');

const API_URL = process.env.API_URL || 'http://localhost:8000/api/v1';

async function testConnection() {
  console.log('\n🔍 Test de connexion au backend...\n');

  try {
    // Test 1: Backend accessible
    console.log('1️⃣ Test: Backend accessible');
    const response = await axios.get(`${API_URL}/datasets`);
    console.log('✅ Backend répond !');
    console.log(`   → ${response.data.total} datasets trouvés\n`);

    // Test 2: Datasets
    if (response.data.total === 0) {
      console.log('⚠️ ATTENTION: Aucun dataset dans la base de données');
      console.log('   → Utilisez "Ajouter un dataset" pour en créer\n');
    } else {
      console.log('✅ Datasets présents');
      console.log(`   → Exemples: ${response.data.datasets.slice(0, 3).map(d => d.name).join(', ')}\n`);
    }

    // Test 3: Recherche
    console.log('2️⃣ Test: Recherche');
    const searchResponse = await axios.get(`${API_URL}/datasets?search=test`);
    console.log('✅ Recherche fonctionne');
    console.log(`   → ${searchResponse.data.total} résultats pour "test"\n`);

  } catch (error) {
    console.error('\n❌ ERREUR DE CONNEXION\n');

    if (error.code === 'ECONNREFUSED') {
      console.error('Le backend ne répond pas sur:', API_URL);
      console.error('\nSolution:');
      console.error('1. Ouvrir un nouveau terminal');
      console.error('2. cd backend');
      console.error('3. python -m uvicorn main:app --reload --port 8000');
    } else {
      console.error('Erreur:', error.message);
    }
  }
}

testConnection();
```

**Utilisation :**
```bash
cd /home/kompany-konga/stochastiqdata_site/frontend
node test-connection.js
```

---

## ✅ Checklist de Démarrage

Avant de tester votre site, vérifier que :

### Backend
- [ ] Backend démarré : `cd backend && python -m uvicorn main:app --reload`
- [ ] Backend accessible : `curl http://localhost:8000/api/v1/datasets`
- [ ] Base de données a des datasets : Vérifier Supabase ou créer des datasets de test

### Frontend
- [ ] Dépendances installées : `cd frontend && npm install`
- [ ] Fichier `.env` créé avec clés Clerk valides
- [ ] CSS compilé : `npm run build`
- [ ] Frontend démarré : `npm run dev`
- [ ] Accessible sur http://localhost:3000

### Configuration
- [ ] `frontend/.env` contient `API_URL=http://localhost:8000/api/v1`
- [ ] `frontend/.env` contient les clés Clerk valides
- [ ] `backend/.env` contient les clés Supabase valides

### Tests
- [ ] Page d'accueil charge
- [ ] Connexion Clerk fonctionne
- [ ] Recherche retourne des résultats
- [ ] Favoris fonctionnent (si connecté)
- [ ] Profil s'affiche (si connecté)

---

## 🆘 Si rien ne fonctionne

### 1. Tout réinitialiser

```bash
# Arrêter tous les serveurs (Ctrl+C dans chaque terminal)

# Frontend
cd /home/kompany-konga/stochastiqdata_site/frontend
rm -rf node_modules
npm install
npm run build

# Redémarrer dans l'ordre

# Terminal 1 - Backend
cd /home/kompany-konga/stochastiqdata_site/backend
python -m uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd /home/kompany-konga/stochastiqdata_site/frontend
npm run dev
```

### 2. Vérifier les logs

**Backend :**
Regarder le terminal où tourne le backend, chercher :
- ❌ Erreurs de connexion Supabase
- ❌ Erreurs 500
- ✅ Requêtes qui passent (200 OK)

**Frontend :**
```bash
# Logs Winston
tail -f logs/error.log
tail -f logs/combined.log
```

**Navigateur :**
- F12 → Console : Chercher erreurs JavaScript en rouge
- F12 → Network : Vérifier les requêtes HTTP

### 3. Vérifier les ports

```bash
# Vérifier que les ports sont bien utilisés
netstat -tulpn | grep :3000  # Frontend
netstat -tulpn | grep :8000  # Backend

# Si un port est déjà utilisé par un autre processus
# Tuer le processus ou changer le port
```

---

## 📞 Support

Si le problème persiste après avoir suivi ce guide :

1. **Vérifier les logs** :
   - Backend terminal
   - Frontend logs/error.log
   - Console navigateur (F12)

2. **Noter les erreurs exactes** :
   - Message d'erreur complet
   - Code d'erreur (400, 404, 500)
   - Stack trace si disponible

3. **Vérifier la configuration** :
   - Fichiers .env correctement remplis
   - Clés API valides
   - Ports corrects

**IMPORTANT :** Ne JAMAIS partager vos clés API réelles quand vous demandez de l'aide !
