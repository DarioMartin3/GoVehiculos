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
  const isSocio = role === 'socio';

  const sidebarDashboardLink = document.querySelector(
    '#sidebar-placeholder a[href="/dashboard_general_tecnico.html"]'
  );
  const sidebarUsersLink = document.querySelector(
    '#sidebar-placeholder a[href="/dashboard_user_directory.html"]'
  );
  const sidebarVehiculosLink = document.getElementById('sidebar-vehiculos');
  const sidebarTuVehiculoLink = document.getElementById('sidebar-tu-vehiculo');

  if (sidebarDashboardLink) {
    sidebarDashboardLink.classList.toggle('hidden', !isAdmin);
  }
  if (sidebarUsersLink) {
    sidebarUsersLink.classList.toggle('hidden', !isAdmin);
  }
  if (sidebarVehiculosLink) {
    sidebarVehiculosLink.classList.toggle('hidden', !isAdmin);
  }
  if (sidebarTuVehiculoLink) {
    sidebarTuVehiculoLink.classList.toggle('hidden', !isAdmin);
  }
  if (sidebarTuVehiculoLink) {
    sidebarTuVehiculoLink.classList.toggle('hidden', !isSocio);
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
  persistAuthUserProfile(profile);

  applySidebarUserName();
  applySidebarAdminOnlyLinks();
  applyAuthenticatedHeaderState(current);
  applyHeaderUserInitials();
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

async function fetchUserDirectory() {
  const token = localStorage.getItem('auth_token');
  if (!token) {
    throw new Error('Debes iniciar sesión para ver el directorio.');
  }

  const response = await fetch(`${API_BASE_URL}/auth/users`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || 'No se pudo cargar el directorio de usuarios.');
  }

  return data;
}

let userDirectoryCache = [];
let editingDirectoryUserId = null;
let directoryEditSubmitting = false;

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function getUserDirectoryStatusLabel(estado) {
  if (estado === 1 || estado === '1') {
    return { label: 'Activo', className: 'bg-green-50 text-green-700' };
  }

  if (estado === 2 || estado === '2') {
    return { label: 'Inactivo', className: 'bg-surface-container text-slate-500' };
  }

  if (estado === 3 || estado === '3') {
    return { label: 'En validacion', className: 'bg-tertiary-fixed text-tertiary' };
  }

  if (estado === 4 || estado === '4') {
    return { label: 'Rechazado', className: 'bg-red-50 text-red-700' };
  }

  return { label: 'Pendiente', className: 'bg-tertiary-fixed text-tertiary' };
}

function updateUserDirectoryStats(users) {
  const totalEl = document.getElementById('stats-total-users');
  const clientEl = document.getElementById('stats-client-users');
  const partnerEl = document.getElementById('stats-partner-users');

  if (!totalEl && !clientEl && !partnerEl) return;

  const safeUsers = Array.isArray(users) ? users : [];
  const total = safeUsers.length;
  const clients = safeUsers.filter((user) => (user.rol || '').toString().trim().toLowerCase() === 'cliente').length;
  const partners = safeUsers.filter((user) => (user.rol || '').toString().trim().toLowerCase() === 'socio').length;

  if (totalEl) totalEl.textContent = String(total);
  if (clientEl) clientEl.textContent = String(clients);
  if (partnerEl) partnerEl.textContent = String(partners);
}

function normalizeUserRole(value) {
  return (value || '').toString().trim().toLowerCase();
}

