import morfeusz2
from morfeusz2 import Morfeusz
from enum import Enum
from distutils.util import strtobool

class TokenNumbering(Enum):
    separate = morfeusz2.SEPARATE_NUMBERING
    continuous = morfeusz2.CONTINUOUS_NUMBERING

class CaseHandling(Enum):
    conditional = morfeusz2.CONDITIONALLY_CASE_SENSITIVE
    strict = morfeusz2.STRICTLY_CASE_SENSITIVE
    ignore = morfeusz2.IGNORE_CASE

class WhitespaceHandling(Enum):
    skip = morfeusz2.SKIP_WHITESPACES
    append = morfeusz2.APPEND_WHITESPACES
    keep = morfeusz2.KEEP_WHITESPACES

AGGLUTINATION_RULES = ['strict', 'isolated', 'permissive']
PAST_TENSE_SEGMENTATION = ['split', 'composite']

class MorfeuszOptionParser:
    def __init__(self, url_params):
        self.url_params = dict(url_params)
        self.morfeusz_opts = {}
        self.issues = []

    def get_opts(self):
        return self.morfeusz_opts

    def __consume_param(self, param):
        value = self.url_params[param]
        del self.url_params[param]
        return value

    def __report_unsupported(self, param, value, accepted):
        self.issues.append('unsupported value "%s" for parameter "%s"; available: %s' % \
            (value, param, ', '.join(['"%s"' % s for s in accepted])))

    def set_dictionary_path(self, env_var):
        import os
        self.morfeusz_opts['dict_path'] = os.environ.get(env_var)

    def parse_bool(self, url_param, morfeusz_param):
        if not url_param in self.url_params:
            return

        param_value = self.__consume_param(url_param)
        self.morfeusz_opts[morfeusz_param] = bool(strtobool(param_value))

    def parse_string(self, url_param, morfeusz_param, accepted_values):
        if not url_param in self.url_params:
            return

        param_value = self.__consume_param(url_param)

        if not param_value in accepted_values:
            self.__report_unsupported(url_param, param_value, accepted_values)
            return

        self.morfeusz_opts[morfeusz_param] = param_value

    def parse_enum(self, url_param, morfeusz_param, enum_class, bool_option=None):
        if not url_param in self.url_params:
            return

        param_value = self.__consume_param(url_param)

        if not param_value in enum_class.__members__:
            accepted_values = ['%s' % e.name for e in enum_class]
            self.__report_unsupported(url_param, param_value, accepted_values)
            return

        enum_member = enum_class[param_value]
        value = enum_member.value if bool_option is None else (enum_member is bool_option)
        self.morfeusz_opts[morfeusz_param] = value

    def parse_actions(self, url_param):
        if not url_param in self.url_params:
            self.issues.append('missing mandatory "%s" parameter' % url_param)
            return

        param_value = self.__consume_param(url_param)

        if not param_value in ['analyze', 'generate']:
            self.issues.append('unsupported action "%s"; available: %s')
            return

        self.action = param_value
        self.morfeusz_opts['analyse'] = param_value == 'analyze'
        self.morfeusz_opts['generate'] = param_value == 'generate'

        if param_value == 'analyze':
            if not 'text' in self.url_params:
                self.issues.append('missing mandatory "text" parameter')
            else:
                self.text = self.__consume_param('text')
        elif param_value == 'generate':
            if not 'titles' in self.url_params:
                self.issues.append('missing mandatory "titles" parameter')
            else:
                self.titles = self.__consume_param('titles').split('|')

    def validate(self, record):
        success = True

        if self.issues:
            record['errors'] = self.issues
            success = False

        if self.url_params:
            record['warnings'] = ['unknown parameter "%s=%s"' % (k, v) for k, v in self.url_params.items()]

        return success

def tag_items(interp_list):
    item = {}

    if len(interp_list) == 3:
        morph_info = interp_list[2]
        item['start'] = interp_list[0]
        item['end'] = interp_list[1]
    else:
        morph_info = interp_list

    item['form'] = morph_info[0]
    item['lemma'] = morph_info[1]
    item['tag'] = morph_info[2]
    item['name'] = morph_info[3]
    item['labels'] = morph_info[4]

    return item

def process_request(params):
    option_parser = MorfeuszOptionParser(params)
    option_parser.parse_bool('expandDag', 'expand_dag')
    option_parser.parse_bool('expandTags', 'expand_tags')
    option_parser.parse_bool('expandDot', 'expand_dot')
    option_parser.parse_bool('expandUnderscore', 'expand_underscore')
    option_parser.parse_string('agglutinationRules', 'aggl', AGGLUTINATION_RULES)
    option_parser.parse_string('pastTenseSegmentation', 'praet', PAST_TENSE_SEGMENTATION)
    option_parser.parse_enum('tokenNumbering', 'separate_numbering', TokenNumbering, TokenNumbering.separate)
    option_parser.parse_enum('caseHandling', 'case_handling', CaseHandling)
    option_parser.parse_enum('whitespaceHandling', 'whitespace', WhitespaceHandling)
    option_parser.parse_actions('action')

    results = []
    response = {'results': results}

    if option_parser.validate(response):
        option_parser.set_dictionary_path('MORFEUSZ_DICT_PATH')
        morfeusz = Morfeusz(**option_parser.get_opts())

        if option_parser.action == 'analyze':
            for interp_list in morfeusz.analyse(option_parser.text):
                if isinstance(interp_list, list):
                    subitem = []
                    results.append(subitem)

                    for item in interp_list:
                        subitem.append(tag_items(item))
                else:
                    results.append(tag_items(interp_list))
        elif option_parser.action == 'generate':
            for title in option_parser.titles:
                subitem = []
                results.append(subitem)

                for interp_list in morfeusz.generate(title):
                    subitem.append(tag_items(interp_list))

        response['version'] = morfeusz2.__version__
        response['dictionaryId'] = morfeusz.dict_id()

    return response
