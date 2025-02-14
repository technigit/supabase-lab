////////////////////////////////////////////////////////////////////////////////
//
// Supabase Lab
//
// core.py - Core variables and functions
//
// Copyright (c) 2024, 2025 Andy Warmack
// This file is part of Supabase Lab, licensed under the MIT License.
// See the LICENSE file in the project root for more information.
////////////////////////////////////////////////////////////////////////////////

const readline = require('readline');

// clear text to the end of the line for asynchronous messages
const ANSI_ERASE_LINE = '\x1b[K';

////////////////////////////////////////////////////////////////////////////////
// all primary environment values and functions are accessed here
////////////////////////////////////////////////////////////////////////////////

class Main {
  // get base working directory
  static base_dir = __dirname;

  // general settings
  static auth_prompt = '> ';        // authentication prompt before logging in
  static verbose = false;           // extra output for debugging
  static version = '';              // version set from lab.js
}

////////////////////////////////////////////////////////////////////////////////
// all session values are accessed here
////////////////////////////////////////////////////////////////////////////////

class Session {
  // default url
  static url = 'http://127.0.0.1:54321';

  // user credentials
  static jwt_token = null;

  // session settings
  static authenticated = false;     // authentication status
  static config = {};               // configuration values
  static config_dir = '../config';  // default config directory
  static prompt = '>> ';            // session prompt after logging in
  static supabase = null;           // Supabase connection object
  static current_input = '';        // asynchronous input line buffer
  
  // user input handler
  static rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: true,
  });
}

////////////////////////////////////////////////////////////////////////////////
// output functions
////////////////////////////////////////////////////////////////////////////////

function writeln(content) {
  if (typeof content === 'undefined') {
    console.log();
  } else {
    if (typeof content === 'object' && content !== null) {
      content = JSON.stringify(content);
    }
    console.log(`\r${content}${ANSI_ERASE_LINE}`);
    process.stdout.write(`\r${get_prompt()}${Session.current_input}`);
  }
}

function get_prompt() {
  return Session.authenticated ? Session.prompt : Main.auth_prompt;
}

function show_prompt(rl) {
  Session.current_input = '';
  rl.setPrompt(get_prompt());
  rl.prompt();
}

function update_prompt() {
  Session.rl.setPrompt(get_prompt());
}

function show_info() {
  let should_show = true;
  if ('suppress_header' in Session.config && Session.config['suppress_header']) {
    should_show = false;
  }
  if (should_show) {
    writeln(`${ANSI_ERASE_LINE}\nSupabase Lab\n${Main.version}\n`);
  }
}

function show_time(date_string) {
    const date = new Date(date_string);
    return date.toLocaleString();
}

function info_print(message) {
  writeln(`<i> ${message}`);
}

function error_print(message) {
  writeln(`<E> ${message}`);
}

function handle_error(message, e, force_verbose = false) {
  writeln(`${message}: ${e.name}: ${e.message}`);
  if (verbose() || force_verbose) {
    console.error(e.stack);
  }
}

function print_item(print_data, indent = '') {
  if (typeof print_data === 'object' && print_data !== null) {
    for (const key in print_data) {
      if (key in print_data) {
        let key_element = print_data[key];
        if (key != 'password') {
          if (typeof key_element === 'object') {
            key_element = '{' + Object.entries(key_element).map(([key, value]) => `${key}: ${value}`).join(', ') + '}';
          }
          writeln(`${indent}${key}: ${key_element}`);
        } else {
          writeln(`${indent}${key}: ${'*'.repeat(key_element.length)}`);
        }
      }
    }
  } else if (Array.isArray(print_data)) {
    let i = 0;
    print_data.forEach((item) => {
      writeln(`${indent}${i++}: ${item}`);
    });
  } else {
    writeln(`${indent}{print_data}`);
  }
}

function verbose() {
  let local_verbose = Main.verbose;
  if ('verbose' in Session.config) {
    local_verbose = Session.config['verbose'];
  }
  return local_verbose;
}

module.exports.Main = Main;
module.exports.Session = Session;
module.exports.writeln = writeln;
module.exports.get_prompt = get_prompt;
module.exports.show_prompt = show_prompt;
module.exports.update_prompt = update_prompt;
module.exports.show_info = show_info;
module.exports.show_time = show_time;
module.exports.info_print = info_print;
module.exports.error_print = error_print;
module.exports.handle_error = handle_error;
module.exports.print_item = print_item;
module.exports.verbose = verbose;
