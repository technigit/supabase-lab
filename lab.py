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

import asyncio
import getpass
import re
import sys

# for interactive up/down arrow history
import readline # pylint: disable=unused-import

import backend
import core
import dev
import session

core.Main.version = 'v0.0.3'

################################################################################
# command-line interface
################################################################################

async def prompt():

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
            await parse(line)

        # error handling
        except EOFError:
            await session.exit_completely(True)
        except KeyboardInterrupt:
            await session.exit_completely(True)
        except Exception as e: # pylint: disable=broad-exception-caught
            core.handle_error('prompt()', e)

        # detect terminated session
        try:
            await core.Session.supabase.auth.get_user()
        except: # pylint: disable=bare-except
            core.Session.authenticated = False

async def parse(line):
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
        await backend.sign_in(email, password)

    # exit
    elif command == 'exit':
        await session.exit_completely()

    # print
    elif command == 'print':
        if args is not None:
            print(args)
        else:
            print()

    # logout
    elif command == 'logout':
        await backend.sign_out()

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

################################################################################
# start here
################################################################################

async def main():

    # get default configuration
    session.get_config(['default.cfg'])

    # check for additional config file specification
    if len(sys.argv) > 1:
        session.get_config(sys.argv[1:])

    core.show_info()

    # the Supabase client module is required
    if backend.supabase_imported():
        await backend.connect()
    else:
        core.info_print('Supabase client for Python is required:  https://github.com/supabase/supabase-py')

    # get user input
    try:
        await prompt()
    except: # pylint: disable=bare-except
        pass

try:
    asyncio.run(main())
except: # pylint: disable=bare-except
    pass
