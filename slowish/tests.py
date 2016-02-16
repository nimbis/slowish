import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory
from django.http import Http404

from .models import SlowishAccount, SlowishUser, SlowishContainer
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
        """
        Verify that tokens view responds correctly to an invalid post.
        """

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
        """
        Verify that the tokens view gives a token to an authorized user.
        """

        self.user = create_user()

        data = user_data

        # Ensure we get a succesful return with valid credentials
        response = self.client.post(
            reverse('tokens'),
            json.dumps(data), content_type="application/json")
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
            json.dumps(data), content_type="application/json")
        self.assertEquals(response.status_code, 401)


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
    def account_view_get(self, use_invalid_token=False):
        request = self.factory.get(
            reverse('account',
                    kwargs={'account_id': self.user.account.id}))
        if (use_invalid_token):
            request.META['HTTP_X_AUTH_TOKEN'] = 'bogus'
        else:
            request.META['HTTP_X_AUTH_TOKEN'] = self.user.token
        return account(request, self.user.account.id)

    def container_view_put(self, container_name):
        request = self.factory.put(
            reverse('container',
                    kwargs={'account_id': self.user.account.id,
                            'container_name': container_name}))
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

    def test_account_authorized(self):
        """
        Verify that the account view requires a valid token.
        """

        # First attempt to connect with an invalid token. This should fail.
        response = self.account_view_get(use_invalid_token=True)
        self.assertEquals(response.status_code, 401)

        # Then, try again with the correct token, which should work
        response = self.account_view_get()
        self.assertEquals(response.status_code, 200)
        self.assertJSONEqual(response.content, "[]")

    def test_account_ordered(self):
        """ Ensure that containers are listed in alphabetical order."""

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

    def test_account_content(self):
        """
        Verify the json response content from the account view
        """

        # With no containers, we expect an empty list
        response = self.account_view_get()
        self.assertJSONEqual(response.content, "[]")

    def test_container_authorized(self):
        """
        Verify that the container view requires a valid token.
        """

        SlowishContainer.objects.create(
            account=self.user.account,
            name='test')

        # First attempt to connect with an invalid token. This should fail.
        response = self.container_view_get('test', use_invalid_token=True)
        self.assertEquals(response.status_code, 401)

        # Then, try again with the correct token, which should work,
        # (and gives a "204"---No content response status)
        response = self.container_view_get('test')
        self.assertEquals(response.status_code, 204)

    def test_container_create(self):
        """
        Verify we can create a new container.
        """

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

    def test_container_does_not_exist(self):
        """ Verify a 404 status for a non-existent container. """

        with self.assertRaises(Http404):
            self.container_view_get('does_not_exist')
