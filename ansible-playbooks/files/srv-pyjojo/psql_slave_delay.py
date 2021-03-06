#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley
# License Apache Commons v2
# -- jojo --
# description: Show slave delay
# http_method: get
# lock: False
# tags: Postgres, Psql
# -- jojo --

from os import linesep
from common import CmdRun, ToolKit
import re

# Spawn Instances
run = CmdRun()        # <class> Run
toolkit = ToolKit()  # <class> Misc. functions


# ******************
# *  SQL SENTENCE  *
# ******************
sql = ("SELECT now() - pg_last_xact_replay_timestamp() AS time_lag;")
sql_code = toolkit.write_temp(sql)


# ****************
# *  SQL RUNNER  *
# ****************
query_result = run.sql(sql_code)


# **********************
# *  OUTPUT PROCESSOR  *
# **********************
print(query_result)
exitcode = 0  # We good
error_scenario_1 = False
error_scenario_2 = False
error_scenario_3 = False
delay = "-NaN"

# Match the format of  -00:00:00.000549
#   or   00:00:00.346472
regexp = re.compile(r'^ [- ]?(\d{2}):(\d{2}):(\d{2})\.(\d+)$')

for line in query_result.split(linesep):
    if regexp.search(line) is not None:
        delay = line.lstrip()

    if ("psql:/tmp/" in line) and (" ERROR:  " in line):
        toolkit.print_stderr(line)
        error_scenario_1 = True
        exitcode = 1  # Parse Errors should flag an API error code.
    if " FATAL: " in line:
        toolkit.print_stderr(line)
        error_scenario_2 = True
        exitcode = 1  # Parse Errors should flag an API error code.

if delay != "-NaN":
    secs = delay.split(':')[2]
    msecs = "0.{msec}".format(msec=secs.split(".")[1])
    hours = delay.split(':')[0]
    mins = delay.split(':')[1]
    delay_sum_seconds = float(secs.split(
        ".")[0]) + (float(hours) * 3600) + (float(mins) * 60) + float(msecs)
else:
    exitcode = 1
    error_scenario_3 = True
    secs = delay
    hours = delay
    mins = delay
    delay_sum_seconds = delay

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
    if error_scenario_3:
        error_hint.append('REPLICA_DELAY_SELECT_WAS_EMPTY')
    if len(error_hint) == 0:
        error_hint = ['UNKNOWN']
    print("jojo_return_value execution_status=rollback")
    print("jojo_return_value error_reason_indicator={error}".format(
        error=error_hint))

print("jojo_return_value slave_delay={ts}".format(ts=delay))
print("jojo_return_value slave_delta_in_seconds={ts}".format(
    ts=delay_sum_seconds))

toolkit.exit(exitcode)
