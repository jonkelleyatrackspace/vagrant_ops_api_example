#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Deletes a role
# param: role - Your ROLE name
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

define_param = "ROLE"
p            = ParamHandle2()
p.value      = params[define_param]
p.name       = define_param
p.max_length = Constants.POSTGRES_NAMEDATA_LEN
p.require    = True
p.sanitizier = "sql"
sanitized_arguement[define_param] = p.get()


# ******************
# *  SQL SENTENCE  *
# ******************
clean_sql = ("BEGIN; DROP ROLE {rolename}; END;"
             ).format(rolename=sanitized_arguement["ROLE"])
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
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))