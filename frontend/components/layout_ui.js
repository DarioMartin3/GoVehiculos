(function () {
  const toastTimeoutByScope = {};
  const confirmResolverByScope = {};

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function showScopedToast(scope, message, type = 'info') {
    const toast = document.getElementById(`${scope}-toast`);
    if (!toast) return;

    const timeoutId = toastTimeoutByScope[scope];
    if (timeoutId) {
      clearTimeout(timeoutId);
      delete toastTimeoutByScope[scope];
    }

    toast.textContent = message;
    toast.classList.remove('hidden', 'bg-green-600', 'bg-red-600', 'bg-slate-800', 'text-white');
    toast.classList.add('text-white');

    if (type === 'success') {
      toast.classList.add('bg-green-600');
    } else if (type === 'error') {
      toast.classList.add('bg-red-600');
    } else {
      toast.classList.add('bg-slate-800');
    }

    toastTimeoutByScope[scope] = setTimeout(() => {
      toast.classList.add('hidden');
      delete toastTimeoutByScope[scope];
    }, 2600);
  }

  function closeScopedConfirmModal(scope, confirmed) {
    const modal = document.getElementById(`${scope}-confirm-modal`);
    if (modal) {
      modal.classList.add('hidden');
    }

    const resolver = confirmResolverByScope[scope];
    if (resolver) {
      resolver(Boolean(confirmed));
      delete confirmResolverByScope[scope];
    }
  }

  function openScopedConfirmModal(scope, message, confirmText = 'Confirmar') {
    const modal = document.getElementById(`${scope}-confirm-modal`);
    const messageEl = document.getElementById(`${scope}-confirm-message`);
    const acceptBtn = document.getElementById(`${scope}-confirm-accept`);

    if (!modal || !messageEl || !acceptBtn) {
      return Promise.resolve(window.confirm(message));
    }

    messageEl.textContent = message;
    acceptBtn.textContent = confirmText;
    modal.classList.remove('hidden');

    return new Promise((resolve) => {
      confirmResolverByScope[scope] = resolve;
    });
  }

  function initScopedConfirmModal(scope) {
    const modal = document.getElementById(`${scope}-confirm-modal`);
    const backdrop = document.getElementById(`${scope}-confirm-backdrop`);
    const cancelBtn = document.getElementById(`${scope}-confirm-cancel`);
    const acceptBtn = document.getElementById(`${scope}-confirm-accept`);

    if (!modal || !backdrop || !cancelBtn || !acceptBtn) return;
    if (modal.dataset.boundConfirmModal === '1') return;

    backdrop.addEventListener('click', () => closeScopedConfirmModal(scope, false));
    cancelBtn.addEventListener('click', () => closeScopedConfirmModal(scope, false));
    acceptBtn.addEventListener('click', () => closeScopedConfirmModal(scope, true));

    modal.dataset.boundConfirmModal = '1';
  }

  function showUserToast(message, type = 'info') {
    showScopedToast('user', message, type);
  }

  function openUserConfirmModal(message, confirmText = 'Confirmar') {
    return openScopedConfirmModal('user', message, confirmText);
  }

  function initUserConfirmModal() {
    initScopedConfirmModal('user');
  }

  function showVehicleToast(message, type = 'info') {
    showScopedToast('vehicle', message, type);
  }

  function openVehicleConfirmModal(message, confirmText = 'Confirmar') {
    return openScopedConfirmModal('vehicle', message, confirmText);
  }

  function initVehicleConfirmModal() {
    initScopedConfirmModal('vehicle');
  }

  window.LayoutUi = {
    escapeHtml,
    showUserToast,
    openUserConfirmModal,
    initUserConfirmModal,
    showVehicleToast,
    openVehicleConfirmModal,
    initVehicleConfirmModal,
  };
})();
