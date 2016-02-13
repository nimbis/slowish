import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from .models import SlowishAccount, SlowishUser

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
