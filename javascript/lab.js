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

const readline = require('readline');

core.Main.version = 'v0.0.5js';

////////////////////////////////////////////////////////////////////////////////
// command-line interface
////////////////////////////////////////////////////////////////////////////////

let exit_command = false;

// readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

// central input loop
const prompt = async () => {
  return new Promise((resolve) => {
    // prompt for auth/session input
    rl.question(core.Session.authenticated ? core.Session.prompt : core.Main.auth_prompt, async (line) => {
      await parse(line);
      resolve(line);
    });
  });
};

const parse = async (line) => {

  function parse_dot_references(match) {
    var dot_ref = match.slice(1);
    var ref_value = core.Session.config[dot_ref] ?? match;
    if (typeof ref_value === 'boolean') {
      ref_value = String(ref_value);
    }
    if (dot_ref == 'password') {
      ref_value = '*'.repeat(ref_value.length);
    }
    return ref_value;
  }

// parse input
  line = line.replace(/\.\w+/g, parse_dot_references);
  var command = line;
  var args = '';
  const m = line.match(/^(\S*)\s(.*)$/);
  if (m) {
    command = m[1];
    args = m[2];
  }

  switch (command) {
    // login
    case 'login':
      var email = '';
      var password = '';
      if ('email' in core.Session.config && 'password' in core.Session.config) {
        email = core.Session.config['email'];
        password = core.Session.config['password'];
      }
      if (email == '') {
        console.log('Email:');
      }
      if (password == '' ) {
        console.log('Password:');
      }
      await backend.sign_in(email, password);
      break;

    // exit
    case 'exit':
      exit_command = true;
      rl.close();
      break;

    // print
    case 'print':
      if (args) {
        console.log(args);
      } else {
        console.log();
      }
      break;

    // logout
    case 'logout':
      backend.sign_out();
      break;

    // undocumented, for development purposes
    case 'debug':
      dev.debug(args);
      break;
    case 'dev':
      await dev.dev(args);
      break;

    // unknown command
    default:
      console.log('?\n   login\n   exit\n   print [text]');
  }
};

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
  
  // handle session closure
  rl.on('close', () => {
    if (!exit_command) {
      console.log();
    }
    session.exit_completely();
  });
  try {
    while (core.Main.running) {
      await prompt();
    }
  } catch (e) {
    core.handle_error('core', e);
  } finally {
    rl.close();
  }
};

// get user input
main().catch(error => console.error(error));
