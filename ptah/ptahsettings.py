""" ptah settings """
import pytz
import logging
import sqlahelper
import sqlalchemy
import translationstring
from email.utils import formataddr

from pyramid.compat import bytes_
from pyramid.events import ApplicationCreated

import ptah
from ptah import manage, settings

_ = translationstring.TranslationStringFactory('ptah')

log = logging.getLogger('ptah')


ptah.register_settings(
    ptah.CFG_ID_PTAH,

    ptah.form.BoolField(
        'auth',
        title = _('Authentication policy'),
        description = _('Enable authentication policy.'),
        default = False),

    ptah.form.TextField(
        'secret',
        title = _('Authentication policy secret'),
        description = _('The secret (a string) used for auth_tkt '
                        'cookie signing'),
        default = ''),

    ptah.form.IntegerField(
        'settings_dbpoll',
        title = _('Settings db poll interval (seconds).'),
        description = _('If you allow to change setting ttw. '
                        '"0" means do not poll'),
        default = 0),

    ptah.form.TextField(
        'manage',
        title = 'Ptah manage id',
        default = 'ptah-manage'),

    ptah.form.LinesField(
        'managers',
        title = 'Manage login',
        description = 'List of user logins with access rights to '\
                            'ptah management ui.',
        default = ()),

    ptah.form.TextField(
        'manager_role',
        title = 'Manager role',
        description = 'Specific role with access rights to ptah management ui.',
        default = ''),

    ptah.form.LinesField(
        'disable_modules',
        title = 'Hide Modules in Management UI',
        description = 'List of modules names to hide in manage ui',
        default = ()),

    ptah.form.LinesField(
        'disable_models',
        title = 'Hide Models in Model Management UI',
        description = 'List of models to hide in model manage ui',
        default = ()),

    ptah.form.TextField(
        'email_from_name',
        default = 'Site administrator'),

    ptah.form.TextField(
        'email_from_address',
        validator = ptah.form.Email(),
        required = False,
        default = 'admin@localhost'),

    title = _('Ptah settings'),
)

ptah.register_settings(
    ptah.CFG_ID_SQLA,

    ptah.form.TextField(
        'url',
        default = '',
        title = 'Engine URL',
        description = 'SQLAlchemy database engine URL'),

    ptah.form.BoolField(
        'cache',
        default = True,
        title = 'Cache',
        description = 'Eanble SQLAlchemy statement caching'),

    title = 'SQLAlchemy settings',
    description = 'Configuration settings for a SQLAlchemy database engine.'
    )


ptah.register_settings(
    ptah.CFG_ID_FORMAT,

    ptah.form.TimezoneField(
        'timezone',
        default = pytz.timezone('US/Central'),
        title = _('Timezone'),
        description = _('Site wide timezone.')),

    ptah.form.TextField(
        'date_short',
        default = '%m/%d/%y',
        title = _('Date'),
        description = _('Date short format')),

    ptah.form.TextField(
        'date_medium',
        default = '%b %d, %Y',
        title = _('Date'),
        description = _('Date medium format')),

    ptah.form.TextField(
        'date_long',
        default = '%B %d, %Y',
        title = _('Date'),
        description = _('Date long format')),

    ptah.form.TextField(
        'date_full',
        default = '%A, %B %d, %Y',
        title = _('Date'),
        description = _('Date full format')),

    ptah.form.TextField(
        'time_short',
        default = '%I:%M %p',
        title = _('Time'),
        description = _('Time short format')),

    ptah.form.TextField(
        'time_medium',
        default = '%I:%M %p',
        title = _('Time'),
        description = _('Time medium format')),

    ptah.form.TextField(
        'time_long',
        default = '%I:%M %p %z',
        title = _('Time'),
        description = _('Time long format')),

    ptah.form.TextField(
        'time_full',
        default = '%I:%M:%S %p %Z',
        title = _('Time'),
        description = _('Time full format')),

    ttw = True,
    title = 'Site formats',
    )


ptah.register_settings(
    ptah.CFG_ID_PASSWORD,

    ptah.form.ChoiceField(
        'manager',
        title = 'Password manager',
        description = 'Available password managers '\
            '("plain", "ssha", "bcrypt")',
        vocabulary = ptah.form.SimpleVocabulary.from_values(
            "plain", "ssha",),
        default = 'plain'),

    ptah.form.IntegerField(
        'min_length',
        title = 'Length',
        description = 'Password minimium length.',
        default = 5),

    ptah.form.BoolField(
        'letters_digits',
        title = 'Letters and digits',
        description = 'Use letters and digits in password.',
        default = False),

    ptah.form.BoolField(
        'letters_mixed_case',
        title = 'Letters mixed case',
        description = 'Use letters in mixed case.',
        default = False),

    ttw = True,
    title = 'Password tool settings',
    )


def set_mailer(config, mailer):
    PTAH = ptah.get_settings(ptah.CFG_ID_PTAH, config.registry)
    PTAH['Mailer'] = mailer


class DummyMailer(object):

    def send(self, from_, to_, message):
        log.warning("Mailer is not configured.")


@ptah.subscriber(ptah.events.SettingsInitializing)
def initialized(ev):
    PTAH = ptah.get_settings(ptah.CFG_ID_PTAH, ev.registry)

    # mail
    PTAH['Mailer'] = DummyMailer()
    PTAH['full_email_address'] = formataddr(
        (PTAH['email_from_name'], PTAH['email_from_address']))

    # sqla
    SQLA = ptah.get_settings(ptah.CFG_ID_SQLA, ev.registry)
    url = SQLA['url']
    if url:
        engine_args = {}
        if SQLA['cache']:
            cache = {}
            engine_args['execution_options'] = \
                {'compiled_cache': cache}
            SQLA['sqlalchemy_cache'] = cache
        try:
            engine = sqlahelper.get_engine()
        except: # pragma: no cover
            engine = sqlalchemy.engine_from_config(
                {'sqlalchemy.url': url}, 'sqlalchemy.', **engine_args)
            sqlahelper.add_engine(engine)

    # ptah manage
    if PTAH['manage']:
        ev.config.add_route(
            'ptah-manage', '/ptah-manage/*traverse',
            factory=ptah.manage.PtahManageRoute, use_global_views=True)
        ptah.manage.set_access_manager(
            ptah.manage.PtahAccessManager())


@ptah.subscriber(ApplicationCreated)
def starting(ev):
    # load db settings
    s_ob = ptah.config.get_cfg_storage(
        settings.SETTINGS_OB_ID, default_factory=settings.Settings)
    s_ob.load_fromdb()
