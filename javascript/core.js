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

////////////////////////////////////////////////////////////////////////////////
// all primary environment values and functions are accessed here
////////////////////////////////////////////////////////////////////////////////

class Main {
  // get base working directory
  static base_dir = __dirname;

  // general settings
  static auth_prompt = '> ';        // authentication prompt before logging in
  static running = true;            // acceptiong auth/session input
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
}

////////////////////////////////////////////////////////////////////////////////
// output functions
////////////////////////////////////////////////////////////////////////////////

function show_info() {
  var should_show = true;
  if ('suppress_header' in Session.config && Session.config['suppress_header']) {
    should_show = false;
  }
  if (should_show) {
    console.log(`\nSupabase Lab\n${Main.version}\n`);
  }
}

function show_time(date_string) {
    const date = new Date(date_string);
    return date.toLocaleString();
}

function info_print(message) {
  console.log(`<i> ${message}`);
}

function error_print(message) {
  console.log(`<E> ${message}`);
}

function handle_error(message, e, force_verbose = false) {
  console.log(`${message}: ${e.name}: ${e.message}`);
  if (verbose() || force_verbose) {
      console.error(e.stack);
  }
}

function print_item(print_data, indent = '') {
  if (typeof print_data === 'object' && print_data !== null) {
    for (const key in print_data) {
      if (key in print_data) {
        if (key != 'password') {
          console.log(`${indent}${key}: ${print_data[key]}`);
        } else {
          console.log(`${indent}${key}: ${'*'.repeat(print_data[key].length)}`);
        }
      }
    }
  } else if (Array.isArray(print_data)) {
    let i = 0;
    print_data.forEach((item) => {
      console.log(`${indent}${i++}: ${item}`);
    });
  } else {
    print(`${indent}{print_data}`);
  }
}

function verbose() {
  var local_verbose = Main.verbose;
  if ('verbose' in Session.config) {
    local_verbose = Session.config['verbose'];
  }
  return local_verbose;
}

module.exports.Main = Main;
module.exports.Session = Session;
module.exports.show_info = show_info;
module.exports.show_time = show_time;
module.exports.info_print = info_print;
module.exports.error_print = error_print;
module.exports.handle_error = handle_error;
module.exports.print_item = print_item;
module.exports.verbose = verbose;
