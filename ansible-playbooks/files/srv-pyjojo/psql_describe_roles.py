#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley
# License Apache Commons v2
# -- jojo --
# description: Retrieve a list of roles.
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


# ******************
# *  SQL SENTENCE  *
# ******************
sql = ("\du")
sql_code = temp_file.write(sql)


# ****************
# *  SQL RUNNER  *
# ****************
output = run.sql(sql_code)
print(output)
print("jojo_return_value execution_status=ok")

temp_file.close()  # Cleanup temp SQL
exit(0)  # Exit with status
