PROMPT_DNI = """Analizá esta imagen de un documento de identidad argentino (DNI).
            Extraé los siguientes campos y devolvé ÚNICAMENTE un JSON válido con esta estructura, sin texto adicional:
            {
            "nombre": "<nombre/s de pila>",
            "apellido": "<apellido/s>",
            "dni": "<número de DNI sin puntos ni espacios>",
            "fecha_nacimiento": "<fecha en formato YYYY-MM-DD>"
            }
            Si no podés leer algún campo con certeza, dejá el valor como cadena vacía."""
