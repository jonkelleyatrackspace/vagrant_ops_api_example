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

param = "DATABASE"
term_db = parameter.return_if_nil(
    param=params[param],
    return_if=False,
    return_else=True
)

param = "APPLICATION"
term_application = parameter.return_if_nil(
    param=params[param],
    return_if=False,
    return_else=True
)

param = "USER"
term_user = parameter.return_if_nil(
    param=params[param],
    return_if=False,
    return_else=True
)

param = "PID"
term_pid = parameter.return_if_nil(
    param=params[param],
    return_if=False,
    return_else=True
)

param = "CLIENT_ADDRESS"
term_ip = parameter.return_if_nil(
    param=params[param],
    return_if=False,
    return_else=True
)

if term_db:
    arg_identifier = "datname"
    arg_key = params['DATABASE']
elif term_application:
    arg_identifier = "application_name"
    arg_key = params['APPLICATION']
elif term_user:
    arg_identifier = "usename"
    arg_key = params['USER']
elif term_pid:
    arg_identifier = "procpid"
    arg_key = params['PID']
elif term_ip:
    arg_identifier = "client_addr"
    arg_key = params['CLIENT_ADDRESS']
else:
    toolkit.print_stderr(
        "Must provide at least 1 parameter to kill connections by.")
    exit(1)

# ---------------------------
# --- Define SQL Sentence ---
# This formats the SQL verbs into a complete query sentence.
clean_sql = ("SELECT row_to_json(t)  FROM ("
             "    SELECT pg_terminate_backend(pid)"
             "     FROM pg_stat_activity"
             "       WHERE {identifier} = '{key}'"
             ") as t; ;"
             ).format(identifier=real_escape_string.sql(arg_identifier), key=real_escape_string.sql(arg_key))

# ---------------
# --- Run SQL ---
toolkit.fail_beyond_maxlength(maxlength=1000, string=clean_sql)
sql_code = temp_file.write(clean_sql)

# ---------------
# --- Run SQL ---
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

# Process result
for line in output.split(linesep):
    if line == "ROLLBACK":
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode = 1  # Rollbacks should flag an API error code.
    if "psql:/tmp/" in line and " ERROR:  " in line:
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if " FATAL:  " in line and "terminating connection due" in line:
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if "connection unexpectedly" in line or "terminated abnormally" in line:
        toolkit.print_stderr(line)
        error_scenario_3 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if "connection to server" in line and "lost" in line:
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
