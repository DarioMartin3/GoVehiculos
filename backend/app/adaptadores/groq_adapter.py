from app.adaptadores.document_validator import DocumentValidatorAdapter
import requests
import re
import json

from app.core.config import GROQ_API_KEY

class GroqDocumentAdapter(DocumentValidatorAdapter):

    def __init__(self, max_tokens: int = 512):
        self.max_tokens = max_tokens

    def extraer_datos(self, prompt: str, imagen: bytes) -> dict:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "meta-llama/llama-4-scout-17b-16e-instruct",
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{imagen}"
                                },
                            },
                            {"type": "text", "text": prompt},
                        ],
                    }
                ],
            },
        )

        if not response.ok:
            raise ValueError(f"Groq error {response.status_code}: {response.text}")

        raw = response.json()["choices"][0]["message"]["content"].strip()
        print("=== RESPUESTA GROQ ===")
        print(raw)
        print("=====================")

        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("No se pudo interpretar la respuesta del modelo")

        extracted = json.loads(json_match.group())

        return extracted