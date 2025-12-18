from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from chatbot.models import ChatSession, ChatMessage
from .models import Cattle


class DoctorChatHistoryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.doctor = User.objects.create_user(
            username='doc1', password='pass123', is_doctor=True
        )
        self.farmer = User.objects.create_user(
            username='farmer1', password='pass123', is_farmer=True
        )
        self.cattle = Cattle.objects.create(
            owner=self.farmer,
            tag_number='TAG-9',
            name='Lakshmi',
            breed='Sahiwal',
            age_years=6,
            daily_milk_yield=11.2,
        )
        context = {
            'animal_id': self.cattle.pk,
            'name': self.cattle.name,
            'tag_number': self.cattle.tag_number,
            'breed': self.cattle.breed,
            'age_years': self.cattle.age_years,
            'milk_yield': self.cattle.daily_milk_yield,
            'issue': 'Low milk yield',
        }
        self.session = ChatSession.objects.create(user=self.farmer, context=context)
        ChatMessage.objects.create(session=self.session, role='user', text='Milk production dropped')
        ChatMessage.objects.create(session=self.session, role='bot', text='Increase protein in ration')

    def test_doctor_can_view_chat_history(self):
        self.client.force_login(self.doctor)
        response = self.client.get(reverse('doctor_chat_history'))
        self.assertEqual(response.status_code, 200)
        session_data = response.context['session_data']
        self.assertEqual(len(session_data), 1)
        entry = session_data[0]
        self.assertEqual(entry['farmer'], self.farmer)
        self.assertEqual(entry['context']['name'], self.cattle.name)
        self.assertEqual(entry['message_count'], 2)
        self.assertEqual(entry['messages'][0].text, 'Milk production dropped')

    def test_non_doctor_redirected_from_history(self):
        self.client.force_login(self.farmer)
        response = self.client.get(reverse('doctor_chat_history'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/dashboard/doctor/', response['Location'])


class AuthRedirectTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.farmer = User.objects.create_user(
            username='farmer_login', password='pass12345', is_farmer=True
        )
        self.doctor = User.objects.create_user(
            username='doctor_login', password='pass12345', is_doctor=True
        )

    def test_login_redirects_farmers_to_home(self):
        response = self.client.post(reverse('login'), {
            'username': 'farmer_login',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('home'))

    def test_login_redirects_doctors_to_home(self):
        response = self.client.post(reverse('login'), {
            'username': 'doctor_login',
            'password': 'pass12345',
        })
        self.assertRedirects(response, reverse('home'))

    def test_register_flow_redirects_to_home(self):
        response = self.client.post(reverse('register'), {
            'username': 'new_farmer',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'email': 'new_farmer@example.com',
            'user_type': 'farmer',
        })
        self.assertRedirects(response, reverse('home'))
        new_user = get_user_model().objects.get(username='new_farmer')
        self.assertTrue(getattr(new_user, 'is_farmer', False))


class ManageCattleTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.farmer = User.objects.create_user(
            username='farmer_manage', password='pass123', is_farmer=True
        )

    def _login(self):
        self.client.force_login(self.farmer)

    def test_farmer_can_add_cattle(self):
        self._login()
        response = self.client.post(reverse('manage_cattle'), {
            'tag_number': 'T-200',
            'name': 'Ganga',
            'breed': 'Gir',
            'age_years': 4,
            'daily_milk_yield': 15.5,
            'last_vaccination_date': '2025-01-01',
        })
        self.assertRedirects(response, reverse('manage_cattle'))
        cattle = Cattle.objects.get(owner=self.farmer)
        self.assertEqual(cattle.name, 'Ganga')
        self.assertEqual(cattle.tag_number, 'T-200')

    def test_farmer_can_update_cattle(self):
        self._login()
        cattle = Cattle.objects.create(
            owner=self.farmer,
            tag_number='T-300',
            name='Kamdhenu',
            breed='Sahiwal',
            age_years=6,
            daily_milk_yield=12.0,
        )
        response = self.client.post(reverse('manage_cattle'), {
            'cattle_id': str(cattle.pk),
            'tag_number': 'T-300',
            'name': 'Kamdhenu',
            'breed': 'Sahiwal',
            'age_years': 7,
            'daily_milk_yield': 13.0,
            'last_vaccination_date': '',
        })
        self.assertRedirects(response, reverse('manage_cattle'))
        cattle.refresh_from_db()
        self.assertEqual(cattle.age_years, 7)
        self.assertEqual(cattle.daily_milk_yield, 13.0)

    def test_farmer_can_delete_cattle(self):
        self._login()
        cattle = Cattle.objects.create(
            owner=self.farmer,
            tag_number='DEL-1',
            name='ToRemove',
            breed='Gir',
            age_years=5,
            daily_milk_yield=10.0,
        )
        response = self.client.post(reverse('manage_cattle'), {
            'delete_id': str(cattle.pk),
        })
        self.assertRedirects(response, reverse('manage_cattle'))
        self.assertFalse(Cattle.objects.filter(pk=cattle.pk).exists())
