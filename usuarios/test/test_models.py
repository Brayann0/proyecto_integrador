from django.test import TestCase
from django.contrib.auth import get_user_model
from usuarios.models import PersonaNoRegistrada

User = get_user_model()


class UsuarioModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="12345",
            username="testuser",
            nombre="Brayan",
            apellido="Triviño",
            identificacion="123456"
        )

    def test_usuario_creado_correctamente(self):
        """Verifica que el usuario se crea correctamente con los campos personalizados"""
        self.assertEqual(self.user.email, "testuser@example.com")
        self.assertTrue(self.user.check_password("12345"))
        self.assertEqual(self.user.nombre, "Brayan")
        self.assertEqual(str(self.user), "testuser@example.com")

    def test_campos_existentes(self):
        """Verifica que el modelo Usuario tiene los campos personalizados"""
        campos = [f.name for f in User._meta.fields]
        for campo in ["nombre", "apellido", "email", "identificacion"]:
            self.assertIn(campo, campos)


class PersonaNoRegistradaModelTest(TestCase):
    def setUp(self):
        self.persona = PersonaNoRegistrada.objects.create(
            nombre="Carlos Pérez",
            cedula="1234567890",
            email="carlos@example.com"
        )

    def test_persona_no_registrada_creacion(self):
        """Verifica que la persona no registrada se crea correctamente"""
        self.assertEqual(self.persona.nombre, "Carlos Pérez")
        self.assertEqual(str(self.persona), "Carlos Pérez (1234567890)")

    def test_fecha_registro_automatica(self):
        """Verifica que la fecha de registro se asigna automáticamente"""
        self.assertIsNotNone(self.persona.fecha_registro)
    