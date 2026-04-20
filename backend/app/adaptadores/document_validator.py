from abc import ABC, abstractmethod

class DocumentValidatorAdapter(ABC):
    @abstractmethod
    def extraer_datos(self, prompt: str, imagen: bytes) -> dict:
        pass