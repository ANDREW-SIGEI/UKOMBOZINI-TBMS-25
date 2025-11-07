import json
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import date
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from ukombozini.apps.groups.models import Group
from ukombozini.apps.loans.models import Loan, Guarantor, LoanApplication
from ukombozini.apps.users.models import CustomUser

User = get_user_model()


class GuarantorModelTest(TestCase):
    """Test Guarantor model functionality"""

    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            user_type='admin'
        )
        self.field_officer = User.objects.create_user(
            username='field_officer',
            email='fo@test.com',
            password='password123',
            user_type='field_officer'
        )
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@test.com',
            password='password123',
            user_type='member',
            assigned_county='Nairobi',
            assigned_constituency='Westlands',
            assigned_ward='Westlands'
        )
        self.member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='password123',
            user_type='member',
            assigned_county='Nairobi',
            assigned_constituency='Westlands',
            assigned_ward='Westlands'
        )

        # Create group
        self.group = Group.objects.create(
            name='Test Group',
            formation_date=date.today(),
            county='Nairobi',
            constituency='Westlands',
            ward='Westlands',
            chairperson_name='Chairperson',
            chairperson_phone='+254700000000',
            contact_phone='+254700000000',
            created_by=self.admin
        )

        # Use CustomUser directly as members
        self.member_obj1 = self.member1
        self.member_obj2 = self.member2

        # Set savings for test members
        self.member_obj2.get_total_savings = lambda: Decimal('50000.00')

        # Create loan
        self.loan = Loan.objects.create(
            loan_type='short_term',
            group=self.group,
            member=self.member_obj1,
            principal_amount=Decimal('50000.00'),
            interest_rate=Decimal('12.00'),
            short_term_months=6,
            created_by=self.field_officer
        )

    def test_guarantor_creation(self):
        """Test creating a guarantor"""
        guarantor = Guarantor.objects.create(
            loan=self.loan,
            member=self.member_obj2,
            guarantee_amount=Decimal('10000.00'),
            relationship='group_member'
        )

        self.assertEqual(guarantor.loan, self.loan)
        self.assertEqual(guarantor.member, self.member_obj2)
        self.assertEqual(guarantor.guarantee_amount, Decimal('10000.00'))
        self.assertEqual(guarantor.status, 'pending')
        self.assertEqual(guarantor.guarantee_percentage, Decimal('20.00'))

    def test_guarantor_eligibility_check(self):
        """Test guarantor eligibility checking"""
        # Test self-guarantor (should fail)
        guarantor = Guarantor(loan=self.loan, member=self.member_obj1)
        can_guarantee, reason = guarantor.can_be_guarantor()
        self.assertFalse(can_guarantee)
        self.assertIn("Cannot guarantee your own loan", reason)

        # Test valid guarantor
        guarantor = Guarantor(loan=self.loan, member=self.member_obj2)
        can_guarantee, reason = guarantor.can_be_guarantor()
        self.assertTrue(can_guarantee)

    def test_loan_available_guarantors(self):
        """Test getting available guarantors for a loan"""
        available = self.loan.get_available_guarantors()
        self.assertEqual(len(available), 1)
        self.assertEqual(available[0]['id'], self.member_obj2.id)
        self.assertTrue(available[0]['can_guarantee'])

    def test_loan_add_guarantor(self):
        """Test adding a guarantor to a loan"""
        success, guarantor, message = self.loan.add_guarantor(
            member_id=self.member_obj2.id,
            guarantee_amount=Decimal('10000.00')
        )

        self.assertTrue(success)
        self.assertEqual(guarantor.loan, self.loan)
        self.assertEqual(guarantor.member, self.member_obj2)
        self.assertEqual(guarantor.guarantee_amount, Decimal('10000.00'))

    def test_loan_guarantee_summary(self):
        """Test loan guarantee summary"""
        # Add approved guarantor
        guarantor = Guarantor.objects.create(
            loan=self.loan,
            member=self.member_obj2,
            guarantee_amount=Decimal('10000.00'),
            status='approved'
        )

        summary = self.loan.guarantee_summary
        self.assertEqual(summary['approved_guarantors'], 1)
        self.assertEqual(summary['total_guarantee_amount'], Decimal('10000.00'))
        self.assertEqual(summary['guarantee_coverage_percentage'], Decimal('20.00'))


