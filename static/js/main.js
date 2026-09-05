/**
 * Connectly - Modern Contact Book Application
 * Frontend JavaScript: Theme Switcher, Real-time Search, Modals, Ajax Favorites, Avatar Preview
 */

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initFlashAlerts();
  initLiveSearch();
  initFavoriteToggles();
  initAvatarPreview();
  initDeleteModals();
  initDuplicateDetector();
  initCategoryChart();
});

/* ==========================================================================
   1. Theme Switcher (Dark / Light Mode)
   ========================================================================== */
function initTheme() {
  const themeToggleBtn = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');
  
  // Check stored preference or system preference
  const storedTheme = localStorage.getItem('connectly_theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  
  const currentTheme = storedTheme || (prefersDark ? 'dark' : 'light');
  applyTheme(currentTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const activeTheme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      localStorage.setItem('connectly_theme', newTheme);
    });
  }

  function applyTheme(theme) {
    if (theme === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      if (themeIcon) {
        themeIcon.className = 'fas fa-sun';
      }
    } else {
      document.documentElement.removeAttribute('data-theme');
      if (themeIcon) {
        themeIcon.className = 'fas fa-moon';
      }
    }
  }
}

/* ==========================================================================
   2. Auto-Dismiss Flash Alerts
   ========================================================================== */
function initFlashAlerts() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    // Dismiss button
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      });
    }

    // Auto dismiss after 5 seconds
    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 400);
      }
    }, 5000);
  });
}

/* ==========================================================================
   3. Real-Time Client-side Search / Filter
   ========================================================================== */
function initLiveSearch() {
  const searchInput = document.getElementById('live-search-input');
  const contactCards = document.querySelectorAll('.contact-card');
  const emptySearchState = document.getElementById('search-empty-state');
  const contactsGrid = document.querySelector('.contacts-grid');

  if (!searchInput || contactCards.length === 0) return;

  searchInput.addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase().trim();
    let visibleCount = 0;

    contactCards.forEach(card => {
      const name = (card.getAttribute('data-name') || '').toLowerCase();
      const phone = (card.getAttribute('data-phone') || '').toLowerCase();
      const email = (card.getAttribute('data-email') || '').toLowerCase();
      const company = (card.getAttribute('data-company') || '').toLowerCase();
      const category = (card.getAttribute('data-category') || '').toLowerCase();
      const city = (card.getAttribute('data-city') || '').toLowerCase();

      const match = name.includes(term) || 
                    phone.includes(term) || 
                    email.includes(term) || 
                    company.includes(term) || 
                    category.includes(term) ||
                    city.includes(term);

      if (match) {
        card.style.display = '';
        visibleCount++;
      } else {
        card.style.display = 'none';
      }
    });

    if (emptySearchState) {
      if (visibleCount === 0) {
        emptySearchState.style.display = 'block';
        if (contactsGrid) contactsGrid.style.display = 'none';
      } else {
        emptySearchState.style.display = 'none';
        if (contactsGrid) contactsGrid.style.display = 'grid';
      }
    }
  });
}

/* ==========================================================================
   4. Asynchronous Favorite Toggles
   ========================================================================== */
function initFavoriteToggles() {
  const favForms = document.querySelectorAll('.favorite-toggle-form');

  favForms.forEach(form => {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = form.querySelector('.favorite-btn');
      const icon = btn.querySelector('i');
      const actionUrl = form.getAttribute('action');

      try {
        const response = await fetch(actionUrl, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.is_favorite) {
            btn.classList.add('is-favorite');
            if (icon) icon.className = 'fas fa-star';
            btn.title = 'Remove from favorites';
          } else {
            btn.classList.remove('is-favorite');
            if (icon) icon.className = 'far fa-star';
            btn.title = 'Add to favorites';
          }
        } else {
          // Fallback to standard form submit
          form.submit();
        }
      } catch (err) {
        form.submit();
      }
    });
  });
}

/* ==========================================================================
   5. Live Avatar Preview for Forms
   ========================================================================== */
