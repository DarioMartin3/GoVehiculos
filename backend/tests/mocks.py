from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, Mock

from app.entidades.user_account import UserAccount
from app.entidades.vehiculo import Vehiculo, VehiculoPatente


APP_DIR = Path(__file__).resolve().parents[1] / "app"


@dataclass(frozen=True)
class AppMockCatalog:
    class_methods: dict[str, list[str]]
    module_functions: dict[str, list[str]]


def _module_name(path: Path) -> str:
    return ".".join(path.relative_to(APP_DIR).with_suffix("").parts)


def _is_mockable_name(name: str, include_private: bool) -> bool:
    if name.startswith("__") and name.endswith("__"):
        return False
    if include_private:
        return True
    return not name.startswith("_")


def scan_app_methods(include_private: bool = False) -> AppMockCatalog:
    """Lee backend/app y devuelve clases/metodos y funciones mockeables."""
    class_methods: dict[str, list[str]] = {}
    module_functions: dict[str, list[str]] = {}

    for path in sorted(APP_DIR.rglob("*.py")):
        if "__pycache__" in path.parts or path.name == "__init__.py":
            continue

        module = _module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        functions: list[str] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if _is_mockable_name(node.name, include_private):
                    functions.append(node.name)
                continue

            if isinstance(node, ast.ClassDef):
                methods = [
                    item.name
                    for item in node.body
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and _is_mockable_name(item.name, include_private)
                ]
                if methods:
                    class_methods[f"{module}.{node.name}"] = methods

        if functions:
            module_functions[module] = functions

    return AppMockCatalog(class_methods=class_methods, module_functions=module_functions)


def build_class_mock(qualified_class: str, include_private: bool = False) -> MagicMock:
    """Crea un mock con spec de metodos para una clase de backend/app."""
    catalog = scan_app_methods(include_private=include_private)
    methods = catalog.class_methods.get(qualified_class)
    if methods is None:
        raise KeyError(f"No se encontro la clase mockeable: {qualified_class}")

    mock = MagicMock(name=qualified_class, spec_set=methods)
    for method in methods:
        setattr(mock, method, MagicMock(name=f"{qualified_class}.{method}"))
    return mock


def build_module_function_mocks(module: str, include_private: bool = False) -> MagicMock:
    """Crea un mock con spec de funciones para un modulo de backend/app."""
    catalog = scan_app_methods(include_private=include_private)
    functions = catalog.module_functions.get(module)
    if functions is None:
        raise KeyError(f"No se encontro el modulo con funciones mockeables: {module}")

    mock = MagicMock(name=module, spec_set=functions)
    for function in functions:
        setattr(mock, function, MagicMock(name=f"{module}.{function}"))
    return mock


def build_all_class_mocks(include_private: bool = False) -> dict[str, MagicMock]:
    catalog = scan_app_methods(include_private=include_private)
    return {
        qualified_class: build_class_mock(qualified_class, include_private=include_private)
        for qualified_class in catalog.class_methods
    }


def build_all_module_function_mocks(include_private: bool = False) -> dict[str, MagicMock]:
    catalog = scan_app_methods(include_private=include_private)
    return {
        module: build_module_function_mocks(module, include_private=include_private)
        for module in catalog.module_functions
    }


def build_all_app_mocks(include_private: bool = False) -> dict[str, dict[str, MagicMock]]:
    """Devuelve mocks para todas las clases y funciones detectadas en backend/app."""
    return {
        "classes": build_all_class_mocks(include_private=include_private),
        "functions": build_all_module_function_mocks(include_private=include_private),
    }


_VEHICULO_DEFAULT = Vehiculo(
    id=7,
    usuario_id=11,
    patente="AA123BB",
    anio=2018,
    fecha_ingreso="2026-06-09",
    estado_vehiculo="En validacion",
    modelo_id=1,
    modelo_nombre="Corolla",
    marca_nombre="Toyota",
)


class VehiculoRepositoryMock:
    def __init__(
        self,
        *,
        patente_existente: bool = False,
        modelo_existente: bool = True,
        vehiculo_creado: Vehiculo | None = None,
        vehiculo_existente: bool = True,
        vehiculos_lista: list[Vehiculo] | None = None,
        update_ok: bool = True,
    ):
        _vehiculo = vehiculo_creado or _VEHICULO_DEFAULT
        self.create_vehicle = Mock(return_value=7)
        self.get_vehicle_by_patente = Mock(
            return_value=VehiculoPatente(id=99, patente="AA123BB") if patente_existente else None
        )
        self.get_modelo_by_id = Mock(
            return_value={"id": 1, "nombre": "Corolla", "marca_id": 1, "marca_nombre": "Toyota"}
            if modelo_existente
            else None
        )
        self.get_vehicle_by_id = Mock(return_value=_vehiculo if vehiculo_existente else None)
        self.list_vehicles = Mock(
            return_value=vehiculos_lista if vehiculos_lista is not None else [_vehiculo]
        )
        self.update_vehicle_by_id = Mock(return_value=update_ok)
        self.update_vehicle_status_by_id = Mock(return_value=update_ok)


class CursorMock:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ConnectionMock:
    def __init__(self):
        self.committed = False
        self.rolled_back = False
        self.cursor_instance = CursorMock()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class ConversacionRepositoryMock:
    def __init__(
        self,
        *,
        fase_error: Exception | None = None,
        soporte_error: Exception | None = None,
        derivacion_error: Exception | None = None,
    ):
        self.actualizar_fase_conversacion = Mock()
        self.get_fase_id = Mock(side_effect=fase_error, return_value=3)
        self.get_support_operator_id = Mock(side_effect=soporte_error, return_value=5)
        self.crear_derivacion = Mock(side_effect=derivacion_error, return_value=10)


class UsuarioRepositoryMock:
    def __init__(
        self,
        *,
        usuario_existente: UserAccount | None = None,
        crear_retorna: int = 20,
        password_hash: str | None = "password_vieja",
        perfil: dict | None = None,
        update_password_ok: bool = True,
        update_perfil_ok: bool = True,
    ):
        _perfil = perfil if perfil is not None else {
            "id": 20,
            "email": "juan@test.com",
            "nombre": "Juan",
            "apellido": "Pérez",
        }
        self.get_by_email = Mock(return_value=usuario_existente)
        self.create = Mock(return_value=crear_retorna)
        self.get_password_hash_by_user_id = Mock(return_value=password_hash)
        self.update_password_by_user_id = Mock(return_value=update_password_ok)
        self.get_profile_by_user_id = Mock(return_value=_perfil)
        self.update_persona_by_user_id = Mock(return_value=update_perfil_ok)


class PersonaRepositoryMock:
    def __init__(self, *, crear_retorna: int = 10):
        self.create = Mock(return_value=crear_retorna)
