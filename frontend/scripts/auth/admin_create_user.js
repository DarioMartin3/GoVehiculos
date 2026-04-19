const adminCreateUserApiBaseUrl = typeof API_BASE_URL !== 'undefined' ? API_BASE_URL : 'http://localhost:8000';
let adminCreateUserSubmitting = false;

function setAdminCreateUserSubmittingState(isSubmitting) {
  const form = document.getElementById('admin-create-user-form');
  if (!form) return;

  const submitButton = form.querySelector('button[type="submit"]');
  if (!submitButton) return;

  adminCreateUserSubmitting = isSubmitting;
  submitButton.disabled = isSubmitting;
  submitButton.classList.toggle('opacity-60', isSubmitting);
  submitButton.classList.toggle('cursor-not-allowed', isSubmitting);

  const label = submitButton.querySelector('span.material-symbols-outlined')
    ? submitButton.lastChild
    : null;
  if (label && label.nodeType === Node.TEXT_NODE) {
    label.textContent = isSubmitting ? ' Creando usuario...' : ' Crear Usuario';
  }
}

function isValidDni(dni) {
  return /^\d{7,10}$/.test(dni);
}

function isValidPhone(phone) {
  return /^[0-9+\-\s()]{8,20}$/.test(phone);
}

function setAdminCreateUserMessage(text, isError = false) {
  const message = document.getElementById('admin-create-user-message');
  if (!message) return;

  message.textContent = text;
  message.classList.toggle('text-error', isError);
  message.classList.toggle('text-primary', !isError);
}

async function loadCountriesForAdminCreateUser() {
  const paisSelect = document.getElementById('pais');
  if (!paisSelect) return;

  try {
    const response = await fetch(`${adminCreateUserApiBaseUrl}/auth/paises`);
    if (!response.ok) return;

    const countries = await response.json();
    const currentValue = paisSelect.value;
    paisSelect.innerHTML = '<option value="">Seleccionar pais</option>';

    countries.forEach((country) => {
      const option = document.createElement('option');
      option.value = String(country.id);
      option.textContent = country.nombre;
      paisSelect.appendChild(option);
    });

    if (currentValue) {
      paisSelect.value = currentValue;
    }
  } catch (error) {
    // Silencio: el usuario podrá intentar cargar luego.
  }
}

async function handleAdminCreateUserSubmit(event) {
  event.preventDefault();

  if (adminCreateUserSubmitting) return;

  const form = document.getElementById('admin-create-user-form');
  if (!form) return;

  const nombre = document.getElementById('name')?.value.trim() || '';
  const apellido = document.getElementById('surname')?.value.trim() || '';
  const email = document.getElementById('email')?.value.trim() || '';
  const rol = document.getElementById('assigned_role')?.value.trim() || '';
  const dni = document.getElementById('dni')?.value.trim() || null;
  const telefono = document.getElementById('phone')?.value.trim() || null;
  const paisValue = document.getElementById('pais')?.value || '';
  const estadoUsuarioValue = document.getElementById('estado_usuario')?.value || '1';
  const password = document.getElementById('password')?.value || '';
  const confirmPassword = document.getElementById('confirm_password')?.value || '';

  const pais = paisValue ? Number.parseInt(paisValue, 10) : null;
  const estado_usuario = Number.parseInt(estadoUsuarioValue, 10);

  if (!nombre || !apellido || !email || !rol || !dni || !telefono || !pais || !password) {
    setAdminCreateUserMessage('Completá todos los campos requeridos.', true);
    return;
  }

  if (!isValidDni(dni)) {
    setAdminCreateUserMessage('El DNI debe contener solo números (7 a 10 dígitos).', true);
    return;
  }

  if (!isValidPhone(telefono)) {
    setAdminCreateUserMessage('El teléfono tiene un formato inválido.', true);
    return;
  }

  if (password.length < 8) {
    setAdminCreateUserMessage('La contraseña debe tener al menos 8 caracteres.', true);
    return;
  }

  if (password !== confirmPassword) {
    setAdminCreateUserMessage('Las contraseñas no coinciden.', true);
    return;
  }

  const payload = {
    nombre,
    apellido,
    email,
    telefono,
    dni,
    pais,
    password,
    rol,
    estado_usuario,
  };

  try {
    setAdminCreateUserSubmittingState(true);
    setAdminCreateUserMessage('Creando usuario...');

    const response = await fetch(`${adminCreateUserApiBaseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      setAdminCreateUserMessage(data.detail || 'No se pudo crear el usuario.', true);
      return;
    }

    setAdminCreateUserMessage('Usuario creado correctamente.');
    form.reset();
  } catch (error) {
    setAdminCreateUserMessage('No se pudo conectar con el backend.', true);
  } finally {
    setAdminCreateUserSubmittingState(false);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('admin-create-user-form');
  if (!form) return;

  form.addEventListener('submit', handleAdminCreateUserSubmit);
  loadCountriesForAdminCreateUser();
});
