PROMPT_CEDULA_TRASERA = """Analizá esta imagen de la parte trasera de una Cédula Verde de vehículo argentina.
Extraé los datos del titular y devolvé ÚNICAMENTE un JSON válido con esta estructura, sin texto adicional:
{
  "nombre": "<nombre/s de pila del titular>",
  "apellido": "<apellido/s del titular>",
  "dni": "<número de DNI sin puntos ni espacios>"
}
Si no podés leer algún campo con certeza, dejá el valor como cadena vacía."""

PROMPT_CEDULA_EXTRACCION = """Analizá esta imagen de una Cédula Verde de vehículo argentina.
Extraé los siguientes campos y devolvé ÚNICAMENTE un JSON válido con esta estructura, sin texto adicional:
{
  "marca": "<marca del vehículo>",
  "modelo": "<modelo del vehículo>",
  "patente": "<dominio/patente sin guiones ni espacios>",
  "anio": <año de fabricación como número entero>
}
Si no podés leer algún campo con certeza, dejá el valor como cadena vacía o null."""
