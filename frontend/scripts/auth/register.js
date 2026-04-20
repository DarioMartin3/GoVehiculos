const registerApiBaseUrl = typeof API_BASE_URL !== "undefined" ? API_BASE_URL : "http://localhost:8000";

let documentoValidado = false;

function setMessage(text, isError = false) {
    const message = document.getElementById("register-message");
    if (!message) return;
    message.textContent = text;
    message.classList.toggle("text-error", isError);
    message.classList.toggle("text-primary", !isError);
}

function setDocumentStatus(text, state) {
    const el = document.getElementById("document-validation-status");
    const submitBtn = document.querySelector("#register-form button[type='submit']");
    if (!el) return;

    el.textContent = text;
    el.classList.remove("hidden", "text-green-600", "text-error", "text-slate-500");

    if (state === "success") {
        el.classList.add("text-green-600");
        documentoValidado = true;
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.classList.remove("opacity-40", "cursor-not-allowed", "grayscale");
        }
    } else if (state === "error") {
        el.classList.add("text-error");
        documentoValidado = false;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add("opacity-40", "cursor-not-allowed", "grayscale");
        }
    } else {
        el.classList.add("text-slate-500");
        documentoValidado = false;
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.classList.add("opacity-40", "cursor-not-allowed", "grayscale");
        }
    }
}

function getFormFields() {
    return {
        nombre: document.getElementById("first-name")?.value.trim() || "",
        apellido: document.getElementById("last-name")?.value.trim() || "",
        dni: document.getElementById("dni")?.value.trim() || "",
        fechaNacimiento: document.getElementById("fecha-nacimiento")?.value || "",
    };
}

async function handleDocumentoChange(event) {
    const file = event.target.files?.[0];
    if (!file) return;

    const { nombre, apellido, dni, fechaNacimiento } = getFormFields();

    if (!nombre || !apellido || !dni || !fechaNacimiento) {
        setDocumentStatus("Completá nombre, apellido, DNI y fecha de nacimiento antes de subir el documento.", "error");
        event.target.value = "";
        return;
    }

    setDocumentStatus("Validando documento...", "loading");

    const formData = new FormData();
    formData.append("documento", file);
    formData.append("nombre", nombre);
    formData.append("apellido", apellido);
    formData.append("dni", dni);
    formData.append("fecha_nacimiento", fechaNacimiento);

    try {
        const response = await fetch(`${registerApiBaseUrl}/documents/validate-document`, {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            setDocumentStatus(data.detail || "No se pudo validar el documento.", "error");
            return;
        }

        if (data.valido) {
            setDocumentStatus("Documento validado correctamente.", "success");
        } else {
            setDocumentStatus(data.mensaje || "Los datos no coinciden con el documento.", "error");
        }
    } catch {
        setDocumentStatus("No se pudo conectar con el servicio de validación.", "error");
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();

    const form = document.getElementById("register-form");
    if (!form) return;

    if (!documentoValidado) {
        setMessage("Debés validar tu documento antes de registrarte.", true);
        return;
    }

    const nombre = document.getElementById("first-name")?.value.trim() || "";
    const apellido = document.getElementById("last-name")?.value.trim() || "";
    const dni = document.getElementById("dni")?.value.trim() || null;
    const telefono = document.getElementById("phone")?.value.trim() || null;
    const email = document.getElementById("email")?.value.trim() || "";
    const password = document.getElementById("password")?.value || "";
    const confirmPassword = document.getElementById("confirm-password")?.value || "";
    const paisValue = document.getElementById("pais")?.value || "";
    const pais = paisValue ? Number.parseInt(paisValue, 10) : null;
    const fechaNacimiento = document.getElementById("fecha-nacimiento")?.value || null;

    if (!nombre || !apellido || !email || !password || !pais || !telefono || !dni || !fechaNacimiento) {
        setMessage("Completá todos los campos requeridos.", true);
        return;
    }

    if (password.length < 8) {
        setMessage("La contraseña debe tener al menos 8 caracteres.", true);
        return;
    }

    if (password !== confirmPassword) {
        setMessage("Las contraseñas no coinciden.", true);
        return;
    }

    const payload = {
        nombre,
        apellido,
        email,
        telefono,
        dni,
        pais,
        fecha_nacimiento: fechaNacimiento,
        password,
        rol: "cliente",
        estado_usuario: 1,
    };

    try {
        setMessage("Registrando usuario...");

        const response = await fetch(`${registerApiBaseUrl}/auth/register`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            setMessage(data.detail || "No se pudo registrar el usuario.", true);
            return;
        }

        setMessage("Usuario registrado correctamente.");
        form.reset();
        documentoValidado = false;
        setDocumentStatus("", "loading");
    } catch {
        setMessage("No se pudo conectar con el backend.", true);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");
    if (!form) return;

    const submitBtn = form.querySelector("button[type='submit']");
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.classList.add("opacity-40", "cursor-not-allowed", "grayscale");
    }

    const documentoInput = document.getElementById("documento-input");
    if (documentoInput) documentoInput.addEventListener("change", handleDocumentoChange);

    form.addEventListener("submit", handleRegisterSubmit);
});
