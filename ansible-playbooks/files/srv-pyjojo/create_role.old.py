#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Create a new ROLE in Postgres.
# param: role - Your ROLE name
# param: password - Role PASSWORD
# param: createrole - If bool set, Toggle CEATEROLE else NOCREATEROLE
# param: createuser - If bool set, Toggle CREATEUSER else NOCREATEUSER
# param: createdb - If bool set, Toggle CREATEDB else NOCREATEDB
# param: inherit - If bool set, Toggle INHERIT else NOINHERIT
# param: login - If bool set, Toggle LOGIN else NOLOGIN
# param: connection_limit - Maximum connections default is 10. Max is 25.
# param: connection_limit_bust - Raise to max_val(150)
# param: encrypted - If bool set, Toggle UNENCRYPTED else ENCRYPTED
# param: rolename - Which role (only one currently) to add to
# param: groupname -  Which group (only one currently) to add to
# http_method: post
# lock: False
# tags: Postgres, PGaaS, cit-ops
# -- jojo --

from os import linesep
from common import MkTemp, Sanitize, CmdRun, Environment
from common import ToolKit, Constants, ParamHandle

# Spawn Instances
parameter = ParamHandle()     # <class> Parameter manipulation
real_escape_string = Sanitize()  # <class> Escape Routines
toolkit = ToolKit()           # <class> Misc. functions
environment = Environment()    # <class> Manages Env Vars
temp_file = MkTemp()           # <class> Do /tmp/ build/teardown
params = parameter.get()       # <dict>  Input params
run = CmdRun()                # <class> Runs the query

# ----------------------------------
# --- Define Required Parameters ---
# This should be a list of required params from the API handoff.
parameter.require_to_run(
    parameters=['ROLE', 'PASSWORD', 'CONNECTION_LIMIT'], params=params)

# -------------------------
# --- Bounds Validation ---
#
err = "less then 63 bytes for input"
role = params['ROLE']
if len(role) > Constants.POSTGRES_NAMEDATA_LEN:
    parameter.raise_error(keyname='ROLE', value=role, expected_msg=err)
else:
    arg_role = role

password = params['PASSWORD']
if len(password) > Constants.POSTGRES_NAMEDATA_LEN:
    parameter.raise_error(keyname='PASSWORD', value=password, expected_msg=err)
else:
    arg_pass = password

# -----------------------
# --- Parameter Logic ---
# Perform basic logic parse on params and build the SQL query verbs.
param = "CREATEROLE"
arg_createrole = parameter.return_if_true(
    param=params[param],
    return_if=" {verb} ".format(verb=param),
    return_else=" NO{verb} ".format(verb=param),
    return_nomatch=" NO{verb} ".format(verb=param)
)

param = "CREATEUSER"
arg_createuser = parameter.return_if_true(
    param=params[param],
    return_if=" {verb} ".format(verb=param),
    return_else=" NO{verb} ".format(verb=param),
    return_nomatch=" NO{verb} ".format(verb=param)
)

param = "CREATEDB"
arg_createdb = parameter.return_if_true(
    param=params[param],
    return_if=" {verb} ".format(verb=param),
    return_else=" NO{verb} ".format(verb=param),
    return_nomatch=" NO{verb} ".format(verb=param)
)

param = "INHERIT"
arg_inherit = parameter.return_if_true(
    param=params[param],
    return_if=" {verb} ".format(verb=param),
    return_else=" NO{verb} ".format(verb=param),
    return_nomatch=" NO{verb} ".format(verb=param)
)

param = "LOGIN"
arg_login = parameter.return_if_true(
    param=params[param],
    return_if=" {verb} ".format(verb=param),
    return_else=" NO{verb} ".format(verb=param),
    return_nomatch=" NO{verb} ".format(verb=param)
)

param = "ENCRYPTED"
arg_encrypted = parameter.return_if_true(
    param=params[param],
    return_if=" {verb} ".format(verb=param),
    return_else=" UN{verb} ".format(verb=param),
    return_nomatch=" UN{verb} ".format(verb=param)
)

param = "ROLENAME"
arg_role_name = parameter.return_if_nil(
    param=params[param],
    return_if="",
    return_else=" IN ROLE {rolename} ".format(rolename=params[param])
)

param = "GROUPNAME"
arg_group_name = parameter.return_if_nil(
    param=params[param],
    return_if="",
    return_else=" IN GROUP {groupname} ".format(groupname=params[param])
)

