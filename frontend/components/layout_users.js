(function () {
  const layoutShell = window.LayoutShell;
  const layoutUi = window.LayoutUi;

  if (!layoutShell) {
    throw new Error('No se cargó layout_shell.js antes de layout_users.js');
  }
  if (!layoutUi) {
    throw new Error('No se cargó layout_ui.js antes de layout_users.js');
  }

  const API_BASE_URL = layoutShell.API_BASE_URL;
  const { setButtonLoadingState } = layoutShell;
  const {
    escapeHtml,
    showUserToast,
    openUserConfirmModal,
    initUserConfirmModal,
  } = layoutUi;

  let userDirectoryCache = [];
  let editingDirectoryUserId = null;
  let directoryEditSubmitting = false;

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

  async function fetchCountries() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/paises`);
      if (!response.ok) return [];
      return await response.json();
    } catch (error) {
      return [];
    }
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
      showUserToast('No se encontró el usuario para editar.', 'error');
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
      showUserToast('Usuario actualizado correctamente.', 'success');
      await initUserDirectoryPage('dashboard_user_directory.html');
    } catch (error) {
      setDirectoryEditModalMessage(error.message || 'No se pudo actualizar el usuario.', true);
      showUserToast(error.message || 'No se pudo actualizar el usuario.', 'error');
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
    if (button.disabled) return;

    const userId = parseInt(button.dataset.userId, 10);
    if (!userId) return;

    const action = button.dataset.userAction;

    try {
      setButtonLoadingState(button, true);

      if (action === 'edit') {
        openDirectoryEditModal(userId);
        return;
      }

      if (action === 'delete') {
        const confirmed = await openUserConfirmModal('Esta acción hará una baja lógica y dejará el usuario inactivo. ¿Continuar?', 'Dar de baja');
        if (!confirmed) return;
        await deactivateDirectoryUser(userId);
        showUserToast('Usuario dado de baja correctamente.', 'success');
      }

      if (action === 'activate') {
        const confirmed = await openUserConfirmModal('Este usuario volverá a estado activo. ¿Continuar?', 'Activar');
        if (!confirmed) return;
        await activateDirectoryUser(userId);
        showUserToast('Usuario activado correctamente.', 'success');
      }

      await initUserDirectoryPage('dashboard_user_directory.html');
    } catch (error) {
      showUserToast(error.message || 'No se pudo completar la acción.', 'error');
    } finally {
      setButtonLoadingState(button, false);
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
        .map((part) => part.trim().charAt(0).toUpperCase())
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
    initUserConfirmModal();

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

  window.LayoutUsers = {
    initUserDirectoryPage,
  };
})();
