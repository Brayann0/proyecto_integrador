from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
import time

User = get_user_model()


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="login@test.com",
            password="123456",
            username="loginuser",
            nombre="Brayan",
            apellido="Triviño"
        )

    def test_login_exitosa(self):
        """El usuario puede iniciar sesión correctamente"""
        response = self.client.post(reverse("usuarios:login"), {
            "username": "login@test.com",
            "password": "123456",
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn("/usuarios/dashboard/", response.url or "")

    def test_login_invalido(self):
        """Login inválido muestra mensaje de error"""
        response = self.client.post(reverse("usuarios:login"), {
            "username": "login@test.com",
            "password": "wrongpass",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter a correct email and password")


class RegisterViewTest(TestCase):
    def test_registro_usuario_valido(self):
        """El usuario se registra correctamente"""
        response = self.client.post(reverse("usuarios:register"), {
            "username": "nuevo",
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "email": "nuevo@test.com",
            "identificacion": "999",
            "password": "123456",
            "password2": "123456",
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(email="nuevo@test.com").exists())

    def test_registro_invalido(self):
        """Debe mostrar errores si hay datos inválidos"""
        response = self.client.post(reverse("usuarios:register"), {
            "username": "nuevo",
            "nombre": "Nuevo",
            "apellido": "Usuario",
            "email": "invalido",
            "identificacion": "999",
            "password": "123456",
            "password2": "000000",
        })

        self.assertContains(response, "Enter a valid email address.")
        self.assertContains(response, "Las contraseñas no coinciden")


class DashboardAccessTest(TestCase):
    def setUp(self):
        self.user_normal = User.objects.create_user(
            email="normal@test.com",
            password="123456",
            username="normal",
            nombre="Normal",
            apellido="User"
        )
        self.user_admin = User.objects.create_superuser(
            email="admin@test.com",
            password="123456",
            username="admin",
            nombre="Admin",
            apellido="User"
        )

    def test_dashboard_normal_requiere_login(self):
        """El dashboard normal requiere login"""
        response = self.client.get(reverse("usuarios:dashboard_normal"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/usuarios/login/", response.url)

    def test_dashboard_normal_usuario_autenticado(self):
        """Usuario autenticado puede acceder a su dashboard"""
        self.client.login(email="normal@test.com", password="123456")
        response = self.client.get(reverse("usuarios:dashboard_normal"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_admin_superuser(self):
        """Superusuario accede al dashboard admin"""
        self.client.login(email="admin@test.com", password="123456")
        response = self.client.get(reverse("usuarios:dashboard_superuser"))
        self.assertEqual(response.status_code, 200)


# 🧠 PRUEBA DE RENDIMIENTO
class PerformanceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="perf@test.com",
            password="123456",
            username="perfuser",
            nombre="Test",
            apellido="Rendimiento"
        )

    def test_tiempo_respuesta_dashboard(self):
        """Mide el tiempo de respuesta del dashboard"""
        self.client.login(email="perf@test.com", password="123456")

        inicio = time.time()
        response = self.client.get(reverse("usuarios:dashboard_normal"))
        fin = time.time()

        duracion = fin - inicio
        print(f"⏱ Tiempo de respuesta: {duracion:.3f} segundos")

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            duracion, 1.0,
            f"❌ La vista demoró demasiado ({duracion:.3f}s). Debe responder en menos de 1 segundo."
        )
