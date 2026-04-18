async function loadComponent(id, path) {
  const el = document.getElementById(id);
  if (!el) return;
  const res = await fetch(path);
  const html = await res.text();
  el.innerHTML = html;
}

const API_BASE_URL = 'http://localhost:8000';

function setLoginMessage(text, isError = false) {
  const message = document.getElementById('login-message');
  if (!message) return;
  message.textContent = text;
  message.classList.toggle('text-error', isError);
  message.classList.toggle('text-primary', !isError);
}

async function handleLoginSubmit(event) {
  event.preventDefault();

  const email = document.getElementById('login-email')?.value.trim() || '';
  const password = document.getElementById('login-password')?.value || '';

  if (!email || !password) {
    setLoginMessage('Completá email y contraseña.', true);
    return;
  }

  try {
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

  document.querySelectorAll('[data-open-login]').forEach(trigger => {
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

function getAuthUser() {
  const authUserStr = localStorage.getItem('auth_user');
  if (!authUserStr) return null;

  try {
    return JSON.parse(authUserStr);
  } catch (e) {
    return null;
  }
}

function applySidebarAdminOnlyLinks() {
  const authUser = getAuthUser();
  const role = (authUser?.rol || '').toString().trim().toLowerCase();
  const isAdmin = role === 'administrador' || role === 'admin';

  const sidebarDashboardLink = document.querySelector(
    '#sidebar-placeholder a[href="/dashboard_general_tecnico.html"]'
  );
  const sidebarUsersLink = document.querySelector(
    '#sidebar-placeholder a[href="/dashboard_user_directory.html"]'
  );

  if (sidebarDashboardLink) {
    sidebarDashboardLink.classList.toggle('hidden', !isAdmin);
  }
  if (sidebarUsersLink) {
    sidebarUsersLink.classList.toggle('hidden', !isAdmin);
  }
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

  // Obtener el rol del usuario
  const userRole = authUser?.rol || null;
  
  const dashboardPages = [
    'dashboard_general_tecnico.html',
    'dashboard_user_directory.html',
    'deshboard_vehiculos.html',
    'dashboard_tecnico.html',
    'crear_rol_empleado.html',
    'perfil_view.html',
  ];
  const showDashboardActions = dashboardPages.includes(current) || (current === 'index.html' && token);

  const btnCrear = document.getElementById('nav-crear-cuenta');
  const btnSignUp = document.getElementById('nav-sign-up');
  const dashActions = document.getElementById('nav-dashboard-actions');
  const btnDashboard = document.getElementById('nav-dashboard');
  const btnSocio = document.getElementById('nav-socio');

  if (token) {
    if (btnCrear) btnCrear.classList.add('hidden');
    if (btnSignUp) btnSignUp.classList.add('hidden');
  }

  // Si NO está logueado (rol = null), ocultar "Conviertete en Socio" y Dashboard
  if (!token || !userRole) {
    if (btnDashboard) btnDashboard.classList.add('hidden');
    if (btnSocio) btnSocio.classList.add('hidden');
  } else {
    // Si está logueado, aplicar lógica de visibilidad según rol
    
    // Normalizar el rol para evitar problemas de mayúsculas o espacios
    const rolSeguro = userRole ? userRole.toLowerCase().trim() : '';
    // Ocultar Dashboard para roles cliente y socio
    if (btnDashboard && ['cliente', 'socio'].includes(rolSeguro)) {
      btnDashboard.classList.add('hidden');
    } else if (btnDashboard) {
      btnDashboard.classList.remove('hidden');
    }

    // Ocultar "Conviertete en Socio" para todos EXCEPTO cliente
    if (btnSocio && rolSeguro !== 'cliente') {
      btnSocio.classList.add('hidden');
    } else if (btnSocio) {
      btnSocio.classList.remove('hidden');
    }
  }

  if (showDashboardActions && dashActions) {
    dashActions.classList.remove('hidden');
    dashActions.classList.add('flex');
    const footerPlaceholder = document.getElementById('footer-placeholder');
    if (footerPlaceholder && dashboardPages.includes(current)) {
      footerPlaceholder.classList.add('ml-64');
    }
  }
}

function syncAuthenticatedUiAfterLogin(current) {
  applyAuthenticatedHeaderState(current);
  applySidebarUserName();
  applySidebarAdminOnlyLinks();
}

document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([
    loadComponent('header-placeholder', '/components/header.html'),
    loadComponent('sidebar-placeholder', '/components/sidebar.html'),
    loadComponent('footer-placeholder', '/components/footer.html'),
    loadComponent('login-modal-placeholder', '/components/login-modal.html'),
  ]);
  initLoginModal();
  initAuth();
  initLogout();

  const current = window.location.pathname.split('/').pop() || 'index.html';

  // Sidebar: marcar link activo
  document.querySelectorAll('[data-sidebar-link]').forEach(function (link) {
    const href = link.getAttribute('href').split('/').pop();
    if (href && href !== '#' && href === current) {
      link.classList.remove('text-slate-600', 'hover:translate-x-1');
      link.classList.add('bg-white', 'dark:bg-slate-800', 'text-blue-700', 'dark:text-blue-300', 'font-semibold', 'shadow-sm');
    }
  });

  // Sidebar: mostrar botón Add New User solo en User Directory
  const addUserBtn = document.getElementById('sidebar-add-user-btn');
  if (addUserBtn && current === 'dashboard_user_directory.html') {
    addUserBtn.classList.remove('hidden');
  }

  applyAuthenticatedHeaderState(current);
  applySidebarUserName();
  applySidebarAdminOnlyLinks();
});
