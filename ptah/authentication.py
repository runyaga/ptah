from zope.interface import implementer
from pyramid.security import authenticated_userid
from pyramid.threadlocal import get_current_request

import ptah
from ptah import config
from ptah.uri import resolve, resolver
from ptah.util import tldata
from ptah.interfaces import IAuthInfo, IAuthentication


class _Superuser(object):
    """ Default ptah superuser. check_permission always pass with superuser """

    def __init__(self):
        self.__uri__ = 'ptah-auth:superuser'
        self.login = ''
        self.name = 'Manager'

    def __repr__(self):
        return '<ptah Superuser>'


SUPERUSER = _Superuser()
SUPERUSER_URI = 'ptah-auth:superuser'


@resolver('ptah-auth')
def superuser_resolver(uri):
    """System super user"""
    if uri == SUPERUSER_URI:
        return SUPERUSER


AUTH_CHECKER_ID = 'ptah:authchecker'
AUTH_PROVIDER_ID = 'ptah:authprovider'
AUTH_SEARCHER_ID = 'ptah:authsearcher'


def auth_checker(checker):
    """ register authentication checker::

        @ptah.auth_checker
        def my_checker(info):
            ...

    """
    info = config.DirectiveInfo()
    discr = (AUTH_CHECKER_ID, hash(checker))
    intr = config.Introspectable(
        AUTH_CHECKER_ID, discr, checker.__name__, AUTH_CHECKER_ID)
    intr['name'] = '{0}.{1}'.format(info.codeinfo.module, checker.__name__)
    intr['callable'] = checker
    intr['codeinfo'] = info.codeinfo

    info = config.DirectiveInfo()
    info.attach(
        config.Action(
            lambda config, checker: config.get_cfg_storage(AUTH_CHECKER_ID)\
                .update({id(checker): checker}),
            (checker,), discriminator=discr, introspectables=(intr,))
        )
    return checker


def pyramid_auth_checker(config, checker):
    """ pyramid configurator directive for authentication checker registration::

        config = Configurator()
        config.include('ptah')

        def my_checker(info):
           ...

        config.ptah_auth_checker(my_checker)
    """
    discr = (AUTH_CHECKER_ID, hash(checker))
    intr = ptah.config.Introspectable(AUTH_CHECKER_ID, discr, '', AUTH_CHECKER_ID)
    intr['callable'] = checker

    config.action(
        discr,
        lambda config, checker: config.get_cfg_storage(AUTH_CHECKER_ID)\
            .update({id(checker): checker}),
        (config, checker), introspectables=(intr,))


def auth_provider(name):
    """ decorator for authentication provider registration::

       @ptah.auth_provider('my-provider')
       class AuthProvider(object):
           ...
    """
    info = config.DirectiveInfo()

    def wrapper(cls):
        discr = (AUTH_PROVIDER_ID, name)
        intr = config.Introspectable(
            AUTH_PROVIDER_ID, discr, name, AUTH_PROVIDER_ID)
        intr['id'] = name
        intr['name'] = '{0}.{1}'.format(info.codeinfo.module, cls.__name__)
        intr['provider'] = cls
        intr['codeinfo'] = info.codeinfo

        info.attach(
            config.Action(
                lambda config, n, p: config.get_cfg_storage(AUTH_PROVIDER_ID)\
                    .update({n: cls()}),
                (name, cls), discriminator=discr, introspectables=(intr,))
            )
        return cls

    return wrapper


def register_auth_provider(name, provider):
    """ authentication provider registration::

       class AuthProvider(object):
           ...

       ptah.register_auth_provider('my-provider', AuthProvider())
    """
    info = config.DirectiveInfo()
    discr = (AUTH_PROVIDER_ID, name)
    intr = config.Introspectable(
        AUTH_PROVIDER_ID, discr, name, AUTH_PROVIDER_ID)
    intr['id'] = name
    intr['name'] = '{0}.{1}'.format(
        info.codeinfo.module, provider.__class__.__name__)
    intr['provider'] = provider
    intr['codeinfo'] = info.codeinfo

    info.attach(
        config.Action(
            lambda config, n, p: config.get_cfg_storage(AUTH_PROVIDER_ID)\
                .update({n: p}),
            (name, provider), discriminator=discr, introspectables=(intr,))
        )


def pyramid_auth_provider(config, name, provider):
    """ pyramid configurator directive for
    authentication provider registration::

       class AuthProvider(object):
           ...

       config = Configurator()
       config.include('ptah')
       config.ptah_auth_provider('my-provider', AuthProvider())
    """
    info = ptah.config.DirectiveInfo()
    discr = (AUTH_PROVIDER_ID, name)
    intr = ptah.config.Introspectable(
        AUTH_PROVIDER_ID, discr, name, AUTH_PROVIDER_ID)
    intr['id'] = name
    intr['name'] = '{0}.{1}'.format(
        info.codeinfo.module, provider.__class__.__name__)
    intr['provider'] = provider
    intr['codeinfo'] = info.codeinfo

    config.action(
        discr,
        lambda config, n, p: \
            config.get_cfg_storage(AUTH_PROVIDER_ID).update({n: p}),
        (config, name, provider), introspectables=(intr,))