# Parse connection limits
param_connlimit = params['CONNECTION_LIMIT']
if parameter.is_nil(param_connlimit):
    # If no input, we plan on just setting 10 sockets.
    connection_limit = 10
elif not parameter.is_nil(params['CONNECTION_LIMIT_BUST']):
    # Limit busting has been toggled
    if int(param_connlimit) > Constants.POSTGRES_MAXIMUM_CONNECTION_LIMIT:
        # If the proposed limit is not beyond the POSTGRES_MAXIMUM_CONNECTION_LIMIT, stop
        # We expect a smaller value.
        msg = "value <{max}".format(
            max=Constants.POSTGRES_MAXIMUM_CONNECTION_LIMIT)
        parameter.raise_error(
            keyname='CONNECTION_LIMIT',
            value=param_connlimit,
            expected_msg=msg
        )
    # Set the busted limit
    connection_limit = param_connlimit
else:
    # User-submitted connection limit (no limit busting)
    if int(param_connlimit) > Constants.POSTGRES_CONNECTION_LIMIT:
        # If the proposed limit is beyond the POSTGRES_CONNECTION_LIMIT, stop
        # We expect a smaller value.
        msg = "value <{max}".format(max=Constants.POSTGRES_CONNECTION_LIMIT)
        parameter.raise_error(
            keyname='CONNECTION_LIMIT',
            value=param_connlimit,
            expected_msg=msg
        )
    # Set the requested limit
    connection_limit = param_connlimit
arg_connlimit = " CONNECTION LIMIT {max} ".format(max=connection_limit)

# ---------------------------
# --- Define SQL Sentence ---
# This formats the SQL verbs into a complete query sentence.
clean_sql = ("BEGIN; CREATE ROLE {username} WITH {connection_limit}{createuser}"
             "{createrole}{createdb}{inherit}{login}{encrypted} PASSWORD '{password}'"
             " {inrole}{ingroup}; END;"
             ).format(
    username=real_escape_string.sql(arg_role),
    password=real_escape_string.sql(arg_pass),
    createuser=real_escape_string.sql(arg_createuser),
    createrole=real_escape_string.sql(arg_createrole),
    createdb=real_escape_string.sql(arg_createdb),
    inherit=real_escape_string.sql(arg_inherit),
    login=real_escape_string.sql(arg_login),
    connection_limit=real_escape_string.sql(arg_connlimit),
    encrypted=real_escape_string.sql(arg_encrypted),
    inrole=real_escape_string.sql(arg_role_name),
    ingroup=real_escape_string.sql(arg_group_name),
)

# ---------------
# --- Run SQL ---
toolkit.fail_beyond_maxlength(maxlength=2000, string=clean_sql)
sql_code = temp_file.write(clean_sql)

# ---------------
# --- Run SQL ---
# main.set_command_mode.sql(sql_code)  #TODO config class to pull prefs
# for command formattting
output = run.sql(sql_code)
print(output)

# -----------------------
# --- OUTPUT FILTER ---
# Report back intelligible errors to the user.
exitcode = 0
error_scenario_1 = False
error_scenario_2 = False
error_scenario_3 = False
error_scenario_4 = False

# Parse Output
for line in output.split(linesep):
    if ("ERROR:" in line) and (" role " in line) and ("already exists" in line):
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if (line == "ROLLBACK") or ("transaction is aborted, commands ignored" in line):
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode = 1  # Rollbacks should flag an API error code.
    if ("psql:/tmp/" in line) and (" ERROR:  " in line):
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if " FATAL: " in line:
        toolkit.print_stderr(line)
        error_scenario_4 = True
        exitcode = 1  # Parse Errors should flag an API error code.

# Report Output
if exitcode == 0:
    # We good
    print("jojo_return_value execution_status=ok")
else:
    # Errors should flag an API error code.
    error_hint = []
    if error_scenario_1:
        error_hint.append('ROLE_ALREADY_EXIST')
    if error_scenario_2:
        error_hint.append('TRANSACTION_ROLLBACK')
    if error_scenario_3:
        error_hint.append('SQL_ERROR')
    if error_scenario_4:
        error_hint.append('FATAL_ERROR')
    if len(error_hint) == 0:
        error_hint = ['UNKNOWN']
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))

# TODO add a toolbox.exit(), rename toolbox to main
temp_file.close()  # Cleanup temp SQL
exit(exitcode)  # Exit with status
