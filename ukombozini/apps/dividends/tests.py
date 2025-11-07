from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Dividend
from .calculators import DividendCalculator

class DividendModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_dividend_creation(self):
        dividend = Dividend.objects.create(
            user=self.user,
            amount=Decimal('100.00'),
            date=timezone.now().date(),
            description='Test dividend'
        )
        self.assertEqual(dividend.user, self.user)
        self.assertEqual(dividend.amount, Decimal('100.00'))
        self.assertEqual(str(dividend), f'Dividend for {self.user.username}: 100.00')

class DividendCalculatorTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        Dividend.objects.create(user=self.user, amount=Decimal('100.00'), date=timezone.now().date(), description='Dividend 1')
        Dividend.objects.create(user=self.user, amount=Decimal('200.00'), date=timezone.now().date(), description='Dividend 2')

    def test_calculate_total_dividends(self):
        total = DividendCalculator.calculate_total_dividends(self.user)
        self.assertEqual(total, Decimal('300.00'))

    def test_calculate_average_dividend(self):
        average = DividendCalculator.calculate_average_dividend(self.user)
        self.assertEqual(average, Decimal('150.00'))

    def test_get_dividend_summary(self):
        summary = DividendCalculator.get_dividend_summary(self.user)
        self.assertEqual(summary['total_dividends'], Decimal('300.00'))
        self.assertEqual(summary['number_of_dividends'], 2)
        self.assertEqual(summary['average_dividend'], Decimal('150.00'))

class DividendAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_list_dividends(self):
        Dividend.objects.create(user=self.user, amount=Decimal('100.00'), date=timezone.now().date(), description='Test dividend')
        response = self.client.get('/api/dividends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_create_dividend(self):
        data = {
            'amount': '150.00',
            'date': timezone.now().date().isoformat(),
            'description': 'New dividend'
        }
        response = self.client.post('/api/dividends/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Dividend.objects.count(), 1)
        self.assertEqual(Dividend.objects.get().user, self.user)
