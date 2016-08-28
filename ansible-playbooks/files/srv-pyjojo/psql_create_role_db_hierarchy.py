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
from common import MkTemp, Sanitize, CmdRun
from common import ToolKit, Constants, ParamHandle2

# Spawn Instances
parameter     = ParamHandle2()    # <class> Parameter manipulation
real_escape_string = Sanitize()   # <class> Escape Routines
toolkit       = ToolKit()         # <class> Misc. functions
temp_file     = MkTemp()          # <class> Do /tmp/ build/teardown
params        = parameter.list()  # <dict>  Input params list
run           = CmdRun()          # <class> Runs the query


# ************************************
# *  DEFINE PARAMETERS AND VALIDATE  *
# ************************************
sanitized_arguement = {}

define_param = "APPLICATION"
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.require    = True
p.sanitizier = "sql"
sanitized_arguement[define_param] = p.get()

define_param = "SUPER_PASSWORD"
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.require    = True
p.sanitizier = "sql"
sanitized_arguement[define_param] = p.get()


define_param = "SVC_PASSWORD"
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.require    = True
p.sanitizier = "sql"
sanitized_arguement[define_param] = p.get()

define_param = "SUPER_SVC_LOGIN"
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier = "sql"
sanitized_arguement[define_param] = p.get()

define_param = "SUPER_SVC_LOGIN"
sql_when_true  = " LOGIN ".format(verb=define_param)
sql_when_false = " NOLOGIN ".format(verb=define_param)
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param = "SUPER_MAXSOCK"
val_when_nil = " 3 "
val_when_not = " {x} ".format(x=params[define_param])
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier = "sql"
p.set_value_if_undefined(custom_if_value=val_when_nil, custom_else_value=val_when_not)
sanitized_arguement[define_param] = p.get()

define_param = "SVC_LOGIN"
sql_when_true  = " LOGIN ".format(verb=define_param)
sql_when_false = " NOLOGIN ".format(verb=define_param)
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier = "sql"
p.convert_to_bool(sql_when_true,sql_when_false,sql_when_false)
sanitized_arguement[define_param] = p.get()

define_param = "SVC_MAXSOCK"
val_when_nil = " 2 "
val_when_not = " {x} ".format(x=params[define_param])
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.sanitizier = "sql"
p.set_value_if_undefined(custom_if_value=val_when_nil, custom_else_value=val_when_not)
sanitized_arguement[define_param] = p.get()


# ******************
# *  SQL SENTENCE  *
# ******************
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
    myapplication=sanitized_arguement['APPLICATION'],
    super_password=sanitized_arguement['SUPER_PASSWORD'],
    super_login=sanitized_arguement['SUPER_SVC_LOGIN'],
    super_maxsock=sanitized_arguement['SUPER_MAXSOCK'],
    svc_login=sanitized_arguement['SVC_LOGIN'],
    svc_maxsock=sanitized_arguement['SVC_MAXSOCK'],
    svc_password=sanitized_arguement['SVC_PASSWORD']
)
toolkit.fail_beyond_maxlength(maxlength=1500, string=clean_sql)
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
error_scenario_5 = False

# Parse Output
for line in output.split(linesep):
    if ("ERROR:" in line) and (" role " in line) and ("already exists" in line):
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if ("ERROR:" in line) and (" database " in line) and ("already exists" in line):
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if (line == "ROLLBACK") or ("transaction is aborted, commands ignored" in line):
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode         = 1  # Rollbacks should flag an API error code.
    if ("psql:/tmp/" in line) and (" ERROR:  " in line):
        toolkit.print_stderr(line)
        error_scenario_4 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if " FATAL: " in line:
        toolkit.print_stderr(line)
        error_scenario_5 = True
        exitcode         = 1  # Parse Errors should flag an API error code.

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
