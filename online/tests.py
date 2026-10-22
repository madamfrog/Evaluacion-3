from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from online.models import Preguntas, Respuesta, Usuario


class ConversationAccessTests(TestCase):
    def setUp(self):
        self.owner = self.create_user('owner', 'owner@example.com')
        self.other = self.create_user('other', 'other@example.com')
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

    def test_user_cannot_view_another_users_conversation(self):
        self.client.force_login(self.other)

        response = self.client.get(
            reverse('respuestas', args=[self.other.id, self.question.idPregunta])
        )

        self.assertRedirects(response, f'/Inicio/{self.other.id}')

    def test_admin_and_technician_can_view_conversations(self):
        for username, email, role in (
            ('admin', 'admin@example.com', {'admin': True}),
            ('tech', 'tech@example.com', {'tecnico': True}),
        ):
            with self.subTest(role=username):
                user = self.create_user(username, email, **role)
                self.client.force_login(user)
                response = self.client.get(
                    reverse('respuestas', args=[user.id, self.question.idPregunta])
                )
                self.assertEqual(response.status_code, 200)

    def test_reply_uses_url_question_not_tampered_hidden_question(self):
        another_question = Preguntas.objects.create(
            Titulo='Otra consulta',
            Pregunta='No hay audio',
            Fecha_creacion=timezone.now(),
            Usuario=self.other,
        )
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('respuestas', args=[self.owner.id, self.question.idPregunta]),
            {
                'Respuesta': 'Prueba reiniciar el juego.',
                'id_Pregunta': another_question.idPregunta,
                'Usuario': self.other.id,
                'FechaHora': timezone.now().isoformat(),
            },
        )

        self.assertRedirects(
            response,
            f'/Respuesta/{self.owner.id}/{self.question.idPregunta}',
        )
        respuesta = Respuesta.objects.get()
        self.assertEqual(respuesta.id_Pregunta_id, self.question.idPregunta)
        self.assertEqual(respuesta.Usuario_id, self.owner.id)

    def test_logout_requires_post(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('Logout'))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_inactive_users_cannot_log_in(self):
        self.owner.activo = False
        self.owner.save()

        response = self.client.post(
            reverse('Login'),
            {'Usuario': self.owner.usuario, 'password': 'test-password-123'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse('_auth_user_id' in self.client.session)
        self.assertTrue(response.context['form'].non_field_errors())
