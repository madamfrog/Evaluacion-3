from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from online.models import Preguntas, Usuario


class AdministrationAccessTests(TestCase):
    def setUp(self):
        self.admin = self.create_user('admin', 'admin@example.com', admin=True)
        self.owner = self.create_user('owner', 'owner@example.com')
        self.question = Preguntas.objects.create(
            Titulo='Consulta',
            Pregunta='No inicia el juego',
            Fecha_creacion=timezone.now(),
            Usuario=self.owner,
        )

    def create_user(self, username, email, **fields):
        user = Usuario.objects.create(
            usuario=username,
            correo=email,
            **fields,
        )
        user.set_password('test-password-123')
        user.save()
        return user

    def test_non_admin_cannot_delete_question_by_spoofing_admin_id(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('borrar_pregunta', args=[self.admin.id, self.question.idPregunta])
        )

        self.assertRedirects(response, f'/Inicio/{self.owner.id}')
        self.assertTrue(Preguntas.objects.filter(pk=self.question.pk).exists())

    def test_admin_can_delete_question_only_with_post(self):
        self.client.force_login(self.admin)

        get_response = self.client.get(
            reverse('borrar_pregunta', args=[self.owner.id, self.question.idPregunta])
        )
        self.assertEqual(get_response.status_code, 405)
        self.assertTrue(Preguntas.objects.filter(pk=self.question.pk).exists())

        post_response = self.client.post(
            reverse('borrar_pregunta', args=[self.owner.id, self.question.idPregunta])
        )
        self.assertRedirects(post_response, '/Administracion/')
        self.assertFalse(Preguntas.objects.filter(pk=self.question.pk).exists())

    def test_user_deletion_requires_post_and_prevents_self_deletion(self):
        self.client.force_login(self.admin)

        get_response = self.client.get(
            reverse('eliminar_usuario', args=[self.owner.id])
        )
        self.assertEqual(get_response.status_code, 405)
        self.assertTrue(Usuario.objects.filter(pk=self.owner.pk).exists())

        post_response = self.client.post(
            reverse('eliminar_usuario', args=[self.admin.id])
        )
        self.assertRedirects(post_response, '/GestionUsuarios/')
        self.assertTrue(Usuario.objects.filter(pk=self.admin.pk).exists())

    def test_admin_can_delete_another_user_with_post(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('eliminar_usuario', args=[self.owner.id])
        )

        self.assertRedirects(response, '/GestionUsuarios/')
        self.assertFalse(Usuario.objects.filter(pk=self.owner.pk).exists())

    def test_analytics_route_is_available_to_admin(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('analytics_ia'))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('error', response.context['analytics_data'])

    def test_technician_cannot_access_analytics(self):
        technician = self.create_user(
            'tech',
            'tech@example.com',
            tecnico=True,
        )
        self.client.force_login(technician)

        response = self.client.get(reverse('analytics_ia'))

        self.assertRedirects(response, f'/Inicio/{technician.id}')
