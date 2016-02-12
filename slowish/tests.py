from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client


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
