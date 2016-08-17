#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2 
# -- jojo --
# description: Retrieve pg stats connection activity (whos connected)
# http_method: get
# lock: False
# tags: Postgres, PGaaS, cit-ops
# -- jojo --

from common import MkTemp, CmdRun

# Spawn Instances
temp_file = MkTemp()   # <class> Do /tmp/ build/teardown
run = CmdRun()   # <class> Run

# ---------------------------
# --- Define SQL Sentence ---
# This formats the SQL verbs into a complete query sentence.
sql = ("BEGIN; select * from pg_stat_activity; COMMIT;")
sql_code = temp_file.write(sql)

# ---------------
# --- Run SQL ---
output = run.sql(sql_code)
print(output)

# -----------------------
# --- OUTPUT FILTER ---
# Report back intelligible errors to the user.
print("jojo_return_value execution_status=ok")
temp_file.close()  # Cleanup temp SQL
exit(0)  # Exit with status
