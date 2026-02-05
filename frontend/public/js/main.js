// StochastiQdata - Frontend JavaScript

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initClock();
  initSearch();
  initUserMenu();
  initMobileSidebar();
});

// ============================================
// SÉCURITÉ - PROTECTION XSS
// ============================================
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ============================================
// GESTION DU THÈME (MODE SOMBRE)
// ============================================
function initTheme() {
  const themeToggle = document.getElementById('themeToggle');

  // Charger le thème sauvegardé
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  // Toggle au clic
  themeToggle?.addEventListener('click', () => {
    const isDark = document.documentElement.classList.toggle('dark');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
  });
}

// ============================================
// HORLOGE TEMPS RÉEL
// ============================================
function initClock() {
  const dateElement = document.getElementById('currentDate');

  function updateDate() {
    if (dateElement) {
      const now = new Date();
      dateElement.textContent = now.toLocaleDateString('fr-FR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
      });
    }
  }

  // Mettre à jour
  updateDate();
}

// ============================================
// RECHERCHE DYNAMIQUE
// ============================================
function initSearch() {
  const searchInput = document.getElementById('searchInput');
  const searchResults = document.getElementById('searchResults');
  let debounceTimer;

  searchInput?.addEventListener('input', (e) => {
    const query = e.target.value.trim();

    clearTimeout(debounceTimer);

    if (query.length < 2) {
      searchResults?.classList.add('hidden');
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.datasets && data.datasets.length > 0) {
          renderSearchResults(data.datasets);
          searchResults?.classList.remove('hidden');
        } else {
          searchResults.innerHTML = `
            <div class="p-4 text-center text-gray-500 dark:text-gray-400">
              Aucun résultat pour "<span class="text-gray-900 dark:text-white font-medium">${escapeHtml(query)}</span>"
            </div>
          `;
          searchResults?.classList.remove('hidden');
        }
      } catch (error) {
        console.error('Search error:', error);
      }
    }, 300);
  });

  // Fermer les résultats au clic extérieur
  document.addEventListener('click', (e) => {
    if (!searchInput?.contains(e.target) && !searchResults?.contains(e.target)) {
      searchResults?.classList.add('hidden');
    }
  });

  // Navigation clavier
  searchInput?.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      searchResults?.classList.add('hidden');
      searchInput.blur();
    }
  });
}

function renderSearchResults(datasets) {
  const searchResults = document.getElementById('searchResults');
  if (!searchResults) return;

  const html = datasets.map(dataset => `
    <a href="/modeling/${escapeHtml(dataset.id)}" class="flex items-center gap-3 p-3 hover:bg-gray-50 dark:hover:bg-navy-700 transition-colors border-b border-gray-100 dark:border-navy-700 last:border-0">
      <div class="w-10 h-10 rounded-lg bg-primary-100 dark:bg-primary-500/20 flex items-center justify-center shrink-0">
        <svg class="w-5 h-5 text-primary-600 dark:text-primary-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 22h14a2 2 0 0 0 2-2V7l-5-5H6a2 2 0 0 0-2 2v4"/>
          <path d="M14 2v4a2 2 0 0 0 2 2h4"/>
        </svg>
      </div>
      <div class="flex-1 min-w-0">
        <p class="text-gray-900 dark:text-white font-medium truncate">${escapeHtml(dataset.name)}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400 truncate">${escapeHtml(dataset.description) || 'Pas de description'}</p>
      </div>
      <div class="text-sm font-bold ${getScoreClass(dataset.global_score)}">
        ${parseInt(dataset.global_score) || 0}
      </div>
    </a>
  `).join('');

  searchResults.innerHTML = html;
}

function getScoreClass(score) {
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-primary-500';
  if (score >= 40) return 'text-yellow-500';
  return 'text-red-500';
}

// ============================================
// MENU UTILISATEUR
// ============================================
function initUserMenu() {
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userMenu = document.getElementById('userMenu');

  userMenuBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    userMenu?.classList.toggle('hidden');
  });

  // Fermer au clic extérieur
  document.addEventListener('click', (e) => {
    if (!userMenuBtn?.contains(e.target) && !userMenu?.contains(e.target)) {
      userMenu?.classList.add('hidden');
    }
  });
}

// ============================================
// SIDEBAR MOBILE
// ============================================
function initMobileSidebar() {
  const hamburgerBtn = document.getElementById('hamburgerBtn');
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');

  if (!sidebar || !overlay) return;

  // Fonction pour ouvrir le sidebar
  const openSidebar = () => {
    sidebar.classList.remove('-translate-x-[calc(100%+3rem)]');
    sidebar.classList.add('translate-x-0');
    overlay.classList.remove('hidden');
  };

  // Fonction pour fermer le sidebar
  const closeSidebar = () => {
    sidebar.classList.add('-translate-x-[calc(100%+3rem)]');
    sidebar.classList.remove('translate-x-0');
    overlay.classList.add('hidden');
  };

  // Toggle depuis bouton hamburger
  hamburgerBtn?.addEventListener('click', openSidebar);

  // Fermer au clic sur overlay
  overlay.addEventListener('click', closeSidebar);

  // Fermer quand on clique sur un lien de navigation (mobile)
  const navLinks = sidebar.querySelectorAll('.nav-item, a[href]');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 1024) {
        closeSidebar();
      }
    });
  });
}

// ============================================
// MODAL RATING
// ============================================
window.openRatingModal = function(datasetId) {
  const modal = document.getElementById('ratingModal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.dataset.datasetId = datasetId;
  }
};

window.closeRatingModal = function() {
  const modal = document.getElementById('ratingModal');
  if (modal) {
    modal.classList.add('hidden');
  }
};

// Fermer modal au clic sur le fond
document.getElementById('ratingModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'ratingModal') {
    closeRatingModal();
  }
});

// ============================================
// ADD DATASET BUTTON
// ============================================
document.getElementById('addDatasetBtn')?.addEventListener('click', () => {
  alert('Fonctionnalité "Ajouter un dataset" à venir !');
});

// ============================================
// LOGIN BUTTON
// ============================================
document.getElementById('loginBtn')?.addEventListener('click', () => {
  // Ouvrir le modal de connexion
  const modal = document.getElementById('loginModal');
  if (modal) {
    modal.classList.remove('hidden');
  }
});

window.closeLoginModal = function() {
  const modal = document.getElementById('loginModal');
  if (modal) {
    modal.classList.add('hidden');
  }
};

// Fermer modal login au clic sur le fond
document.getElementById('loginModal')?.addEventListener('click', (e) => {
  if (e.target.id === 'loginModal') {
    closeLoginModal();
  }
});

// ============================================
// FAVORIS (utilise Clerk pour l'authentification)
// ============================================

// Favoris SUPPRIMÉS - Fonctionnalité retirée

// Initialiser au chargement
document.addEventListener('DOMContentLoaded', () => {
  // Favoris supprimés
});
