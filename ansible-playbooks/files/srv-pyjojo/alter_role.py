#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Perform ALTER on a ROLE
# param: role - Your ROLE name
# param: createrole - If bool set, Toggle CEATEROLE else NOCREATEROLE
# param: createuser - If bool set, Toggle CREATEUSER else NOCREATEUSER
# param: createdb - If bool set, Toggle CREATEDB else NOCREATEDB
# param: inherit - If bool set, Toggle INHERIT else NOINHERIT
# param: login - If bool set, Toggle LOGIN else NOLOGIN
# param: connection_limit - Maximum connections default is 10. Max is 25.
# param: connection_limit_bust - Raise to max_val(150)
# param: rolename - Which role (only one currently) to add to
# param: groupname -  Which group (only one currently) to add to
# http_method: post
# lock: False
# tags: Postgres, PGaaS, cit-ops
# -- jojo --

from os import linesep
from common import MkTemp, Sanitize, CmdRun
from common import ToolKit, Constants, ParamHandle2

# Spawn Instances
parameter      = ParamHandle2()    # <class> Parameter manipulation
real_escape_string = Sanitize()    # <class> Escape Routines
toolkit        = ToolKit()         # <class> Misc. functions
temp_file      = MkTemp()          # <class> Do /tmp/ build/teardown
params         = parameter.list()  # <dict>  Input params list
run            = CmdRun()          # <class> Runs the query


# ************************************
# *  DEFINE PARAMETERS AND VALIDATE  *
# ************************************
define_param   = "ROLE"
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.require      = True
sanitized_arguement[define_param] = p.get()

define_param   = "CREATEROLE"
sql_when_true  = " {verb} ".format(verb=define_param)
sql_when_false = " NO{verb} ".format(verb=define_param)
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "CREATEUSER"
sql_when_true  = " {verb} ".format(verb=define_param)
sql_when_false = " NO{verb} ".format(verb=define_param)
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "CREATEDB"
sql_when_true  = " {verb} ".format(verb=define_param)
sql_when_false = " NO{verb} ".format(verb=define_param)
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "INHERIT"
sql_when_true  = " {verb} ".format(verb=define_param)
sql_when_false = " NO{verb} ".format(verb=define_param)
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "LOGIN"
sql_when_true  = " {verb} ".format(verb=define_param)
sql_when_false = " NO{verb} ".format(verb=define_param)
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "ROLENAME"
sql_when_true  = " IN ROLE {rolename} ".format(rolename=params[define_param])
sql_when_false = ""
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.set_value_if_defined(sql_when_true, sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "GROUPNAME"
sql_when_true  = " IN GROUP {groupname} ".format(groupname=params[define_param])
sql_when_false = ""
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier   = "sql"
p.set_value_if_defined(sql_when_true, sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param   = "CONNECTION_LIMIT"
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.max_length   = 3
p.sanitizier   = "sql"
sanitized_arguement[define_param] = p.get()

define_param   = "CONNECTION_LIMIT_BUST"
p              = ParamHandle2()
p.value        = params[define_param]
p.name         = define_param
p.sanitizier   = "sql"
p.set_value_if_defined() # Set to True is defined for bool comparisons
sanitized_arguement[define_param] = p.get()

# Handling connection limit parsing requires advanced work
#  While imposing limits and limit busting...
phelper = ParamHandle2() # Using the parameter instance tools for validation.
if phelper.is_nil(sanitized_arguement['CONNECTION_LIMIT']):
    # If no input, we plan on just setting 10 sockets.
    connection_limit = 10
elif sanitized_arguement['CONNECTION_LIMIT_BUST']:
    # Limit busting has been toggled
    if int(sanitized_arguement['CONNECTION_LIMIT']) > Constants.POSTGRES_MAXIMUM_CONNECTION_LIMIT:
        # If the proposed limit is not beyond the POSTGRES_MAXIMUM_CONNECTION_LIMIT, stop
        # We expect a smaller value.
        msg = "value <{max}".format(
            max=Constants.POSTGRES_MAXIMUM_CONNECTION_LIMIT)
        phelper.raise_error(
            keyname='CONNECTION_LIMIT',
            value=sanitized_arguement['CONNECTION_LIMIT'],
            expected_msg=msg
        )
    # Set the busted limit
    connection_limit = sanitized_arguement['CONNECTION_LIMIT']
else:
    # User-submitted connection limit (no limit busting)
    if int(sanitized_arguement['CONNECTION_LIMIT']) > Constants.POSTGRES_CONNECTION_LIMIT:
        # If the proposed limit is beyond the POSTGRES_CONNECTION_LIMIT, stop
        # We expect a smaller value.
        msg = "value <{max}".format(max=Constants.POSTGRES_CONNECTION_LIMIT)
        phelper.raise_error(
            keyname='CONNECTION_LIMIT',
            value=sanitized_arguement['CONNECTION_LIMIT'],
            expected_msg=msg
        )
    # Set the requested limit
    connection_limit = sanitized_arguement['CONNECTION_LIMIT']
arg_connlimit = " CONNECTION LIMIT {max} ".format(max=connection_limit)


# ******************
# *  SQL SENTENCE  *
# ******************
clean_sql = ("BEGIN; ALTER ROLE {rolname} WITH {connection_limit}{createuser}"
             "{createrole}{createdb}{inherit}{login}"
             " {inrole}{ingroup}; END;"
             ).format(
    rolname=sanitized_arguement['ROLE'],
    createuser=sanitized_arguement['CREATEUSER'],
    createrole=sanitized_arguement['CREATEROLE'],
    createdb=sanitized_arguement['CREATEDB'],
    inherit=sanitized_arguement['INHERIT'],
    login=sanitized_arguement['LOGIN'],
    connection_limit=real_escape_string.sql(arg_connlimit),
    inrole=sanitized_arguement['ROLENAME'],
    ingroup=sanitized_arguement['GROUPNAME'],
)
toolkit.fail_beyond_maxlength(maxlength=2000, string=clean_sql)
sql_code = temp_file.write(clean_sql)



# ****************
# *  SQL RUNNER  *
# ****************
output = run.sql(sql_code)


# **********************
# *  OUTPUT PROCESSOR  *
# **********************
print(output)
exitcode = 0
error_scenario_1 = False
error_scenario_2 = False
error_scenario_3 = False
error_scenario_4 = False

for line in output.split(linesep):
    if line == "ROLLBACK":
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode         = 1  # Rollbacks should flag an API error code.
    if "psql:/tmp/" in line and " ERROR:  " in line:
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if ("ERROR:" in line) and (" role " in line) and ("does not exist" in line):
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if " FATAL: " in line:
        toolkit.print_stderr(line)
        error_scenario_4 = True
        exitcode         = 1  # Parse Errors should flag an API error code.

# Report Output
if exitcode == 0:
    # We good
    print("jojo_return_value execution_status=ok")
else:
    # Errors should flag an API error code.
    error_hint = []
    if error_scenario_1:
        error_hint.append('TRANSACTION_ROLLBACK')
    if error_scenario_2:
        error_hint.append('SQL_ERROR')
    if error_scenario_3:
        error_hint.append('ROLE_DOES_NOT_EXIST')
    if error_scenario_4:
        error_hint.append('FATAL_ERROR')
    if len(error_hint) == 0:
        error_hint = ['UNKNOWN']
    if error_scenario_3:
        error_hint.append('ROLE_DOES_NOT_EXIST')
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))

temp_file.close()  # Cleanup temp SQL
exit(exitcode)  # Exit with status
