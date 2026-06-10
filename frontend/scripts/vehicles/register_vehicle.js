const vehicleRegisterApiBaseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8000';

let vehicleRegisterSubmitting = false;
let titularValidado = false;
let seguroValidado = false;

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

function lockZone(zoneId, labelText = 'Completá el paso anterior primero') {
  const zone = document.querySelector(`[data-target="${zoneId}"]`);
  const input = document.getElementById(zoneId);
  const label = document.getElementById(`${zoneId}-label`);
  if (!zone) return;
  zone.dataset.locked = 'true';
  zone.classList.add('cursor-not-allowed', 'opacity-50');
  zone.classList.remove('cursor-pointer', 'hover:bg-surface-container-high');
  if (input) input.disabled = true;
  if (label) label.textContent = labelText;
}

function unlockZone(zoneId, labelText) {
  const zone = document.querySelector(`[data-target="${zoneId}"]`);
  const input = document.getElementById(zoneId);
  const label = document.getElementById(`${zoneId}-label`);
  if (!zone) return;
  delete zone.dataset.locked;
  zone.classList.remove('cursor-not-allowed', 'opacity-50');
  zone.classList.add('cursor-pointer', 'hover:bg-surface-container-high');
  if (input) input.disabled = false;
  if (label && labelText) label.textContent = labelText;
}

function setSeguroStatus(text, isError = false) {
  const el = document.getElementById('seguro-status');
  if (!el) return;
  if (!text) {
    el.classList.add('hidden');
    el.textContent = '';
    return;
  }
  el.textContent = text;
  el.classList.remove('hidden');
  el.classList.toggle('text-error', isError);
  el.classList.toggle('text-primary', !isError);
}

function setFotoVehiculoStatus(text, isError = false) {
  const el = document.getElementById('foto-vehiculo-status');
  if (!el) return;
  if (!text) {
    el.classList.add('hidden');
    el.textContent = '';
    return;
  }
  el.textContent = text;
  el.classList.remove('hidden');
  el.classList.toggle('text-error', isError);
  el.classList.toggle('text-primary', !isError);
}

function validateFotoVehiculo(file) {
  const allowed = new Set(['image/jpeg', 'image/jpg', 'image/png', 'image/webp']);
  if (!allowed.has(file.type)) {
    setFotoVehiculoStatus('Formato no soportado. Usá JPG, PNG o WEBP.', true);
    const input = document.getElementById('foto-vehiculo');
    if (input) input.value = '';
    return;
  }
  setFotoVehiculoStatus('');
}

function setCedulaTitularStatus(text, isError = false) {
  const el = document.getElementById('cedula-titular-status');
  if (!el) return;
  if (!text) {
    el.classList.add('hidden');
    el.textContent = '';
    return;
  }
  el.textContent = text;
  el.classList.remove('hidden');
  el.classList.toggle('text-error', isError);
  el.classList.toggle('text-primary', !isError);
}

function setCedulaExtractStatus(text, isError = false) {
  const el = document.getElementById('cedula-extract-status');
  if (!el) return;
  if (!text) {
    el.classList.add('hidden');
    el.textContent = '';
    return;
  }
  el.textContent = text;
  el.classList.remove('hidden');
  el.classList.toggle('text-error', isError);
  el.classList.toggle('text-primary', !isError);
}

function clearCedulaExtractedData() {
  const patenteInput = document.getElementById('patente');
  const marcaDisplay = document.getElementById('marca-display');
  const modeloDisplay = document.getElementById('modelo-display');
  const modeloIdInput = document.getElementById('modelo_id');
  if (patenteInput) patenteInput.value = '';
  if (marcaDisplay) {
    marcaDisplay.textContent = 'Se detectará desde la cédula';
    marcaDisplay.classList.add('text-outline-variant', 'italic');
    marcaDisplay.classList.remove('text-on-surface', 'font-semibold');
  }
  if (modeloDisplay) {
    modeloDisplay.textContent = 'Se detectará desde la cédula';
    modeloDisplay.classList.add('text-outline-variant', 'italic');
    modeloDisplay.classList.remove('text-on-surface', 'font-semibold');
  }
  if (modeloIdInput) modeloIdInput.value = '';
}

