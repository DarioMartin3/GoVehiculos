from abc import ABC, abstractmethod

from app.prompts.reservas_prompt import SYSTEM_PROMPT_RESERVAS
from app.prompts.vehiculos_prompt import SYSTEM_PROMPT_VEHICULOS
from app.prompts.pagos_prompt import SYSTEM_PROMPT_PAGOS
from app.prompts.cuenta_prompt import SYSTEM_PROMPT_CUENTA
from app.prompts.tecnico_prompt import SYSTEM_PROMPT_TECNICO
from app.prompts.seguros_prompt import SYSTEM_PROMPT_SEGUROS


class BotTopicStrategy(ABC):
    @property
    @abstractmethod
    def key(self) -> str: ...

    @property
    @abstractmethod
    def system_prompt(self) -> str: ...


class ReservasStrategy(BotTopicStrategy):
    @property
    def key(self) -> str:
        return 'reservas'

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_RESERVAS


class VehiculosStrategy(BotTopicStrategy):
    @property
    def key(self) -> str:
        return 'vehiculos'

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_VEHICULOS


class PagosStrategy(BotTopicStrategy):
    @property
    def key(self) -> str:
        return 'pagos'

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_PAGOS


class CuentaStrategy(BotTopicStrategy):
    @property
    def key(self) -> str:
        return 'cuenta'

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_CUENTA


class TecnicoStrategy(BotTopicStrategy):
    @property
    def key(self) -> str:
        return 'tecnico'

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_TECNICO


class SegurosStrategy(BotTopicStrategy):
    @property
    def key(self) -> str:
        return 'seguros'

    @property
    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_SEGUROS


class BotService:
    def __init__(self):
        strategies: list[BotTopicStrategy] = [
            ReservasStrategy(),
            VehiculosStrategy(),
            PagosStrategy(),
            CuentaStrategy(),
            TecnicoStrategy(),
            SegurosStrategy(),
        ]
        self._registry: dict[str, BotTopicStrategy] = {s.key: s for s in strategies}

    def get_strategy(self, prompt_key: str) -> BotTopicStrategy:
        strategy = self._registry.get(prompt_key)
        if strategy is None:
            raise ValueError(f"No existe estrategia registrada para la clave '{prompt_key}'")
        return strategy

    def get_system_prompt(self, prompt_key: str) -> str:
        return self.get_strategy(prompt_key).system_prompt
