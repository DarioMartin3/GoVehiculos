PROMPT_SEGURO = """Analizá esta imagen de una póliza de seguro de vehículo.
Extraé los siguientes campos y devolvé ÚNICAMENTE un JSON válido con esta estructura, sin texto adicional:
{
  "nombre": "<nombre/s de pila del asegurado>",
  "apellido": "<apellido/s del asegurado>",
  "dni": "<número de DNI sin puntos ni espacios>",
  "fecha_nacimiento": "<fecha en formato YYYY-MM-DD>",
  "marca": "<marca del vehículo>",
  "modelo": "<modelo del vehículo>"
}
Si no podés leer algún campo con certeza, dejá el valor como cadena vacía."""
