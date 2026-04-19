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

function applyProfilePageData(profile) {
  if (!profile) return;

  const profileFullName = document.getElementById('profile-full-name');
  const profileNombre = document.getElementById('profile-nombre');
  const profileApellido = document.getElementById('profile-apellido');
  const profileDni = document.getElementById('profile-dni');
  const profileEmail = document.getElementById('profile-email');
  const profileTelefono = document.getElementById('profile-telefono');
  const profilePais = document.getElementById('profile-pais');

  const fullName = [profile.nombre, profile.apellido].filter(Boolean).join(' ').trim() || 'Usuario';

  if (profileFullName) profileFullName.textContent = fullName;
  if (profileNombre) profileNombre.textContent = profile.nombre || '-';
  if (profileApellido) profileApellido.textContent = profile.apellido || '-';
  if (profileDni) profileDni.textContent = profile.dni || '-';
  if (profileEmail) profileEmail.textContent = profile.email || '-';
  if (profileTelefono) profileTelefono.textContent = profile.telefono || '-';
  if (profilePais) profilePais.textContent = profile.pais || '-';
}

async function initProfilePage(current) {
  if (current !== 'perfil_view.html') return;

  const profile = await fetchAuthenticatedProfile();
  if (!profile) return;

  applyProfilePageData(profile);

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

  applySidebarUserName();
  applySidebarAdminOnlyLinks();
  applyAuthenticatedHeaderState(current);
}

function setPasswordChangeMessage(text, isError = false) {
  const message = document.getElementById('password-change-message');
  if (!message) return;

  message.textContent = text;
  message.classList.toggle('text-error', isError);
  message.classList.toggle('text-primary', !isError);
}

async function handlePasswordChangeSubmit() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    setPasswordChangeMessage('Debes iniciar sesión para cambiar la contraseña.', true);
    return;
  }

  const currentPassword = document.getElementById('current-password')?.value || '';
  const newPassword = document.getElementById('new-password')?.value || '';
  const confirmPassword = document.getElementById('confirm-new-password')?.value || '';

  if (!currentPassword || !newPassword || !confirmPassword) {
    setPasswordChangeMessage('Completá todos los campos de contraseña.', true);
    return;
  }

  if (newPassword !== confirmPassword) {
    setPasswordChangeMessage('La confirmación no coincide con la nueva contraseña.', true);
    return;
  }

  if (newPassword.length < 8) {
    setPasswordChangeMessage('La nueva contraseña debe tener al menos 8 caracteres.', true);
    return;
  }

  try {
    setPasswordChangeMessage('Actualizando contraseña...');
    const endpoints = ['/auth/change-password', '/auth/change_password'];
    let response = null;
    let data = null;

    for (const endpoint of endpoints) {
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      data = await response.json().catch(() => ({}));

      // Si la ruta no existe en esta versión del backend, probar la siguiente.
      if (response.status === 404 && data?.detail === 'Not Found') {
        continue;
      }

      break;
    }

    if (!response || !response.ok) {
      const detail = data?.detail || 'No se pudo actualizar la contraseña.';
      const message = detail === 'Not Found'
        ? 'No encontramos el endpoint de cambio de contraseña. Reiniciá backend y frontend.'
        : detail;
      setPasswordChangeMessage(message, true);
      return;
    }

    setPasswordChangeMessage(data?.message || 'Contraseña actualizada correctamente.');

    const currentInput = document.getElementById('current-password');
    const newInput = document.getElementById('new-password');
    const confirmInput = document.getElementById('confirm-new-password');
    if (currentInput) currentInput.value = '';
    if (newInput) newInput.value = '';
    if (confirmInput) confirmInput.value = '';
  } catch (error) {
    setPasswordChangeMessage('No se pudo conectar con el backend.', true);
  }
}

function initPasswordChange(current) {
  if (current !== 'perfil_view.html') return;

  const savePasswordBtn = document.getElementById('save-password-btn');
  if (!savePasswordBtn) return;

  savePasswordBtn.addEventListener('click', (event) => {
    event.preventDefault();
    handlePasswordChangeSubmit();
  });
}

