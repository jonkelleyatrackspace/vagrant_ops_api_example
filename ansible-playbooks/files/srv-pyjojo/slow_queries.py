#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Identify slow queries
# http_method: get
# lock: False
# tags: Postgres, PGaaS, cit-ops
# -- jojo --

from os import linesep
from common import MkTemp, CmdRun, ToolKit

# Spawn Instances
temp_file = MkTemp()   # <class> Do /tmp/ build/teardown
run = CmdRun()   # <class> Run
toolkit = ToolKit()  # <class> Misc. functions

# ---------------------------
# --- Define SQL Sentence ---
# This formats the SQL verbs into a complete query sentence.
sql = ("SELECT"
       "    pid,"
       "    current_timestamp - xact_start as xact_runtime,"
       "    query"
       " FROM pg_stat_activity WHERE query NOT LIKE '%pg_stat_activity%' "
       " ORDER BY xact_start;"
       )
sql_code = temp_file.write(sql)

# ---------------
# --- Run SQL ---
query_result = run.sql(sql_code)
print(query_result)

# -----------------------
# --- OUTPUT FILTER ---
# Report back intelligible errors to the user.
exitcode = 0  # We good
error_scenario_1 = False
error_scenario_2 = False

for line in query_result.split(linesep):
    if ("psql:/tmp/" in line) and (" ERROR:  " in line):
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if " FATAL: " in line:
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode = 1  # Parse Errors should flag an API error code.

# Report Output
if exitcode == 0:
    # We good
    print("jojo_return_value execution_status=ok")
else:
    # Errors should flag an API error code.
    error_hint = []
    if error_scenario_1:
        error_hint.append('SQL_ERROR')
    if error_scenario_2:
        error_hint.append('FATAL_ERROR')
    if len(error_hint) == 0:
        error_hint = ['UNKNOWN']
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))

# TODO add a toolbox.exit(), rename toolbox to main
temp_file.close()  # Cleanup temp SQL
exit(exitcode)  # Exit with status