async function validateSeguro(file) {
  const token = getVehicleAuthToken();
  if (!token) {
    setSeguroStatus('Debes iniciar sesión para validar el seguro.', true);
    return;
  }

  const marca  = document.getElementById('marca-display')?.textContent?.trim() || '';
  const modelo = document.getElementById('modelo-display')?.textContent?.trim() || '';

  if (!marca || marca === 'Se detectará desde la cédula' || !modelo || modelo === 'Se detectará desde la cédula') {
    setSeguroStatus('Primero cargá la cédula frontal para detectar marca y modelo.', true);
    return;
  }

  seguroValidado = false;
  setSeguroStatus('Verificando seguro...');

  const formData = new FormData();
  formData.append('seguro', file);
  formData.append('marca', marca);
  formData.append('modelo', modelo);

  try {
    const response = await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos/seguro/validar`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setSeguroStatus(data.detail || 'No se pudo validar el seguro.', true);
      return;
    }

    if (data.valido) {
      seguroValidado = true;
      setSeguroStatus('Seguro verificado correctamente.');
    } else {
      seguroValidado = false;
      setSeguroStatus(data.mensaje || 'Los datos del seguro no coinciden.', true);
    }
  } catch {
    setSeguroStatus('No se pudo conectar con el servicio de validación.', true);
  }
}

async function validateCedulaTrasera(file) {
  const token = getVehicleAuthToken();
  if (!token) {
    setCedulaTitularStatus('Debes iniciar sesión para validar la cédula.', true);
    return;
  }

  titularValidado = false;
  setCedulaTitularStatus('Verificando titular...');

  const formData = new FormData();
  formData.append('cedula', file);

  try {
    const response = await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos/cedula/validar-titular`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setCedulaTitularStatus(data.detail || 'No se pudo validar el titular.', true);
      return;
    }

    if (data.valido) {
      titularValidado = true;
      setCedulaTitularStatus('Titular verificado correctamente.');
      unlockZone('seguro-pdf', 'JPG o PNG · hasta 10MB');
    } else {
      titularValidado = false;
      setCedulaTitularStatus(data.mensaje || 'Los datos del titular no coinciden.', true);
      lockZone('seguro-pdf');
      seguroValidado = false;
      setSeguroStatus('');
    }
  } catch {
    setCedulaTitularStatus('No se pudo conectar con el servicio de validación.', true);
    lockZone('seguro-pdf');
    seguroValidado = false;
    setSeguroStatus('');
  }
}

