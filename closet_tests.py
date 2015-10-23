import os
import closet
import unittest
import tempfile

class ClosetTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, closet.app.config['DATABASE'] = tempfile.mkstemp()
        closet.app.config['TESTING'] = True
        self.app = closet.app.test_client()
        closet.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(closet.app.config['DATABASE'])

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    # Test cases

    def test_empty_db(self):
        """Start with a blank database."""
        rv = self.app.get('/')
        assert b'Your closet is empty.' in rv.data

    def test_login_logout(self):
        """Make sure login and logout works"""
        rv = self.login(closet.app.config['USERNAME'],
                        closet.app.config['PASSWORD'])
        assert b'You were logged in' in rv.data
        rv = self.logout()
        assert b'You were logged out' in rv.data
        rv = self.login(closet.app.config['USERNAME'] + 'x',
                        closet.app.config['PASSWORD'])
        assert b'Invalid username' in rv.data
        rv = self.login(closet.app.config['USERNAME'],
                        closet.app.config['PASSWORD'] + 'x')
        assert b'Invalid password' in rv.data

    def test_add(self):
        """Test that adding garments works"""
        self.login(closet.app.config['USERNAME'],
                   closet.app.config['PASSWORD'])
        rv = self.app.post('/add', data=dict(
            description='<Hat>'
        ), follow_redirects=True)
        assert b'Your closet is empty.' not in rv.data
        assert b'&lt;Hat&gt;' in rv.data

if __name__ == '__main__':
    unittest.main()
