""" password tool """
from os import urandom
from random import randint
from codecs import getencoder
from hashlib import sha1
from base64 import urlsafe_b64encode, urlsafe_b64decode
from datetime import timedelta
from zope import interface
from memphis import config

import ptah
from ptah import token

from service import authService
from settings import AUTH_SETTINGS
from interfaces import _, IPasswordTool


TOKEN_TYPE = token.registerTokenType(
    '2871cd61-8995-43d2-9b96-d841ec06b8de', timedelta(minutes=10))


class PlainPasswordManager(object):
    """PLAIN password manager."""

    def encode(self, password, salt=None):
        return '{plain}%s'%password

    def check(self, encoded, password):
        if encoded != password:
            return encoded == '{plain}%s'%password
        return True


class SSHAPasswordManager(object):
    """SSHA password manager."""

    _encoder = getencoder("utf-8")

    def encode(self, password, salt=None):
        if salt is None:
            salt = urandom(4)
        hash = sha1(self._encoder(password)[0])
        hash.update(salt)
        return '{ssha}' + urlsafe_b64encode(hash.digest() + salt)

    def check(self, encoded_password, password):
        # urlsafe_b64decode() cannot handle unicode input string. We
        # encode to ascii. This is safe as the encoded_password string
        # should not contain non-ascii characters anyway.
        encoded_password = encoded_password.encode('ascii')
        byte_string = urlsafe_b64decode(encoded_password[6:])
        salt = byte_string[20:]
        return encoded_password == self.encodePassword(password, salt)


class PasswordTool(object):
    """ Password management utility. """
    interface.implements(IPasswordTool)

    min_length = 5
    letters_digits = False
    letters_mixed_case = False

    pm = {'{plain}': PlainPasswordManager(),
          '{ssha}': SSHAPasswordManager(),
          }
    passwordManager = pm['{plain}']

    def checkPassword(self, encodedPassword, password):
        for prefix, pm in self.pm.items():
            if encodedPassword.startswith(prefix):
                return pm.check(encodedPassword, password)

        return self.passwordManager.check(encodedPassword, password)

    def encodePassword(self, password, salt=None):
        return self.passwordManager.encode(password, salt)

    def getPrincipal(self, passcode):
        data = token.tokenService.get(TOKEN_TYPE, passcode)

        if data is not None:
            return ptah.resolve(data)

    def generatePasscode(self, uuid):
        return token.tokenService.generate(TOKEN_TYPE, uuid)

    def removePasscode(self, passcode):
        token.tokenService.remove(passcode)

    def validatePassword(self, password):
        if len(password) < self.min_length:
            #return _('Password should be at least ${count} characters.',
            #         mapping={'count': self.min_length})
            return 'Password should be at least %s characters.'%\
                self.min_length
        elif self.letters_digits and \
                (password.isalpha() or password.isdigit()):
            return _('Password should contain both letters and digits.')
        elif self.letters_mixed_case and \
                (password.isupper() or password.islower()):
            return _('Password should contain letters in mixed case.')

    def passwordStrength(self, password):
        return 100.0


passwordTool = PasswordTool()


@config.handler(config.SettingsInitializing)
def initializing(ev):

    mng = PasswordTool.pm.get(AUTH_SETTINGS.pwdmanager)
    if mng is None:
        mng = PasswordTool.pm.get('{%s}'%AUTH_SETTINGS.pwdmanager)

    if mng is None:
        mng = PasswordTool.pm['{plain}']

    passwordTool.passwordManager = mng
