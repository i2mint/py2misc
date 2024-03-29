"""
This module is about generating, validating, and operating on (parametrized) fields (i.e. stings, e.g. paths).
"""

import re
import os
from functools import partial, wraps
from types import MethodType

from py2store.signatures import set_signature_of_func
from py2store.errors import KeyValidationError, _assert_condition

import string

str_formatter = string.Formatter()


def mk_str_making_func(str_format: str, input_trans=None, method=False, module=None, name=None):
    fields = tuple(x[1] for x in str_formatter.parse(str_format))
    n_fields = len(fields)

    if method:
        def _mk(self, *args, **kwargs):
            n = len(args) + len(kwargs)
            if n > n_fields:
                raise ValueError(f"You have too many arguments: (args, kwargs) is ({args}, {kwargs})")
            elif n < n_fields:
                raise ValueError(f"You have too few arguments: (args, kwargs) is ({args}, {kwargs})")
            kwargs = dict({k: v for k, v in zip(fields, args)}, **kwargs)
            if input_trans is not None:
                kwargs = input_trans(**kwargs)
            return str_format.format(**kwargs)

        set_signature_of_func(_mk, ['self'] + list(fields))
    else:

        def _mk(*args, **kwargs):
            n = len(args) + len(kwargs)
            if n > n_fields:
                raise ValueError(f"You have too many arguments: (args, kwargs) is ({args}, {kwargs})")
            elif n < n_fields:
                raise ValueError(f"You have too few arguments: (args, kwargs) is ({args}, {kwargs})")
            kwargs = dict({k: v for k, v in zip(fields, args)}, **kwargs)
            if input_trans is not None:
                kwargs = input_trans(**kwargs)
            return str_format.format(**kwargs)

        set_signature_of_func(_mk, fields)

    if module is not None:
        _mk.__module__ = module

    if name is not None:
        _mk.__qualname__ = name

    return _mk


