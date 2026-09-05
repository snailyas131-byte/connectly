import io
import unittest
from datetime import date
from app import create_app
from models import db, User, Contact, Category
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key-12345'


class ConnectlyTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register_user(self, full_name="Alice Smith", email="alice@example.com", password="password123"):
        return self.client.post('/register', data={
            'full_name': full_name,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)

    def login_user(self, email="alice@example.com", password="password123"):
        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def logout_user(self):
        return self.client.get('/logout', follow_redirects=True)

    # ---------------------------------------------------------
    # 1. AUTHENTICATION TESTS
    # ---------------------------------------------------------
    def test_user_registration_success(self):
        response = self.register_user()
        self.assertEqual(response.status_code, 200)
        user = User.query.filter_by(email="alice@example.com").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.full_name, "Alice Smith")
        # Check default categories were created
        categories = Category.query.filter_by(user_id=user.id).all()
        self.assertTrue(len(categories) >= 6)

    def test_duplicate_registration_fails(self):
        self.register_user(email="alice@example.com")
        # Try registering again with same email
        response = self.register_user(email="alice@example.com")
        self.assertIn(b"An account with this email address already exists", response.data)

    def test_login_success_and_failure(self):
        self.register_user(email="alice@example.com", password="password123")
        
        # Wrong password
        resp_fail = self.login_user(email="alice@example.com", password="wrongpassword")
        self.assertIn(b"Invalid email or password", resp_fail.data)

        # Correct password
        resp_success = self.login_user(email="alice@example.com", password="password123")
        self.assertEqual(resp_success.status_code, 200)
        self.assertIn(b"Welcome back, Alice", resp_success.data)

    def test_logout(self):
        self.register_user()
        self.login_user()
        resp = self.logout_user()
        self.assertIn(b"You have been logged out successfully", resp.data)

    # ---------------------------------------------------------
    # 2. CONTACT CRUD TESTS
    # ---------------------------------------------------------
    def test_add_contact_success(self):
        self.register_user()
        self.login_user()

        response = self.client.post('/contacts/new', data={
            'first_name': 'Sarah',
            'last_name': 'Connor',
            'phone': '+1 (555) 234-5678',
            'email': 'sarah@cyberdyne.io',
            'company': 'Cyberdyne Systems',
            'job_title': 'Security Lead',
            'city': 'San Francisco',
            'notes': 'Key contact'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact added successfully", response.data)
        self.assertIn(b"Sarah Connor", response.data)

        contact = Contact.query.filter_by(first_name='Sarah').first()
        self.assertIsNotNone(contact)
        self.assertEqual(contact.company, 'Cyberdyne Systems')

    def test_add_contact_validation_missing_name(self):
        self.register_user()
        self.login_user()

        response = self.client.post('/contacts/new', data={
            'first_name': '',
            'phone': '1234567890'
        }, follow_redirects=True)

        self.assertIn(b"First name is required", response.data)

    def test_add_contact_validation_missing_contact_method(self):
        self.register_user()
        self.login_user()

        response = self.client.post('/contacts/new', data={
            'first_name': 'John',
            'phone': '',
            'email': ''
        }, follow_redirects=True)

        self.assertIn(b"Please provide at least one contact method", response.data)

    def test_edit_contact_success(self):
        self.register_user()
        self.login_user()

        # Create contact
        self.client.post('/contacts/new', data={
            'first_name': 'John',
            'last_name': 'Doe',
            'phone': '555-111-2222'
        }, follow_redirects=True)

        contact = Contact.query.filter_by(first_name='John').first()

        # Edit contact
        response = self.client.post(f'/contacts/{contact.id}/edit', data={
            'first_name': 'John',
            'last_name': 'Updated',
            'phone': '555-999-8888',
            'email': 'john.updated@example.com',
            'city': 'New York'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact updated successfully", response.data)
        
        db.session.refresh(contact)
        self.assertEqual(contact.last_name, 'Updated')
        self.assertEqual(contact.city, 'New York')

    def test_delete_contact_success(self):
        self.register_user()
        self.login_user()

        self.client.post('/contacts/new', data={
            'first_name': 'DeleteMe',
            'phone': '555-000-0000'
        }, follow_redirects=True)

        contact = Contact.query.filter_by(first_name='DeleteMe').first()
        self.assertIsNotNone(contact)

        response = self.client.post(f'/contacts/{contact.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Contact deleted successfully", response.data)

        deleted = Contact.query.filter_by(first_name='DeleteMe').first()
        self.assertIsNone(deleted)

    def test_toggle_favorite(self):
        self.register_user()
        self.login_user()

        self.client.post('/contacts/new', data={
            'first_name': 'FavPerson',
            'email': 'fav@example.com'
        }, follow_redirects=True)

        contact = Contact.query.filter_by(first_name='FavPerson').first()
        self.assertFalse(contact.is_favorite)

        # Toggle favorite via POST
        response = self.client.post(f'/contacts/{contact.id}/toggle-favorite', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertTrue(json_data['is_favorite'])

        db.session.refresh(contact)
        self.assertTrue(contact.is_favorite)

    # ---------------------------------------------------------
    # 3. MULTI-USER ISOLATION & SECURITY TESTS
    # ---------------------------------------------------------
    def test_cross_user_isolation(self):
        # Create User A & Contact
        self.register_user(full_name="Alice", email="alice@test.com", password="password123")
        self.login_user(email="alice@test.com", password="password123")
        self.client.post('/contacts/new', data={'first_name': 'AliceContact', 'phone': '111-222-3333'})
        alice_contact = Contact.query.filter_by(first_name='AliceContact').first()
        self.logout_user()

        # Create User B
        self.register_user(full_name="Bob", email="bob@test.com", password="password123")
        self.login_user(email="bob@test.com", password="password123")

        # Bob tries to VIEW Alice's contact -> Must 404
        resp_view = self.client.get(f'/contacts/{alice_contact.id}')
        self.assertEqual(resp_view.status_code, 404)

        # Bob tries to EDIT Alice's contact -> Must 404
        resp_edit = self.client.post(f'/contacts/{alice_contact.id}/edit', data={'first_name': 'Hacked', 'phone': '000'})
        self.assertEqual(resp_edit.status_code, 404)

        # Bob tries to DELETE Alice's contact -> Must 404
        resp_del = self.client.post(f'/contacts/{alice_contact.id}/delete')
        self.assertEqual(resp_del.status_code, 404)

        # Verify Alice's contact is untouched
        db.session.refresh(alice_contact)
        self.assertEqual(alice_contact.first_name, 'AliceContact')

    # ---------------------------------------------------------
    # 4. DUPLICATE DETECTION TESTS
    # ---------------------------------------------------------
    def test_duplicate_contact_warning(self):
        self.register_user()
        self.login_user()

        # Create first contact
        self.client.post('/contacts/new', data={
            'first_name': 'Contact1',
            'phone': '555-999-1111',
            'email': 'duplicate@example.com'
        }, follow_redirects=True)

        # Attempt to create second contact with same email without ignore flag
        response = self.client.post('/contacts/new', data={
            'first_name': 'Contact2',
            'phone': '555-888-2222',
            'email': 'duplicate@example.com'
        }, follow_redirects=True)

        self.assertIn(b"Potential Duplicate Contact Detected", response.data)
        self.assertIn(b"duplicate@example.com", response.data)

        # Now post with ignore_duplicate = 1
        response2 = self.client.post('/contacts/new', data={
            'first_name': 'Contact2',
            'phone': '555-888-2222',
            'email': 'duplicate@example.com',
            'ignore_duplicate': '1'
        }, follow_redirects=True)

        self.assertIn(b"Contact added successfully", response2.data)

    # ---------------------------------------------------------
    # 5. CSV IMPORT & EXPORT TESTS
    # ---------------------------------------------------------
    def test_csv_export(self):
        self.register_user()
        self.login_user()

        self.client.post('/contacts/new', data={
            'first_name': 'ExportPerson',
            'last_name': 'Test',
            'phone': '555-444-3333',
            'email': 'export@example.com',
            'company': 'Export Corp',
            'city': 'Chicago'
        }, follow_redirects=True)

        response = self.client.get('/contacts/export')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')
        self.assertIn(b'ExportPerson', response.data)
        self.assertIn(b'Export Corp', response.data)

    def test_csv_import_valid_and_error_handling(self):
        self.register_user()
        self.login_user()

        csv_content = """first_name,last_name,phone,email,company,city,category
Alice,Imported,555-101-0001,alice.imp@example.com,Tech Co,Boston,Work
Bob,SkippedMissingMethod,,,,Seattle,Friends
Charlie,DuplicateCheck,555-101-0001,charlie@example.com,Corp,Miami,Other
David,Imported2,555-101-0002,david@example.com,Design,Austin,Clients
"""
        csv_file = (io.BytesIO(csv_content.encode('utf-8')), 'test_import.csv')

        response = self.client.post(
            '/contacts/import',
            data={'csv_file': csv_file},
            content_type='multipart/form-data',
            follow_redirects=True
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"contacts imported", response.data)

        # Alice and David should be imported (2 imported, 1 duplicate Charlie, 1 invalid Bob)
        c_alice = Contact.query.filter_by(first_name='Alice').first()
        self.assertIsNotNone(c_alice)
        self.assertEqual(c_alice.company, 'Tech Co')

        c_david = Contact.query.filter_by(first_name='David').first()
        self.assertIsNotNone(c_david)

    # ---------------------------------------------------------
    # 6. SEARCH, SORT & FILTER TESTS
    # ---------------------------------------------------------
    def test_dashboard_search_and_filter(self):
        self.register_user()
        self.login_user()

        # Add 3 contacts
        self.client.post('/contacts/new', data={'first_name': 'Alexander', 'last_name': 'Graham', 'phone': '555-111-0001'})
        self.client.post('/contacts/new', data={'first_name': 'Nikola', 'last_name': 'Tesla', 'phone': '555-111-0002', 'company': 'Wardenclyffe'})
        self.client.post('/contacts/new', data={'first_name': 'Ada', 'last_name': 'Lovelace', 'email': 'ada@analytics.io', 'is_favorite': '1'})

        # Search query for 'Tesla'
        resp_search = self.client.get('/dashboard?q=Tesla')
        self.assertIn(b'data-name="Nikola Tesla"', resp_search.data)
        self.assertNotIn(b'data-name="Alexander Graham"', resp_search.data)

        # Favorites filter
        resp_fav = self.client.get('/dashboard?favorites=1')
        self.assertIn(b'data-name="Ada Lovelace"', resp_fav.data)
        self.assertNotIn(b'data-name="Nikola Tesla"', resp_fav.data)

        # Sorting
        resp_sort = self.client.get('/dashboard?sort=name_asc')
        self.assertEqual(resp_sort.status_code, 200)

    # ---------------------------------------------------------
    # 7. API ENDPOINTS & FILE VALIDATION TESTS
    # ---------------------------------------------------------
    def test_api_check_duplicate_and_stats(self):
        self.register_user()
        self.login_user()

        self.client.post('/contacts/new', data={'first_name': 'Sam', 'phone': '555-432-1098', 'email': 'sam@example.com'})

        # Test duplicate detector API
        resp_api = self.client.get('/api/check-duplicate?phone=555-432-1098')
        data = resp_api.get_json()
        self.assertTrue(data['has_duplicate'])
        self.assertTrue(len(data['warnings']) > 0)

        # Test stats API
        resp_stats = self.client.get('/api/stats')
        stats_data = resp_stats.get_json()
        self.assertEqual(stats_data['total'], 1)

    def test_api_categories_management(self):
        self.register_user()
        self.login_user()

        # Create new category via API
        resp_cat = self.client.post('/api/categories', json={'name': 'VIP Mentors'})
        self.assertEqual(resp_cat.status_code, 201)
        cat_json = resp_cat.get_json()
        self.assertTrue(cat_json['success'])
        self.assertEqual(cat_json['name'], 'VIP Mentors')

        # List categories
        resp_list = self.client.get('/api/categories')
        self.assertEqual(resp_list.status_code, 200)
        names = [c['name'] for c in resp_list.get_json()]
        self.assertIn('VIP Mentors', names)

    def test_image_upload_invalid_extension_rejected(self):
        self.register_user()
        self.login_user()

        bad_file = (io.BytesIO(b"malicious script content"), "script.exe")
        resp = self.client.post(
            '/contacts/new',
            data={
                'first_name': 'Hacker',
                'phone': '555-000-1111',
                'profile_picture': bad_file
            },
            content_type='multipart/form-data',
            follow_redirects=True
        )
        self.assertIn(b"Invalid image format", resp.data)


if __name__ == '__main__':
    unittest.main()
