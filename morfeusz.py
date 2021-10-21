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

CONCRAFT_FORBIDDEN = {
    'expand_tags': False,
    'expand_dag': True,
    'expand_dot': False,
    'praet': 'composite',
    'whitespace': morfeusz2.KEEP_WHITESPACES
}

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

    def parse_bool(self, url_param, morfeusz_param, default):
        if not url_param in self.url_params:
            self.morfeusz_opts[morfeusz_param] = default
        else:
            param_value = self.__consume_param(url_param)
            self.morfeusz_opts[morfeusz_param] = bool(strtobool(param_value))

    def parse_string(self, url_param, morfeusz_param, accepted_values, default):
        if not url_param in self.url_params:
            self.morfeusz_opts[morfeusz_param] = default
            return

        param_value = self.__consume_param(url_param)

        if not param_value in accepted_values:
            self.__report_unsupported(url_param, param_value, accepted_values)
            return

        self.morfeusz_opts[morfeusz_param] = param_value

    def parse_enum(self, url_param, morfeusz_param, enum_class, default, bool_option=None):
        if not url_param in self.url_params:
            enum_member = default
        else:
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
        actions = ['analyze', 'generate']

        if not param_value in actions:
            self.issues.append('unsupported action "%s"; available: %s' % (param_value, actions))
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

def tag_items(interp, action):
    item = {}

    if action == 'analyze':
        # analysis
        item['start'] = interp[0]
        item['end'] = interp[1]
        morph_info = interp[2]

        if len(interp) == 6:
            # Concraft enabled
            item['probability'] = float(interp[3])
            item['disamb'] = interp[5] is not None
    elif action == 'generate':
        # generation
        morph_info = interp
    else:
        return item

    item['form'] = morph_info[0].replace('_', ' ')
    item['lemma'] = morph_info[1].replace('_', ' ')
    item['tag'] = morph_info[2]
    item['name'] = morph_info[3]
    item['labels'] = morph_info[4]

    return item

def process_request(params, concraft):
    option_parser = MorfeuszOptionParser(params)
    option_parser.parse_bool('expandDag', 'expand_dag', False)
    option_parser.parse_bool('expandTags', 'expand_tags', False)
    option_parser.parse_bool('expandDot', 'expand_dot', True)
    option_parser.parse_bool('expandUnderscore', 'expand_underscore', True)
    option_parser.parse_string('agglutinationRules', 'aggl', AGGLUTINATION_RULES, 'strict')
    option_parser.parse_string('pastTenseSegmentation', 'praet', PAST_TENSE_SEGMENTATION, 'split')
    option_parser.parse_enum('tokenNumbering', 'separate_numbering', TokenNumbering, TokenNumbering.separate, TokenNumbering.separate)
    option_parser.parse_enum('caseHandling', 'case_handling', CaseHandling, CaseHandling.conditional)
    option_parser.parse_enum('whitespaceHandling', 'whitespace', WhitespaceHandling, WhitespaceHandling.skip)
    option_parser.parse_actions('action')

    results = []
    response = {'results': results}

    if option_parser.validate(response):
        option_parser.set_dictionary_path('MORFEUSZ_DICT_PATH')
        opts = option_parser.get_opts()
        morfeusz = None

        try:
            morfeusz = Morfeusz(**opts)

            if option_parser.action == 'analyze':
                dag = morfeusz.analyse(option_parser.text)

                if concraft is not None and len([k for k in opts if k in CONCRAFT_FORBIDDEN and opts[k] == CONCRAFT_FORBIDDEN[k]]) == 0:
                    dag = concraft.disamb(dag)

                for interp in dag:
                    if isinstance(interp, list):
                        subitem = []
                        results.append(subitem)

                        for item in interp:
                            subitem.append(tag_items(item, option_parser.action))
                    elif isinstance(interp, tuple):
                        results.append(tag_items(interp, option_parser.action))
            elif option_parser.action == 'generate':
                for title in option_parser.titles:
                    subitem = []
                    results.append(subitem)

                    for interp in morfeusz.generate(title):
                        subitem.append(tag_items(interp, option_parser.action))

            response['version'] = morfeusz2.__version__
            response['dictionaryId'] = morfeusz.dict_id()
            response['copyright'] = morfeusz.dict_copyright()
        finally:
            # HACK: memory deallocation seems broken (affects Py3 bindings, not the C++ lib)
            if morfeusz is not None:
                morfeusz2._Morfeusz.__swig_destroy__(morfeusz._morfeusz_obj)

    return response