function initAvatarPreview() {
  const avatarInput = document.getElementById('profile_picture_input');
  const avatarPreview = document.getElementById('avatar_preview');

  if (avatarInput && avatarPreview) {
    avatarInput.addEventListener('change', function () {
      const file = this.files[0];
      if (file) {
        if (file.size > 5 * 1024 * 1024) {
          alert('File size exceeds the 5MB limit. Please select a smaller image.');
          this.value = '';
          return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
          avatarPreview.src = e.target.result;
          avatarPreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  }
}

/* ==========================================================================
   6. Delete Confirmation Modal
   ========================================================================== */
function initDeleteModals() {
  const modal = document.getElementById('delete-modal');
  const deleteForms = document.querySelectorAll('.delete-contact-btn');
  const modalForm = document.getElementById('modal-delete-form');
  const modalContactName = document.getElementById('modal-contact-name');
  const cancelBtn = document.getElementById('modal-cancel-btn');
  const closeBtn = document.getElementById('modal-close-btn');

  if (!modal) return;

  deleteForms.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const contactId = btn.getAttribute('data-id');
      const contactName = btn.getAttribute('data-name') || 'this contact';
      const actionUrl = btn.getAttribute('data-url') || `/contacts/${contactId}/delete`;

      if (modalForm) modalForm.action = actionUrl;
      if (modalContactName) modalContactName.textContent = contactName;

      openModal(modal);
    });
  });

  if (cancelBtn) cancelBtn.addEventListener('click', () => closeModal(modal));
  if (closeBtn) closeBtn.addEventListener('click', () => closeModal(modal));

  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal(modal);
  });

  function openModal(m) {
    m.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeModal(m) {
    m.classList.remove('show');
    document.body.style.overflow = '';
  }
}

/* ==========================================================================
   7. Real-Time Duplicate Detection on Forms
   ========================================================================== */
function initDuplicateDetector() {
  const phoneInput = document.getElementById('contact_phone');
  const emailInput = document.getElementById('contact_email');
  const warningContainer = document.getElementById('realtime-duplicate-warning');
  const contactIdInput = document.getElementById('contact_id');

  if (!phoneInput && !emailInput) return;

  let debounceTimer;

  function checkDuplicates() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      const phone = phoneInput ? phoneInput.value.trim() : '';
      const email = emailInput ? emailInput.value.trim() : '';
      const excludeId = contactIdInput ? contactIdInput.value.trim() : '';

      if (!phone && !email) {
        if (warningContainer) warningContainer.style.display = 'none';
        return;
      }

      try {
        const params = new URLSearchParams({ phone, email, exclude_id: excludeId });
        const res = await fetch(`/api/check-duplicate?${params}`);
        if (res.ok) {
          const data = await res.json();
          if (data.has_duplicate && warningContainer) {
            warningContainer.innerHTML = `
              <div class="duplicate-warning-box">
                <i class="fas fa-exclamation-triangle" style="font-size: 1.25rem; margin-top: 0.1rem;"></i>
                <div>
                  <strong>Potential duplicate detected:</strong>
                  <ul style="margin-top: 0.3rem; padding-left: 1.2rem;">
                    ${data.warnings.map(w => `<li>${w}</li>`).join('')}
                  </ul>
                </div>
              </div>
            `;
            warningContainer.style.display = 'block';
          } else if (warningContainer) {
            warningContainer.style.display = 'none';
          }
        }
      } catch (err) {
        // Silent catch for live detector
      }
    }, 450);
  }

  if (phoneInput) phoneInput.addEventListener('input', checkDuplicates);
  if (emailInput) emailInput.addEventListener('input', checkDuplicates);
}

/* ==========================================================================
   8. Category Distribution Chart (Chart.js Integration)
   ========================================================================== */
function initCategoryChart() {
  const chartCanvas = document.getElementById('categoryChart');
  if (!chartCanvas || typeof Chart === 'undefined') return;

  fetch('/api/stats')
    .then(res => res.json())
    .then(data => {
      if (!data.categories || data.categories.length === 0) {
        const chartWrapper = chartCanvas.parentElement;
        if (chartWrapper) {
          chartWrapper.innerHTML = '<p class="text-muted" style="text-align: center; padding: 2rem 0;">No contacts categorized yet.</p>';
        }
        return;
      }

      const labels = data.categories.map(c => c.category);
      const counts = data.categories.map(c => c.count);
      const bgColors = [
        '#4f46e5', '#8b5cf6', '#10b981', '#f59e0b',
        '#0ea5e9', '#ec4899', '#6366f1', '#14b8a6'
      ];

      new Chart(chartCanvas, {
        type: 'doughnut',
        data: {
          labels: labels,
          datasets: [{
            data: counts,
            backgroundColor: bgColors.slice(0, labels.length),
            borderWidth: 2,
            borderColor: document.documentElement.getAttribute('data-theme') === 'dark' ? '#151d30' : '#ffffff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                boxWidth: 12,
                padding: 14,
                font: { size: 12, family: 'Inter, sans-serif' },
                color: document.documentElement.getAttribute('data-theme') === 'dark' ? '#cbd5e1' : '#475569'
              }
            }
          },
          cutout: '68%'
        }
      });
    })
    .catch(() => {});
}

