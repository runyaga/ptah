""" paste commands """
import argparse
import io
import textwrap

from collections import OrderedDict
from pyramid.config import Configurator
from pyramid.compat import configparser

import ptah
from ptah import config
from ptah.settings import SETTINGS_OB_ID
from ptah.settings import SETTINGS_GROUP_ID


grpTitleWrap = textwrap.TextWrapper(
    initial_indent='* ',
    subsequent_indent='  ')

grpDescriptionWrap = textwrap.TextWrapper(
    initial_indent='    ',
    subsequent_indent='    ')

nameWrap = textwrap.TextWrapper(
    initial_indent='  - ',
    subsequent_indent='    ')

nameTitleWrap = textwrap.TextWrapper(
    initial_indent='       ',
    subsequent_indent='       ')

nameDescriptionWrap = textwrap.TextWrapper(
    initial_indent=' * ',
    subsequent_indent='')


def main(init=True):
    if init:  # pragma: no cover
        pconfig = Configurator()
        pconfig.begin()
        pconfig.include('ptah')
        config.initialize(pconfig, autoinclude=True)
        pconfig.commit()
        ptah.initialize_settings(pconfig, None)

    args = SettingsCommand.parser.parse_args()
    cmd = SettingsCommand(args)
    cmd.run()


class SettingsCommand(object):
    """ 'settings' command"""

    parser = argparse.ArgumentParser(description="ptah settings management")
    parser.add_argument('-a', '--all', action="store_true",
                        dest='all',
                        help='List all registered settings')
    parser.add_argument('-l', '--list',
                        dest='section', default='',
                        help='List registered settings')
    parser.add_argument('-p', '--print', action="store_true",
                        dest='printcfg',
                        help='Print default settings in ConfigParser format')

    def __init__(self, args):
        self.options = args

    def run(self):
        # print defaults
        if self.options.printcfg:
            data = config.get_cfg_storage(SETTINGS_OB_ID).export(True)

            parser = configparser.ConfigParser(dict_type=OrderedDict)
            for key, val in sorted(data.items()):
                parser.set(configparser.DEFAULTSECT, key, val)

            fp = io.BytesIO()
            try:
                parser.write(fp)
            finally:
                pass

            print (fp.getvalue())
            return

        if self.options.all:
            section = ''
        else:
            section = self.options.section

        # print description
        groups = sorted(config.get_cfg_storage(SETTINGS_GROUP_ID).items())

        for name, group in groups:
            if section and name != section:
                continue

            print ('')
            title = group.__title__ or name

            print (grpTitleWrap.fill(title.encode('utf-8')))
            if group.__description__:
                print (grpDescriptionWrap.fill(
                    group.__description__.encode('utf-8')))

            print ('')
            for node in group.__fields__.values():
                default = '<required>' if node.required else node.default
                print (nameWrap.fill(
                    ('%s.%s: %s (%s: %s)' % (
                        name, node.name, node.title,
                        node.__class__.__name__, default)).encode('utf-8')))

                print (nameTitleWrap.fill(node.description.encode('utf-8')))
                print ('')
