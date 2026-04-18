const API_BASE_URL = "http://localhost:8000";

function setMessage(text, isError = false) {
    const message = document.getElementById("register-message");
    if (!message) {
        return;
    }
    message.textContent = text;
    message.classList.toggle("text-error", isError);
    message.classList.toggle("text-primary", !isError);
}

async function handleRegisterSubmit(event) {
    event.preventDefault();

    const form = document.getElementById("register-form");
    if (!form) {
        return;
    }

    const nombre = document.getElementById("first-name")?.value.trim() || "";
    const apellido = document.getElementById("last-name")?.value.trim() || "";
    const dni = document.getElementById("dni")?.value.trim() || null;
    const telefono = document.getElementById("phone")?.value.trim() || null;
    const email = document.getElementById("email")?.value.trim() || "";
    const password = document.getElementById("password")?.value || "";
    const confirmPassword = document.getElementById("confirm-password")?.value || "";

    if (!nombre || !apellido || !email || !password) {
        setMessage("Completá nombre, apellido, correo y contraseña.", true);
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
        pais: null,
        estado_persona: 1,
        password,
        rol: "cliente",
        estado_usuario: 1,
    };

    try {
        setMessage("Registrando usuario...");

        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();

        if (!response.ok) {
            setMessage(data.detail || "No se pudo registrar el usuario.", true);
            return;
        }

        setMessage("Usuario registrado correctamente.");
        form.reset();
    } catch (error) {
        setMessage("No se pudo conectar con el backend.", true);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("register-form");
    if (!form) {
        return;
    }
    form.addEventListener("submit", handleRegisterSubmit);
});