@implementer(IAuthInfo)
class AuthInfo(object):
    """ Authentication information """

    def __init__(self, principal, status=False, message=''):
        self.__uri__ = getattr(principal, '__uri__', None)
        self.principal = principal
        self.status = status
        self.message = message
        self.arguments = {}


_not_set = object()

USER_KEY = '__ptah_userid__'
EFFECTIVE_USER_KEY = '__ptah_effective__userid__'


@implementer(IAuthentication)
class Authentication(object):
    """ Ptah authentication utility """

    def authenticate(self, credentials):
        providers = config.get_cfg_storage(AUTH_PROVIDER_ID)
        for pname, provider in providers.items():
            principal = provider.authenticate(credentials)
            if principal is not None:
                info = AuthInfo(principal)

                for checker in \
                        config.get_cfg_storage(AUTH_CHECKER_ID).values():
                    if not checker(info):
                        return info

                info.status = True
                return info

        return AuthInfo(None)

    def authenticate_principal(self, principal):
        info = AuthInfo(principal)

        for checker in \
                config.get_cfg_storage(AUTH_CHECKER_ID).values():
            if not checker(info):
                return info

        info.status = True
        return info

    def set_userid(self, uri):
        tldata.set(USER_KEY, uri)

    def get_userid(self):
        uri = tldata.get(USER_KEY, _not_set)
        if uri is _not_set:
            self.set_userid(authenticated_userid(get_current_request()))
            return tldata.get(USER_KEY)
        return uri

    def set_effective_userid(self, uri):
        tldata.set(EFFECTIVE_USER_KEY, uri)

    def get_effective_userid(self):
        uri = tldata.get(EFFECTIVE_USER_KEY, _not_set)
        if uri is _not_set:
            return self.get_userid()
        return uri

    def get_current_principal(self):
        return resolve(self.get_userid())

    def get_principal_bylogin(self, login):
        providers = config.get_cfg_storage(AUTH_PROVIDER_ID)

        for pname, provider in providers.items():
            principal = provider.get_principal_bylogin(login)
            if principal is not None:
                return principal

auth_service = Authentication()


def search_principals(term):
    """ Search principals by term, it uses principal_searcher functions """
    searchers = config.get_cfg_storage(AUTH_SEARCHER_ID)
    for name, searcher in searchers.items():
        for principal in searcher(term):
            yield principal


def register_principal_searcher(name, searcher):
    """ register principal searcher """
    discr = (AUTH_SEARCHER_ID, name)
    intr = config.Introspectable(AUTH_SEARCHER_ID, discr, name, AUTH_SEARCHER_ID)
    intr['name'] = name
    intr['callable'] = searcher

    info = config.DirectiveInfo()
    info.attach(
        config.Action(
            lambda config, name, searcher:
               config.get_cfg_storage(AUTH_SEARCHER_ID).update({name:searcher}),
            (name, searcher), discriminator=discr, introspectables=(intr,))
        )


def pyramid_principal_searcher(config, name, searcher):
    """ pyramid configurator directive for principal searcher registration """
    discr = (AUTH_SEARCHER_ID, name)
    intr = ptah.config.Introspectable(
        AUTH_SEARCHER_ID, discr, name, AUTH_SEARCHER_ID)
    intr['name'] = name
    intr['callable'] = searcher

    config.action(
        (AUTH_SEARCHER_ID, name),
        lambda config, name, searcher:
            config.get_cfg_storage(AUTH_SEARCHER_ID).update({name:searcher}),
        (config, name, searcher), introspectables=(intr,))


def principal_searcher(name):
    """ decorator for principal searcher registration::

        @ptah.principal_searcher('test')
        def searcher(term):
           ...

        searcher function recives text as term variable, and
        should return iterator to principal objects.
     """
    info = config.DirectiveInfo()

    def wrapper(searcher):
        discr = (AUTH_SEARCHER_ID, name)
        intr = config.Introspectable(
            AUTH_SEARCHER_ID, discr, name, AUTH_SEARCHER_ID)
        intr['name'] = name
        intr['callable'] = searcher

        info.attach(
            config.Action(
                lambda config, name, searcher:
                    config.get_cfg_storage(AUTH_SEARCHER_ID)\
                        .update({name: searcher}),
                (name, searcher), discriminator=discr, introspectables=(intr,))
            )

        return searcher

    return wrapper
