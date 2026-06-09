from __future__ import annotations

import unittest
import sys
import types
from unittest.mock import Mock, patch

sys.modules.setdefault("psycopg2", types.SimpleNamespace(connect=Mock()))
sys.modules.setdefault(
    "jose",
    types.SimpleNamespace(
        JWTError=ValueError,
        jwt=types.SimpleNamespace(encode=Mock(return_value="token"), decode=Mock(return_value={})),
    ),
)

from app.servicios.chat_service import BotExternalServiceError
from app.servicios.licencia_validation_service import LicenciaValidationService
from app.servicios.vehiculo_service import VehiculoService
from tests.mocks import (
    ConnectionMock,
    ConversacionRepositoryMock,
    VehiculoRepositoryMock,
)


class RegistrarVehiculoTests(unittest.TestCase):
    def _service(self, repo: VehiculoRepositoryMock, context=(11, "cliente")) -> VehiculoService:
        service = VehiculoService(vehiculo_repository=repo)
        service.token_service = Mock()
        service.token_service.get_context = Mock(return_value=context)
        return service

    @patch("app.servicios.vehiculo_service.get_connection", return_value=ConnectionMock())
    def test_registra_vehiculo_valido_con_mocks(self, _connection):
        repo = VehiculoRepositoryMock()
        result = self._service(repo).register_vehicle("token-cliente", "AA123BB", 1, 2018)

        self.assertEqual(result["patente"], "AA123BB")
        self.assertEqual(result["modelo_nombre"], "Corolla")
        repo.create_vehicle.assert_called_once()

    def test_rechaza_patente_invalida(self):
        with self.assertRaisesRegex(ValueError, "La patente debe tener entre 6 y 10 caracteres"):
            self._service(VehiculoRepositoryMock()).register_vehicle("token-cliente", "AA 123 BB", 1, 2018)

    def test_rechaza_anio_invalido(self):
        with self.assertRaisesRegex(ValueError, "El año del vehículo no es válido"):
            self._service(VehiculoRepositoryMock()).register_vehicle("token-cliente", "AA123BB", 1, 1979)

    def test_rechaza_modelo_inexistente(self):
        with self.assertRaisesRegex(ValueError, "El modelo seleccionado no existe"):
            self._service(VehiculoRepositoryMock(modelo_existente=False)).register_vehicle(
                "token-cliente", "AA123BB", 999, 2018
            )

    def test_rechaza_patente_duplicada(self):
        with self.assertRaisesRegex(ValueError, "Ya existe un vehículo con esa patente"):
            self._service(VehiculoRepositoryMock(patente_existente=True)).register_vehicle(
                "token-cliente", "AA123BB", 1, 2018
            )

    def test_rechaza_rol_no_autorizado(self):
        with self.assertRaisesRegex(ValueError, "Permiso denegado"):
            self._service(VehiculoRepositoryMock(), context=(4, "operador")).register_vehicle(
                "token-operador", "AB456CD", 1, 2018
            )

    def test_rechaza_token_invalido(self):
        service = self._service(VehiculoRepositoryMock())
        service.token_service.get_context.side_effect = ValueError("Token inválido")

        with self.assertRaisesRegex(ValueError, "Token inválido"):
            service.register_vehicle("token-invalido", "AA123BB", 1, 2018)


class ChatBotTests(unittest.TestCase):
    @patch("app.servicios.chat_service._groq")
    @patch("app.servicios.chat_service._bot_service")
    def test_ask_bot_retorna_respuesta_para_categoria_valida(self, bot_service, groq):
        from app.servicios.chat_service import ask_bot

        bot_service.get_system_prompt.return_value = "prompt reservas"
        groq.chat.return_value = "Podés ver tus reservas desde Mis Reservas."

        result = ask_bot("¿Cómo veo mis reservas?", "reservas")

        self.assertEqual(result["autor"], "bot")
        self.assertIn("reservas", result["cuerpo"])
        self.assertIn("enviado_at", result)

    @patch("app.servicios.chat_service._bot_service")
    def test_ask_bot_rechaza_categoria_inexistente(self, bot_service):
        from app.servicios.chat_service import ask_bot

        bot_service.get_system_prompt.side_effect = ValueError(
            "No existe estrategia registrada para la clave 'categoria_inexistente'"
        )

        with self.assertRaisesRegex(ValueError, "categoria_inexistente"):
            ask_bot("Necesito ayuda", "categoria_inexistente")

    @patch("app.servicios.chat_service._groq")
    @patch("app.servicios.chat_service._bot_service")
    def test_ask_bot_propaga_error_controlado_si_falla_servicio_externo(self, bot_service, groq):
        from app.servicios.chat_service import ask_bot

        bot_service.get_system_prompt.return_value = "prompt pagos"
        groq.chat.side_effect = RuntimeError("servicio caido")

        with self.assertRaises(BotExternalServiceError):
            ask_bot("¿Cómo pago mi reserva?", "pagos")


