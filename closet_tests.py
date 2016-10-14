import os
import closet
import unittest
import tempfile


def in_response(response, value):
    return value.encode() in response.data


def is_404(response):
    response.status_code == 404


class ClosetTestBase(unittest.TestCase):

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


class ClosetTestCase(ClosetTestBase):

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


class ModelBase(unittest.TestCase):

    # Model based view test helpers

    def __init__(self, *args, **kwargs):
        super(ModelBase, self).__init__(*args, **kwargs)
        self.base_url = '/'
        self.add_url = 'add'
        self.edit_url = 'edit'
        self.delete_url = 'delete'
        self.name = ''
        self.nice_name = ''
        self.name_field = 'name'
        self.id_field = 'slug'
        self.fields = {}

    def get_url(self, *args):
        """Create a URL from a tuple of strings based on the base url"""
        try:
            url = '/'.join((self.base_url, ) + args)
        except TypeError:
            url = '/'.join((self.base_url, ) + args[0])
        return url.rstrip('/')

    def get(self, url):
        """Process a GET request to the app"""
        return self.app.get(get_url(url), follow_redirects=True)

    def post(self, url, data):
        """Process a POST request to the app"""
        return self.app.post(get_url(url), data=data, follow_redirects=True)

    def verify_object(self, data):
        """Verify the model object data"""
        rv = self.get(data[self.id_field])
        result = not is_404(rv)
        if result:
            for key, value in data:
                if not in_response(rv, value):
                    return False
        return result

    def get_add_form(self):
        """Test that the "add" form is accessible and contains all the
        fields
        """
        rv = self.get(self.add_url)
        assert not is_404(rv)
        assert in_response(rv, 'Add {}'.format(self.nice_name))
        for field, name in self.fields:
            assert in_response(rv, name)
        return rv

    def get_edit_form(self, data):
        """Test that the edit form is accessible and contains all the
        fields
        """
        self.add_success(data)
        rv = self.get((data[self.id_field], self.edit_url))
        assert not is_404(rv)
        assert in_response(rv, 'Edit {}'.format(data[self.name_field]))
        for field, name in self.fields:
            assert in_response(rv, name)
        return rv

    def get_delete_confirmation_form(self, data):
        """Test that the delete confirmation form is accessible"""
        self.add_success(data)
        rv = self.get((data[self.id_field], self.delete_url))
        assert not is_404(rv)
        assert in_response(rv, 'Delete {}'.format(data[self.name_field]))
        return rv

    def add_success(self, data):
        """Test that adding a model with the given data succeeds"""
        rv = self.post(self.add_url, data)
        assert not in_response(rv, 'Add {}'.format(self.nice_name))
        assert self.verify_object(data)
        return rv

    def edit_success(self, id_, data):
        """Test that updating a model with the given data succeeds"""
        rv = self.post((id_, self.edit_url), data)
        assert not in_response(rv, 'Edit {}'.format(data[self.name_field]))
        assert self.verify_object(data)
        return rv

    def update_success(self, data, new_data):
        """Test that updating a model with the given data succeeds"""
        self.add_success(data)
        return self.edit_success(data[self.id_field], new_data)

    def delete_success(self, id_):
        """Test that deleting the specified model succeeds"""
        rv = self.post((id_, self.delete_url), dict(post='yes'))
        assert not self.verify_object({self.id_field: id_})
        return rv

    def add_fail(self, data, message):
        """Test that adding a model with the given data fails"""
        rv = self.post(self.add_url, data)
        assert in_response(rv, 'Add {}'.format(self.nice_name))
        assert in_response(rv, message)
        return rv

    def edit_fail(self, id_, data, message):
        """Test that updating a model with the given data fails"""
        rv = self.post((id_, self.edit_url), data)
        assert in_response(rv, 'Edit {}'.format(data[self.name_field]))
        assert in_response(rv, message)
        return rv

    def update_fail(self, data, new_data, message):
        """Test that updating a model with the given data fails"""
        self.add_success(data)
        return self.edit_fail(data[self.id_field], new_data, message)

    def delete_fail(self, id_, message):
        """Test that deleting the specified model fails"""
        rv = self.post((id_, self.delete_url), dict(post='yes'))
        assert in_response(rv, message)
        assert self.verify_object({self.id_field: id_})
        return rv

    def bad_data_fail(self, good_data, bad_data, message):
        """Test that adding and updating a model with the given data
        fails
        """
        self.add_fail(bad_data, message)
        self.update_fail(good_data, bad_data, message)

    def add_required_field_fail(self, field, data):
        """Test that adding a model with a blank or missing required
        field fails
        """
        message = '{} is required'.format(self.fields[field])
        data = data.copy()

        data[field] = ''
        self.add_fail(data, message)
        assert not self.verify_object(data)

        del data[field]
        self.add_fail(data, message)
        assert not self.verify_object(data)

    def update_required_field_fail(self, field, data):
        """Test that updating a model with a blank or missing required
        field fails
        """
        message = '{} is required'.format(self.fields[field])
        data = data.copy()
        id_ = data[self.id_field]
        self.add_success(data)

        data[field] = ''
        self.edit_fail(id_, data, message)
        assert not self.verify_object(data)

        del data[field]
        self.edit_fail(id_, data, message)
        assert not self.verify_object(data)

        # Delete base model?

    def required_field_fail(self, field, data):
        """Test that adding and updating a model with a blank or missing
        required field fails
        """
        self.add_required_field_fail(field, data)
        self.update_required_field_fail(field, data)

    def add_existing_key_fail(self, data):
        """Test that adding a model with an existing key fails"""
        message = 'exists'
        rv = self.add_success(data)
        assert not in_response(rv, message)
        return self.add_fail(data, message)

    def update_existing_key_fail(self, data, new_data):
        """Test that adding a model with an existing key fails"""
        message = 'exists'
        rv = self.add_success(data)
        assert not in_response(rv, message)
        rv = self.add_success(new_data)
        assert not in_response(rv, message)
        rv = self.update_fail(data, message)
        assert self.verify_object(new_data)
        return rv

    def existing_key_fail(self, data, new_data):
        """Test that adding and updating a model with an existing key
        fails
        """
        message = 'exists'
        rv = self.add_success(data)
        assert not in_response(rv, message)
        self.add_fail(data, message)
        rv = self.add_success(new_data)
        assert not in_response(rv, message)
        self.update_fail(data, message)
        assert self.verify_object(new_data)

    def data_sorted(self, before_data, after_data, url):
        """Test that the models will be sorted in the correct order"""
        self.add_success(after_data)
        self.add_success(before_data)

        rv = self.get(url)
        after_index = rv.data.index(after_data[self.name_field].encode())
        before_index = rv.data.index(before_data[self.name_field].encode())
        assert after_index > before_index

    def delete_does_not_exist_fail(self, id_):
        """Test that deleting a model that does not exist fails"""
        assert is_404(self.get((id_, self.delete_url)))
        self.delete_fail(id_, 'does not exist')


