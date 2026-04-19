const vehicleRegisterApiBaseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8000';

let vehicleRegisterSubmitting = false;

function setVehicleRegisterMessage(text, isError = false) {
  const message = document.getElementById('vehicle-register-message');
  if (!message) return;

  message.textContent = text;
  message.classList.toggle('text-error', isError);
  message.classList.toggle('text-primary', !isError);
}

function setVehicleRegisterSubmittingState(isSubmitting) {
  vehicleRegisterSubmitting = isSubmitting;

  const submitButton = document.getElementById('vehicle-register-submit');
  if (!submitButton) return;

  submitButton.disabled = isSubmitting;
  submitButton.classList.toggle('opacity-60', isSubmitting);
  submitButton.classList.toggle('cursor-not-allowed', isSubmitting);
}

function getVehicleAuthToken() {
  return localStorage.getItem('auth_token');
}

async function loadVehicleBrands() {
  const brandSelect = document.getElementById('marca');
  if (!brandSelect) return;

  const response = await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos/marcas`);
  if (!response.ok) return;

  const brands = await response.json();
  brandSelect.innerHTML = '<option value="">Seleccionar marca</option>';

  brands.forEach((brand) => {
    const option = document.createElement('option');
    option.value = String(brand.id);
    option.textContent = brand.nombre;
    brandSelect.appendChild(option);
  });
}

async function loadVehicleModels(marcaId) {
  const modelSelect = document.getElementById('modelo');
  if (!modelSelect) return;

  modelSelect.innerHTML = '<option value="">Seleccionar modelo</option>';
  modelSelect.disabled = true;

  if (!marcaId) return;

  const response = await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos/modelos?marca_id=${encodeURIComponent(marcaId)}`);
  if (!response.ok) return;

  const models = await response.json();
  models.forEach((model) => {
    const option = document.createElement('option');
    option.value = String(model.id);
    option.textContent = model.nombre;
    modelSelect.appendChild(option);
  });

  modelSelect.disabled = models.length === 0;
}

function isValidPatent(patente) {
  return /^[A-Z0-9]{6,10}$/.test(patente);
}

function sanitizePatentInput(value) {
  return (value || '').toString().toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10);
}

function isValidYear(anio) {
  const year = Number.parseInt(anio, 10);
  const currentYear = new Date().getFullYear();
  return Number.isInteger(year) && year >= 1980 && year <= currentYear + 1;
}

async function handleVehicleRegisterSubmit(event) {
  event.preventDefault();

  if (vehicleRegisterSubmitting) return;

  const token = getVehicleAuthToken();
  if (!token) {
    setVehicleRegisterMessage('Debes iniciar sesión para registrar un vehículo.', true);
    return;
  }

  const patente = (document.getElementById('patente')?.value || '').trim().toUpperCase();
  const marcaId = document.getElementById('marca')?.value || '';
  const modeloId = document.getElementById('modelo')?.value || '';
  const anio = document.getElementById('anio')?.value || '';

  if (!patente || !marcaId || !modeloId || !anio) {
    setVehicleRegisterMessage('Completá patente, marca, modelo y año.', true);
    return;
  }

  if (!isValidPatent(patente)) {
    setVehicleRegisterMessage('La patente debe tener entre 6 y 10 caracteres alfanuméricos, sin espacios ni símbolos.', true);
    return;
  }

  if (!isValidYear(anio)) {
    setVehicleRegisterMessage('El año del vehículo no es válido.', true);
    return;
  }

  try {
    setVehicleRegisterSubmittingState(true);
    setVehicleRegisterMessage('Registrando vehículo...');

    const response = await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        patente,
        modelo_id: Number.parseInt(modeloId, 10),
        anio: Number.parseInt(anio, 10),
      }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setVehicleRegisterMessage(data.detail || 'No se pudo registrar el vehículo.', true);
      return;
    }

    setVehicleRegisterMessage('Vehículo registrado correctamente.');
    const form = document.getElementById('vehicle-register-form');
    if (form) form.reset();
    const modelSelect = document.getElementById('modelo');
    if (modelSelect) {
      modelSelect.innerHTML = '<option value="">Seleccionar modelo</option>';
      modelSelect.disabled = true;
    }
  } catch (error) {
    setVehicleRegisterMessage('No se pudo conectar con el backend.', true);
  } finally {
    setVehicleRegisterSubmittingState(false);
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('vehicle-register-form');
  const brandSelect = document.getElementById('marca');
  const patentInput = document.getElementById('patente');

  if (!form || !brandSelect || !patentInput) return;

  try {
    await loadVehicleBrands();
  } catch (error) {
    setVehicleRegisterMessage('No se pudieron cargar las marcas de vehículos.', true);
  }

  brandSelect.addEventListener('change', async () => {
    await loadVehicleModels(brandSelect.value);
  });

  patentInput.maxLength = 10;
  patentInput.addEventListener('input', () => {
    const sanitized = sanitizePatentInput(patentInput.value);
    if (sanitized !== patentInput.value) {
      patentInput.value = sanitized;
    }
  });

  form.addEventListener('submit', handleVehicleRegisterSubmit);
});