class LoanApplicationModelTest(TestCase):
    """Test LoanApplication model functionality"""

    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            user_type='admin'
        )
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@test.com',
            password='password123',
            user_type='member',
            assigned_county='Nairobi',
            assigned_constituency='Westlands',
            assigned_ward='Westlands'
        )

        # Create group
        self.group = Group.objects.create(
            name='Test Group',
            formation_date=date.today(),
            county='Nairobi',
            constituency='Westlands',
            ward='Westlands',
            chairperson_name='Chairperson',
            chairperson_phone='+254700000000',
            contact_phone='+254700000000',
            created_by=self.admin
        )

        # Use CustomUser directly as member
        self.member_obj1 = self.member1

        # Create loan
        self.loan = Loan.objects.create(
            loan_type='short_term',
            group=self.group,
            member=self.member_obj1,
            principal_amount=Decimal('50000.00'),
            interest_rate=Decimal('12.00'),
            short_term_months=6,
            created_by=self.admin
        )

    def test_loan_application_creation(self):
        """Test creating a loan application"""
        application = LoanApplication.objects.create(
            loan=self.loan,
            applicant=self.member1,
            group=self.group,
            required_guarantors=1,
            min_guarantee_percentage=Decimal('20.00')
        )

        self.assertEqual(application.loan, self.loan)
        self.assertEqual(application.applicant, self.member1)
        self.assertEqual(application.status, 'draft')
        self.assertEqual(application.required_guarantors, 1)
        self.assertEqual(application.min_guarantee_percentage, Decimal('20.00'))

    def test_application_can_submit(self):
        """Test application submission eligibility"""
        application = LoanApplication.objects.create(
            loan=self.loan,
            applicant=self.member1,
            group=self.group,
            required_guarantors=1,
            min_guarantee_percentage=Decimal('20.00')
        )

        # Should not be able to submit without guarantors
        can_submit, errors = application.can_submit()
        self.assertFalse(can_submit)
        self.assertIn("Requires 1 guarantors", errors[0])

        # Add guarantor
        member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='password123',
            user_type='member'
        )
        Guarantor.objects.create(
            loan=self.loan,
            member=member2,
            guarantee_amount=Decimal('10000.00'),
            status='approved'
        )

        # Should now be able to submit
        can_submit, errors = application.can_submit()
        self.assertTrue(can_submit)
        self.assertEqual(len(errors), 0)


