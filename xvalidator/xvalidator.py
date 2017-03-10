#!/usr/bin/env python
# coding: utf-8

import argparse
import os
import yaml
import glob2
import logging
import json
import re
import collections

_log = logging.getLogger(__name__)

TYPES = {
  'int': int,
  'bool': bool,
  'list': list,
  'str': str
}

def complete(text, state):
    if str(text).startswith('~/'):
        home = os.path.expanduser('~/')
        p = os.path.join(home, text[2:])
    else:
        p = text
        home = None

    items = glob2.glob(p + '*')
    if items is not None and home is not None:
        items = ['~/' + x[len(home):] for x in items]
    return (items + [None])[state]


def set_readline():
    try:
        import readline
        readline.set_completer_delims(' \t\n;')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(complete)
    except:
        pass


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


color = AttributeDict({
    'PURPLE': '\033[35m',
    'CYAN':  '\033[36m',
    'BLUE':  '\033[34m',
    'GREEN':  '\033[32m',
    'YELLOW':  '\033[33m',
    'RED':  '\033[31m',
    'BOLD':  '\033[1m',
    'UNDERLINE':  '\033[4m',
    'ITALIC':  '\033[3m',
    'END':  '\033[0m',
})


def dict_to_str(d, fmt='%s=%s\n'):
    s = ''
    for x in d:
        s += fmt % (x, d[x])
    return s


def str2bool(v):
    if v is None:
        return False
    return v.lower() in ("yes", "true", "t", "1", "y")


known_types = {
    'int': int,
    'bool': str2bool,
    'str': str,
    'float': float
}


def term_color(text, *text_colors):
    return ''.join(text_colors) + text + color.END


def get_parser(path):
    ext = os.path.splitext(path)[1]
    if ext == '.yaml' or ext == '.yml':
        return yaml
    elif ext == '.json':
        return json
    else:
        exit('Parser format not supported: %s' % ext)


class Field:
    def __init__(self, options):
        self.required = options.get('required', False)
        self.type = TYPES[options.get('type', 'str')]
        self.validation = options.get('validation', None)
        self.item = options.get('item', None)


def validate(src, schema, path, errors):
    result = {}
    for x in schema:
        sa = schema[x]
        sa_path = path+[x]
        sa_path_str = '\\'.join(sa_path)

        src_value = None
        if src is not None and x in src:
            result[x] = True
            src_value = src[x]

            validate_value(errors, sa, sa_path, sa_path_str, src_value)

    if src:
        for x in src:
            src_value = src[x]
            x_path = path+[x]
            x_path_str = '\\'.join(x_path)
            if x not in result:
                found = False
                for e in schema:
                    if re.match(e, x) is not None:
                        found = result[x] = True
                        sa = schema[e]
                        validate_value(errors, sa, x_path, x_path_str, src_value)
                        break

                if not found:
                    errors.append('%s is not defined in this schema' % x_path_str)


def validate_value(errors, sa, sa_path, sa_path_str, src_value):
    if isinstance(sa, collections.Mapping):
        validate(src_value, sa, sa_path, errors)
    else:
        if src_value is None:
            if sa.required:
                errors.append('%s is required' % sa_path_str)
        else:
            if not isinstance(src_value, sa.type):
                errors.append('%s has an invalid type ("%s" expected)' % (sa_path_str, sa.type.__name__))
            elif sa.type == list:
                if sa.required:
                    if len(src_value) == 0:
                        errors.append('%s requires at least 1 list item' % sa_path_str)
                    else:
                        for idx, item in enumerate(src_value):
                            item_path = sa_path + ['[%s]' % idx]
                            item_path_str = '\\'.join(item_path)
                            validate_value(errors, sa.item, item_path, item_path_str, item)
            elif sa.type == str:
                if sa.validation:
                    if re.match(sa.validation, src_value) is None:
                        errors.append('%s failed validation' % sa_path_str)


class YamlLoader(yaml.Loader):

    def __init__(self, stream):
        if stream is not None:
            if isinstance(stream, file):
                self._root = os.path.split(stream.name)[0]
            elif isinstance(stream, dict):
                d = stream
                stream = d['fhd']
                self._root = os.path.splitext(stream.name)[0]
                self._context = d['context']

        super(YamlLoader, self).__init__(stream)

    def field(self, node):
        item = self.construct_mapping(node, 9999)

        return Field(item)

    def yaml_file(self, node):
        filename = os.path.join(self._root, self.construct_scalar(node))
        with open(filename, 'r') as fhd:
            return yaml.load(fhd, Loader=YamlLoader)


YamlLoader.add_constructor('!field', YamlLoader.field)
YamlLoader.add_constructor('!yaml', YamlLoader.yaml_file)


def main():
    try:
        options = {}
        set_readline()

        parser = argparse.ArgumentParser(
            description='Validate json or yaml files.')

        parser.add_argument(
            '-l',
            '--log-level',
            dest='log_level',
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='optional. Set the log level.')

        subparsers = parser.add_subparsers(help='actions')

        parser_a = subparsers.add_parser('validate', help='scaffold a directory')
        parser_a.add_argument('-s', '--schema', required=False, help='Schema used to validate')
        parser_a.add_argument('file', help='File to validate')
        parser_a.set_defaults(func=validate_cli)

        args = parser.parse_args()
        logging.getLogger('requests').setLevel(logging.ERROR)
        logging.basicConfig(level=getattr(logging, args.log_level))

        args.func(args)
    except KeyboardInterrupt:
        exit(0)


def validate_cli(args):

    with open(args.file, 'r') as fhd:
        src = yaml.load(fhd, YamlLoader)
    if args.schema is None:
        test = src
        schema = test['schema']
        tests = test['tests']
    else:
        with open(args.schema, 'r') as fhd:
            schema = yaml.load(fhd, YamlLoader)
        tests = [{'pass':src}]

    for test in tests:
        errors = []
        if 'pass' in test:
            validate(test['pass'], schema, [], errors)

    if errors:
        print '%s failed validation' % args.file
        print ''
        for err in errors:
            print '- %s' % err
    else:
        print '%s is valid' % args.file


if __name__ == '__main__':
    main()
