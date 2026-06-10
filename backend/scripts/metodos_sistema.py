"""
Script de documentación de todos los métodos del sistema GoVehiculos.
Muestra clases, métodos, parámetros y tipos de retorno de cada capa.
Ejecutar desde la carpeta backend/ con: python scripts/metodos_sistema.py
"""
import inspect


# ---------------------------------------------------------------------------
# Utilidad de impresión
# ---------------------------------------------------------------------------

def imprimir_clase(clase, nombre_capa: str) -> None:
    print(f"\n  {'─' * 60}")
    print(f"  Clase: {clase.__name__}  [{nombre_capa}]")
    print(f"  {'─' * 60}")
    metodos = [
        (nombre, obj)
        for nombre, obj in inspect.getmembers(clase, predicate=inspect.isfunction)
        if not nombre.startswith("__")
    ]
    if not metodos:
        print("    (sin métodos públicos)")
        return
    for nombre, funcion in metodos:
        sig = inspect.signature(funcion)
        print(f"    + {nombre}{sig}")


def imprimir_funciones_modulo(modulo, nombre_modulo: str) -> None:
    print(f"\n  {'─' * 60}")
    print(f"  Módulo: {nombre_modulo}  [Servicio — funciones sueltas]")
    print(f"  {'─' * 60}")
    funciones = [
        (nombre, obj)
        for nombre, obj in inspect.getmembers(modulo, predicate=inspect.isfunction)
        if obj.__module__ == modulo.__name__
    ]
    if not funciones:
        print("    (sin funciones públicas)")
        return
    for nombre, funcion in funciones:
        sig = inspect.signature(funcion)
        print(f"    + {nombre}{sig}")


# ---------------------------------------------------------------------------
# Capa de Entidades
# ---------------------------------------------------------------------------

def documentar_entidades() -> None:
    print("\n" + "=" * 65)
    print("  CAPA: ENTIDADES DE DOMINIO")
    print("=" * 65)

    from app.entidades.persona import Persona
    from app.entidades.user_account import UserAccount
    from app.entidades.vehiculo import Vehiculo, VehiculoPatente
    from app.entidades.mensaje import Mensaje

    for clase in [Persona, UserAccount, Vehiculo, VehiculoPatente, Mensaje]:
        imprimir_clase(clase, "Entidad")


# ---------------------------------------------------------------------------
# Capa de Servicios
# ---------------------------------------------------------------------------

def documentar_servicios() -> None:
    print("\n" + "=" * 65)
    print("  CAPA: SERVICIOS DE NEGOCIO")
    print("=" * 65)

    from app.servicios.auth_service import AuthService
    from app.servicios.vehiculo_service import VehiculoService
    from app.servicios.licencia_service import LicenciaService
    from app.servicios.token_service import TokenService
    from app.servicios import conversacion_service

    for clase in [AuthService, VehiculoService, LicenciaService, TokenService]:
        imprimir_clase(clase, "Servicio")

    imprimir_funciones_modulo(conversacion_service, "conversacion_service")


# ---------------------------------------------------------------------------
# Capa de Repositorios
# ---------------------------------------------------------------------------

def documentar_repositorios() -> None:
    print("\n" + "=" * 65)
    print("  CAPA: REPOSITORIOS (acceso a datos)")
    print("=" * 65)

    from app.repositorios.usuario_repository import UsuarioRepository
    from app.repositorios.persona_repository import PersonaRepository
    from app.repositorios.vehiculo_repository import VehiculoRepository
    from app.repositorios.documento_vehiculo_repository import DocumentoVehiculoRepository
    from app.repositorios.conversacion_repository import ConversacionRepository
    from app.repositorios.licencia_repository import LicenciaRepository
    from app.repositorios.pais_repository import PaisRepository

    for clase in [
        UsuarioRepository,
        PersonaRepository,
        VehiculoRepository,
        DocumentoVehiculoRepository,
        ConversacionRepository,
        LicenciaRepository,
        PaisRepository,
    ]:
        imprimir_clase(clase, "Repositorio")


# ---------------------------------------------------------------------------
# Patrón Strategy (Bot)
# ---------------------------------------------------------------------------

def documentar_strategies() -> None:
    print("\n" + "=" * 65)
    print("  CAPA: PATRÓN STRATEGY — BotTopicStrategy")
    print("=" * 65)

    from app.servicios.bot_service import (
        BotTopicStrategy,
        BotService,
        ReservasStrategy,
        VehiculosStrategy,
        PagosStrategy,
        CuentaStrategy,
        TecnicoStrategy,
        SegurosStrategy,
    )

    for clase in [
        BotTopicStrategy,
        BotService,
        ReservasStrategy,
        VehiculosStrategy,
        PagosStrategy,
        CuentaStrategy,
        TecnicoStrategy,
        SegurosStrategy,
    ]:
        imprimir_clase(clase, "Strategy")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  SISTEMA GoVehiculos — Documentación de Métodos")
    print("=" * 65)

    documentar_entidades()
    documentar_servicios()
    documentar_repositorios()
    documentar_strategies()

    print("\n" + "=" * 65)
    print("  FIN DEL REPORTE")
    print("=" * 65 + "\n")
