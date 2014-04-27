#!/usr/bin/env python
import logging
import os
from os import path
import re
import sys

logger = logging.getLogger('ycm-extra-conf')

CONF_FILE_NAME = '.project-deps'
DEPS_EVALUATOR_SEPARATOR = 20 * '=*-.'
ECHO_DEPS_EVALUATOR_SEPARATOR = 'echo "%s"' % DEPS_EVALUATOR_SEPARATOR
LOCAL_PREFIX = 'LOCAL_'
EXPORT_PREFIX = 'EXPORT_'


def EvaluateProjectDeps(path, var_list):
    cmds = ['source %s' % path]
    for v in var_list:
        cmds.append(ECHO_DEPS_EVALUATOR_SEPARATOR)
        cmds.append('echo $%s' % v)
    cmds.append(ECHO_DEPS_EVALUATOR_SEPARATOR)
    result = []
    with os.popen('; '.join(cmds)) as out:
        n = 0
        for line in out.readlines():
            line = line.strip()
            if line == DEPS_EVALUATOR_SEPARATOR:
                if n > 0:
                    current_value = current_value.strip()
                    logger.info('%s = %s', var_list[n - 1], current_value)
                    result.append(current_value)
                n += 1
                if n > len(var_list):
                    break
                current_value = ''
            elif n > 0:
                current_value += line
    return dict(zip(var_list, result))


def ParsePathListStr(list_str):
    result = [part.strip() for part in list_str.split(':')]
    result = [part for part in result if part]
    return result


def UnionAll(list_of_list):
    return reduce(lambda x, y: x + y, list_of_list, [])


class BasicLanguageDesc(object):

    SYS_INCLUDE_START_RE = re.compile(r'^#include\ <.*>\ search starts here:')
    SYS_INCLUDE_RE = re.compile(r'^\s*(([^\\ \(\n]|\\.)*)')
    SYS_INCLUDE_END_RE = re.compile(r'^End of')

    def __init__(self, base_flags, compiler_varname, default_compiler,
            sys_include_varname, include_varname, flag_varname):
        self.base_flags = base_flags
        self.compiler_varname = compiler_varname
        self.default_compiler = default_compiler
        self.sys_include_varname = sys_include_varname
        self.include_varname = include_varname
        self.flag_varname = flag_varname
        self._all_sysinclude_varname = self._AllVarNames(sys_include_varname)
        self._all_include_varname = self._AllVarNames(include_varname)
        self._all_flag_varname = self._AllVarNames(flag_varname)

    @staticmethod
    def _AllVarNames(name):
        return [name, LOCAL_PREFIX + name, EXPORT_PREFIX + name]

    def SysIncludes(self, cc):
        args = self.base_flags + ['-E', '-v', '-c', '/dev/null',
                                  '-o', '/dev/null', '2>&1']
        cmd = cc + ' ' + ' '.join(args)
        logger.info('Command to export system include path: %s', cmd)
        result = []
        with os.popen(cmd) as f:
            started_sysinc = False
            for line in f.readlines():
                if started_sysinc:
                    if self.SYS_INCLUDE_END_RE.match(line):
                        break
                    m = self.SYS_INCLUDE_RE.match(line)
                    if m:
                        result.append(m.group(1))
                elif self.SYS_INCLUDE_START_RE.match(line):
                    started_sysinc = True

        logger.info('System include path exported by compiler is %s', result)

        return result

    def Flags(self, unused_filename, deps_config):
        if deps_config:
            vals = EvaluateProjectDeps(deps_config,
                    [self.compiler_varname] + self._all_sysinclude_varname +
                    self._all_include_varname + self._all_flag_varname)

            compiler = vals[self.compiler_varname].strip() or self.default_compiler
            sys_inc = UnionAll(ParsePathListStr(vals[var]) for var
                    in self._all_sysinclude_varname)
            inc = UnionAll(ParsePathListStr(vals[var]) for var
                    in self._all_include_varname)
            flags = UnionAll(ParsePathListStr(vals[var]) for var
                    in self._all_flag_varname)

        else:
            compiler = self.default_compiler
            sys_inc, inc, flags = [], [], []

        sys_inc += self.SysIncludes(compiler)
        sys_inc_flags = UnionAll(['-isystem', x] for x in sys_inc)
        inc_flags = ['-I%s' % d for d in inc]
        flags = self.base_flags + sys_inc_flags + inc_flags + flags

        return flags


LANGUAGE_DESC = {
    'C':
        BasicLanguageDesc(
            base_flags = ['-x', 'c'],
            compiler_varname = 'CC',
            default_compiler = 'gcc',
            sys_include_varname = 'CSYSINCLUDES',
            include_varname = 'CINCLUDES',
            flag_varname = 'CFLAGS',
        ),
   'C++':
       BasicLanguageDesc(
           base_flags = [
               '-std=c++11',
               # '-Wc++98-compat',
               '-fexceptions',
               '-x', 'c++',
           ],
           compiler_varname = 'CXX',
           default_compiler = 'g++',
           sys_include_varname = 'CXXSYSINCLUDES',
           include_varname = 'CXXINCLUDES',
           flag_varname = 'CXXFLAGS',
       )
}

def FlagsForFile(filename, **kwargs):
    filename = path.abspath(filename)
    _, ext = path.splitext(filename)
    ext = ext.lower()
    lang = 'C' if ext == '.c' else 'C++'
    desc = LANGUAGE_DESC[lang]

    dirname = path.dirname(filename)
    conf_file =  dirname + '/' + CONF_FILE_NAME
    while not path.exists(conf_file):
        if dirname in ('', '/'):
            conf_file = None
            break
        dirname = path.dirname(dirname)
        conf_file = dirname + '/' + CONF_FILE_NAME

    if conf_file:
        logger.info('Found config file %s for %s.', conf_file, filename)
    else:
        logger.info('Does not found config file for %s.', filename)
    flags = desc.Flags(filename, conf_file)

    return {'flags': flags, 'do_cache': True}

def main():
    logging.basicConfig(level=logging.INFO)
    for filename in sys.argv[1:]:
        flags = FlagsForFile(filename)
        print flags['flags']

if __name__ == '__main__':
    main()
