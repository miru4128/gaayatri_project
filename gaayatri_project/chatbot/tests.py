import json
from typing import cast
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from core.models import Cattle
from .models import ChatSession, ChatMessage
from .constants import DEFAULT_LOCATION_LABEL
from .services import GroqResponse


@override_settings(CHATBOT_API_KEY='test-key')
class ChatApiTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='farmer1', password='pass123', is_farmer=True
        )
        self.cattle = Cattle.objects.create(
            owner=self.user,
            tag_number='T-101',
            name='Gauri',
            breed='Gir',
            age_years=5,
            daily_milk_yield=12.5,
        )
        self.cattle_id = str(self.cattle.pk)

    def _post(self, payload):
        return self.client.post(
            reverse('chatbot:api'),
            data=json.dumps(payload),
            content_type='application/json',
        )

    @patch('chatbot.views.call_groq_sync', return_value=GroqResponse('Mock reply', None))
    def test_chat_api_saves_context_with_cattle_details(self, mock_call):
        self.client.force_login(self.user)
        payload = {
            'message': 'My cow has mastitis',
            'context': {
                'animal_id': self.cattle_id,
                'issue': 'Mastitis',
            },
        }

        response = self._post(payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data['ok'])
        session_id = data['session_id']
        session = ChatSession.objects.get(pk=session_id)

        self.assertEqual(session.user, self.user)
        self.assertEqual(session.context['animal_id'], int(self.cattle_id))
        self.assertEqual(session.context['breed'], self.cattle.breed)
        self.assertEqual(session.context['name'], self.cattle.name)
        self.assertEqual(session.context['issue'], 'Mastitis')

        messages = ChatMessage.objects.filter(session=session).order_by('created_at')
        self.assertEqual(messages.count(), 2)
        self.assertEqual(messages[0].role, 'user')
        self.assertEqual(messages[1].role, 'bot')
        mock_call.assert_called_once()

    @patch('chatbot.views.call_groq_sync', return_value=GroqResponse('Follow up reply', None))
    def test_chat_api_creates_new_session_when_context_changes(self, mock_call):
        self.client.force_login(self.user)

        first_payload = {
            'message': 'Need help with feed plan',
            'context': {
                'animal_id': self.cattle_id,
                'issue': 'Feeding',
            },
        }
        first_response = self._post(first_payload)
        first_data = first_response.json()
        first_session_id = first_data['session_id']

        # Change context to manual entry to trigger a new session
        second_payload = {
            'message': 'Now my Jersey cow has fever',
            'context': {
                'name': 'Tulsi',
                'breed': 'Jersey',
                'age_years': 4,
                'milk_yield': 10,
                'issue': 'Fever',
            },
        }
        second_response = self._post(second_payload)
        second_data = second_response.json()
        second_session_id = second_data['session_id']

        self.assertNotEqual(first_session_id, second_session_id)
        self.assertEqual(
            ChatSession.objects.filter(user=self.user).count(),
            2,
        )
        self.assertEqual(
            ChatMessage.objects.filter(session_id=second_session_id).count(),
            2,
        )
        # Ensure the new session stored manual context values
        new_context = ChatSession.objects.get(pk=second_session_id).context
        self.assertEqual(new_context['name'], 'Tulsi')
        self.assertEqual(new_context['breed'], 'Jersey')
        self.assertEqual(new_context['issue'], 'Fever')

    @patch('chatbot.views.call_groq_sync', return_value=GroqResponse('Sanitised response', None))
    def test_chat_api_masks_ip_and_defaults_to_india(self, mock_call):
        self.client.force_login(self.user)
        payload = {
            'message': 'Need help with mastitis care',
            'context': {
                'animal_id': self.cattle_id,
                'issue': 'Mastitis',
            },
        }

        response = self.client.post(
            reverse('chatbot:api'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_FORWARDED_FOR='203.0.113.24',
        )

        self.assertEqual(response.status_code, 200)
        session_id = response.json()['session_id']
        user_message = ChatMessage.objects.filter(session_id=session_id, role='user').first()
        self.assertIsNotNone(user_message)
        user_message = cast(ChatMessage, user_message)
        self.assertIsInstance(user_message.location, str)
        location_value = user_message.location or ''
        self.assertEqual(location_value, DEFAULT_LOCATION_LABEL)
        self.assertNotIn('203.0.113.24', location_value)
        mock_call.assert_called_once()

    @patch('chatbot.views.call_groq_sync')
    def test_chat_api_refuses_human_health_requests(self, mock_call):
        self.client.force_login(self.user)
        payload = {
            'message': 'I have a high fever and need medicine suggestions',
        }

        response = self._post(payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIn('doctor', data['reply'].lower())
        mock_call.assert_not_called()
        bot_message = ChatMessage.objects.filter(role='bot').last()
        self.assertIsNotNone(bot_message)
        bot_message = cast(ChatMessage, bot_message)
        self.assertIn('doctor', bot_message.text.lower())
