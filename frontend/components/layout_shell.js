(function () {
  const API_BASE_URL = 'http://localhost:8000';

  async function loadComponent(id, path) {
    const el = document.getElementById(id);
    if (!el) return;
    const res = await fetch(path);
    const html = await res.text();
    el.innerHTML = html;
  }

  function setElementHidden(element, hidden) {
    if (!element) return;
    element.classList.toggle('hidden', hidden);
  }

  function setButtonLoadingState(button, isLoading, loadingText = 'Procesando...') {
    if (!button) return;

    if (!button.dataset.originalText) {
      button.dataset.originalText = button.innerHTML;
    }

    button.disabled = isLoading;
    button.classList.toggle('opacity-60', isLoading);
    button.classList.toggle('cursor-not-allowed', isLoading);

    if (!button.querySelector('.material-symbols-outlined')) {
      button.innerHTML = isLoading ? loadingText : button.dataset.originalText;
    }
  }

  function setLoginMessage(text, isError = false) {
    const message = document.getElementById('login-message');
    if (!message) return;
    message.textContent = text;
    message.classList.toggle('text-error', isError);
    message.classList.toggle('text-primary', !isError);
  }

  function getAuthUser() {
    const authUserStr = localStorage.getItem('auth_user');
    if (!authUserStr) return null;

    try {
      return JSON.parse(authUserStr);
    } catch (e) {
      return null;
    }
  }

  function getUserInitials(user) {
    const nameInitials = [user?.nombre, user?.apellido]
      .map((part) => (part || '').toString().trim())
      .filter(Boolean)
      .map((part) => part.charAt(0).toUpperCase())
      .join('');

    if (nameInitials) {
      return nameInitials;
    }

    const emailInitial = (user?.email || '').toString().trim().charAt(0).toUpperCase();
    return emailInitial || '?';
  }

  function applyHeaderUserInitials() {
    const initialsEl = document.getElementById('nav-user-initials');
    if (!initialsEl) return;

    const authUser = getAuthUser();
    initialsEl.textContent = getUserInitials(authUser);
  }

  function applySidebarAdminOnlyLinks() {
    const authUser = getAuthUser();
    const role = (authUser?.rol || '').toString().trim().toLowerCase();
    const isAdmin = role === 'administrador' || role === 'admin';
    const isSocio = role === 'socio';

    const sidebarDashboardLink = document.getElementById('sidebar-dashboard');
    const sidebarUsersLink = document.getElementById('sidebar-users');
    const sidebarVehiculosLink = document.getElementById('sidebar-vehiculos');
    const sidebarTuVehiculoLink = document.getElementById('sidebar-tu-vehiculo');

    setElementHidden(sidebarDashboardLink, !isAdmin);
    setElementHidden(sidebarUsersLink, !isAdmin);
    setElementHidden(sidebarVehiculosLink, !isAdmin);
    setElementHidden(sidebarTuVehiculoLink, !isSocio);
  }

  function applySidebarUserName() {
    const sidebarUserName = document.getElementById('sidebar-user-name');
    if (!sidebarUserName) return;

    const authUser = getAuthUser();
    const fullName = [authUser?.nombre, authUser?.apellido]
      .filter(Boolean)
      .join(' ')
      .trim();

    if (fullName) {
      sidebarUserName.textContent = fullName;
    }
  }

  function applyAuthenticatedHeaderState(current) {
    const token = localStorage.getItem('auth_token');
    const authUser = getAuthUser();
    const userRole = authUser?.rol || null;

    const dashboardPages = [
      'dashboard_general_tecnico.html',
      'dashboard_user_directory.html',
      'deshboard_vehiculos.html',
      'dashboard_tecnico.html',
      'crear_rol_empleado.html',
      'perfil_view.html',
      'select_topic_chat.html',
      'chat_bot.html',
    ];

    const navActionsPages = [...dashboardPages, 'index_registrar_vehiculo.html'];

    const showDashboardActions = navActionsPages.includes(current) || (current === 'index.html' && token);

    const btnCrear = document.getElementById('nav-crear-cuenta');
    const btnSignUp = document.getElementById('nav-sign-up');
    const dashActions = document.getElementById('nav-dashboard-actions');
    const btnDashboard = document.getElementById('nav-dashboard');
    const btnSocio = document.getElementById('nav-socio');

    if (token) {
      setElementHidden(btnCrear, true);
      setElementHidden(btnSignUp, true);
    } else {
      setElementHidden(btnCrear, false);
      setElementHidden(btnSignUp, false);
    }

    if (!token || !userRole) {
      setElementHidden(btnDashboard, true);
      setElementHidden(btnSocio, true);
    } else {
      const rolSeguro = userRole.toLowerCase().trim();
      setElementHidden(btnDashboard, ['cliente', 'socio'].includes(rolSeguro));
      setElementHidden(btnSocio, rolSeguro !== 'cliente');
    }

    if (showDashboardActions && dashActions) {
      dashActions.classList.remove('hidden');
      dashActions.classList.add('flex');
      const footerPlaceholder = document.getElementById('footer-placeholder');
      if (footerPlaceholder && dashboardPages.includes(current)) {
        footerPlaceholder.classList.add('ml-64');
      }
    } else if (dashActions) {
      dashActions.classList.add('hidden');
      dashActions.classList.remove('flex');
    }

    applyHeaderUserInitials();
  }

  function persistAuthUserProfile(profile) {
    if (!profile) return;

    const existingAuthUser = getAuthUser() || {};
    localStorage.setItem(
      'auth_user',
      JSON.stringify({
        ...existingAuthUser,
        id: profile.id,
        email: profile.email,
        rol: profile.rol,
        nombre: profile.nombre,
        apellido: profile.apellido,
      })
    );
  }

  async function fetchAuthenticatedProfile() {
    const token = localStorage.getItem('auth_token');
    if (!token) return null;

    try {
      const response = await fetch(`${API_BASE_URL}/auth/profile`, {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        return null;
      }

      return response.json();
    } catch (error) {
      return null;
    }
  }

  async function hydrateAuthUserFromProfile(current) {
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    const profile = await fetchAuthenticatedProfile();
    if (!profile) return;

    persistAuthUserProfile(profile);
    applySidebarUserName();
    applySidebarAdminOnlyLinks();
    applyAuthenticatedHeaderState(current);
  }

  function syncAuthenticatedUiAfterLogin(current) {
    applyAuthenticatedHeaderState(current);
    applySidebarUserName();
    applySidebarAdminOnlyLinks();
    hydrateAuthUserFromProfile(current).catch(() => {});
  }

  async function handleLoginSubmit(event) {
    event.preventDefault();

    const submitButton = document.querySelector('#login-form button[type="submit"]');
    if (submitButton?.disabled) return;

    const email = document.getElementById('login-email')?.value.trim() || '';
    const password = document.getElementById('login-password')?.value || '';

    if (!email || !password) {
      setLoginMessage('Completá email y contraseña.', true);
      return;
    }

    try {
      setButtonLoadingState(submitButton, true, 'Ingresando...');
      setLoginMessage('Iniciando sesión...');
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();
      if (!response.ok) {
        setLoginMessage(data.detail || 'No se pudo iniciar sesión.', true);
        return;
      }

      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      setLoginMessage('Sesión iniciada.');

      const modal = document.getElementById('login-modal');
      if (modal) modal.classList.add('hidden');

      const current = window.location.pathname.split('/').pop() || 'index.html';
      syncAuthenticatedUiAfterLogin(current);
    } catch (error) {
      setLoginMessage('No se pudo conectar con el backend.', true);
    } finally {
      setButtonLoadingState(submitButton, false);
    }
  }

  function initAuth() {
    const loginForm = document.getElementById('login-form');
    if (!loginForm) return;
    loginForm.addEventListener('submit', handleLoginSubmit);
  }

  function initLoginModal() {
    const modal = document.getElementById('login-modal');
    const backdrop = document.getElementById('login-modal-backdrop');
    const closeBtn = document.getElementById('login-modal-close');

    if (!modal || !backdrop || !closeBtn) return;

    document.querySelectorAll('[data-open-login]').forEach((trigger) => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        modal.classList.remove('hidden');
      });
    });

    function closeModal() {
      modal.classList.add('hidden');
    }

    closeBtn.addEventListener('click', closeModal);
    backdrop.addEventListener('click', closeModal);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') closeModal();
    });
  }

  function initLogout() {
    document.querySelectorAll('[data-logout-link]').forEach((link) => {
      link.addEventListener('click', (event) => {
        event.preventDefault();
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        sessionStorage.clear();
        window.location.href = '/index.html';
      });
    });
  }

  window.LayoutShell = {
    API_BASE_URL,
    loadComponent,
    setElementHidden,
    setButtonLoadingState,
    getAuthUser,
    applyHeaderUserInitials,
    applySidebarAdminOnlyLinks,
    applySidebarUserName,
    applyAuthenticatedHeaderState,
    persistAuthUserProfile,
    fetchAuthenticatedProfile,
    hydrateAuthUserFromProfile,
    syncAuthenticatedUiAfterLogin,
    initAuth,
    initLoginModal,
    initLogout,
  };
})();
