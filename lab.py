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

import backend
import core
import dev
import session

core.Main.version = 'v0.0.2'

################################################################################
# command-line interface
################################################################################

def prompt():

    def parse_dot_references(match):
        dot_ref = match.group(0)[1:]
        ref_value = core.Session.config.get(dot_ref, match.group(0))
        if isinstance(ref_value, bool):
            ref_value = str(ref_value)
        if dot_ref == 'password': # don't show passwords in clear text when using the print command
            ref_value = '*' * len(ref_value)
        return ref_value

    while core.Main.running:
        try:
            # prompt for auth/session input
            line = input(core.Session.prompt if core.Session.authenticated else core.Main.auth_prompt)
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
                email = ''
                password = ''
                if 'email' in core.Session.config and 'password' in core.Session.config:
                    email = core.Session.config['email']
                    password = core.Session.config['password']
                if email == '':
                    print('Email: ', end='')
                    email = input()
                if password == '':
                    password = getpass.getpass('Password: ')
                backend.sign_in(email, password)

            # exit
            elif command == 'exit':
                session.exit_completely()

            # print
            elif command == 'print':
                if args is not None:
                    print(args)
                else:
                    print()
            elif command == 'logout':
                backend.sign_out()

            # undocumented, for development purposes
            elif command == 'debug':
                dev.debug(args)
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
            session.exit_completely(True)
        except KeyboardInterrupt:
            session.exit_completely(True)
        except Exception as e: # pylint: disable=broad-exception-caught
            core.handle_error('prompt()', e)

        # detect terminated session
        try:
            core.Session.supabase.auth.get_user()
        except: # pylint: disable=bare-except
            core.Session.authenticated = False

################################################################################
# start here
################################################################################

# get default configuration
session.get_config(['default.cfg'])

# check for additional config file specification
if len(sys.argv) > 1:
    session.get_config(sys.argv[1:])

core.show_info()

# the supabase client module is required
if backend.supabase_imported():
    backend.connect()
else:
    core.info_print('Supabase client for Python is required:  https://github.com/supabase/supabase-py')

# get user input
prompt()