async function fetchCountries() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/paises`);
    if (!response.ok) return [];
    return await response.json();
  } catch (error) {
    return [];
  }
}

function setProfileEditMessage(text, isError = false) {
  const message = document.getElementById('profile-edit-message');
  if (!message) return;
  message.textContent = text;
  message.classList.toggle('text-error', isError);
  message.classList.toggle('text-primary', !isError);
}

function toggleProfileEditMode(enable) {
  const editBtn = document.getElementById('edit-profile-btn');
  const cancelBtn = document.getElementById('cancel-profile-btn');
  const saveActions = document.getElementById('profile-save-actions');
  
  const emailDisplay = document.getElementById('profile-email-display');
  const emailInput = document.getElementById('profile-email-input');
  const telefonoDisplay = document.getElementById('profile-telefono-display');
  const telefonoInput = document.getElementById('profile-telefono-input');
  const paisDisplay = document.getElementById('profile-pais-display');
  const paisInput = document.getElementById('profile-pais-input');

  if (enable) {
    editBtn.classList.add('hidden');
    cancelBtn.classList.remove('hidden');
    saveActions.classList.remove('hidden');

    emailDisplay.classList.add('hidden');
    emailInput.classList.remove('hidden');
    emailInput.value = document.getElementById('profile-email').textContent;

    telefonoDisplay.classList.add('hidden');
    telefonoInput.classList.remove('hidden');
    telefonoInput.value = document.getElementById('profile-telefono').textContent;

    paisDisplay.classList.add('hidden');
    paisInput.classList.remove('hidden');

    setProfileEditMessage('');
  } else {
    editBtn.classList.remove('hidden');
    cancelBtn.classList.add('hidden');
    saveActions.classList.add('hidden');

    emailDisplay.classList.remove('hidden');
    emailInput.classList.add('hidden');

    telefonoDisplay.classList.remove('hidden');
    telefonoInput.classList.add('hidden');

    paisDisplay.classList.remove('hidden');
    paisInput.classList.add('hidden');

    setProfileEditMessage('');
  }
}

async function handleProfileEditSave() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    setProfileEditMessage('Debes iniciar sesión.', true);
    return;
  }

  const emailInput = document.getElementById('profile-email-input');
  const telefonoInput = document.getElementById('profile-telefono-input');
  const paisInput = document.getElementById('profile-pais-input');

  const email = emailInput?.value.trim() || null;
  const telefono = telefonoInput?.value.trim() || null;
  const pais = paisInput?.value ? parseInt(paisInput.value) : null;

  if (!email && !telefono && !pais) {
    setProfileEditMessage('Debes cambiar al menos un campo.', true);
    return;
  }

  try {
    setProfileEditMessage('Guardando cambios...');
    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        email: email,
        telefono: telefono,
        pais: pais,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      setProfileEditMessage(data.detail || 'No se pudo actualizar el perfil.', true);
      return;
    }

    document.getElementById('profile-email').textContent = data.email || '-';
    document.getElementById('profile-telefono').textContent = data.telefono || '-';
    document.getElementById('profile-pais').textContent = data.pais || '-';

    const existingAuthUser = getAuthUser() || {};
    localStorage.setItem(
      'auth_user',
      JSON.stringify({
        ...existingAuthUser,
        email: data.email,
      })
    );

    setProfileEditMessage('Cambios guardados exitosamente.');
    setTimeout(() => toggleProfileEditMode(false), 1500);
  } catch (error) {
    setProfileEditMessage('No se pudo conectar con el backend.', true);
  }
}

async function initProfileEdit(current) {
  if (current !== 'perfil_view.html') return;

  const editBtn = document.getElementById('edit-profile-btn');
  const cancelBtn = document.getElementById('cancel-profile-btn');
  const saveBtn = document.getElementById('save-profile-btn');

  if (!editBtn || !cancelBtn || !saveBtn) return;

  const countries = await fetchCountries();
  const paisInput = document.getElementById('profile-pais-input');
  if (paisInput && countries.length > 0) {
    countries.forEach(country => {
      const option = document.createElement('option');
      option.value = country.id;
      option.textContent = country.nombre;
      paisInput.appendChild(option);
    });
  }

  editBtn.addEventListener('click', (event) => {
    event.preventDefault();
    toggleProfileEditMode(true);
  });

  cancelBtn.addEventListener('click', (event) => {
    event.preventDefault();
    toggleProfileEditMode(false);
  });

  saveBtn.addEventListener('click', (event) => {
    event.preventDefault();
    handleProfileEditSave();
  });
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
  await initProfilePage(current);
  initPasswordChange(current);
  await initProfileEdit(current);
});
