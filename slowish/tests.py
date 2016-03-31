import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory
from django.http import Http404

from .models import SlowishAccount, SlowishUser, SlowishContainer, SlowishFile
from .views import account, container


user_data = {
    "auth": {
        "passwordCredentials": {
            "username": "user",
            "password": "secret",
        },
        "tenantId": "1234",
    }
}


def create_user():
    account = SlowishAccount.objects.create(
        id=user_data["auth"]["tenantId"])
    return SlowishUser.objects.create(
        account=account,
        username=user_data["auth"]["passwordCredentials"]["username"],
        password=user_data["auth"]["passwordCredentials"]["password"])


class TokensViewTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_tokens_invalid(self):
        """Verify that tokens view responds correctly to an invalid post."""

        # This post does not supply any of the required
        # credentials. It should receive a response indicating that
        # authentication failed.
        response = self.client.post(reverse('tokens'))
        self.assertEquals(response.status_code, 401)
        self.assertJSONEqual(
            response.content,
            '{"unauthorized":{"code":401,"message":'
            '"Unable to authenticate user with credentials provided."}}')

    def test_tokens_authorized(self):
        """Verify that the tokens view gives a token to an authorized user."""

        self.user = create_user()

        # Test the __unicode__ methods in SlowishAccount and SlowishUser
        self.assertEquals(str(self.user.account), "1234")
        self.assertEquals(str(self.user), "user (in account 1234)")

        data = user_data

        # Ensure we get a succesful return with valid credentials
        response = self.client.post(
            reverse('tokens'),
            json.dumps(data),
            content_type="application/json")
        self.assertEquals(response.status_code, 200)
        content = json.loads(response.content)
        url = (content['access']['serviceCatalog'][0]
               ['endpoints'][0]['publicURL'])
        self.assertEquals(url, "http://testserver/slowish/files/1234")
        self.assertEquals(content['access']['token']['id'], self.user.token)

        # Try again, but this time with an invalid password, which
        # should yield an authorization failure
        data["auth"]["passwordCredentials"]["password"] = "incorrect"
        response = self.client.post(
            reverse('tokens'),
            json.dumps(data),
            content_type="application/json")
        self.assertEquals(response.status_code, 401)

    def test_tokens_with_tenant_name(self):
        """Verify that we can authenticate with a 'tenantName' entry."""

        self.user = create_user()

        # Drop the tenantId from the data
        data = user_data.copy()
        del data["auth"]["tenantId"]

        # Ensure that we can't authenticate that way
        response = self.client.post(
            reverse('tokens'),
            json.dumps(data),
            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Add a tenantName instead
        data["auth"]["tenantName"] = "1234"

        # And verify that that works
        response = self.client.post(
            reverse('tokens'),
            json.dumps(data),
            content_type="application/json")
        self.assertEquals(response.status_code, 200)


class FilesViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = create_user()

    # The various files views are a little tricky to invoke. We would
    # like to just use self.client.get() but we can't because we need
    # to install a custom HTTP_X_AUTH_TOKEN header. So, instead we use
    # RequestFactory to assemble the request and then we pass that
    # request directly into the account() view function.
    #
    # Here are some helper functions to make that more convenient
    def account_view_get(self,
                         use_invalid_token=False,
                         query=''):

        url = reverse('account', kwargs={'account_id': self.user.account.id})
        url += query

        request = self.factory.get(url)

        if (use_invalid_token):
            request.META['HTTP_X_AUTH_TOKEN'] = 'bogus'
        else:
            request.META['HTTP_X_AUTH_TOKEN'] = self.user.token

        return account(request, self.user.account.id)

    def container_view_put(self, container_name):
        url = reverse('container',
                      kwargs={'account_id': self.user.account.id,
                              'container_name': container_name})
        request = self.factory.put(url)
        request.META['HTTP_X_AUTH_TOKEN'] = self.user.token
        return container(request, self.user.account.id, container_name)

    def container_view_get(self, container_name, use_invalid_token=False):
        request = self.factory.get(
            reverse('container',
                    kwargs={'account_id': self.user.account.id,
                            'container_name': container_name}))
        if (use_invalid_token):
            request.META['HTTP_X_AUTH_TOKEN'] = 'bogus'
        else:
            request.META['HTTP_X_AUTH_TOKEN'] = self.user.token
        return container(request, self.user.account.id, container_name)

    def file_view_put(self, container_name, path):
        url = reverse('file',
                      kwargs={'account_id': self.user.account.id,
                              'container_name': container_name,
                              'path': path})
        request = self.factory.put(url)
        request.META['HTTP_X_AUTH_TOKEN'] = self.user.token
        return container(request, self.user.account.id, container_name, path)

    def file_view_get(self, container_name, path='', query=''):
        url = reverse('file',
                      kwargs={'account_id': self.user.account.id,
                              'container_name': container_name,
                              'path': path})
        url += query
        request = self.factory.get(url)
        request.META['HTTP_X_AUTH_TOKEN'] = self.user.token
        return container(request, self.user.account.id, container_name, path)

    def test_account_authorized(self):
        """Verify that the account view requires a valid token."""

        # First attempt to connect with an invalid token. This should fail.
        response = self.account_view_get(use_invalid_token=True)
        self.assertEquals(response.status_code, 401)

        # Then, try again with the correct token, which should work
        response = self.account_view_get()
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, "[]")

    def test_account_ordered(self):
        """Ensure that containers are listed in alphabetical order."""

        acc = self.user.account
        SlowishContainer.objects.create(account=acc, name='foo')
        SlowishContainer.objects.create(account=acc, name='bar')
        SlowishContainer.objects.create(account=acc, name='baz')

        response = self.account_view_get()
        self.assertJSONEqual(
            response.content,
            '[{"count": 0, "bytes": 0, "name": "bar"},'
            '{"count": 0, "bytes": 0, "name": "baz"},'
            '{"count": 0, "bytes": 0, "name": "foo"}]')

    def test_account_range(self):
        """Test marker and end_marker parameters when listing containers."""

        account = self.user.account
        names = ['this', 'is', 'a', 'collection', 'of', 'container',
                 'names', 'in', 'no', 'particular', 'order']
        for name in names:
            SlowishContainer.objects.create(account=account, name=name)

        response = self.account_view_get(query="?marker=order")
        self.assertJSONEqual(
            response.content,
            '[{"count": 0, "bytes": 0, "name": "particular"},'
            '{"count": 0, "bytes": 0, "name": "this"}]')

        response = self.account_view_get(query="?end_marker=container")
        self.assertJSONEqual(
            response.content,
            '[{"count": 0, "bytes": 0, "name": "a"},'
            '{"count": 0, "bytes": 0, "name": "collection"}]')

        response = self.account_view_get(
            query="?marker=container&end_marker=names")
        self.assertJSONEqual(
            response.content,
            '[{"count": 0, "bytes": 0, "name": "in"},'
            '{"count": 0, "bytes": 0, "name": "is"}]')

    def test_account_content(self):
        """Verify the json response content from the account view."""

        # With no containers, we expect an empty list
        response = self.account_view_get()
        self.assertJSONEqual(response.content, "[]")

    def test_container_authorized(self):
        """Verify that the container view requires a valid token."""

        SlowishContainer.objects.create(
            account=self.user.account,
            name='test')

        # First attempt to connect with an invalid token. This should fail.
        response = self.container_view_get('test', use_invalid_token=True)
        self.assertEquals(response.status_code, 401)

        # Then, try again with the correct token, which should work
        response = self.container_view_get('test')
        self.assertEquals(response.status_code, 200)

    def test_container_create(self):
        """Verify we can create a new container."""

        # Prior to creation, there shold be an empty list of containers
        response = self.account_view_get()
        self.assertJSONEqual(response.content, "[]")

        # Issue a PUT request to create a new container (returns a
        # status of 201==Created)
        response = self.container_view_put('new_container')
        self.assertEquals(response.status_code, 201)

        # Trying to create again is fine and gives a 200==OK status
        response = self.container_view_put('new_container')
        self.assertEquals(response.status_code, 200)

        # Verify that the newly created container now appears in the
        # list of containers
        response = self.account_view_get()
        self.assertJSONEqual(
            response.content,
            '[{"count": 0, "bytes": 0, "name": "new_container"}]')

        # Test the __unicode__ method within SlowishContainer
        container = SlowishContainer.objects.get(name="new_container")
        self.assertEquals(str(container), "new_container (in account 1234)")

    def test_file_create(self):
        """Verify we can create a file within a container."""

        # Create a container
        self.container_view_put('container')

        # Create a file within that container (returns status of
        # 201==Created)
        response = self.file_view_put('container', 'path/to/file')
        self.assertEquals(response.status_code, 201)

        # Trying to create again is fine and gives a 200=OK status
        response = self.file_view_put('container', 'path/to/file')
        self.assertEquals(response.status_code, 200)

        # Test the __unicode__ method within SlowishFile
        file = SlowishFile.objects.get(path="path/to/file")
        self.assertEquals(
            str(file),
            "path/to/file (in container container (in account 1234))")

        # Create a couple of more files
        self.file_view_put("container", "another/file")
        self.file_view_put("container", "and/yet/one/more")

        # Query list of files in container
        response = self.file_view_get("container")
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            '[{"bytes": 0, "content_type": "application/directory",'
            '"name": "and/yet/one/more"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "another/file"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "path/to/file"}]')

    def test_files_range(self):
        """Verify marker and end_marker parameters for file list."""

        container = SlowishContainer.objects.create(
            account=self.user.account,
            name="blob")

        names = ['this', 'is', 'a', 'collection', 'of', 'file',
                 'names', 'in', 'no', 'particular', 'order']
        for name in names:
            SlowishFile.objects.create(
                container=container,
                path=name)

        response = self.file_view_get("blob", query="?marker=order")
        self.assertJSONEqual(
            response.content,
            '[{"bytes": 0, "content_type": "application/directory",'
            '"name": "particular"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "this"}]')

        response = self.file_view_get("blob", query="?end_marker=file")
        self.assertJSONEqual(
            response.content,
            '[{"bytes": 0, "content_type": "application/directory",'
            '"name": "a"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "collection"}]')

        response = self.file_view_get(
            "blob",
            query="?marker=file&end_marker=names")
        self.assertJSONEqual(
            response.content,
            '[{"bytes": 0, "content_type": "application/directory",'
            '"name": "in"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "is"}]')

    def test_files_prefix(self):
        """Verify query of files matching a prefix."""

        # Create several files in a container
        self.container_view_put("containter")
        self.file_view_put("container", "this/file/is/your/file")
        self.file_view_put("container", "this/file/is/my/file")
        self.file_view_put("container", "from/california")
        self.file_view_put("container", "to/the/new/york/island")
        self.file_view_put("container", "this/file/is/made/for/you/and/me")

        # List only those files matching a prefix
        response = self.file_view_get("container", query="?prefix=this/file")
        self.assertJSONEqual(
            response.content,
            '[{"bytes": 0, "content_type": "application/directory",'
            '"name": "this/file/is/made/for/you/and/me"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "this/file/is/my/file"},'
            '{"bytes": 0, "content_type": "application/directory",'
            '"name": "this/file/is/your/file"}]')

    # We don't yet support getting file contents, but we can at least
    # ask about directory objects that we have stored as files within
    # a container.
    def test_directory_get(self):
        """Verify that a specific file in a container can be queried."""

        self.container_view_put('container')
        self.file_view_put('container', 'path/to/file')

        # Verify file query returns successful status
        response = self.file_view_get("container", "path/to/file")
        self.assertEquals(response.status_code, 200)

        # And a non-existent file should fail
        response = self.file_view_get("container", "does/not/exist")
        self.assertEquals(response.status_code, 404)

    def test_container_does_not_exist(self):
        """Verify a 404 status for a non-existent container."""

        with self.assertRaises(Http404):
            self.container_view_get('does_not_exist')
