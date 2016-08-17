#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 

from __future__ import print_function        # for print_stderr
from sys import stderr                       # for print_stderr
from os import environ as env                # for paramaters
from os import chmod, chown, unlink          # for tempfile
from tempfile import NamedTemporaryFile      # for tempfile
from pwd import getpwnam                     # for tempfile
from subprocess import Popen, PIPE, STDOUT   # for command runs
from pwd import getpwnam                     # for tempfile
import re as regex                           # for eval sanitize

class CmdRun():
    """
    CLASS: Handles the execution of commands using subprocess.
           run() is the main business end of the class, while subsequent functions
           are primarily made to aid customized command processing.
    """

    def run(self, command):
        """
        Runs a command and returns combined STDERR/STDOUT

        :param command: <STR> command to run
        :return <str>:
        """
        out = Popen(command.split(), stderr=STDOUT, stdout=PIPE, shell=False)
        stdout = out.communicate()[0]
        return stdout

    def sql(self, sql_code):
        """
        Runs a set of SQL code using run(), and returns the run() object back.
        :param sql_code: <STR> SQL query to run
        :return <FUNCTION self.run>:
        """
        sql_shell = "/usr/bin/sudo -u postgres /usr/bin/psql -U postgres -a -f {sql}".format(
            sql=sql_code)
        return self.run(sql_shell)

    def ansible(self, x):
        """
        """
        sql_shell = "ansible-playbook {x}".format(x=x)
        return False

    def fabric(self, x):
        """
        """
        sql_shell = "fab {x}".format(x=x)
        return False

    def web(self, x):
        """
        """
        # Call requests handler class. TODO rax identity class.
        return False


class MkTemp():
    """
    CLASS: This class handles the writing and cleanup of temporary files.
           Uses tempfile.NamedTemporaryFile, which is like bash `mktemp`
    """

    def harden_permissions(self, fname):
        """
        Sets permissions on the tmpfiles for reasonable security.
        """
        uid = getpwnam('postgres').pw_uid
        gid = getpwnam('postgres').pw_gid
        chmod(fname, 0600)      # o+rw
        chown(fname, uid, gid)  # chown postgres: fname

    def write(self, content):
        """
        Write intermediary contents to a temporary file handle
        """
        with NamedTemporaryFile(mode='w+b', delete=False) as f:
            self.f = f.name
            f.write(content)  # Write
            self.harden_permissions(f.name)
            return f.name

    def close(self):
        unlink(self.f)


class Constants():
    """
    CLASS: Fixed properties that rarely change
    """
    # Postgres uses  no more than  NAMEDATALEN-1 bytes
    # of an  identifier;  longer names can be written in
    # commands, but they will be truncated.  By default,
    # NAMEDATALEN is 64 so the maximum identifier length
    # is 63 bytes.
    POSTGRES_NAMEDATA_LEN = 64

    # User selectable socket limits can go this high
    POSTGRES_CONNECTION_LIMIT = 25

    # Busted user selectable socket limits can go this high
    # We don't need to get sockets too high.
    POSTGRES_MAXIMUM_CONNECTION_LIMIT = 150


class Environment():
    """
    CLASS: Manages environment properties.
    """

    def params(self, sanitizer):
        """
        Returns json params from parent environment

        """
        sanitize = Sanitize()
        params = {}
        for param, value in env.iteritems():
            if not sanitizer:
                params[param] = value
            elif sanitizer == "sql":
                params[param] = Sanitize.sql(value)
            elif sanitizer == "nonalphanumeric":
                params[param] = Sanitize.non_alphanumeric_text(value)

        return params


class ToolKit():
    """
    CLASS: Misc. functions
    """

    def print_stderr(self, *args, **kwargs):
        """
        Prints a message to stderr.
        Requires sys.stderr

        """
        print(*args, file=stderr, **kwargs)

    def fail_beyond_maxlength(self, maxlength=0, string=""):
        """
        If a string is beyond a certain length, fail.
        Long inputs are indicative of fuzzing in some instances.
        It's a security bailout
        """
        if len(string) > maxlength:
            print("jojo_return_value execution_status=rollback")
            print("jojo_return_value error_reason_indicator=UNKNOWN")
            exit(1)


