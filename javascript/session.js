////////////////////////////////////////////////////////////////////////////////
//
// Supabase Lab
//
// session.py - Session functions
//
// Copyright (c) 2024, 2025 Andy Warmack
// This file is part of Supabase Lab, licensed under the MIT License.
// See the LICENSE file in the project root for more information.
////////////////////////////////////////////////////////////////////////////////

const fs = require('fs');

const core = require('./core');
const backend = require('./backend');

const SPACE_DELIM = '\x00';

////////////////////////////////////////////////////////////////////////////////
// get session configuration values
////////////////////////////////////////////////////////////////////////////////

async function get_config(configFiles) {
  for (const file of configFiles) {
    const filePath = core.Main.base_dir + '/' + core.Session.config_dir + '/' + file;

    try {
      const data = await fs.promises.readFile(filePath, 'utf-8');
      const lines = data.split('\n'); // Split the file content into lines

      for (const line of lines) {
        if (line.startsWith('#') || line == '') {
          continue;
        }
        let key = null;
        let value = null;
        let m = line.match(/^(\S*)\s*=\s*(.*)$/);
        if (!m) {
          m = line.match(/^(\S*)\s*=()$/);
          if (!m) {
            m = line.match(/'^(\S*)\s*=(\{.*\})$/);
          }
        }
        if (m) {
          key = m[1];
          value = m[2].replace(/\{([^}]*)\}/g, (match, p1) => {
            return '{' + p1.replace(/ /g, SPACE_DELIM) + '}';
          });
          if (['t', 'true', 'y', '1'].includes(value.toLowerCase())) {
            value = true;
          } else if (['f', 'false', 'n', '0'].includes(value.toLowerCase())) {
            value = false;
          }
          if (m) {
            core.Session.config[key] = value;
          }
        } else {
          core.writeln(`${line}?`);
        }
      }
    } catch (error) {
      if (error.code === 'ENOENT') {
        core.error_print(`File not found: ${file}`);
      } else {
        console.error(`Error reading file ${file}:`, error);
      }
    }
  }
}

async function exit_completely() {
  if (core.Session.authenticated) {
    backend.sign_out();
  }
  core.writeln('Bye.');
  process.exit(0);
}

module.exports.get_config = get_config;
module.exports.exit_completely = exit_completely;
