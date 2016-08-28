#!/bin/python
# -*- coding: utf-8 -*-
# Copyright 2016, Jonathan Kelley  
# License Apache Commons v2
# -- jojo --
# description: A proof of concept that can trigger an ansible playbook called package_version.yml to get info about a specific package version
# param: package - The package to retrieve the information about
# http_method: post
# lock: False
# -- jojo --

from common import CmdRun, Constants, ParamHandle2
import json

# Spawn Instances
parameter2  = ParamHandle2()    # <class> Parameter manipulation
run         = CmdRun()          # <class> Runs the query
params      = parameter2.list() # <dict>  A dict of params 



# ************************************
# *  DEFINE PARAMETERS AND VALIDATE  *
# ************************************
arguement = {}

define_param       = "PACKAGE"
p                  = ParamHandle2()
p.value            = params[define_param]
p.name             = define_param
p.require          = True
p.max_length       = Constants.LINUX_MAX_FILE_NAME_LENGTH
arguement[define_param] = {'package': p.get()} # Define as extra-vars dict item


# ****************************
# *  DEFINE ANSIBLE OPTIONS  *
# ****************************
# This will be used to define the argv keyvalue pairs passed to ansible.
# Special (non arguements) include:
#  - ansible_opts['playbook'] which is the path to the playbook file
#  - ansible_opts['append_args'] which value should include any appendable arg like -vvvv
ansible_opts = {}

ansible_opts['playbook']            = '/opt/playbooks/ansible-playbooks/package_version.yml'
ansible_opts['append_args']         = '-v'
ansible_opts['--limit']             = '\"vagrant\"'
ansible_opts['--inventory-file']    = '/opt/playbooks/ansible-hosts'
ansible_opts['--user']              = 'vagrant'
ansible_opts['--extra-vars']        = json.dumps(arguement['PACKAGE'])


# *****************
# *  RUN ANSIBLE  *
# *****************
output = run.ansible(ansible_opts)


# *************
# *  RESULTS  *
# *************
print(output)
exit(0)