class Sanitize():
    """
    CLASS:  String sanitization functions for safe eval
            You put a string in, get  a string out.
    """

    def non_alphanumeric_text(self, varied_input):
        """
        Should return a string safe to run anywhere, considering
        it's only alpha-numeric text.

        :param your_string: The string you wish to escape.
        """
        return regex.sub(r'\W+', '', varied_input)

    def sql(self, sql):
        """
        Ported from php-7.0.9/ext/mysqli/tests/mysqli_real_escape_string.phpt

        It escapes statement, terminators, escapes, newlines, returns, quotes for 
        sanitization. Nullchars will error before here, but makes those safe too,
        because the DB can't use them.

        :param sql: The string you wish to escape.
        """
        # SELECT * FR; DROP DATABASE POSTGRES to SELECT * FR\; DROP DATABASE
        # POSTGRES
        escaped = regex.sub(r';', '\\\\;', sql)
        # фу\\бар to фу\\\\бар (Escape escapes)
        escaped = regex.sub(r'[\\\\]', '\\\\\\\\', escaped)
        # 阿卜拉\n轻 to 阿卜拉\\n轻 (Escape newline)
        escaped = regex.sub(r'\n', '\\\\n', escaped)
        # 张明安\r在 to 张明安\\r在 (Escape return)
        escaped = regex.sub(r'\r', '\\\\r', escaped)
        # бар"фус to бар\"фус
        escaped = regex.sub(r'\"', '\\"', escaped)
        # лала'лали to лала\'лали
        escaped = regex.sub(r'\'', '\\\\\'', escaped)
        # replace nullchar
        escaped = regex.sub(r'\0', '<NULL>', escaped)
        return escaped


class ParamHandle():
    """
    CLASS: Parameter handling. This class does a multitude of things,
           including getting the parameters from the environment() class,
           as well as helping with params, such as ensuring required 
           env params exist, or that they are not '' (nil)
    """

    def __init__(self):
        self.err = ToolKit()
        self.env = Environment()

    def get(self, sanitizer=None):
        """
        This will return a dictionary of environment variables.
        It will first pass the strings through a sanitizer, which if 
        given the correct options will sanitize the string.
        """
        return self.env.params(sanitizer)

    def is_nil(self, param):
        """
        Returns true/false depending on if the user
        provided this parameter with a value to the API or not.
        Useful for boolean/value checks.
        An empty parameter is seen as ''"'"''"'"''

        If you think the context is strange, consider
        that export x='"'"''"'"' is basically x="''"
        Which is the escapes occuring at higher abstraction.

        :param param: Input parameter from environ()
        :return: <BOOL>
        """

        # if param == "\\'\\'\\\"\\'\\\"\\'\\'\\\"\\'\\\"\\'\\'":
        #\\'\\'\\\"\\'\\\"\\'\\'\\\"\\'\\\"\\'\\'
        if param == """''\"'\"''\"'\"''""":
            return True
        else:
            return False

    def require_to_run(self, parameters=[], params={}):
        """
        Used during pre-flight check.
        Used to check an env dict for parameters that
        were supplied empty to the user. Exit if found.

        :parameters: is a list of your required parameters
        :params: is the paramHandle.get() function, a dict
        """
        nil_params = []
        for param, value in params.iteritems():
            if param in parameters and self.is_nil(value):
                nil_params.append(param)

        if len(nil_params) > 1:
            print("jojo_return_value missing_params={bad_params}".format(
                bad_params=nil_params))
            print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_IS_NULL")
            self.err.print_stderr("Multiple Required Parameters: `{bad_params}` were not provided in JSON contract. Please set required values.".format(
                bad_params=nil_params))
            exit(1)
        elif len(nil_params) > 0:
            print("jojo_return_value missing_params={bad_param}".format(
                bad_param=nil_params))
            print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_IS_NULL")
            self.err.print_stderr("Required Parameter: `{bad_param}` was not provided in JSON contract. Please set required value.".format(
                bad_param=nil_params))
            exit(1)

    def fail_if_nil(self, keyname, value):
        """
        Causes an error message then exits, used when a parameter is nil.
        """
        if self.is_nil(value):
            print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_IS_NULL")
            self.err.print_stderr(
                "Parameter `{name}` provided with value: \'\' (nil), expected a value.".format(name=keyname))
            exit(1)

    def raise_error(self, keyname, value, expected_msg):
        """
        Causes an error message then exits, used when a parameter is invalid.
        """
        print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_INPUT")
        self.err.print_stderr("Parameter `{key}` provided with value: {param}, expected: {expect} value.".format(
            key=keyname, expect=expected_msg, param=value))
        exit(1)

    def return_if_not_nil(self, param, return_if=True, return_else=False):
        """
        Returns return_if if input is nil. Else returns return_else.
        Used for parameter processing.
        """
        if not self.is_nil(param):
            return return_if
        else:
            return return_else

    def return_if_nil(self, param, return_if=True, return_else=False):
        """
        Returns return_if if input is nil. Else returns return_else.
        Used for parameter processing.
        """
        if self.is_nil(param):
            return return_if
        else:
            return return_else

    def return_if_true(self, param, return_if=True, return_else=False, return_nomatch=False):
        """
        Returns return_if if input is True. Else returns return_else.
        return_nomatch returns if it is neither true nor false.
        Used for parameter processing.
        """
        if param.lower().startswith('t') or param == "1" or param.lower().startswith('y'):
            return return_if
        elif param.lower().startswith('f') or param == "0" or param.lower().startswith('n'):
            return return_else
        else:
            return return_nomatch

    def return_if_false(self, param, return_if=True, return_else=False, return_nomatch=False):
        """
        Returns return_if if input is False. Else returns return_else.
        return_nomatch returns if it is neither true nor false.
        Used for parameter processing.
        """
        if param.lower().startswith('f') or param == "0" or param.lower().startswith('y'):
            return return_if
        elif param.lower().startswith('t') or param == "1" or param.lower().startswith('n'):
            return return_else
        else:
            return return_nomatch