#
# assert_condition = partial(_assert_condition, err_cls=KeyValidationError)
#
# path_sep = os.path.sep
#
# base_validation_funs = {
#     "be a": isinstance,
#     "be in": lambda val, check_val: val in check_val,
#     "be at least": lambda val, check_val: val >= check_val,
#     "be more than": lambda val, check_val: val > check_val,
#     "be no more than": lambda val, check_val: val <= check_val,
#     "be less than": lambda val, check_val: val < check_val,
# }
#
# dflt_validation_funs = base_validation_funs
# dflt_all_kwargs_should_be_in_validation_dict = False
# dflt_ignore_misunderstood_validation_instructions = False
#
# dflt_arg_pattern = r'.+'
#
# day_format = "%Y-%m-%d"
# day_format_pattern = re.compile('\d{4}-\d{2}-\d{2}')
#
# capture_template = '({format})'
# named_capture_template = '(?P<{name}>{format})'
#
fields_re = re.compile('(?<={)[^}]+(?=})')
#
#
# def validate_kwargs(kwargs_to_validate,
#                     validation_dict,
#                     validation_funs=None,
#                     all_kwargs_should_be_in_validation_dict=False,
#                     ignore_misunderstood_validation_instructions=False
#                     ):
#     """
#     Utility to validate a dict. It's main use is to validate function arguments (expressing the validation checks
#     in validation_dict) by doing validate_kwargs(locals()), usually in the beginning of the function
#     (to avoid having more accumulated variables than we need in locals())
#     :param kwargs_to_validate: as the name implies...
#     :param validation_dict: A dict specifying what to validate. Keys are usually name of variables (when feeding
#         locals()) and values are dicts, themselves specifying check:check_val pairs where check is a string that
#         points to a function (see validation_funs argument) and check_val is an object that the kwargs_to_validate
#         value will be checked against.
#     :param validation_funs: A dict of check:check_function(val, check_val) where check_function is a function returning
#         True if val is valid (with respect to check_val).
#     :param all_kwargs_should_be_in_validation_dict: If True, will raise an error if kwargs_to_validate contains
#         keys that are not in validation_dict.
#     :param ignore_misunderstood_validation_instructions: If True, will raise an error if validation_dict contains
#         a key that is not in validation_funs (safer, since if you mistype a key in validation_dict, the function will
#         tell you so!
#     :return: True if all the validations passed.
#
#     >>> validation_dict = {
#     ...     'system': {
#     ...         'be in': {'darwin', 'linux'}
#     ...     },
#     ...     'fv_version': {
#     ...         'be a': int,
#     ...         'be at least': 5
#     ...     }
#     ... }
#     >>> validate_kwargs({'system': 'darwin'}, validation_dict)
#     True
#     >>> try:
#     ...     validate_kwargs({'system': 'windows'}, validation_dict)
#     ... except AssertionError as e:
#     ...     assert str(e).startswith('system must be in')  # omitting the set because inconsistent order
#     >>> try:
#     ...     validate_kwargs({'fv_version': 9.9}, validation_dict)
#     ... except AssertionError as e:
#     ...     print(e)
#     fv_version must be a <class 'int'>
#     >>> try:
#     ...     validate_kwargs({'fv_version': 4}, validation_dict)
#     ... except AssertionError as e:
#     ...     print(e)
#     fv_version must be at least 5
#     >>> validate_kwargs({'fv_version': 6}, validation_dict)
#     True
#     """
#     validation_funs = dict(base_validation_funs or {}, **(validation_funs or {}))
#     for var, val in kwargs_to_validate.items():  # for every (var, val) pair of kwargs
#         if var in validation_dict:  # if var is in the validation_dict
#             for check, check_val in validation_dict[var].items():  # for every (key, val) of this dict
#                 if check in base_validation_funs:  # if you have a validation check for it
#                     if not validation_funs[check](val, check_val):  # check it's valid
#                         raise AssertionError("{} must {} {}".format(var, check, check_val))  # and raise an error if not
#                 elif not ignore_misunderstood_validation_instructions:  # should ignore if check not understood?
#                     raise AssertionError("I don't know what to do with the validation check '{}'".format(
#                         check
#                     ))
#         elif all_kwargs_should_be_in_validation_dict:  # should all variables have checks?
#             raise AssertionError("{} wasn't in the validation_dict")
#     return True
#
#
# empty_field_p = re.compile('{}')
#
#
# def get_fields_from_template(template):
#     """
#     Get list from {item} items of template string
#     :param template: a "template" string (a string with {item} items
#     -- the kind that is used to mark token for str.format)
#     :return: a list of the token items of the string, in the order they appear
#     >>> get_fields_from_template('this{is}an{example}of{a}template')
#     ['is', 'example', 'a']
#     """
#     # TODO: Need to use the string module, and need to auto-name the fields instead of refusing unnamed
#     assert not empty_field_p.search(template), "All fields must be named: That is, no empty {} allowed"
#     return fields_re.findall(template)
# #
#
# # until_slash = "[^" + path_sep + "]+"
# # until_slash_capture = '(' + until_slash + ')'
#
# def mk_format_mapping_dict(format_dict, required_keys, sep=path_sep):
#     until_sep = "[^" + re.escape(sep) + "]+"
#     new_format_dict = format_dict.copy()
#     for k in required_keys:
#         if k not in new_format_dict:
#             new_format_dict[k] = until_sep
#     return new_format_dict
#
#
# def mk_capture_patterns(mapping_dict):
#     new_mapping_dict = dict()
#     for k, v in mapping_dict.items():
#         new_v = capture_template.format(format=v)
#         new_mapping_dict[k] = new_v
#     return new_mapping_dict
#
#
# def mk_named_capture_patterns(mapping_dict):
#     new_mapping_dict = dict()
#     for k, v in mapping_dict.items():
#         new_v = named_capture_template.format(name=k, format=v)
#         new_mapping_dict[k] = new_v
#     return new_mapping_dict
#
#
# def template_to_pattern(mapping_dict, template):
#     if mapping_dict:
#         p = re.compile("{}".format("|".join(['{' + re.escape(x) + '}' for x in list(mapping_dict.keys())])))
#         return p.sub(lambda x: mapping_dict[x.string[(x.start() + 1):(x.end() - 1)]], template)
#     else:
#         return template
#
#
# def mk_extract_pattern(template, format_dict=None, named_capture_patterns=None, name=None):
#     format_dict = format_dict or {}
#     named_capture_patterns = named_capture_patterns or mk_named_capture_patterns(format_dict)
#     assert name is not None
#     mapping_dict = dict(format_dict, **{name: named_capture_patterns[name]})
#     p = re.compile("{}".format("|".join(
#         ['{' + re.escape(x) + '}' for x in list(mapping_dict.keys())])))
#
#     return re.compile(p.sub(lambda x: mapping_dict[x.string[(x.start() + 1):(x.end() - 1)]], template))
#
#
# def mk_pattern_from_template_and_format_dict(template, format_dict=None):
#     """Make a compiled regex to match template
#
#     Args:
#         template: A format string
#         format_dict: A dict whose keys are template fields and values are regex strings to capture them
#
#     Returns: a compiled regex
#
#     >>> mk_pattern_from_template_and_format_dict('{here}/and/{there}')
#     re.compile('(?P<here>[^/]+)/and/(?P<there>[^/]+)')
#     >>> p = mk_pattern_from_template_and_format_dict('{here}/and/{there}', {'there': '\d+'})
#     >>> p
#     re.compile('(?P<here>[^/]+)/and/(?P<there>\\\d+)')
#     >>> type(p)
#     <class 're.Pattern'>
#     >>> p.match('HERE/and/1234').groupdict()
#     {'here': 'HERE', 'there': '1234'}
#     """
#     format_dict = format_dict or {}
#
#     fields = get_fields_from_template(template)
#     format_dict = mk_format_mapping_dict(format_dict, fields)
#     named_capture_patterns = mk_named_capture_patterns(format_dict)
#     return re.compile(template_to_pattern(named_capture_patterns, template))
#
#
# def mk_prefix_templates_dicts(template):
#     fields = get_fields_from_template(template)
#     prefix_template_dict_including_name = dict()
#     none_and_fields = [None] + fields
#     for name in none_and_fields:
#         if name == fields[-1]:
#             prefix_template_dict_including_name[name] = template
#         else:
#             if name is None:
#                 next_name = fields[0]
#             else:
#                 next_name = fields[1 + next(i for i, _name in enumerate(fields) if _name == name)]
#             p = '{' + next_name + '}'
#             template_idx_of_next_name = re.search(p, template).start()
#             prefix_template_dict_including_name[name] = template[:template_idx_of_next_name]
#
#     prefix_template_dict_excluding_name = dict()
#     for i, name in enumerate(fields):
#         prefix_template_dict_excluding_name[name] = prefix_template_dict_including_name[none_and_fields[i]]
#     prefix_template_dict_excluding_name[None] = template
#
#     return prefix_template_dict_including_name, prefix_template_dict_excluding_name
#
#
# def mk_kwargs_trans(**trans_func_for_key):
#     """ Make a dict transformer from functions that depends solely on keys (of the dict to be transformed)
#     Used to easily make process_kwargs and process_info_dict arguments for LinearNaming.
#     """
#     assert all(map(callable, trans_func_for_key.values())), "all argument values must be callable"
#
#     def key_based_val_trans(**kwargs):
#         for k, v in kwargs.items():
#             if k in trans_func_for_key:
#                 kwargs[k] = trans_func_for_key[k](v)
#         return kwargs
#
#     return key_based_val_trans
#
#
# def _mk(self, *args, **kwargs):
#     """
#     Make a full name with given kwargs. All required name=val must be present (or infered by self.process_kwargs
#     function.
#     The required fields are in self.fields.
#     Does NOT check for validity of the vals.
#     :param kwargs: The name=val arguments needed to construct a valid name
#     :return: an name
#     """
#     n = len(args) + len(kwargs)
#     if n > self.n_fields:
#         raise ValueError(f"You have too many arguments: (args, kwargs) is ({args},{kwargs})")
#     elif n < self.n_fields:
#         raise ValueError(f"You have too few arguments: (args, kwargs) is ({args},{kwargs})")
#     kwargs = dict({k: v for k, v in zip(self.fields, args)}, **kwargs)
#     if self.process_kwargs is not None:
#         kwargs = self.process_kwargs(**kwargs)
#     return self.template.format(**kwargs)
#
#
# class StrTupleDict(object):
#
#     def __init__(self, template: (str, tuple, list), format_dict=None,
#                  process_kwargs=None, process_info_dict=None,
#                  named_tuple_type_name='NamedTuple',
#                  sep: str = path_sep):
#         """Converting from and to strings, tuples, and dicts.
#
#         Args:
#             template: The string format template
#             format_dict: A {field_name: field_value_format_regex, ...} dict
#             process_kwargs: A function taking the field=value pairs and producing a dict of processed
#                 {field: value,...} dict (where both fields and values could have been processed.
#                 This is useful when we need to process (format, default, etc.) fields, or their values,
#                 according to the other fields of values in the collection.
#                 A specification of {field: function_to_process_this_value,...} wouldn't allow the full powers
#                 we are allowing here.
#             process_info_dict: A sort of converse of format_dict.
#                 This is a {field_name: field_conversion_func, ...} dict that is used to convert info_dict values
#                 before returning them.
#             name_separator: Used
#
#         >>> ln = StrTupleDict('/home/{user}/fav/{num}.txt',
#         ...	                  format_dict={'user': '[^/]+', 'num': '\d+'},
#         ...	                  process_info_dict={'num': int},
#         ...                   sep='/'
#         ...	                 )
#         >>> ln.is_valid('/home/USER/fav/123.txt')
#         True
#         >>> ln.is_valid('/home/US/ER/fav/123.txt')
#         False
#         >>> ln.is_valid('/home/US/ER/fav/not_a_number.txt')
#         False
#         >>> ln.mk('USER', num=123)  # making a string (with args or kwargs)
#         '/home/USER/fav/123.txt'
#         >>> # Note: but ln.mk('USER', num='not_a_number') would fail because num is not valid
#         >>> ln.info_dict('/home/USER/fav/123.txt')  # note in the output, 123 is an int, not a string
#         {'user': 'USER', 'num': 123}
#         >>>
#         >>> # Trying with template given as a tuple, and with different separator
#         >>> ln = StrTupleDict(template=('first', 'last', 'age'),
#         ...                   format_dict={'age': '-*\d+'},
#         ...                   process_info_dict={'age': int},
#         ...                   sep=',')
#         >>> ln.tuple_to_str(('Thor', "Odinson", 1500))
#         'Thor,Odinson,1500'
#         >>> ln.str_to_dict('Loki,Laufeyson,1070')
#         {'first': 'Loki', 'last': 'Laufeyson', 'age': 1070}
#         >>> ln.str_to_tuple('Odin,Himself,-1')
#         ('Odin', 'Himself', -1)
#         >>> ln.tuple_to_dict(('Odin', 'Himself', -1))
#         {'first': 'Odin', 'last': 'Himself', 'age': -1}
#         >>> ln.dict_to_tuple({'first': 'Odin', 'last': 'Himself', 'age': -1})
#         ('Odin', 'Himself', -1)
#         """
#         if format_dict is None:
#             format_dict = {}
#
#         self.sep = sep
#
#         if isinstance(template, str):
#             self.template = template
#         else:
#             self.template = self.sep.join([f"{{{x}}}" for x in template])
#
#         fields = get_fields_from_template(self.template)
#
#         format_dict = mk_format_mapping_dict(format_dict, fields)
#
#         named_capture_patterns = mk_named_capture_patterns(format_dict)
#
#         pattern = template_to_pattern(named_capture_patterns, self.template)
#         pattern += '$'
#         pattern = re.compile(pattern)
#
#         extract_pattern = {}
#         for name in fields:
#             extract_pattern[name] = mk_extract_pattern(self.template, format_dict, named_capture_patterns, name)
#
#         if isinstance(process_info_dict, dict):
#             _processor_for_kw = process_info_dict
#
#             def process_info_dict(**info_dict):
#                 return {k: _processor_for_kw.get(k, lambda x: x)(v) for k, v in info_dict.items()}
#
#         self.fields = fields
#         self.n_fields = len(fields)
#         self.format_dict = format_dict
#         self.named_capture_patterns = named_capture_patterns
#         self.pattern = pattern
#         self.extract_pattern = extract_pattern
#         self.process_kwargs = process_kwargs
#         self.process_info_dict = process_info_dict
#
#         def _mk(self, *args, **kwargs):
#             """
#             Make a full name with given kwargs. All required name=val must be present (or infered by self.process_kwargs
#             function.
#             The required fields are in self.fields.
#             Does NOT check for validity of the vals.
#             :param kwargs: The name=val arguments needed to construct a valid name
#             :return: an name
#             """
#             n = len(args) + len(kwargs)
#             if n > self.n_fields:
#                 raise ValueError(f"You have too many arguments: (args, kwargs) is ({args},{kwargs})")
#             elif n < self.n_fields:
#                 raise ValueError(f"You have too few arguments: (args, kwargs) is ({args},{kwargs})")
#             kwargs = dict({k: v for k, v in zip(self.fields, args)}, **kwargs)
#             if self.process_kwargs is not None:
#                 kwargs = self.process_kwargs(**kwargs)
#             return self.template.format(**kwargs)
#
#         set_signature_of_func(_mk, ['self'] + self.fields)
#         self.mk = MethodType(_mk, self)
#         self.NamedTuple = namedtuple(named_tuple_type_name, self.fields)
#
#     def is_valid(self, s: str):
#         """Check if the name has the "upload format" (i.e. the kind of fields that are _ids of fv_mgc, and what
#         name means in most of the iatis system.
#         :param s: the string to check
#         :return: True iff name has the upload format
#         """
#         return bool(self.pattern.match(s))
#
#     def str_to_dict(self, s: str):
#         """
#         Get a dict with the arguments of an name (for example group, user, subuser, etc.)
#         :param s:
#         :return: a dict holding the argument fields and values
#         """
#         m = self.pattern.match(s)
#         if m:
#             info_dict = m.groupdict()
#             if self.process_info_dict:
#                 return self.process_info_dict(**info_dict)
#             else:
#                 return info_dict
#         else:
#             raise ValueError(f"Invalid string format: {s}")
#
#     def str_to_tuple(self, s: str):
#         info_dict = self.str_to_dict(s)
#         return tuple(info_dict[x] for x in self.fields)
#
#     def str_to_namedtuple(self, s: str):
#         return self.dict_to_namedtuple(self.str_to_dict(s))
#
#     def super_dict_to_str(self, d: dict):
#         """Like dict_to_str, but the input dict can have extra keys that are not used by dict_to_str"""
#         return self.mk(**{k: v for k, v in d.items() if k in self.fields})
#
#     def dict_to_str(self, d: dict):
#         return self.mk(**d)
#
#     def dict_to_tuple(self, d):
#         assert_condition(len(self.fields) == len(d), f"len(d)={len(d)} but len(fields)={len(self.fields)}")
#         return tuple(d[f] for f in self.fields)
#
#     def dict_to_namedtuple(self, d):
#         return self.NamedTuple(**d)
#
#     def tuple_to_dict(self, t):
#         assert_condition(len(self.fields) == len(t), f"len(d)={len(t)} but len(fields)={len(self.fields)}")
#         return {f: x for f, x in zip(self.fields, t)}
#
#     def tuple_to_str(self, t):
#         return self.mk(*t)
#
#     def namedtuple_to_tuple(self, nt):
#         return tuple(nt)
#
#     def namedtuple_to_dict(self, nt):
#         return {k: getattr(nt, k) for k in self.fields}
#
#     def namedtuple_to_str(self, nt):
#         return self.dict_to_str(self.namedtuple_to_dict(nt))
#
#     def extract(self, field, s):
#         """Extract a single item from an name
#         :param field: field of the item to extract
#         :param s: the string from which to extract it
#         :return: the value for name
#         """
#         return self.extract_pattern[field].match(s).group(1)
#
#     info_dict = str_to_dict  # alias
#     info_tuple = str_to_tuple  # alias
#
#     def replace_name_elements(self, s: str, **elements_kwargs):
#         """Replace specific name argument values with others
#         :param s: the string to replace
#         :param elements_kwargs: the arguments to replace (and their values)
#         :return: a new name
#         """
#         name_info_dict = self.info_dict(s)
#         for k, v in elements_kwargs.items():
#             name_info_dict[k] = v
#         return self.mk(**name_info_dict)
#
#     def _info_str(self):
#         kv = self.__dict__.copy()
#         exclude = ['process_kwargs', 'extract_pattern', 'prefix_pattern',
#                    'prefix_template_including_name', 'prefix_template_excluding_name']
#         for f in exclude:
#             kv.pop(f)
#         s = ""
#         s += "  * {}: {}\n".format('template', kv.pop('template'))
#         s += "  * {}: {}\n".format('template', kv.pop('sep'))
#         s += "  * {}: {}\n".format('format_dict', kv.pop('format_dict'))
#
#         for k, v in kv.items():
#             if hasattr(v, 'pattern'):
#                 v = v.pattern
#             s += "  * {}: {}\n".format(k, v)
#
#         return s
#
#     def _print_info_str(self):
#         print(self._info_str())