function applyUserDirectoryFilters() {
  const roleFilter = document.getElementById('user-role-filter');
  const statusFilter = document.getElementById('user-status-filter');
  const searchInput = document.getElementById('user-search-input');

  const selectedRole = normalizeUserRole(roleFilter?.value || 'all');
  const selectedStatus = (statusFilter?.value || 'all').toString().trim().toLowerCase();
  const searchTerm = (searchInput?.value || '').toString().trim().toLowerCase();

  const filteredUsers = userDirectoryCache.filter((user) => {
    const userRole = normalizeUserRole(user.rol);
    const userStatus = (user.estado ?? '').toString().trim().toLowerCase();

    const matchesRole = selectedRole === 'all' || userRole === selectedRole;
    const matchesStatus = selectedStatus === 'all' || userStatus === selectedStatus;

    const searchableText = [
      user.nombre,
      user.apellido,
      user.email,
      user.rol,
      user.pais,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();

    const matchesSearch = !searchTerm || searchableText.includes(searchTerm);

    return matchesRole && matchesStatus && matchesSearch;
  });

  renderUserDirectory(filteredUsers);
}

function initUserDirectoryFilters() {
  const roleFilter = document.getElementById('user-role-filter');
  const statusFilter = document.getElementById('user-status-filter');
  const searchInput = document.getElementById('user-search-input');
  const resetButton = document.getElementById('reset-user-filters-btn');

  if (!roleFilter || !statusFilter || !searchInput || !resetButton) return;
  if (resetButton.dataset.boundFilters === '1') return;

  roleFilter.addEventListener('change', applyUserDirectoryFilters);
  statusFilter.addEventListener('change', applyUserDirectoryFilters);
  searchInput.addEventListener('input', applyUserDirectoryFilters);

  resetButton.addEventListener('click', (event) => {
    event.preventDefault();
    roleFilter.value = 'all';
    statusFilter.value = 'all';
    searchInput.value = '';
    applyUserDirectoryFilters();
  });

  resetButton.dataset.boundFilters = '1';
}

function setDirectoryEditModalMessage(text, isError = false) {
  const message = document.getElementById('user-edit-form-message');
  if (!message) return;

  message.textContent = text;
  message.classList.toggle('text-error', isError);
  message.classList.toggle('text-primary', !isError);
}

function setDirectoryEditSubmittingState(isSubmitting) {
  directoryEditSubmitting = isSubmitting;

  const saveButton = document.getElementById('user-edit-save');
  const cancelButton = document.getElementById('user-edit-cancel');
  const closeButton = document.getElementById('user-edit-modal-close');

  if (saveButton) {
    saveButton.disabled = isSubmitting;
    saveButton.classList.toggle('opacity-60', isSubmitting);
    saveButton.classList.toggle('cursor-not-allowed', isSubmitting);
    saveButton.textContent = isSubmitting ? 'Guardando...' : 'Guardar cambios';
  }
  if (cancelButton) cancelButton.disabled = isSubmitting;
  if (closeButton) closeButton.disabled = isSubmitting;
}

function isValidDirectoryEditEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidDirectoryEditPhone(phone) {
  if (!phone) return true;
  return /^[0-9+\-\s()]{7,20}$/.test(phone);
}

async function ensureDirectoryEditCountries() {
  const paisSelect = document.getElementById('edit-user-pais');
  if (!paisSelect) return;
  if (paisSelect.dataset.loadedCountries === '1') return;

  const countries = await fetchCountries();
  paisSelect.innerHTML = '<option value="">Seleccionar pais</option>';
  countries.forEach((country) => {
    const option = document.createElement('option');
    option.value = String(country.id);
    option.textContent = country.nombre;
    paisSelect.appendChild(option);
  });
  paisSelect.dataset.loadedCountries = '1';
}

function openDirectoryEditModal(userId) {
  const modal = document.getElementById('user-edit-modal');
  if (!modal) return;

  const user = userDirectoryCache.find((item) => Number(item.id) === Number(userId));
  if (!user) {
    window.alert('No se encontró el usuario para editar.');
    return;
  }

  editingDirectoryUserId = Number(userId);

  const email = document.getElementById('edit-user-email');
  const rol = document.getElementById('edit-user-rol');
  const nombre = document.getElementById('edit-user-nombre');
  const apellido = document.getElementById('edit-user-apellido');
  const telefono = document.getElementById('edit-user-telefono');
  const pais = document.getElementById('edit-user-pais');
  const estado = document.getElementById('edit-user-estado');

  if (email) email.value = user.email || '';
  if (rol) rol.value = (user.rol || '').toString().trim().toLowerCase();
  if (nombre) nombre.value = user.nombre || '';
  if (apellido) apellido.value = user.apellido || '';
  if (telefono) telefono.value = user.telefono || '';
  if (estado) estado.value = String(user.estado ?? '1');

  ensureDirectoryEditCountries().then(() => {
    const countries = Array.from(pais?.options || []);
    const countryOption = countries.find((option) => option.textContent === (user.pais || ''));
    if (pais) pais.value = countryOption ? countryOption.value : '';
  });

  setDirectoryEditSubmittingState(false);
  setDirectoryEditModalMessage('');
  modal.classList.remove('hidden');
}

function closeDirectoryEditModal(force = false) {
  if (directoryEditSubmitting && !force) return;

  const modal = document.getElementById('user-edit-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  editingDirectoryUserId = null;
  setDirectoryEditSubmittingState(false);
  setDirectoryEditModalMessage('');
}

async function submitDirectoryEditModal(event) {
  event.preventDefault();

  if (directoryEditSubmitting) return;

  if (!editingDirectoryUserId) {
    setDirectoryEditModalMessage('No se encontró el usuario a editar.', true);
    return;
  }

  const email = document.getElementById('edit-user-email')?.value.trim() || '';
  const rol = document.getElementById('edit-user-rol')?.value.trim() || '';
  const nombre = document.getElementById('edit-user-nombre')?.value.trim() || '';
  const apellido = document.getElementById('edit-user-apellido')?.value.trim() || '';
  const telefono = document.getElementById('edit-user-telefono')?.value.trim() || '';
  const paisValue = document.getElementById('edit-user-pais')?.value || '';
  const estadoValue = document.getElementById('edit-user-estado')?.value || '';

  if (!email || !rol || !nombre || !apellido || !estadoValue) {
    setDirectoryEditModalMessage('Completá los campos obligatorios.', true);
    return;
  }

  if (!isValidDirectoryEditEmail(email)) {
    setDirectoryEditModalMessage('Ingresá un email válido.', true);
    return;
  }

  if (!isValidDirectoryEditPhone(telefono)) {
    setDirectoryEditModalMessage('Ingresá un teléfono válido (solo números, espacios, +, -, paréntesis).', true);
    return;
  }

  const parsedPais = paisValue ? parseInt(paisValue, 10) : null;
  const parsedEstado = parseInt(estadoValue, 10);
  if (Number.isNaN(parsedEstado)) {
    setDirectoryEditModalMessage('El estado seleccionado no es válido.', true);
    return;
  }
  if (paisValue && Number.isNaN(parsedPais)) {
    setDirectoryEditModalMessage('El país seleccionado no es válido.', true);
    return;
  }

  const payload = {
    email,
    rol,
    nombre,
    apellido,
    telefono: telefono || null,
    pais: parsedPais,
    estado: parsedEstado,
  };

  try {
    setDirectoryEditSubmittingState(true);
    setDirectoryEditModalMessage('Guardando cambios...');
    await saveDirectoryUser(editingDirectoryUserId, payload);
    closeDirectoryEditModal(true);
    await initUserDirectoryPage('dashboard_user_directory.html');
  } catch (error) {
    setDirectoryEditModalMessage(error.message || 'No se pudo actualizar el usuario.', true);
  } finally {
    setDirectoryEditSubmittingState(false);
  }
}

function initDirectoryEditModal() {
  const modal = document.getElementById('user-edit-modal');
  const closeBtn = document.getElementById('user-edit-modal-close');
  const cancelBtn = document.getElementById('user-edit-cancel');
  const backdrop = document.getElementById('user-edit-modal-backdrop');
  const form = document.getElementById('user-edit-form');

  if (!modal || !closeBtn || !cancelBtn || !backdrop || !form) return;
  if (modal.dataset.boundModal === '1') return;

  closeBtn.addEventListener('click', closeDirectoryEditModal);
  cancelBtn.addEventListener('click', closeDirectoryEditModal);
  backdrop.addEventListener('click', closeDirectoryEditModal);
  form.addEventListener('submit', submitDirectoryEditModal);

  modal.dataset.boundModal = '1';
}

async function saveDirectoryUser(userId, payload) {
  const token = localStorage.getItem('auth_token');
  const response = await fetch(`${API_BASE_URL}/auth/users/${userId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || 'No se pudo actualizar el usuario.');
  }

  return data;
}

async function deactivateDirectoryUser(userId) {
  const token = localStorage.getItem('auth_token');
  const response = await fetch(`${API_BASE_URL}/auth/users/${userId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || 'No se pudo dar de baja al usuario.');
  }

  return data;
}

async function activateDirectoryUser(userId) {
  const token = localStorage.getItem('auth_token');
  const response = await fetch(`${API_BASE_URL}/auth/users/${userId}/activate`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || 'No se pudo activar al usuario.');
  }

  return data;
}

async function handleDirectoryAction(event) {
  const button = event.target.closest('button[data-user-action]');
  if (!button) return;

  const userId = parseInt(button.dataset.userId, 10);
  if (!userId) return;

  const action = button.dataset.userAction;

  try {
    if (action === 'edit') {
      openDirectoryEditModal(userId);
      return;
    }

    if (action === 'delete') {
      const confirmed = window.confirm('Esta acción hará una baja lógica y dejará el usuario inactivo. ¿Continuar?');
      if (!confirmed) return;
      await deactivateDirectoryUser(userId);
    }

    if (action === 'activate') {
      const confirmed = window.confirm('Este usuario volverá a estado activo. ¿Continuar?');
      if (!confirmed) return;
      await activateDirectoryUser(userId);
    }

    await initUserDirectoryPage('dashboard_user_directory.html');
  } catch (error) {
    window.alert(error.message || 'No se pudo completar la acción.');
  }
}

function renderUserDirectory(users) {
  const tbody = document.getElementById('users-table-body');
  if (!tbody) return;

  if (!users || users.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="px-8 py-10 text-center text-slate-500 font-medium">No hay usuarios para mostrar.</td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = users.map((user) => {
    const fullName = [user.nombre, user.apellido].filter(Boolean).join(' ').trim() || 'Sin nombre';
    const initials = [user.nombre, user.apellido]
      .filter(Boolean)
      .map(part => part.trim().charAt(0).toUpperCase())
      .join('') || '?';
    const status = getUserDirectoryStatusLabel(user.estado);
    const isInactive = user.estado === 2 || user.estado === '2';
    const actionButtonHtml = isInactive
      ? `
            <button class="p-2 text-slate-400 hover:text-primary transition-colors hover:bg-primary-fixed rounded-lg" type="button" data-user-action="activate" data-user-id="${user.id}" title="Activar usuario">
              <span class="material-symbols-outlined text-lg">check_circle</span>
            </button>
        `
      : `
            <button class="p-2 text-slate-400 hover:text-error transition-colors hover:bg-error-container rounded-lg" type="button" data-user-action="delete" data-user-id="${user.id}" title="Dar de baja">
              <span class="material-symbols-outlined text-lg">delete</span>
            </button>
        `;

    return `
      <tr class="hover:bg-surface-container-low/30 transition-colors group" data-user-id="${user.id}">
        <td class="px-8 py-6">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-full bg-primary-fixed text-primary flex items-center justify-center font-bold ring-2 ring-primary/5">${escapeHtml(initials)}</div>
            <div>
              <p class="font-headline font-bold text-on-surface">${escapeHtml(fullName)}</p>
              <p class="text-xs text-slate-500">${escapeHtml(user.email)}</p>
            </div>
          </div>
        </td>
        <td class="px-6 py-6">
          <p class="text-sm font-semibold text-on-surface">${escapeHtml(user.rol || '-')}</p>
          <p class="text-xs text-slate-500">${escapeHtml(user.pais || '-')}</p>
        </td>
        <td class="px-6 py-6">
          <span class="px-3 py-1 ${status.className} text-[10px] font-bold uppercase tracking-wider rounded-full">${status.label}</span>
        </td>
        <td class="px-6 py-6 text-right">
          <div class="flex justify-end gap-2">
            <button class="p-2 text-slate-400 hover:text-primary transition-colors hover:bg-primary-fixed rounded-lg" type="button" data-user-action="edit" data-user-id="${user.id}" title="Editar usuario">
              <span class="material-symbols-outlined text-lg">edit</span>
            </button>
            ${actionButtonHtml}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function initUserDirectoryPage(current) {
  if (current !== 'dashboard_user_directory.html') return;

  const tbody = document.getElementById('users-table-body');
  if (!tbody) return;

  initUserDirectoryFilters();
  initDirectoryEditModal();

  if (!tbody.dataset.boundActions) {
    tbody.addEventListener('click', handleDirectoryAction);
    tbody.dataset.boundActions = '1';
  }

  tbody.innerHTML = `
    <tr>
      <td colspan="4" class="px-8 py-10 text-center text-slate-500 font-medium">Cargando usuarios...</td>
    </tr>
  `;

  try {
    const users = await fetchUserDirectory();
    userDirectoryCache = Array.isArray(users) ? users : [];
    updateUserDirectoryStats(users);
    applyUserDirectoryFilters();
  } catch (error) {
    userDirectoryCache = [];
    updateUserDirectoryStats([]);
    tbody.innerHTML = `
      <tr>
        <td colspan="4" class="px-8 py-10 text-center text-error font-semibold">${escapeHtml(error.message || 'No se pudo cargar el directorio.')}</td>
      </tr>
    `;
  }
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

  if (current !== 'perfil_view.html') {
    hydrateAuthUserFromProfile(current).catch(() => {});
  }

  await initProfilePage(current);
  initPasswordChange(current);
  await initProfileEdit(current);
  await initUserDirectoryPage(current);
});
