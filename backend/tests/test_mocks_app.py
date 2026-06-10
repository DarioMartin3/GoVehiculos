from __future__ import annotations

import unittest

from tests.mocks import build_all_app_mocks, build_class_mock, scan_app_methods


class AppMocksTests(unittest.TestCase):
    def test_crea_mocks_para_todas_las_clases_publicas(self):
        catalog = scan_app_methods()
        mocks = build_all_app_mocks()

        self.assertGreater(len(mocks["classes"]), 0)
        self.assertEqual(set(catalog.class_methods), set(mocks["classes"]))

        for qualified_class, methods in catalog.class_methods.items():
            with self.subTest(qualified_class=qualified_class):
                class_mock = mocks["classes"][qualified_class]
                for method in methods:
                    getattr(class_mock, method).return_value = {"mock": method}
                    self.assertEqual(getattr(class_mock, method)(), {"mock": method})

    def test_crea_mocks_para_todas_las_funciones_publicas(self):
        catalog = scan_app_methods()
        mocks = build_all_app_mocks()

        self.assertGreater(len(mocks["functions"]), 0)
        self.assertEqual(set(catalog.module_functions), set(mocks["functions"]))

        for module, functions in catalog.module_functions.items():
            with self.subTest(module=module):
                module_mock = mocks["functions"][module]
                for function in functions:
                    getattr(module_mock, function).return_value = {"mock": function}
                    self.assertEqual(getattr(module_mock, function)(), {"mock": function})

    def test_el_spec_rechaza_metodos_inexistentes(self):
        service_mock = build_class_mock("servicios.vehiculo_service.VehiculoService")

        with self.assertRaises(AttributeError):
            service_mock.metodo_que_no_existe()


if __name__ == "__main__":
    unittest.main()