class DerivarConversacionTests(unittest.TestCase):
    @patch("app.servicios.conversacion_service.get_connection", return_value=ConnectionMock())
    def test_deriva_conversacion_a_soporte(self, _connection):
        from app.servicios import conversacion_service

        with patch.object(conversacion_service, "_repo", ConversacionRepositoryMock()):
            result = conversacion_service.derivar_conversacion_a_soporte(1, "solicitud_usuario")

        self.assertEqual(result["conversacion_id"], 1)
        self.assertEqual(result["fase"], "operario")
        self.assertEqual(result["derivacion_id"], 10)
        self.assertEqual(result["operario_id"], 5)

    @patch("app.servicios.conversacion_service.get_connection", return_value=ConnectionMock())
    def test_deriva_con_motivo_bot_no_resolvio(self, _connection):
        from app.servicios import conversacion_service

        with patch.object(conversacion_service, "_repo", ConversacionRepositoryMock()):
            result = conversacion_service.derivar_conversacion_a_soporte(1, "bot_no_resolvio")

        self.assertEqual(result["fase"], "operario")

    @patch("app.servicios.conversacion_service.get_connection", return_value=ConnectionMock())
    def test_deriva_propaga_error_si_no_existe_fase(self, _connection):
        from app.servicios import conversacion_service

        repo = ConversacionRepositoryMock(fase_error=ValueError("Fase de conversación 'operario' no encontrada"))
        with patch.object(conversacion_service, "_repo", repo):
            with self.assertRaisesRegex(ValueError, "operario"):
                conversacion_service.derivar_conversacion_a_soporte(1, "solicitud_usuario")

    @patch("app.servicios.conversacion_service.get_connection", return_value=ConnectionMock())
    def test_deriva_propaga_error_si_no_hay_soporte(self, _connection):
        from app.servicios import conversacion_service

        repo = ConversacionRepositoryMock(soporte_error=ValueError("No hay usuario soporte disponible"))
        with patch.object(conversacion_service, "_repo", repo):
            with self.assertRaisesRegex(ValueError, "soporte"):
                conversacion_service.derivar_conversacion_a_soporte(1, "solicitud_usuario")

    @patch("app.servicios.conversacion_service.get_connection", return_value=ConnectionMock())
    def test_deriva_propaga_error_si_conversacion_no_existe(self, _connection):
        from app.servicios import conversacion_service

        repo = ConversacionRepositoryMock(derivacion_error=ValueError("Conversación no encontrada"))
        with patch.object(conversacion_service, "_repo", repo):
            with self.assertRaisesRegex(ValueError, "Conversación"):
                conversacion_service.derivar_conversacion_a_soporte(999, "solicitud_usuario")


class ValidarLicenciaTests(unittest.TestCase):
    def _service(self, extracted: dict) -> LicenciaValidationService:
        adapter = Mock()
        adapter.extraer_datos = Mock(return_value=extracted)
        return LicenciaValidationService(adapter)

    def test_valida_licencia_vigente(self):
        result = self._service(
            {
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": "1990-05-14",
                "fecha_vencimiento": "2030-01-01",
            }
        ).validate(b"imagen", "Juan", "Pérez", "1990-05-14")

        self.assertTrue(result["valido"])
        self.assertTrue(result["persona_valida"])
        self.assertFalse(result["vencida"])
        self.assertEqual(result["mensaje"], "Licencia validada correctamente.")

    def test_rechaza_nombre_distinto(self):
        result = self._service(
            {
                "nombre": "Pedro",
                "apellido": "Pérez",
                "fecha_nacimiento": "1990-05-14",
                "fecha_vencimiento": "2030-01-01",
            }
        ).validate(b"imagen", "Juan", "Pérez", "1990-05-14")

        self.assertFalse(result["persona_valida"])
        self.assertIn("nombre", result["mensaje"])

    def test_rechaza_apellido_distinto(self):
        result = self._service(
            {
                "nombre": "Juan",
                "apellido": "Gómez",
                "fecha_nacimiento": "1990-05-14",
                "fecha_vencimiento": "2030-01-01",
            }
        ).validate(b"imagen", "Juan", "Pérez", "1990-05-14")

        self.assertFalse(result["persona_valida"])
        self.assertIn("apellido", result["mensaje"])

    def test_rechaza_fecha_nacimiento_distinta(self):
        result = self._service(
            {
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": "1991-05-14",
                "fecha_vencimiento": "2030-01-01",
            }
        ).validate(b"imagen", "Juan", "Pérez", "1990-05-14")

        self.assertFalse(result["persona_valida"])
        self.assertIn("fecha_nacimiento", result["mensaje"])

    def test_rechaza_licencia_vencida(self):
        result = self._service(
            {
                "nombre": "Juan",
                "apellido": "Pérez",
                "fecha_nacimiento": "1990-05-14",
                "fecha_vencimiento": "2020-01-01",
            }
        ).validate(b"imagen", "Juan", "Pérez", "1990-05-14")

        self.assertFalse(result["valido"])
        self.assertTrue(result["persona_valida"])
        self.assertTrue(result["vencida"])
        self.assertEqual(result["mensaje"], "La licencia está vencida.")

    def test_acepta_nombre_parcial_reconocido_por_ocr(self):
        result = self._service(
            {
                "nombre": "María",
                "apellido": "Sosa",
                "fecha_nacimiento": "2003-09-20",
                "fecha_vencimiento": "2030-01-01",
            }
        ).validate(b"imagen", "María Del Rosario", "Sosa", "2003-09-20")

        self.assertTrue(result["persona_valida"])
        self.assertEqual(result["datos_extraidos"]["nombre"], "María Del Rosario")

    def test_propaga_error_del_adaptador(self):
        adapter = Mock()
        adapter.extraer_datos.side_effect = RuntimeError("OCR no disponible")
        service = LicenciaValidationService(adapter)

        with self.assertRaisesRegex(RuntimeError, "OCR no disponible"):
            service.validate(b"imagen", "Juan", "Pérez", "1990-05-14")


if __name__ == "__main__":
    unittest.main()
