#!/usr/bin/env node

////////////////////////////////////////////////////////////////////////////////
//
// Supabase Lab
//
// lab.py - Main processing module
//
// Copyright (c) 2024, 2025 Andy Warmack
// This file is part of Supabase Lab, licensed under the MIT License.
// See the LICENSE file in the project root for more information.
////////////////////////////////////////////////////////////////////////////////

const core = require('./core');
const backend = require('./backend');
const session = require('./session');
const dev = require('./dev');

core.Main.version = 'v0.0.7js';

////////////////////////////////////////////////////////////////////////////////
// command-line interface
////////////////////////////////////////////////////////////////////////////////

let exit_command = false;

const parse = async (line) => {

  function parse_dot_references(match) {
    let dot_ref = match.slice(1);
    let ref_value = core.Session.config[dot_ref] ?? match;
    if (typeof ref_value === 'boolean') {
      ref_value = String(ref_value);
    }
    if (dot_ref == 'password') {
      ref_value = '*'.repeat(ref_value.length);
    }
    return ref_value;
  }

  // prompt for email
  function email_prompt(prompt) {
    return new Promise((resolve) => {
        core.Session.rl.question(prompt, (email) => {
            resolve(email);
        });
    });
  }

  // prompt for password
  function password_prompt(prompt) {
    return new Promise((resolve) => {
        process.stdout.write(prompt);
        const psw = process.stdout.write;
        process.stdout.write = () => {};
        core.Session.rl.question(prompt, (password) => {
            process.stdout.write = psw;
            process.stdout.write('\n');
            resolve(password);
        });
    });
  }

// parse input
  core.Session.current_input = ''; // clear input for next prompt
  line = line.replace(/\.\w+/g, parse_dot_references);
  let command = line;
  let args = '';
  const m = line.match(/^(\S*)\s(.*)$/);
  if (m) {
    command = m[1];
    args = m[2];
  }

  switch (command) {
    // login
    case 'login': {
      let email = '';
      let password = '';
      if ('email' in core.Session.config && 'password' in core.Session.config) {
        email = core.Session.config['email'];
        password = core.Session.config['password'];
      }
      if (email == '') {
        email = await email_prompt('Email: ');
      }
      if (password == '' ) {
        password = await password_prompt('Password: ');
      }
      await backend.sign_in(email, password);
      core.update_prompt();
      break;
    }

    // exit
    case 'exit': {
      exit_command = true;
      core.Session.rl.close();
      break;
    }

    // print
    case 'print': {
      if (args) {
        core.writeln(args);
      } else {
        core.writeln();
      }
      break;
    }

    // logout
    case 'logout': {
      backend.sign_out();
      break;
    }

    // undocumented, for development purposes
    case 'debug': {
      dev.debug(args);
      break;
    }
    case 'dev': {
      await dev.dev(args);
      break;
    }

    // unknown command
    default: {
      core.writeln('?\n   login\n   exit\n   print [text]');
    }
  }
};

////////////////////////////////////////////////////////////////////////////////
// readline processing
////////////////////////////////////////////////////////////////////////////////

// get user input
core.Session.rl.on('line', async (line) => {
  await parse(line);
  core.show_prompt(core.Session.rl);
});

// handle special keys during input
core.Session.rl.input.on('keypress', (char, key) => {
  if (key.name === 'backspace') {
    core.Session.current_input = core.Session.current_input.slice(0, -1);
  } else if (key.ctrl && key.name === 'u') {
    core.Session.current_input = '';
  } else if ((key.name == 'up') || (key.name === 'down')) {
    core.Session.current_input = core.Session.rl.line;
  } else if (char && char.length === 1 && /^[\x20-\x7E]$/.test(char)) {
    core.Session.current_input += char;
  } else if (key.name === 'return') {
    // EOL
  }
});

// handle session closure
core.Session.rl.on('close', () => {
  if (!exit_command) {
    core.writeln();
  }
  session.exit_completely();
});

////////////////////////////////////////////////////////////////////////////////
// start here
////////////////////////////////////////////////////////////////////////////////

const main = async () => {
  
  // get default configuration
  await session.get_config(['default.cfg']);

  // check for additional config file specification
  if (process.argv.length > 2) {
    await session.get_config(process.argv.slice(2));
  }
 
  // show Supabase Lab information
  core.show_info();
  
  // get Supabase connection
  await backend.connect();
};

main();
