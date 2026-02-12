// ===== Enhanced Plan Website — Client-Side JS =====

document.addEventListener('DOMContentLoaded', () => {
  initProgressBar();
  initSidebar();
  initSearch();
  initBackToTop();
  highlightActivePage();
});

// ===== READING PROGRESS BAR =====
function initProgressBar() {
  const bar = document.getElementById('progress-bar');
  if (!bar) return;

  window.addEventListener('scroll', () => {
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = window.scrollY;
    bar.style.width = docHeight > 0 ? (scrolled / docHeight * 100) + '%' : '0%';
  });
}

// ===== SIDEBAR TOGGLE (mobile) =====
function initSidebar() {
  const hamburger = document.querySelector('.hamburger');
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.querySelector('.sidebar-overlay');

  if (!hamburger || !sidebar) return;

  hamburger.addEventListener('click', () => {
    sidebar.classList.toggle('open');
    if (overlay) overlay.classList.toggle('visible');
  });

  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('visible');
    });
  }
}

// ===== SEARCH =====
function initSearch() {
  const input = document.getElementById('search-input');
  const results = document.getElementById('search-results');
  if (!input || !results) return;

  // Build search index from sidebar data attribute
  let searchIndex = [];
  try {
    const data = document.getElementById('search-data');
    if (data) searchIndex = JSON.parse(data.textContent);
  } catch (e) {
    console.warn('Search index not found');
  }

  input.addEventListener('input', () => {
    const query = input.value.trim().toLowerCase();
    if (query.length < 2) {
      results.classList.remove('visible');
      results.innerHTML = '';
      return;
    }

    const matches = [];
    searchIndex.forEach(page => {
      page.headings.forEach(h => {
        if (h.text.toLowerCase().includes(query)) {
          matches.push({
            page: page.title,
            heading: h.text,
            url: page.url + (h.id ? '#' + h.id : ''),
            query: query
          });
        }
      });
      // Also match page title
      if (page.title.toLowerCase().includes(query)) {
        matches.push({
          page: page.title,
          heading: page.title,
          url: page.url,
          query: query
        });
      }
    });

    // Deduplicate
    const seen = new Set();
    const unique = matches.filter(m => {
      const key = m.url;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });

    if (unique.length === 0) {
      results.innerHTML = '<div class="search-no-results">No results found</div>';
    } else {
      results.innerHTML = unique.slice(0, 15).map(m => {
        const highlighted = m.heading.replace(
          new RegExp(`(${escapeRegex(m.query)})`, 'gi'),
          '<mark>$1</mark>'
        );
        return `<a class="search-result-item" href="${m.url}">
          <div class="result-page">${escapeHTML(m.page)}</div>
          <div class="result-title">${highlighted}</div>
        </a>`;
      }).join('');
    }
    results.classList.add('visible');
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.header-search')) {
      results.classList.remove('visible');
    }
  });

  // Close on Escape
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      results.classList.remove('visible');
      input.blur();
    }
  });
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// ===== BACK TO TOP =====
function initBackToTop() {
  const btn = document.querySelector('.back-to-top');
  if (!btn) return;

  window.addEventListener('scroll', () => {
    btn.classList.toggle('visible', window.scrollY > 400);
  });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

// ===== HIGHLIGHT ACTIVE SIDEBAR LINK =====
function highlightActivePage() {
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.sidebar-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage) {
      link.classList.add('active');
    }
  });
}