class CategoryTestCase(ClosetTestBase, ModelBase):

    def __init__(self, *args, **kwargs):
        super(ModelBase, self).__init__(*args, **kwargs)
        self.base_url = '/categories'
        self.name = 'category'
        self.nice_name = 'Category'
        self.fields = {
            'name': 'Name',
            'parent': 'Parent'}
        self.test_data = {
            'pants': {
                'name': 'Pants',
                'slug': 'pants'},
            'shirts': {
                'name': 'Shirts',
                'slug': 'shirts'},
            'jeans': {
                'name': 'Jeans',
                'slug': 'jeans',
                'parent': 'pants'},
            't-shirts': {
                'name': 'T-shirts',
                'slug': 't-shirts',
                'parent': 'shirts'},
            'hats': {
                'name': 'Hats',
                'slug': 'hats',
                'parent': 'spam'},
            'polo-shirts': {
                'name': 'Polo Shirts',
                'slug': 'polo-shirts'},
            'symbols': {
                'name': ':)',
                'slug': ''},
            'keyword': {
                'name': 'Add',
                'slug': 'add-1'}}

    def setUp(self):
        super(CategoryTestCase, self).setUp()
        self.authenticate()

    def test_get_category_forms(self):
        """Test that the category forms are accessible"""
        self.get_add_form()
        self.get_edit_form(self.test_data['pants'])
        self.get_delete_confirmation_form(self.test_data['shirts'])

    def test_add_category(self):
        """Test that adding a category works"""
        self.add_success(self.test_data['pants'])

    def test_update_category(self):
        """Test that updating a category works"""
        self.update_success(self.test_data['pants'], self.test_data['shirts'])

    def test_delete_category(self):
        """Test that deleting a category works"""
        self.add_success(self.test_data['pants'])
        self.delete_success('pants')

    def test_add_child_category(self):
        """Test that adding a child category works"""
        self.add_success(self.test_data['pants'])
        rv = self.get('pants')
        assert in_response(rv, 'This category is empty.')
        self.add_success(self.test_data['jeans'])
        rv = self.get('pants')
        assert not in_response(rv, 'This category is empty.')
        assert in_response(rv, 'Jeans')

    def test_update_child_category(self):
        """Test that updating child categories works"""
        self.add_success(self.test_data['pants'])
        self.add_success(self.test_data['shirts'])

        self.add_success(self.test_data['jeans'])
        rv = self.get('pants')
        assert not in_response(rv, 'This category is empty.')
        assert in_response(rv, 'Jeans')

        self.edit_success('jeans', self.test_data['t-shirts'])
        rv = self.get('pants')
        assert in_response(rv, 'This category is empty.')
        assert not in_response(rv, 'Jeans')
        assert not in_response(rv, 'T-Shirts')
        rv = self.get('shirts')
        assert not in_response(rv, 'This category is empty.')
        assert in_response(rv, 'T-Shirts')
        assert not in_response(rv, 'Jeans')

    def test_name_required(self):
        """Test that adding/updating a category without a name fails"""
        self.required_field_fail('name', self.test_data['pants'])

    def test_parent_does_not_exist(self):
        """Test that adding/updating a category with a non-existent
        parent fails
        """
        self.bad_data_fail(self.test_data['pants'],
                           self.test_data['hats'], 'Parent does not exist')

    def test_category_already_exists(self):
        self.existing_key_fail(
            self.test_data['pants'],
            self.test_data['shirts'])

    def test_categories_are_sorted(self):
        """Test that categories are sorted alphabetically by name"""
        self.data_sorted(self.test_data['shirts'], self.test_data['pants'])

    def test_delete_category_does_not_exist(self):
        """Test that deleting a category that doesn't exist fails"""
        self.delete_does_not_exist_fail('hats')

    def test_add_category_slug_special(self):
        """Test that adding a category with an incorrect name fails"""
        self.add_success(self.test_data['polo-shirts'])
        assert self.verify_object(dict(name='Polo Shirts', slug='polo-shirts'))

        self.add_fail(self.test_data['symbols'], '')

        self.add_success('Add')

    def test_update_category_slug_special(self):
        """Test that updating a category with an incorrect slug fails"""
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


if __name__ == '__main__':
    unittest.main()
