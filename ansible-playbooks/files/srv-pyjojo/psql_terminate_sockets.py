#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Will terminate sockets to a user or a database.
# param: user - If supplied, will terminate all connections to this user.
# param: database -  If supplied, will terminate all connections to this database.
# param: application -  If supplied, will terminate all connections to this appliccation.
# param: pid -  If supplied, will terminate all connections to this pid.
# param: client_address -  If supplied, will terminate all connections to this IP.
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
environment   = Environment()     # <class> Manages Env Vars
temp_file     = MkTemp()          # <class> Do /tmp/ build/teardown
params        = parameter.list()  # <dict>  Input params list
run           = CmdRun()          # <class> Runs the query


# ************************************
# *  DEFINE PARAMETERS AND VALIDATE  *
# ************************************
sanitized_arguement    = {}

define_param           = "DATABASE"
database               = ParamHandle2()
database.value         = params[define_param]
database.name          = define_param
database.max_length    = Constants.POSTGRES_NAMEDATA_LEN
database.sanitizier    = "sql"
database.set_value_if_defined()
sanitized_arguement[define_param] = database.get()

define_param           = "APPLICATION"
application            = ParamHandle2()
application.value      = params[define_param]
application.name       = define_param
application.max_length = Constants.POSTGRES_NAMEDATA_LEN
application.sanitizier = "sql"
application.set_value_if_defined()
sanitized_arguement[define_param] = application.get()

define_param           = "USER"
user                   = ParamHandle2()
user.value             = params[define_param]
user.name              = define_param
user.max_length        = Constants.POSTGRES_NAMEDATA_LEN
user.sanitizier        = "sql"
user.set_value_if_defined()
sanitized_arguement[define_param] = user.get()

define_param           = "PID"
pid                    = ParamHandle2()
pid.value              = params[define_param]
pid.name               = define_param
pid.max_length         = Constants.POSTGRES_NAMEDATA_LEN
pid.sanitizier         = "sql"
pid.set_value_if_defined()
sanitized_arguement[define_param] = pid.get()

define_param           = "CLIENT_ADDRESS"
clientaddr             = ParamHandle2()
clientaddr.value       = params[define_param]
clientaddr.name        = define_param
clientaddr.max_length  = Constants.POSTGRES_NAMEDATA_LEN
clientaddr.sanitizier  = "sql"
clientaddr.set_value_if_defined()
sanitized_arguement[define_param] = clientaddr.get()

if sanitized_arguement['DATABASE']:
    arg_identifier = "datname"
    arg_key        = database.value
elif sanitized_arguement['APPLICATION']:
    arg_identifier = "application_name"
    arg_key        = application.value
elif sanitized_arguement['USER']:
    arg_identifier = "usename"
    arg_key        = user.value
elif sanitized_arguement['PID']:
    arg_identifier = "procpid"
    arg_key        = pid.value
elif sanitized_arguement['CLIENT_ADDRESS']:
    arg_identifier = "client_addr"
    arg_key        = clientaddr.value
else:
    toolkit.print_stderr(
        "Must provide at least 1 parameter to kill connections by.")
    exit(1)


# ******************
# *  SQL SENTENCE  *
# ******************
clean_sql = ("SELECT row_to_json(t)  FROM ("
             "    SELECT pg_terminate_backend(pid)"
             "     FROM pg_stat_activity"
             "       WHERE {identifier} = '{key}'"
             ") as t; ;"
             ).format(identifier=real_escape_string.sql(arg_identifier), key=real_escape_string.sql(arg_key))
toolkit.fail_beyond_maxlength(maxlength=1000, string=clean_sql)
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

# Process result
for line in output.split(linesep):
    if line == "ROLLBACK":
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode         = 1  # Rollbacks should flag an API error code.
    if "psql:/tmp/" in line and " ERROR:  " in line:
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if " FATAL:  " in line and "terminating connection due" in line:
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if "connection unexpectedly" in line or "terminated abnormally" in line:
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode         = 1  # Parse Errors should flag an API error code.
    if "connection to server" in line and "lost" in line:
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
        error_hint.append('CLIENT_SOCKET_WAS_TERMINATED')
    if error_scenario_4:
        error_hint.append('FATAL_ERROR')
    if len(error_hint) == 0:
        error_hint = ['UNKNOWN']
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))

temp_file.close()  # Cleanup temp SQL
exit(0)  # Exit with status
