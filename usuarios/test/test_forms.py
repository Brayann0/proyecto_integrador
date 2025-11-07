from django.test import TestCase
from usuarios.forms import UserRegistrationForm, LoginForm
from usuarios.models import Usuario


class UserRegistrationFormTest(TestCase):
    def test_form_valido(self):
        """El formulario de registro es válido con datos correctos"""
        form = UserRegistrationForm(data={
            "username": "usuario1",
            "nombre": "Brayan",
            "apellido": "Triviño",
            "email": "correo@test.com",
            "identificacion": "98765",
            "password": "123456",
            "password2": "123456",
        })
        self.assertTrue(form.is_valid())

    def test_email_invalido(self):
        """Debe fallar si el email no es válido"""
        form = UserRegistrationForm(data={
            "username": "usuario2",
            "nombre": "Ana",
            "apellido": "Ruiz",
            "email": "invalido",
            "identificacion": "1111",
            "password": "123456",
            "password2": "123456",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_contrasenas_no_coinciden(self):
        """Debe fallar si las contraseñas no coinciden"""
        form = UserRegistrationForm(data={
            "username": "usuario3",
            "nombre": "Laura",
            "apellido": "Gomez",
            "email": "laura@test.com",
            "identificacion": "2222",
            "password": "123456",
            "password2": "654321",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_guardado_usuario(self):
        """Debe guardar el usuario con la contraseña encriptada"""
        form = UserRegistrationForm(data={
            "username": "usuario4",
            "nombre": "Pedro",
            "apellido": "Lopez",
            "email": "pedro@test.com",
            "identificacion": "3333",
            "password": "123456",
            "password2": "123456",
        })
        self.assertTrue(form.is_valid())
        usuario = form.save()
        self.assertTrue(usuario.check_password("123456"))
        self.assertEqual(usuario.email, "pedro@test.com")


class LoginFormTest(TestCase):
    def test_campos_existentes(self):
        """El formulario de login tiene los campos esperados"""
        form = LoginForm()
        self.assertIn("username", form.fields)
        self.assertIn("password", form.fields)
