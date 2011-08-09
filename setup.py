""" Setup for memphis.config package """
import sys, os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


version='0.7dev'

setup(name='memphis.config',
      version=version,
      description="",
      long_description=(
          'Detailed Documentation\n' +
          '======================\n'
          + '\n\n' +
          read('memphis', 'config', 'README.txt')
          + '\n\n' +
          read('CHANGES.txt')
          ),
      classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Repoze Public License',
        'Programming Language :: Python',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI'],
      author='Nikolay Kim',
      author_email='fafhrd91@gmail.com',
      url='http://pypi.python.org/pypi/memphis.config/',
      license='BSD-derived (http://www.repoze.org/LICENSE.txt)',
      packages = find_packages(),
      namespace_packages = ['memphis'],
      install_requires = [
        'setuptools',
        'Paste',
        'PasteDeploy',
        'PasteScript',
        'ordereddict',
        'colander',
        'martian >= 0.14',
        'zope.component',
        'zope.configuration',
        'zope.event',
        'translationstring',
        ],
      extras_require = dict(
        test=['zope.configuration [test]',
              'zope.processlifetime',]),
      include_package_data = True,
      zip_safe = False,
      entry_points = {
        'memphis': ['grokker = memphis.config.meta',
                    'package = memphis.config'],
        'z3c.autoinclude.plugin':
            ['target = plone'],
        'paste.global_paster_command': [
            'settings = memphis.config.commands:SettingsCommand',
            ],
        },
      )
