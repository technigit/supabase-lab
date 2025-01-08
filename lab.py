#!/usr/bin/env python3

################################################################################
#
# Supabase Lab
#
# lab.py - Main processing module
#
# Copyright (c) 2024, 2025 Andy Warmack
# This file is part of Supabase Lab, licensed under the MIT License.
# See the LICENSE file in the project root for more information.
################################################################################

import getpass
import re
import sys

import core
import dev

core.Main.version = 'v0.0.1'

################################################################################
# command-line interface
################################################################################

def prompt():

    def parse_dot_references(match):
        dot_ref = match.group(0)[1:]
        ref_value = core.Main.config.get(dot_ref, match.group(0))
        if isinstance(ref_value, bool):
            ref_value = str(ref_value)
        if dot_ref == 'password':
            ref_value = '*' * len(ref_value)
        return ref_value

    while core.Main.running:
        try:
            # prompt for auth/session input
            line = input(core.Main.session_prompt if core.Main.session_active else core.Main.auth_prompt)
            line = re.sub(r'\.\w+', parse_dot_references, line)

            # parse input
            command = line
            args = None
            m = re.search(r'^(\S*)\s(.*)$', line)
            if m is not None:
                command = m.group(1)
                args = m.group(2)

            # login
            if command == 'login':
                email = core.Main.email
                password = core.Main.password
                if 'email' in core.Main.config and 'password' in core.Main.config:
                    email = core.Main.config['email']
                    password = core.Main.config['password']
                if email == "":
                    print('Email: ', end='')
                    email = input()
                if password == '':
                    password = getpass.getpass('Password: ')
                core.sign_in(email, password)

            # exit
            elif command == 'exit':
                core.exit_completely()

            # print
            elif command == 'print':
                if args is not None:
                    print(args)
                else:
                    print()
            elif command == 'logout':
                core.sign_out()

            # undocumented, for development purposes
            elif command == 'debug':
                core.debug(args)
            elif command == 'dev':
                dev.dev(args)

            # unknown command
            else:
                print(f"{command}?")
                print('   login')
                print('   exit')
                print('   print [text]')

        # error handling
        except EOFError:
            core.exit_completely(True)
        except KeyboardInterrupt:
            core.exit_completely(True)
        except Exception as e: # pylint: disable=broad-exception-caught
            core.handle_error('prompt()', e)

        # detect terminated session
        try:
            core.Main.supabase.auth.get_user()
        except: # pylint: disable=bare-except
            core.Main.session_active = False

################################################################################
# start here
################################################################################

# get default configuration
core.get_config(['default.cfg'])

# check for additional config file specification
if len(sys.argv) > 1:
    core.get_config(sys.argv[1:])

core.show_info()

# the supabase client module is required
if core.supabase_imported():
    core.connect()
else:
    core.info_print('Supabase client for Python is required:  https://github.com/supabase/supabase-py')

# get user input
prompt()