class ParamHandle2():
    """
    CLASS: Parameter handling. This class does a multitude of things,
           including getting the parameters from the environment() class,
           as well as helping with params, such as ensuring required 
           env params exist, or that they are not '' (nil)
    """
    
    def __init__(self):
        self.err = ToolKit()
        self.env = Environment()

    def get(self, sanitizer=None):
        """
        This will return a dictionary of environment variables.
        It will first pass the strings through a sanitizer, which if 
        given the correct options will sanitize the string.
        """
        return self.env.params(sanitizer)

    def is_nil(self, param):
        """
        Returns true/false depending on if the user
        provided this parameter with a value to the API or not.
        Useful for boolean/value checks.
        An empty parameter is seen as ''"'"''"'"''

        If you think the context is strange, consider
        that export x='"'"''"'"' is basically x="''"
        Which is the escapes occuring at higher abstraction.

        :param param: Input parameter from environ()
        :return: <BOOL>
        """

        # if param == "\\'\\'\\\"\\'\\\"\\'\\'\\\"\\'\\\"\\'\\'":
        #\\'\\'\\\"\\'\\\"\\'\\'\\\"\\'\\\"\\'\\'
        if param == """''\"'\"''\"'\"''""":
            return True
        else:
            return False

    def require_to_run(self, parameters=[], params={}):
        """
        Used during pre-flight check.
        Used to check an env dict for parameters that
        were supplied empty to the user. Exit if found.

        :parameters: is a list of your required parameters
        :params: is the paramHandle.get() function, a dict
        """
        nil_params = []
        for param, value in params.iteritems():
            if param in parameters and self.is_nil(value):
                nil_params.append(param)

        if len(nil_params) > 1:
            print("jojo_return_value missing_params={bad_params}".format(
                bad_params=nil_params))
            print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_IS_NULL")
            self.err.print_stderr("Multiple Required Parameters: `{bad_params}` were not provided in JSON contract. Please set required values.".format(
                bad_params=nil_params))
            exit(1)
        elif len(nil_params) > 0:
            print("jojo_return_value missing_params={bad_param}".format(
                bad_param=nil_params))
            print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_IS_NULL")
            self.err.print_stderr("Required Parameter: `{bad_param}` was not provided in JSON contract. Please set required value.".format(
                bad_param=nil_params))
            exit(1)

    def fail_if_nil(self, keyname, value):
        """
        Causes an error message then exits, used when a parameter is nil.
        """
        if self.is_nil(value):
            print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_IS_NULL")
            self.err.print_stderr(
                "Parameter `{name}` provided with value: \'\' (nil), expected a value.".format(name=keyname))
            exit(1)

    def raise_error(self, keyname, value, expected_msg):
        """
        Causes an error message then exits, used when a parameter is invalid.
        """
        print("jojo_return_value error_reason_indicator=EXPECTED_PARAMETER_INPUT")
        self.err.print_stderr("Parameter `{key}` provided with value: {param}, expected: {expect} value.".format(
            key=keyname, expect=expected_msg, param=value))
        exit(1)

    def return_if_not_nil(self, param, return_if=True, return_else=False):
        """
        Returns return_if if input is nil. Else returns return_else.
        Used for parameter processing.
        """
        if not self.is_nil(param):
            return return_if
        else:
            return return_else

    def return_if_nil(self, param, return_if=True, return_else=False):
        """
        Returns return_if if input is nil. Else returns return_else.
        Used for parameter processing.
        """
        if self.is_nil(param):
            return return_if
        else:
            return return_else

    def return_if_true(self, param, return_if=True, return_else=False, return_nomatch=False):
        """
        Returns return_if if input is True. Else returns return_else.
        return_nomatch returns if it is neither true nor false.
        Used for parameter processing.
        """
        if param.lower().startswith('t') or param == "1" or param.lower().startswith('y'):
            return return_if
        elif param.lower().startswith('f') or param == "0" or param.lower().startswith('n'):
            return return_else
        else:
            return return_nomatch

    def return_if_false(self, param, return_if=True, return_else=False, return_nomatch=False):
        """
        Returns return_if if input is False. Else returns return_else.
        return_nomatch returns if it is neither true nor false.
        Used for parameter processing.
        """
        if param.lower().startswith('f') or param == "0" or param.lower().startswith('y'):
            return return_if
        elif param.lower().startswith('t') or param == "1" or param.lower().startswith('n'):
            return return_else
        else:
            return return_nomatch

