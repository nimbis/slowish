import random
import string

from django.db import models


def generate_token():
    return ''.join([random.SystemRandom().choice(
        string.letters + string.digits) for i in range(150)])


class SlowishAccount(models.Model):
    """An account (aka 'tenant') for Slowish storage."""

    id = models.IntegerField(
        help_text="Also known as Account # within rackspace, eg. '123456'.",
        primary_key=True)

    class Meta:
        verbose_name = "Slowish Account"
        verbose_name_plural = "Slowish Accounts"

    def __unicode__(self):
        return str(self.id)


class SlowishUser(models.Model):
    """
    A username and password to authenticate and access Slowish storage.

    Each SlowishUser is associated with a single SlowishAccount.

    When a SlowishUser authenticates, a token will be generated for
    the user, which can be passed as an HTTP_X_AUTH_TOKEN header to
    authenticate various requests.
    """

    account = models.ForeignKey(SlowishAccount, on_delete=models.CASCADE)

    username = models.CharField(
        help_text="A username, eg. 'first.last'.",
        max_length=255)

    password = models.CharField(
        help_text="Password associated with this username.",
        max_length=255)

    token = models.CharField(
        help_text="Generated token to allow authorized uses of the API.",
        max_length=255,
        default=generate_token)

    class Meta:
        verbose_name = "Slowish User"
        verbose_name_plural = "Slowish Users"
        unique_together = ('account', 'username')

    def __unicode__(self):
        return "{0} (in account {1})".format(self.username, self.account.id)


class SlowishContainer(models.Model):
    """A container, (within a particular account)."""

    account = models.ForeignKey(SlowishAccount, on_delete=models.CASCADE)

    name = models.CharField(
        help_text="A name for this container.",
        max_length=255)

    class Meta:
        verbose_name = "Slowish Container"
        verbose_name_plural = "Slowish Containers"
        unique_together = ('account', 'name')

    def __unicode__(self):
        return "{0} (in account {1})".format(self.name, self.account.id)
