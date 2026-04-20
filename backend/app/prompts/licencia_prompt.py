PROMPT_LICENCIA = """Analizá esta imagen de una Licencia Nacional de Conducir argentina.
Extraé los siguientes campos y devolvé ÚNICAMENTE un JSON válido con esta estructura, sin texto adicional:
{
  "nombre": "<nombre/s de pila>",
  "apellido": "<apellido/s>",
  "fecha_nacimiento": "<fecha en formato YYYY-MM-DD>",
  "fecha_emision": "<fecha en formato YYYY-MM-DD>",
  "fecha_vencimiento": "<fecha en formato YYYY-MM-DD>",
  "clases": [
    {
      "clase": "<código de clase, ej: B1, A1, C2>",
      "fecha_otorgamiento": "<fecha en formato YYYY-MM-DD o null>",
      "fecha_vencimiento": "<fecha en formato YYYY-MM-DD o null>"
    }
  ]
}
Si no podés leer algún campo con certeza, dejá el valor como cadena vacía o null según corresponda."""