if __name__ == "__main__":
    # Just quit.
    exit(0)
    # pkill pyjojo; pyjojo -d --dir /srv/pyjojo&
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "x","password": "qwerty", "login": "true"}' | python -m json.tool
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "x","password": "qwerty", "login": "true", "connection_limit": "5"}' | python -m json.tool
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "x","password": "qwerty", "login": "true", "connection_limit": "555"}' | python -m json.tool
    #
    # HACK CHECK
    #  INSERT NULL THEN DROP postgres; 500 error
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "jon\x00DROP DATABASE postgres; kelley","password": "test",  "login": "true", "connection_limit": "5"}' | python -m json.tool
    #  INSERT NULL THEN DROP postgres; 500 error
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "jonфу\x00张明安\x00фус张明安\r在\x00;DROP DATABASE postgres; kelley","password": "test",  "login": "true", "connection_limit": "5"}' | python -m json.tool
    # HACK CHECK
    #  INSERT escape ; then DROP postgres; 500 error
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "jon\;DROP DATABASE postgres; kelley","password": "test",  "login": "true", "connection_limit": "5"}' | python -m json.tool
    # HACK CHECK
    #  INSERT escape escape ; then DROP postgres; 500 error
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "jon\\;DROP DATABASE postgres; kelley","password": "test",  "login": "true", "connection_limit": "5"}' | python -m json.tool
    # HACK CHECK
    #  INSERT escape escape escape ; then DROP postgres; 500 error
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "jon\\\;DROP DATABASE postgres; kelley","password": "test",  "login": "true", "connection_limit": "5"}' | python -m json.tool
    # HACK CHECK
    #  INSERT escape escape escape escape ; then DROP postgres; 500 error
    # curl -XPOST http://localhost:3000/scripts/createrole -H "Content-Type: application/json" -d '{ "role": "jon\\\\;DROP DATABASE postgres; kelley","password": "test",  "login": "true", "connection_limit": "5"}' | python -m json.tool
    # postgres=# DROP DATABASE acme_staging\\\\\\;
    # Invalid command \. Try \? for help.
    #
    # See scripts
    # curl -XGET http://localhost:3000/scripts/ -H "Content-Type:
    # application/json" | python -m json.tool
