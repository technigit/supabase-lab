#!/usr/bin/env python3

################################################################################
#
# Supabase Lab
#
# session.py - Session functions
#
# Copyright (c) 2024, 2025 Andy Warmack
# This file is part of Supabase Lab, licensed under the MIT License.
# See the LICENSE file in the project root for more information.
################################################################################

import fileinput
import re

import backend
import core

# non-printable null character for internal parsing
SPACE_DELIM = '\x00'


################################################################################
# get session configuration values
################################################################################

def get_config(config_files):
    # read values from a config file, superceding default values
    try:
        with fileinput.FileInput(files=(f"{core.Main.base_dir}/{core.Session.config_dir}/{f}" for f in config_files), mode='r') as lines:
            for line in lines:
                line = line.strip()
                if line.startswith('#') or line == '':
                    continue
                if line != '\n':
                    m = re.match(r'^(\S*)\s*=\s*(.*)$', line)
                    if m is None:
                        m = re.match(r'^(\S*)\s*=()$', line)
                        if m is None:
                            m = re.match(r'^(\S*)\s*=(\{.*\})$', line)
                    if m is not None:
                        key = m.group(1)
                        value = re.sub(r'\{([^}]*)\}', lambda m: '{' + m.group(1).replace(' ', SPACE_DELIM) + '}', m.group(2))
                        if value.lower() in ['t', 'true', 'y', '1']:
                            value = True
                        elif value.lower() in ['f', 'false', 'n', '0']:
                            value = False
                        if m is not None:
                            core.Session.config[key] = value
                    else:
                        print(f"{line}?")
    except FileNotFoundError as e:
        core.error_print(str(e))
    except IsADirectoryError as e:
        core.error_print(str(e))
    except Exception as e: # pylint: disable=broad-exception-caught
        core.handle_error('get_config()', e, True)

################################################################################
# close the current session and exit the program
################################################################################

async def exit_completely(cr = False):
    if cr:
        print('\r')
    if core.Session.authenticated:
        await backend.sign_out()
    print('Bye.')
    core.Main.running = False
