import unittest
from app import create_app, db
from app.models import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            user = User(name='Test User', email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_login_success(self):
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
    
    def test_login_failure(self):
        response = self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_registration(self):
        response = self.client.post('/auth/register', data={
            'name': 'New User',
            'email': 'newuser@example.com',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        
        # Verify user was created
        with self.app.app_context():
            user = User.query.filter_by(email='newuser@example.com').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.name, 'New User')

if __name__ == '__main__':
    unittest.main()