(function () {
  const layoutShell = window.LayoutShell;
  if (!layoutShell) {
    throw new Error('No se cargó layout_shell.js antes de layout_profile.js');
  }

  const API_BASE_URL = layoutShell.API_BASE_URL;
  const {
    getAuthUser,
    applyHeaderUserInitials,
    applySidebarAdminOnlyLinks,
    applySidebarUserName,
    applyAuthenticatedHeaderState,
    persistAuthUserProfile,
    fetchAuthenticatedProfile,
  } = layoutShell;

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

    if (savePasswordBtn.dataset.boundPassword === '1') return;

    savePasswordBtn.addEventListener('click', (event) => {
      event.preventDefault();
      handlePasswordChangeSubmit();
    });

    savePasswordBtn.dataset.boundPassword = '1';
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

    if (!editBtn || !cancelBtn || !saveActions || !emailDisplay || !emailInput || !telefonoDisplay || !telefonoInput || !paisDisplay || !paisInput) {
      return;
    }

    if (enable) {
      editBtn.classList.add('hidden');
      cancelBtn.classList.remove('hidden');
      saveActions.classList.remove('hidden');

      emailDisplay.classList.add('hidden');
      emailInput.classList.remove('hidden');
      emailInput.value = document.getElementById('profile-email')?.textContent || '';

      telefonoDisplay.classList.add('hidden');
      telefonoInput.classList.remove('hidden');
      telefonoInput.value = document.getElementById('profile-telefono')?.textContent || '';

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
    const pais = paisInput?.value ? parseInt(paisInput.value, 10) : null;

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
          email,
          telefono,
          pais,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        setProfileEditMessage(data.detail || 'No se pudo actualizar el perfil.', true);
        return;
      }

      const emailEl = document.getElementById('profile-email');
      const telefonoEl = document.getElementById('profile-telefono');
      const paisEl = document.getElementById('profile-pais');
      if (emailEl) emailEl.textContent = data.email || '-';
      if (telefonoEl) telefonoEl.textContent = data.telefono || '-';
      if (paisEl) paisEl.textContent = data.pais || '-';

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
    if (saveBtn.dataset.boundProfileEdit === '1') return;

    const countries = await fetchCountries();
    const paisInput = document.getElementById('profile-pais-input');
    if (paisInput && countries.length > 0 && paisInput.dataset.loadedCountries !== '1') {
      countries.forEach((country) => {
        const option = document.createElement('option');
        option.value = country.id;
        option.textContent = country.nombre;
        paisInput.appendChild(option);
      });
      paisInput.dataset.loadedCountries = '1';
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

    saveBtn.dataset.boundProfileEdit = '1';
  }

  window.LayoutProfile = {
    initProfilePage,
    initPasswordChange,
    initProfileEdit,
  };
})();
