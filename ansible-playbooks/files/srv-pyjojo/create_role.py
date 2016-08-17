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
from common import ToolKit, Constants, ParamHandle, ParamHandle2

# Spawn Instances
parameter     = ParamHandle()    # <class> Parameter manipulation
parameter2    = ParamHandle2()   # <class> Parameter manipulation
real_escape_string = Sanitize()  # <class> Escape Routines
toolkit       = ToolKit()        # <class> Misc. functions
environment   = Environment()    # <class> Manages Env Vars
temp_file     = MkTemp()         # <class> Do /tmp/ build/teardown
input_params  = parameter.get()  # <dict>  Input params
run           = CmdRun()         # <class> Runs the query


# -------------------------
# --- Bounds Validation ---
# These are parameters that only have a bound restriction.  The 
#  request will fail citing the maximum str length if it matches.
p = params["ROLE"]
role = ParamHandle2()
role.define(p)
role.max_length     = Constants.POSTGRES_NAMEDATA_LEN
role.require        = True
arg_role = role.get()


p = params["PASSWORD"]
password = ParamHandle2()
password.input          = p
password.max_length     = Constants.POSTGRES_NAMEDATA_LEN
password.require        = True
arg_pass = password.get()

# -----------------------
# --- Parameter Logic ---
# Parse user input to make query verbs.
#
# These are mainly booleans, the user should input a true/false 1/0
# but the user may also leave the items undefined to have a default
# assumed.
#
# The value gets evaluated and set in arg_<valuename>'s
# class XClass( object ):
#    def __init__( self ):
#        self.myAttr= None

# x= XClass()
# x.myAttr= 'magic'
# x.myAttr

p = params["CREATEROLE"]
when_true  = " {verb} ".format(verb=p)
when_false = " NO{verb} ".format(verb=p)
when_undef = " NO{verb} ".format(verb=p)

createrole = ParamHandle2()
createrole.require  = False
createrole.value = p
param_createrole = createrole.is_true(
    when_true=when_true,
    when_false=when_false,
    when_undef=when_undef
    )

p = params["CREATEUSER"]
createuser = ParamHandle2()
createuser.input          = p
createuser.require        = False
createuser.when_true      = " {verb} ".format(verb=p)
createuser.when_false     = " NO{verb} ".format(verb=p)
createuser.when_undefined = " NO{verb} ".format(verb=p)
arg_createuser = createuser.is_true()

p = params["CREATEDB"]
createdb = ParamHandle2()
createdb.input          = p
createdb.require        = False
createdb.when_true      = " {verb} ".format(verb=p)
createdb.when_false     = " NO{verb} ".format(verb=p)
createdb.when_undefined = " NO{verb} ".format(verb=p)
arg_creatdb = createdb.is_true()

p = params["INHERIT"]
inherit = ParamHandle2()
inherit.input          = p
inherit.require        = False
inherit.when_true      = " {verb} ".format(verb=p)
inherit.when_false     = " NO{verb} ".format(verb=p)
inherit.when_undefined = " NO{verb} ".format(verb=p)
arg_inherit = inherit.is_true()

p = params["LOGIN"]
inherit = ParamHandle2()
inherit.input          = p
inherit.require        = False
inherit.when_true      = " {verb} ".format(verb=p)
inherit.when_false     = " NO{verb} ".format(verb=p)
inherit.when_undefined = " NO{verb} ".format(verb=p)
arg_inherit = inherit.is_true()

p = params["ENCRYPTED"]
inherit = ParamHandle2()
inherit.input          = p
inherit.require        = False
inherit.when_true      = " {verb} ".format(verb=p)
inherit.when_false     = " UN{verb} ".format(verb=p)
inherit.when_undefined = " UN{verb} ".format(verb=p)
arg_inherit = inherit.is_true()

p = params["ROLENAME"]
rolename = ParamHandle2()
rolename.input          = p
rolename.require        = False
rolename.when_true      = ""
rolename.when_false     = " IN ROLE {rolename} ".format(rolename=p)
arg_rolename = rolename.is_none()

p = params["GROUPNAME"]
groupname = ParamHandle2()
groupname.input          = p
groupname.require        = False
groupname.when_true      = ""
groupname.when_false     = " IN GROUP {groupname} ".format(groupname=p)
arg_groupname = groupname.is_none()

p = params["CONNECTION_LIMIT"]
connect_limit = ParamHandle2()
connect_limit.input        = p
arg_socketlimit = connect_limit.get()

p = params["CONNECTION_LIMIT_BUST"]
connect_limit_bust = ParamHandle2()
connect_limit_bust.input        = p
arg_socketbust = connect_limit_bust.get()

if connect_limit.is_none():
    # If no input, we plan on just setting 10 sockets.
    connection_limit = 10
elif not arg_socketbust.is_none():
    # Limit busting has been toggled
    if int(arg_socketlimit) > Constants.POSTGRES_MAXIMUM_CONNECTION_LIMIT:
        # If the proposed limit is not beyond the POSTGRES_MAXIMUM_CONNECTION_LIMIT, stop
        # We expect a smaller value.
        msg = "value <{max}".format(
            max=Constants.POSTGRES_MAXIMUM_CONNECTION_LIMIT)
        parameter.raise_error(
            keyname='CONNECTION_LIMIT',
            value=arg_socketlimit,
            expected_msg=msg
        )
    # Set the busted limit
    connection_limit = arg_socketlimit
else:
    # User-submitted connection limit (no limit busting)
    if int(arg_socketlimit) > Constants.POSTGRES_CONNECTION_LIMIT:
        # If the proposed limit is beyond the POSTGRES_CONNECTION_LIMIT, stop
        # We expect a smaller value.
        msg = "value <{max}".format(max=Constants.POSTGRES_CONNECTION_LIMIT)
        parameter.raise_error(
            keyname='CONNECTION_LIMIT',
            value=arg_socketlimit,
            expected_msg=msg
        )
    # Set the requested limit
    connection_limit = arg_socketlimit
arg_connlimit = " CONNECTION LIMIT {max} ".format(max=connection_limit)

# ---------------------------
# --- Define SQL Sentence ---
# This strings together the verbs in the section above
#  and string sanitizes a query.

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
temp_file.close()  # Clean open filehandles
exit(exitcode)  # Exit with status
