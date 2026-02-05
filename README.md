# StochastiQdata

Plateforme de notation de datasets pour actuaires. Permet aux professionnels de l'assurance d'évaluer et de noter des datasets selon leur utilité actuarielle, leur qualité et leur documentation.

## Architecture

```
stochastiqdata_site/
├── backend/                 # API FastAPI (Python)
│   ├── app/
│   │   ├── api/            # Endpoints REST
│   │   ├── core/           # Config & database
│   │   ├── middleware/     # Auth Clerk JWT
│   │   └── schemas/        # Pydantic models
│   └── requirements.txt
├── frontend/               # React + Tailwind CSS
│   ├── src/
│   │   ├── components/     # UI components
│   │   ├── hooks/          # Custom hooks
│   │   ├── lib/            # Utils & API client
│   │   ├── pages/          # Pages
│   │   └── types/          # TypeScript types
│   └── package.json
└── supabase/
    └── schema.sql          # Database schema
```

## Stack Technique

- **Frontend**: React 18, TypeScript, Tailwind CSS, Vite
- **Backend**: FastAPI, Python 3.11+
- **Database**: Supabase (PostgreSQL)
- **Auth**: Clerk
- **Déploiement**: Vercel (frontend), Railway/Render (backend)

## Installation

### Prérequis

- Node.js 18+
- Python 3.11+
- Compte Supabase
- Compte Clerk

### 1. Configuration Supabase

1. Créer un projet sur [supabase.com](https://supabase.com)
2. Exécuter le script SQL dans `supabase/schema.sql` via l'éditeur SQL
3. Récupérer les clés API dans Settings > API

### 2. Configuration Clerk

1. Créer une application sur [clerk.com](https://clerk.com)
2. Récupérer la clé publishable et la clé secrète
3. Noter l'issuer JWT (format: `https://xxx.clerk.accounts.dev`)

### 3. Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés

# Lancer le serveur
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Configurer les variables d'environnement
cp .env.example .env

# Lancer le serveur de développement
npm run dev
```

L'application sera disponible sur http://localhost:5173

## API Endpoints

### Datasets

- `GET /api/v1/datasets` - Liste des datasets (pagination, filtres)
- `GET /api/v1/datasets/{id}` - Détail d'un dataset
- `POST /api/v1/datasets` - Créer un dataset (auth requise)
- `DELETE /api/v1/datasets/{id}` - Supprimer un dataset (auth + owner)

### Reviews

- `GET /api/v1/reviews/dataset/{id}` - Avis d'un dataset
- `GET /api/v1/reviews/user/me` - Mes avis (auth requise)
- `POST /api/v1/reviews` - Créer un avis (auth requise)
- `PUT /api/v1/reviews/{id}` - Modifier un avis (auth + owner)
- `DELETE /api/v1/reviews/{id}` - Supprimer un avis (auth + owner)

## Critères de Notation

Chaque dataset est noté sur 3 axes (0-10):

1. **Utilité Actuarielle** (40%) - Pertinence pour les travaux actuariels
2. **Propreté / Biais** (35%) - Qualité des données, valeurs manquantes
3. **Documentation** (25%) - Clarté de la documentation

Le score global est calculé automatiquement via un trigger PostgreSQL.

## Déploiement

### Frontend (Vercel)

```bash
cd frontend
vercel
```

### Backend (Railway/Render)

Configurer les variables d'environnement sur la plateforme choisie et déployer depuis le dossier `backend/`.

## Licence

MIT
