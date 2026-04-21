(function () {
  const layoutShell = window.LayoutShell;
  const layoutUi = window.LayoutUi;

  if (!layoutShell) {
    throw new Error('No se cargó layout_shell.js antes de layout_vehicles.js');
  }
  if (!layoutUi) {
    throw new Error('No se cargó layout_ui.js antes de layout_vehicles.js');
  }

  const API_BASE_URL = layoutShell.API_BASE_URL;
  const { setButtonLoadingState } = layoutShell;
  const {
    escapeHtml,
    showVehicleToast,
    openVehicleConfirmModal,
    initVehicleConfirmModal,
  } = layoutUi;

  let vehicleDashboardCache = [];
  let editingVehicleId = null;
  let vehicleEditSubmitting = false;
  let vehicleEditModelsCache = [];

  function normalizeVehicleText(value) {
    return (value || '').toString().trim().toLowerCase();
  }

  function getVehicleStatusBadge(statusRaw) {
    const status = normalizeVehicleText(statusRaw);
    if (status === 'activo') {
      return { label: 'Activo', className: 'bg-green-50 text-green-700' };
    }
    if (status === 'inactivo') {
      return { label: 'Inactivo', className: 'bg-surface-container text-slate-500' };
    }
    if (status === 'en validacion') {
      return { label: 'En validacion', className: 'bg-tertiary-fixed text-tertiary' };
    }
    if (status === 'rechazado') {
      return { label: 'Rechazado', className: 'bg-red-50 text-red-700' };
    }
    if (status === 'alquilado') {
      return { label: 'Alquilado', className: 'bg-blue-50 text-blue-700' };
    }
    if (status === 'en taller') {
      return { label: 'En Taller', className: 'bg-amber-50 text-amber-700' };
    }
    return { label: statusRaw || 'Sin estado', className: 'bg-surface-container text-slate-600' };
  }

  async function fetchVehicleDashboard() {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      throw new Error('Debes iniciar sesión para ver vehículos.');
    }

    const response = await fetch(`${API_BASE_URL}/vehiculos`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || 'No se pudo cargar el dashboard de vehículos.');
    }

    return data;
  }

  function updateVehicleDashboardStats(vehicles) {
    const totalEl = document.getElementById('stats-total-vehicles');
    const activeEl = document.getElementById('stats-active-vehicles');
    const maintenanceEl = document.getElementById('stats-maintenance-vehicles');

    if (!totalEl && !activeEl && !maintenanceEl) return;

    const safeVehicles = Array.isArray(vehicles) ? vehicles : [];
    const total = safeVehicles.length;
    const active = safeVehicles.filter((vehicle) => normalizeVehicleText(vehicle.estado_vehiculo) === 'activo').length;
    const maintenance = safeVehicles.filter((vehicle) => normalizeVehicleText(vehicle.estado_vehiculo) === 'en taller').length;

    if (totalEl) totalEl.textContent = String(total);
    if (activeEl) activeEl.textContent = String(active);
    if (maintenanceEl) maintenanceEl.textContent = String(maintenance);
  }

  function populateVehicleFilterOptions(vehicles) {
    const brandFilter = document.getElementById('vehicle-brand-filter');
    const yearFilter = document.getElementById('vehicle-year-filter');
    if (!brandFilter || !yearFilter) return;

    const selectedBrand = brandFilter.value || 'all';
    const selectedYear = yearFilter.value || 'all';

    const brands = [...new Set((vehicles || []).map((vehicle) => (vehicle.marca_nombre || '').trim()).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b));
    const years = [...new Set((vehicles || []).map((vehicle) => String(vehicle.anio || '').trim()).filter(Boolean))]
      .sort((a, b) => Number(b) - Number(a));

    brandFilter.innerHTML = '<option value="all">Todas</option>';
    brands.forEach((brand) => {
      const option = document.createElement('option');
      option.value = normalizeVehicleText(brand);
      option.textContent = brand;
      brandFilter.appendChild(option);
    });

    yearFilter.innerHTML = '<option value="all">Todos</option>';
    years.forEach((year) => {
      const option = document.createElement('option');
      option.value = year;
      option.textContent = year;
      yearFilter.appendChild(option);
    });

    brandFilter.value = Array.from(brandFilter.options).some((option) => option.value === selectedBrand)
      ? selectedBrand
      : 'all';
    yearFilter.value = Array.from(yearFilter.options).some((option) => option.value === selectedYear)
      ? selectedYear
      : 'all';
  }

  function renderVehicleDashboard(vehicles) {
    const tbody = document.getElementById('vehicles-table-body');
    const summaryLabel = document.getElementById('vehicles-summary-label');
    if (!tbody) return;

    if (!vehicles || vehicles.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="px-6 py-10 text-center text-slate-500 font-medium">No hay vehículos para mostrar.</td>
        </tr>
      `;
      if (summaryLabel) summaryLabel.textContent = 'Mostrando 0 vehículos';
      return;
    }

    tbody.innerHTML = vehicles.map((vehicle) => {
      const status = getVehicleStatusBadge(vehicle.estado_vehiculo);
      const isInactive = normalizeVehicleText(vehicle.estado_vehiculo) === 'inactivo';
      const actionButtonHtml = isInactive
        ? `
            <div class="flex justify-end gap-2">
              <button class="p-2 text-slate-400 hover:text-primary transition-colors hover:bg-primary-fixed rounded-lg" type="button" data-vehicle-action="activate" data-vehicle-id="${vehicle.id}" title="Activar vehículo">
                <span class="material-symbols-outlined text-lg">check_circle</span>
              </button>
            </div>
          `
        : `
            <div class="flex justify-end gap-2">
              <button class="p-2 text-slate-400 hover:text-primary transition-colors hover:bg-primary-fixed rounded-lg" type="button" data-vehicle-action="edit" data-vehicle-id="${vehicle.id}" title="Editar vehículo">
                <span class="material-symbols-outlined text-lg">edit</span>
              </button>
              <button class="p-2 text-slate-400 hover:text-error transition-colors hover:bg-error-container rounded-lg" type="button" data-vehicle-action="deactivate" data-vehicle-id="${vehicle.id}" title="Dar de baja">
                <span class="material-symbols-outlined text-lg">delete</span>
              </button>
            </div>
          `;

      return `
        <tr class="hover:bg-surface-bright transition-colors group">
          <td class="px-6 py-5">
            <div class="flex items-center gap-4">
              ${vehicle.foto_vehiculo
                ? `<img src="http://localhost:8000/uploads/documentos/${escapeHtml(vehicle.foto_vehiculo)}" alt="Foto del vehículo" class="w-10 h-10 rounded-full object-cover bg-surface-container" onerror="this.style.display='none';this.nextElementSibling.style.display='flex'">`
                : ''}
              <div class="w-10 h-10 rounded-full bg-primary-fixed text-primary items-center justify-center font-bold text-xs ${vehicle.foto_vehiculo ? 'hidden' : 'flex'}">
                ${escapeHtml((vehicle.modelo_nombre || 'M').charAt(0).toUpperCase())}
              </div>
              <div>
                <span class="block text-sm font-bold text-on-surface">${escapeHtml(vehicle.modelo_nombre || '-')}</span>
                <span class="block text-xs text-secondary">ID #${escapeHtml(vehicle.id)}</span>
              </div>
            </div>
          </td>
          <td class="px-6 py-5 text-center">
            <span class="bg-surface-container px-2 py-1 rounded font-mono text-xs text-on-surface-variant font-bold">${escapeHtml(vehicle.patente || '-')}</span>
          </td>
          <td class="px-6 py-5">
            <span class="text-sm font-semibold text-on-surface">${escapeHtml(vehicle.marca_nombre || '-')}</span>
          </td>
          <td class="px-6 py-5">
            <span class="text-sm font-semibold text-on-surface">${escapeHtml(vehicle.anio || '-')}</span>
          </td>
          <td class="px-6 py-5">
            <span class="px-3 py-1 ${status.className} text-[10px] font-bold uppercase tracking-wider rounded-full">${escapeHtml(status.label)}</span>
          </td>
          <td class="px-6 py-5 text-right">
            ${actionButtonHtml}
          </td>
        </tr>
      `;
    }).join('');

    if (summaryLabel) {
      const total = vehicles.length;
      summaryLabel.textContent = `Mostrando ${total} vehículo${total === 1 ? '' : 's'}`;
    }
  }

  function setVehicleEditModalMessage(text, isError = false) {
    const message = document.getElementById('vehicle-edit-form-message');
    if (!message) return;

    message.textContent = text;
    message.classList.toggle('text-error', isError);
    message.classList.toggle('text-primary', !isError);
  }

  function setVehicleEditSubmittingState(isSubmitting) {
    vehicleEditSubmitting = isSubmitting;

    const saveButton = document.getElementById('vehicle-edit-save');
    const cancelButton = document.getElementById('vehicle-edit-cancel');
    const closeButton = document.getElementById('vehicle-edit-modal-close');

    if (saveButton) {
      saveButton.disabled = isSubmitting;
      saveButton.classList.toggle('opacity-60', isSubmitting);
      saveButton.classList.toggle('cursor-not-allowed', isSubmitting);
      saveButton.textContent = isSubmitting ? 'Guardando...' : 'Guardar cambios';
    }
    if (cancelButton) cancelButton.disabled = isSubmitting;
    if (closeButton) closeButton.disabled = isSubmitting;
  }

  async function ensureVehicleEditModels() {
    const modelSelect = document.getElementById('edit-vehicle-modelo');
    if (!modelSelect) return;

    if (vehicleEditModelsCache.length === 0) {
      const response = await fetch(`${API_BASE_URL}/vehiculos/modelos`);
      if (!response.ok) {
        throw new Error('No se pudieron cargar los modelos de vehículos.');
      }

      vehicleEditModelsCache = await response.json();
    }

    modelSelect.innerHTML = '<option value="">Seleccionar modelo</option>';
    vehicleEditModelsCache.forEach((model) => {
      const option = document.createElement('option');
      option.value = String(model.id);
      option.textContent = `${model.marca_nombre} - ${model.nombre}`;
      modelSelect.appendChild(option);
    });
  }

  function sanitizeVehiclePatentInput(value) {
    return (value || '').toString().toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10);
  }

  function isValidVehiclePatent(value) {
    return /^[A-Z0-9]{6,10}$/.test(value);
  }

  function closeVehicleEditModal(force = false) {
    if (vehicleEditSubmitting && !force) return;

    const modal = document.getElementById('vehicle-edit-modal');
    if (!modal) return;

    modal.classList.add('hidden');
    editingVehicleId = null;
    setVehicleEditSubmittingState(false);
    setVehicleEditModalMessage('');
  }

  async function openVehicleEditModal(vehicleId) {
    const modal = document.getElementById('vehicle-edit-modal');
    if (!modal) return;

    const vehicle = vehicleDashboardCache.find((item) => Number(item.id) === Number(vehicleId));
    if (!vehicle) {
      showVehicleToast('No se encontró el vehículo a editar.', 'error');
      return;
    }

    try {
      await ensureVehicleEditModels();
    } catch (error) {
      showVehicleToast(error.message || 'No se pudieron cargar los modelos.', 'error');
      return;
    }

    editingVehicleId = Number(vehicleId);

    const patentInput = document.getElementById('edit-vehicle-patente');
    const yearInput = document.getElementById('edit-vehicle-anio');
    const modelInput = document.getElementById('edit-vehicle-modelo');

    if (patentInput) patentInput.value = vehicle.patente || '';
    if (yearInput) yearInput.value = String(vehicle.anio || '');
    if (modelInput) modelInput.value = String(vehicle.modelo_id || '');

    setVehicleEditSubmittingState(false);
    setVehicleEditModalMessage('');
    modal.classList.remove('hidden');
  }

  async function updateVehicleById(vehicleId, payload) {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/vehiculos/${vehicleId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || 'No se pudo actualizar el vehículo.');
    }

    return data;
  }

  async function deactivateVehicleById(vehicleId) {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/vehiculos/${vehicleId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || 'No se pudo dar de baja al vehículo.');
    }

    return data;
  }

  async function activateVehicleById(vehicleId) {
    const token = localStorage.getItem('auth_token');
    const response = await fetch(`${API_BASE_URL}/vehiculos/${vehicleId}/activate`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || 'No se pudo activar el vehículo.');
    }

    return data;
  }

  async function submitVehicleEditModal(event) {
    event.preventDefault();

    if (vehicleEditSubmitting) return;
    if (!editingVehicleId) {
      setVehicleEditModalMessage('No se encontró el vehículo a editar.', true);
      return;
    }

    const patentInput = document.getElementById('edit-vehicle-patente');
    const yearInput = document.getElementById('edit-vehicle-anio');
    const modelInput = document.getElementById('edit-vehicle-modelo');

    const patente = sanitizeVehiclePatentInput(patentInput?.value || '');
    const anio = Number.parseInt(yearInput?.value || '', 10);
    const modeloId = Number.parseInt(modelInput?.value || '', 10);

    if (!patente || Number.isNaN(anio) || Number.isNaN(modeloId)) {
      setVehicleEditModalMessage('Completá patente, año y modelo.', true);
      return;
    }

    if (!isValidVehiclePatent(patente)) {
      setVehicleEditModalMessage('La patente debe tener entre 6 y 10 caracteres alfanuméricos.', true);
      return;
    }

    if (anio < 1980) {
      setVehicleEditModalMessage('El año del vehículo no es válido.', true);
      return;
    }

    const payload = {
      patente,
      anio,
      modelo_id: modeloId,
    };

    try {
      setVehicleEditSubmittingState(true);
      setVehicleEditModalMessage('Guardando cambios...');
      await updateVehicleById(editingVehicleId, payload);
      closeVehicleEditModal(true);
      showVehicleToast('Vehículo actualizado correctamente.', 'success');
      await initVehicleDashboardPage('deshboard_vehiculos.html');
    } catch (error) {
      setVehicleEditModalMessage(error.message || 'No se pudo actualizar el vehículo.', true);
      showVehicleToast(error.message || 'No se pudo actualizar el vehículo.', 'error');
    } finally {
      setVehicleEditSubmittingState(false);
    }
  }

  function initVehicleEditModal() {
    const modal = document.getElementById('vehicle-edit-modal');
    const closeBtn = document.getElementById('vehicle-edit-modal-close');
    const cancelBtn = document.getElementById('vehicle-edit-cancel');
    const backdrop = document.getElementById('vehicle-edit-modal-backdrop');
    const form = document.getElementById('vehicle-edit-form');
    const patentInput = document.getElementById('edit-vehicle-patente');

    if (!modal || !closeBtn || !cancelBtn || !backdrop || !form || !patentInput) return;
    if (modal.dataset.boundModal === '1') return;

    closeBtn.addEventListener('click', closeVehicleEditModal);
    cancelBtn.addEventListener('click', closeVehicleEditModal);
    backdrop.addEventListener('click', closeVehicleEditModal);
    form.addEventListener('submit', submitVehicleEditModal);

    patentInput.addEventListener('input', () => {
      const sanitized = sanitizeVehiclePatentInput(patentInput.value);
      if (sanitized !== patentInput.value) {
        patentInput.value = sanitized;
      }
    });

    modal.dataset.boundModal = '1';
  }

  async function handleVehicleDashboardAction(event) {
    const button = event.target.closest('button[data-vehicle-action]');
    if (!button) return;
    if (button.disabled) return;

    const vehicleId = Number.parseInt(button.dataset.vehicleId || '', 10);
    const action = button.dataset.vehicleAction || '';
    if (!vehicleId || !action) return;

    try {
      setButtonLoadingState(button, true);

      if (action === 'edit') {
        await openVehicleEditModal(vehicleId);
        return;
      }

      if (action === 'deactivate') {
        const confirmed = await openVehicleConfirmModal('Esta acción hará una baja lógica del vehículo. ¿Continuar?', 'Dar de baja');
        if (!confirmed) return;
        await deactivateVehicleById(vehicleId);
        showVehicleToast('Vehículo dado de baja correctamente.', 'success');
        await initVehicleDashboardPage('deshboard_vehiculos.html');
      }

      if (action === 'activate') {
        const confirmed = await openVehicleConfirmModal('Este vehículo volverá a estado activo. ¿Continuar?', 'Activar');
        if (!confirmed) return;
        await activateVehicleById(vehicleId);
        showVehicleToast('Vehículo activado correctamente.', 'success');
        await initVehicleDashboardPage('deshboard_vehiculos.html');
      }
    } catch (error) {
      showVehicleToast(error.message || 'No se pudo completar la acción.', 'error');
    } finally {
      setButtonLoadingState(button, false);
    }
  }

  function applyVehicleDashboardFilters() {
    const brandFilter = document.getElementById('vehicle-brand-filter');
    const statusFilter = document.getElementById('vehicle-status-filter');
    const yearFilter = document.getElementById('vehicle-year-filter');
    const searchInput = document.getElementById('vehicle-search-input');

    const selectedBrand = normalizeVehicleText(brandFilter?.value || 'all');
    const selectedStatus = normalizeVehicleText(statusFilter?.value || 'all');
    const selectedYear = (yearFilter?.value || 'all').toString().trim();
    const searchTerm = normalizeVehicleText(searchInput?.value || '');

    const filteredVehicles = vehicleDashboardCache.filter((vehicle) => {
      const vehicleBrand = normalizeVehicleText(vehicle.marca_nombre);
      const vehicleStatus = normalizeVehicleText(vehicle.estado_vehiculo);
      const vehicleYear = String(vehicle.anio || '').trim();

      const matchesBrand = selectedBrand === 'all' || vehicleBrand === selectedBrand;
      const matchesStatus = selectedStatus === 'all' || vehicleStatus === selectedStatus;
      const matchesYear = selectedYear === 'all' || vehicleYear === selectedYear;

      const searchableText = [
        vehicle.patente,
        vehicle.modelo_nombre,
        vehicle.marca_nombre,
        vehicle.estado_vehiculo,
        vehicle.anio,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase();

      const matchesSearch = !searchTerm || searchableText.includes(searchTerm);
      return matchesBrand && matchesStatus && matchesYear && matchesSearch;
    });

    renderVehicleDashboard(filteredVehicles);
  }

  function initVehicleDashboardFilters() {
    const brandFilter = document.getElementById('vehicle-brand-filter');
    const statusFilter = document.getElementById('vehicle-status-filter');
    const yearFilter = document.getElementById('vehicle-year-filter');
    const searchInput = document.getElementById('vehicle-search-input');
    const resetButton = document.getElementById('reset-vehicle-filters-btn');

    if (!brandFilter || !statusFilter || !yearFilter || !searchInput || !resetButton) return;
    if (resetButton.dataset.boundFilters === '1') return;

    brandFilter.addEventListener('change', applyVehicleDashboardFilters);
    statusFilter.addEventListener('change', applyVehicleDashboardFilters);
    yearFilter.addEventListener('change', applyVehicleDashboardFilters);
    searchInput.addEventListener('input', applyVehicleDashboardFilters);

    resetButton.addEventListener('click', (event) => {
      event.preventDefault();
      brandFilter.value = 'all';
      statusFilter.value = 'all';
      yearFilter.value = 'all';
      searchInput.value = '';
      applyVehicleDashboardFilters();
    });

    resetButton.dataset.boundFilters = '1';
  }

  async function initVehicleDashboardPage(current) {
    if (current !== 'deshboard_vehiculos.html') return;

    const tbody = document.getElementById('vehicles-table-body');
    if (!tbody) return;

    initVehicleDashboardFilters();
    initVehicleEditModal();
    initVehicleConfirmModal();

    if (!tbody.dataset.boundActions) {
      tbody.addEventListener('click', handleVehicleDashboardAction);
      tbody.dataset.boundActions = '1';
    }

    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-6 py-10 text-center text-slate-500 font-medium">Cargando vehículos...</td>
      </tr>
    `;

    try {
      const vehicles = await fetchVehicleDashboard();
      vehicleDashboardCache = Array.isArray(vehicles) ? vehicles : [];
      updateVehicleDashboardStats(vehicleDashboardCache);
      populateVehicleFilterOptions(vehicleDashboardCache);
      applyVehicleDashboardFilters();
    } catch (error) {
      vehicleDashboardCache = [];
      updateVehicleDashboardStats([]);
      populateVehicleFilterOptions([]);
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="px-6 py-10 text-center text-error font-semibold">${escapeHtml(error.message || 'No se pudo cargar el dashboard de vehículos.')}</td>
        </tr>
      `;
    }
  }

  window.LayoutVehicles = {
    initVehicleDashboardPage,
  };
})();