async function extractCedulaData(file) {
  clearCedulaExtractedData();
  setCedulaExtractStatus('Procesando cédula...');

  const formData = new FormData();
  formData.append('cedula', file);

  try {
    const response = await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos/cedula/extraer`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      setCedulaExtractStatus(data.detail || 'No se pudo procesar la cédula.', true);
      clearCedulaExtractedData();
      lockZone('cedula-trasera');
      lockZone('seguro-pdf');
      titularValidado = false;
      setCedulaTitularStatus('');
      seguroValidado = false;
      setSeguroStatus('');
      return;
    }

    const patenteInput = document.getElementById('patente');
    const marcaDisplay = document.getElementById('marca-display');
    const modeloDisplay = document.getElementById('modelo-display');
    const modeloIdInput = document.getElementById('modelo_id');

    if (patenteInput) patenteInput.value = (data.patente || '').trim().toUpperCase();

    if (marcaDisplay) {
      marcaDisplay.textContent = data.marca || '-';
      marcaDisplay.classList.remove('text-outline-variant', 'italic');
      marcaDisplay.classList.add('text-on-surface', 'font-semibold');
    }
    if (modeloDisplay) {
      modeloDisplay.textContent = data.modelo || '-';
      modeloDisplay.classList.remove('text-outline-variant', 'italic');
      modeloDisplay.classList.add('text-on-surface', 'font-semibold');
    }
    if (modeloIdInput) modeloIdInput.value = String(data.modelo_id || '');

    setCedulaExtractStatus('Patente, marca y modelo detectados correctamente.');
    unlockZone('cedula-trasera', 'JPG o PNG · hasta 10MB');
  } catch {
    setCedulaExtractStatus('No se pudo conectar con el servicio de extracción.', true);
    clearCedulaExtractedData();
    lockZone('cedula-trasera');
    lockZone('seguro-pdf');
    titularValidado = false;
    setCedulaTitularStatus('');
    seguroValidado = false;
    setSeguroStatus('');
  }
}

async function saveDocumentos(vehicleId, token) {
  const formData = new FormData();

  const cedulaFrente  = document.getElementById('cedula-frente')?.files?.[0];
  const cedulaTrasera = document.getElementById('cedula-trasera')?.files?.[0];
  const seguroPdf     = document.getElementById('seguro-pdf')?.files?.[0];
  const fotoVehiculo  = document.getElementById('foto-vehiculo')?.files?.[0];

  if (cedulaFrente)  formData.append('cedula_delantera', cedulaFrente);
  if (cedulaTrasera) formData.append('cedula_trasera',   cedulaTrasera);
  if (seguroPdf)     formData.append('seguro',           seguroPdf);
  if (fotoVehiculo)  formData.append('foto_vehiculo',    fotoVehiculo);

  if (!formData.has('cedula_delantera') && !formData.has('cedula_trasera') &&
      !formData.has('seguro') && !formData.has('foto_vehiculo')) return;

  try {
    await fetch(`${vehicleRegisterApiBaseUrl}/vehiculos/${vehicleId}/documentos`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
  } catch {
    // No bloquea el flujo si falla el guardado de documentos
  }
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
  const anio = document.getElementById('anio')?.value || '';
  const modeloId = document.getElementById('modelo_id')?.value || '';

  if (!patente || !anio || !modeloId) {
    setVehicleRegisterMessage('Ingresá el año y cargá la cédula para detectar patente, marca y modelo.', true);
    return;
  }

  if (!titularValidado) {
    setVehicleRegisterMessage('Cargá la parte trasera de la cédula para verificar que el vehículo te pertenece.', true);
    return;
  }

  if (!seguroValidado) {
    setVehicleRegisterMessage('Cargá el seguro del vehículo para verificar que los datos coinciden.', true);
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

    const vehicleId = data.id;

    if (data.nuevo_token) {
      localStorage.setItem('auth_token', data.nuevo_token);
    }

    setVehicleRegisterMessage('Vehículo registrado. Guardando documentos...');
    await saveDocumentos(vehicleId, data.nuevo_token || token);

    setVehicleRegisterMessage('Vehículo registrado. Redirigiendo...');
    setTimeout(() => { window.location.href = 'deshboard_vehiculos.html'; }, 1200);
  } catch {
    setVehicleRegisterMessage('No se pudo conectar con el backend.', true);
  } finally {
    setVehicleRegisterSubmittingState(false);
  }
}

const UPLOAD_ZONES = [
  { zoneId: 'cedula-frente',  labelId: 'cedula-frente-label',  maxMB: 10 },
  { zoneId: 'cedula-trasera', labelId: 'cedula-trasera-label', maxMB: 10 },
  { zoneId: 'seguro-pdf',     labelId: 'seguro-pdf-label',     maxMB: 10 },
  { zoneId: 'foto-vehiculo',  labelId: 'foto-vehiculo-label',  maxMB: 5  },
];

function setupUploadZones() {
  for (const { zoneId, labelId, maxMB } of UPLOAD_ZONES) {
    const input = document.getElementById(zoneId);
    const label = document.getElementById(labelId);
    const zone = document.querySelector(`[data-target="${zoneId}"]`);
    if (!input || !label || !zone) continue;

    input.addEventListener('change', () => {
      const file = input.files?.[0];
      if (!file) return;
      applyFileSelection(zone, label, file, maxMB);
      if (zoneId === 'cedula-frente') extractCedulaData(file);
      if (zoneId === 'cedula-trasera') validateCedulaTrasera(file);
      if (zoneId === 'seguro-pdf') validateSeguro(file);
      if (zoneId === 'foto-vehiculo') validateFotoVehiculo(file);
    });

    zone.addEventListener('dragover', (e) => {
      e.preventDefault();
      zone.classList.add('bg-surface-container-high');
    });

    zone.addEventListener('dragleave', () => {
      if (!input.files?.length) zone.classList.remove('bg-surface-container-high');
    });

    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      if (zone.dataset.locked === 'true') return;
      const file = e.dataTransfer?.files?.[0];
      if (!file) return;
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      applyFileSelection(zone, label, file, maxMB);
      if (zoneId === 'cedula-frente') extractCedulaData(file);
      if (zoneId === 'cedula-trasera') validateCedulaTrasera(file);
      if (zoneId === 'seguro-pdf') validateSeguro(file);
      if (zoneId === 'foto-vehiculo') validateFotoVehiculo(file);
    });
  }
}

function applyFileSelection(zone, label, file, maxMB) {
  if (file.size > maxMB * 1024 * 1024) {
    label.textContent = `El archivo supera los ${maxMB}MB`;
    label.classList.add('text-error');
    return;
  }
  label.textContent = file.name;
  label.classList.remove('text-error');
  label.classList.add('text-primary', 'font-semibold');
  zone.classList.add('border-primary/50', 'bg-surface-container-high');
  zone.classList.remove('border-outline-variant/30');
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('vehicle-register-form');
  const patentInput = document.getElementById('patente');

  if (!form || !patentInput) return;

  setupUploadZones();
  form.addEventListener('submit', handleVehicleRegisterSubmit);
});
