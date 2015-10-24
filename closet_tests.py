import os
import closet
import unittest
import tempfile


class ClosetTestCase(unittest.TestCase):

    def setUp(self):
        """Set up test environment befor each test"""
        self.db_fd, closet.app.config['DATABASE'] = tempfile.mkstemp()
        closet.app.config['TESTING'] = True
        self.app = closet.app.test_client()
        closet.init_db()

    def tearDown(self):
        """Tear down test environment after each test"""
        os.close(self.db_fd)
        os.unlink(closet.app.config['DATABASE'])

    def login(self, username, password):
        """Login to test website as specified user with the specified
        password
        """
        return self.app.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        """Logout of test website"""
        return self.app.get('/logout', follow_redirects=True)

    def authenticate(self):
        """Login to test website as the standard test user"""
        self.login(closet.app.config['USERNAME'],
                   closet.app.config['PASSWORD'])

    # Generic Tests

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

    # Category Tests

    category_base_url = '/categories'

    def get_category_url(self, *args):
        return '/'.join((self.category_base_url,) + args)

    def test_get_category_form(self):
        """Test that the category form is accessible"""
        self.authenticate()
        rv = self.app.get(self.get_category_url('add'))
        assert b'Add Category' in rv.data
        assert b'Name' in rv.data
        assert b'Slug' in rv.data
        assert b'Parent' in rv.data

    def test_add_root_category(self):
        """Test that adding root categories works"""
        self.authenticate()
        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='<Pants>', slug='pants'
        ), follow_redirects=True)
        assert b'Your closet is empty.' not in rv.data
        assert b'&lt;Pants&gt;' in rv.data
        rv = self.app.get(self.get_category_url('pants'))
        assert b'This category is empty.' in rv.data

    def test_add_child_category(self):
        """Test that adding child categories works"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Jeans', slug='jeans', parent='pants'
        ), follow_redirects=True)
        rv = self.app.get(self.get_category_url('pants'))
        assert b'This category is empty.' not in rv.data
        assert b'Jeans' in rv.data

    def test_add_category_blank_name(self):
        """Test that adding a category with a blank name fails"""
        self.authenticate()
        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='', slug='shirts'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Name is required' in rv.data

    def test_add_category_missing_name(self):
        """Test that adding a category without a name parameter fails"""
        self.authenticate()
        rv = self.app.post(self.get_category_url('add'), data=dict(
            slug='shirts'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Name is required' in rv.data

    def test_add_category_blank_slug(self):
        """Test that adding a category with a blank slug fails"""
        self.authenticate()
        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Shirts', slug=''
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Slug is required' in rv.data

    def test_add_category_missing_slug(self):
        """Test that adding a category without a slug parameter fails"""
        self.authenticate()
        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Shirts'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Slug is required' in rv.data

    def test_add_category_bad_parent(self):
        """Test that adding a category with a non-existent parent fails"""
        self.authenticate()
        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Shirts', slug='shirts', parent='spam'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Parent does not exist' in rv.data

    def test_add_category_bad_slug(self):
        """Test that adding a category with an incorrect slug fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Polo Shirts', slug='polo shirts'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Slug is formatted incorrectly' in rv.data

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name=':)', slug=':)'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Slug is formatted incorrectly' in rv.data

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Add', slug='add'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Slug "add" is not allowed' in rv.data

    def test_add_category_existing_slug(self):
        """Test that adding a category with an existing slug fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)
        assert b'Pants' in rv.data

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)
        assert b'Add Category' in rv.data
        assert b'Slug exists' in rv.data

    def test_categories_are_sorted(self):
        """Test that categories are sorted alphabetically"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)
        assert b'Pants' in rv.data

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Hats', slug='hats'
        ), follow_redirects=True)
        assert b'Hats' in rv.data

        assert rv.data.index(b'Pants') > rv.data.index(b'Hats')

    def test_delete_category(self):
        """Test that deleting a category works"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)
        assert b'Pants' in rv.data

        rv = self.app.get(self.get_category_url('pants', 'delete'),
                          follow_redirects=True)
        assert b'Pants' not in rv.data

    def test_delete_category(self):
        """Test that deleting a category that doesn't exist fails"""
        self.authenticate()

        rv = self.app.get(self.get_category_url('pants', 'delete'),
                          follow_redirects=True)
        assert b'pants does not exist' in rv.data

    def test_update_category(self):
        """Test that adding child categories works"""
        self.authenticate()

        rv = self.app.post(self.category_base_url, data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.category_base_url, data=dict(
            name='Shirts', slug='shirts'
        ), follow_redirects=True)

        rv = self.app.post(self.category_base_url, data=dict(
            name='Jeans', slug='jeans', parent='pants'
        ), follow_redirects=True)
        rv = self.app.get(self.get_category_url('pants'))
        assert b'Jeans' in rv.data

        rv = self.app.post(self.get_category_url('jeans', 'edit'), data=dict(
            name='T-Shirts', slug='t-shirts', parent='shirts'
        ), follow_redirects=True)

        rv = self.app.get(self.get_category_url('pants'))
        assert b'Jeans' not in rv.data

        rv = self.app.get(self.get_category_url('shirts'))
        assert b'T-Shirts' in rv.data
        assert b't-shirts' in rv.data

    def test_update_category_blank_name(self):
        """Test that updating a category with a blank name fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='', slug='shirts'
        ), follow_redirects=True)

        assert b'Edit Pants' in rv.data
        assert b'Name is required' in rv.data

    def test_update_category_missing_name(self):
        """Test that updating a category with a missing name fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            slug='shirts'
        ), follow_redirects=True)

        assert b'Edit Pants' in rv.data
        assert b'Name is required' in rv.data

    def test_update_category_blank_slug(self):
        """Test that updating a category with a blank slug fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='Shirts', slug=''
        ), follow_redirects=True)

        assert b'Edit Pants' in rv.data
        assert b'Slug is required' in rv.data

    def test_update_category_missing_slug(self):
        """Test that updating a category with a missing slug fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='Shirts'
        ), follow_redirects=True)

        assert b'Edit Pants' in rv.data
        assert b'Slug is required' in rv.data

    def test_update_category_bad_parent(self):
        """Test that updating a category with a non-existent parent fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='Shirts', slug='shirts', parent='spam'
        ), follow_redirects=True)

        assert b'Edit Pants' in rv.data
        assert b'Parent does not exist' in rv.data

    def test_update_category_bad_slug(self):
        """Test that updating a category with an incorrect slug fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='Polo Shirts', slug='polo shirts'
        ), follow_redirects=True)
        assert b'Edit Pants' in rv.data
        assert b'Slug is formatted incorrectly' in rv.data

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name=':)', slug=':)'
        ), follow_redirects=True)
        assert b'Edit Pants' in rv.data
        assert b'Slug is formatted incorrectly' in rv.data

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='Add', slug='add'
        ), follow_redirects=True)
        assert b'Edit Pants' in rv.data
        assert b'Slug "add" is not allowed' in rv.data

    def test_update_category_existing_slug(self):
        """Test that updating a category with an existing slug fails"""
        self.authenticate()

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Pants', slug='pants'
        ), follow_redirects=True)
        assert b'Pants' in rv.data

        rv = self.app.post(self.get_category_url('add'), data=dict(
            name='Shirts', slug='shirts'
        ), follow_redirects=True)
        assert b'Shirts' in rv.data

        rv = self.app.post(self.get_category_url('pants', 'edit'), data=dict(
            name='Shirts', slug='shirts'
        ), follow_redirects=True)
        assert b'Edit Pants' in rv.data
        assert b'Slug exists' in rv.data

if __name__ == '__main__':
    unittest.main()