class GuarantorAPITest(APITestCase):
    """Test Guarantor API endpoints"""

    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            user_type='admin'
        )
        self.field_officer = User.objects.create_user(
            username='field_officer',
            email='fo@test.com',
            password='password123',
            user_type='field_officer'
        )
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@test.com',
            password='password123',
            user_type='member',
            assigned_county='Nairobi',
            assigned_constituency='Westlands',
            assigned_ward='Westlands'
        )
        self.member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='password123',
            user_type='member',
            assigned_county='Nairobi',
            assigned_constituency='Westlands',
            assigned_ward='Westlands'
        )

        # Create group
        self.group = Group.objects.create(
            name='Test Group',
            formation_date=date.today(),
            county='Nairobi',
            constituency='Westlands',
            ward='Westlands',
            chairperson_name='Chairperson',
            chairperson_phone='+254700000000',
            contact_phone='+254700000000',
            created_by=self.admin
        )

        # Use CustomUser directly as members
        self.member_obj1 = self.member1
        self.member_obj2 = self.member2

        # Set savings for test members
        self.member_obj2.get_total_savings = lambda: Decimal('50000.00')

        # Create loan
        self.loan = Loan.objects.create(
            loan_type='short_term',
            group=self.group,
            member=self.member_obj1,
            principal_amount=Decimal('50000.00'),
            interest_rate=Decimal('12.00'),
            short_term_months=6,
            created_by=self.field_officer
        )

    def test_available_guarantors_api(self):
        """Test getting available guarantors via API"""
        self.client.force_authenticate(user=self.field_officer)

        url = reverse('available-guarantors', kwargs={'loan_id': self.loan.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.member_obj2.id)
        self.assertTrue(response.data[0]['can_guarantee'])

    def test_add_guarantor_api(self):
        """Test adding a guarantor via API"""
        self.client.force_authenticate(user=self.field_officer)

        url = reverse('add-guarantor', kwargs={'loan_id': self.loan.id})
        data = {
            'member_id': self.member_obj2.id,
            'guarantee_amount': '10000.00',
            'relationship': 'group_member'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('guarantor', response.data)
        self.assertEqual(response.data['guarantor']['guarantee_amount'], '10000.00')

        # Check guarantor was created
        guarantor = Guarantor.objects.get(loan=self.loan, member=self.member_obj2)
        self.assertEqual(guarantor.guarantee_amount, Decimal('10000.00'))

    def test_approve_guarantor_api(self):
        """Test approving a guarantor via API"""
        # Create guarantor
        guarantor = Guarantor.objects.create(
            loan=self.loan,
            member=self.member_obj2,
            guarantee_amount=Decimal('10000.00')
        )

        self.client.force_authenticate(user=self.field_officer)

        url = reverse('approve-guarantor', kwargs={'guarantor_id': guarantor.id})
        data = {
            'action': 'approve',
            'notes': 'Approved by field officer'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Guarantor approved successfully', response.data['message'])

        # Check guarantor was approved
        guarantor.refresh_from_db()
        self.assertEqual(guarantor.status, 'approved')
        self.assertEqual(guarantor.approved_by, self.field_officer)

    def test_reject_guarantor_api(self):
        """Test rejecting a guarantor via API"""
        # Create guarantor
        guarantor = Guarantor.objects.create(
            loan=self.loan,
            member=self.member_obj2,
            guarantee_amount=Decimal('10000.00')
        )

        self.client.force_authenticate(user=self.field_officer)

        url = reverse('approve-guarantor', kwargs={'guarantor_id': guarantor.id})
        data = {
            'action': 'reject',
            'rejection_reason': 'Insufficient savings'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rejected', response.data['message'])

        # Check guarantor was rejected
        guarantor.refresh_from_db()
        self.assertEqual(guarantor.status, 'rejected')
        self.assertEqual(guarantor.rejection_reason, 'Insufficient savings')


class LoanApplicationAPITest(APITestCase):
    """Test LoanApplication API endpoints"""

    def setUp(self):
        # Create test users
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='password123',
            user_type='admin'
        )
        self.member1 = User.objects.create_user(
            username='member1',
            email='member1@test.com',
            password='password123',
            user_type='member',
            assigned_county='Nairobi',
            assigned_constituency='Westlands',
            assigned_ward='Westlands'
        )

        # Create group
        self.group = Group.objects.create(
            name='Test Group',
            formation_date=date.today(),
            county='Nairobi',
            constituency='Westlands',
            ward='Westlands',
            chairperson_name='Chairperson',
            chairperson_phone='+254700000000',
            contact_phone='+254700000000',
            created_by=self.admin
        )

        # Use CustomUser directly as member
        self.member_obj1 = self.member1

        # Create loan
        self.loan = Loan.objects.create(
            loan_type='short_term',
            group=self.group,
            member=self.member_obj1,
            principal_amount=Decimal('50000.00'),
            interest_rate=Decimal('12.00'),
            short_term_months=6,
            created_by=self.admin
        )

    def test_create_loan_application_api(self):
        """Test creating a loan application via API"""
        self.client.force_authenticate(user=self.member1)

        url = reverse('loan-application-list')
        data = {
            'loan': self.loan.id,
            'group': self.group.id,
            'required_guarantors': 1,
            'min_guarantee_percentage': '20.00'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(response.data['required_guarantors'], 1)

    def test_submit_loan_application_api(self):
        """Test submitting a loan application via API"""
        # Create application
        application = LoanApplication.objects.create(
            loan=self.loan,
            applicant=self.member1,
            group=self.group,
            required_guarantors=1,
            min_guarantee_percentage=Decimal('20.00')
        )

        # Add guarantor
        member2 = User.objects.create_user(
            username='member2',
            email='member2@test.com',
            password='password123',
            user_type='member'
        )
        Guarantor.objects.create(
            loan=self.loan,
            member=member2,
            guarantee_amount=Decimal('10000.00'),
            status='approved'
        )

        self.client.force_authenticate(user=self.member1)

        url = reverse('submit-loan-application', kwargs={'application_id': application.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('submitted successfully', response.data['message'])

        # Check application was submitted
        application.refresh_from_db()
        self.assertEqual(application.status, 'submitted')
        self.assertIsNotNone(application.submitted_date)
