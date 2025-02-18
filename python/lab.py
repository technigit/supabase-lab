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

try:
    from prompt_toolkit import PromptSession, Application
    from prompt_toolkit.output import ColorDepth
    from prompt_toolkit.patch_stdout import patch_stdout
    from prompt_toolkit.history import InMemoryHistory
    PROMPT_TOOLKIT_IMPORTED = True
except ImportError:
    PROMPT_TOOLKIT_IMPORTED = False

import backend
import core
import dev
import session

core.Main.version = 'v0.0.7py'

################################################################################
# check for required imports
################################################################################

def prompt_toolkit_imported():
    return PROMPT_TOOLKIT_IMPORTED

################################################################################
# command-line interface
################################################################################

async def prompt():
    # prompt_toolkit setup
    core.Session.prompt_app = Application()
    history = InMemoryHistory()
    input_session = PromptSession(color_depth=ColorDepth.MONOCHROME, history=history)

    # in-place substitutions with config values
    def parse_dot_references(match):
        dot_ref = match.group(0)[1:]
        ref_value = core.Session.config.get(dot_ref, match.group(0))
        if isinstance(ref_value, bool):
            ref_value = str(ref_value)
        if dot_ref == 'password': # don't show passwords in clear text when using the print command
            ref_value = '*' * len(ref_value)
        return ref_value

    # main input loop
    while core.Main.running:
        # prompt for auth/session input
        input_prompt = core.Session.prompt if core.Session.authenticated else core.Main.auth_prompt
        line = await input_session.prompt_async(input_prompt)
        line = re.sub(r'\.\w+', parse_dot_references, line)
        await parse(line)

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

    # nothing
    if command.strip() == '':
        return

    # login
    elif command == 'login':
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
        await dev.dev(args)

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

    # set up initial supabase connection
    await backend.connect()

    # get user input
    try:
        await prompt()
    except EOFError:
        await session.exit_completely()
    except KeyboardInterrupt:
        await session.exit_completely()
    except Exception as e: # pylint: disable=broad-exception-caught
        core.handle_error('prompt()', e)

# get default configuration
session.get_config(['default.cfg'])

# check for additional config file specification
if len(sys.argv) > 1:
    session.get_config(sys.argv[1:])

# show Supabase Lab information
core.show_info()

# check Python dependencies
if backend.supabase_imported() and backend.realtime_imported() and prompt_toolkit_imported():

    # start command-line interface
    with patch_stdout():
        asyncio.run(main())

# provide dependency guidance
else:
    if not backend.supabase_imported():
        core.info_print('The Supabase client for Python is required:  https://github.com/supabase/supabase-py')
    if not backend.realtime_imported():
        core.info_print('The Realtime library is required:  https://github.com/supabase/realtime-py')
    if not prompt_toolkit_imported():
        core.info_print('The Prompt Toolkit library is required:  https://python-prompt-toolkit.readthedocs.io/')
    if not backend.requests_imported():
        core.info_print('The Requests library may be required: https://requests.readthedocs.io/')
