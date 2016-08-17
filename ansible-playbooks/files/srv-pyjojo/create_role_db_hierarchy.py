#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Creates a specified database with specified role and super-role, as well as a specified super_svc and _svc account pair. Uses PostgreSQL+Database+References+and+Standards.
# param: application - The name of your application. It will be application_role and accounts will be named after it.
# param: super_svc_login - If the super svc has login permission
# param: super_maxsock - Super svc maximum sockets
# param: super_password - Super svc password
# param: svc_login - If the svc account has login permission
# param: svc_maxsock - Svc account maximum sockets
# param: svc_password - Svc account password
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
    parameters=['APPLICATION', 'SUPER_PASSWORD', 'SVC_PASSWORD'], params=params)

# -------------------------
# --- Bounds Validation ---
err = "less then 63 bytes for input"
param = params['APPLICATION']
if len(param) > Constants.POSTGRES_NAMEDATA_LEN:
    parameter.raise_error(keyname='APPLICATION', value=param, expected_msg=err)

param = params['SUPER_PASSWORD']
if len(param) > Constants.POSTGRES_NAMEDATA_LEN:
    parameter.raise_error(keyname='SUPER_PASSWORD',
                          value=param, expected_msg=err)

param = params['SVC_PASSWORD']
if len(param) > Constants.POSTGRES_NAMEDATA_LEN:
    parameter.raise_error(keyname='SUPER_PASSWORD',
                          value=param, expected_msg=err)

# -----------------------
# --- Parameter Logic ---
# Perform basic logic parse on params and build the SQL query verbs.

param = params['APPLICATION']
arg_role_application = param

param = params['SUPER_PASSWORD']
arg_super_password = param

param = params['SVC_PASSWORD']
arg_svc_password = param

param = params['SUPER_SVC_LOGIN']
arg_super_login = parameter.return_if_true(
    param=param,
    return_if=" LOGIN ".format(verb=param),
    return_else=" NOLOGIN ".format(verb=param),
    return_nomatch=" LOGIN ".format(verb=param)
)

param = params['SUPER_MAXSOCK']
arg_super_maxsock = parameter.return_if_nil(
    param=param,
    return_if=" 3 ",  # Default 3 sockets for super user
    return_else=" {x} ".format(x=param)
)

param = params['SVC_LOGIN']
arg_svc_login = parameter.return_if_true(
    param=param,
    return_if=" LOGIN ",
    return_else=" NOLOGIN ",
    return_nomatch=" LOGIN "
)

param = params['SVC_MAXSOCK']
arg_svc_maxsock = parameter.return_if_nil(
    param=param,
    return_if=" 2 ",  # Default 2 sockets for svc user
    return_else=" {x} ".format(x=param)
)

# ---------------------------
# --- Define SQL Sentence ---
# This formats the SQL verbs into a complete query sentence.
clean_sql = (
    "\echo on\n"
    "BEGIN;\n"
    "/* Make super role  */\n"
    "CREATE  ROLE  {myapplication}_super_role  NOLOGIN;\n"
    "COMMIT;\n"
    "\n"
    "/* Make database (owned by) super role  */\n"
    "CREATE  DATABASE  {myapplication}  OWNER  {myapplication}_super_role;\n"
    "\n"
    "BEGIN;\n"
    "/* Make SUPER service account  */\n"
    "CREATE  ROLE  {myapplication}_super_svc \n"
    "  {super_login} INHERIT CONNECTION LIMIT{super_maxsock}  PASSWORD  '{super_password}'\n"
    "    IN ROLE  {myapplication}_super_role;\n"
    "\n"
    "/*  Make ROLE for application  */\n"
    "CREATE ROLE  {myapplication}_role  NOLOGIN;\n"
    "\n"
    "/* Make ROLE for application service account */\n"
    "CREATE  ROLE  {myapplication}_svc \n"
    "  {svc_login} INHERIT CONNECTION LIMIT {svc_maxsock}  PASSWORD  '{svc_password}'\n"
    "    IN ROLE  {myapplication}_role;\n"
    "COMMIT;\n"
).format(
    myapplication=real_escape_string.sql(arg_role_application),
    super_password=real_escape_string.sql(arg_super_password),
    super_login=real_escape_string.sql(arg_super_login),
    super_maxsock=real_escape_string.sql(arg_super_maxsock),
    svc_login=real_escape_string.sql(arg_svc_login),
    svc_maxsock=real_escape_string.sql(arg_svc_maxsock),
    svc_password=real_escape_string.sql(arg_svc_password)
)

# ---------------
# --- Run SQL ---
toolkit.fail_beyond_maxlength(maxlength=1500, string=clean_sql)
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
error_scenario_5 = False

# Parse Output
for line in output.split(linesep):
    if ("ERROR:" in line) and (" role " in line) and ("already exists" in line):
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if ("ERROR:" in line) and (" database " in line) and ("already exists" in line):
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if (line == "ROLLBACK") or ("transaction is aborted, commands ignored" in line):
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode = 1  # Rollbacks should flag an API error code.
    if ("psql:/tmp/" in line) and (" ERROR:  " in line):
        toolkit.print_stderr(line)
        error_scenario_4 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if " FATAL: " in line:
        toolkit.print_stderr(line)
        error_scenario_5 = True
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
        error_hint.append('DATABASE_ALREADY_EXIST')
    if error_scenario_3:
        error_hint.append('TRANSACTION_ROLLBACK')
    if error_scenario_4:
        error_hint.append('SQL_ERROR')
    if error_scenario_5:
        error_hint.append('FATAL_ERROR')
    if len(error_hint) == 0:
        error_hint = ['UNKNOWN']
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))

# TODO add a toolbox.exit(), rename toolbox to main
temp_file.close()  # Cleanup temp SQL
exit(exitcode)  # Exit with status
