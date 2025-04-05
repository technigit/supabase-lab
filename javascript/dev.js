////////////////////////////////////////////////////////////////////////////////
//
// Supabase Lab
//
// dev.py - Experimental development
//
// Copyright (c) 2024, 2025 Andy Warmack
// This file is part of Supabase Lab, licensed under the MIT License.
// See the LICENSE file in the project root for more information.
////////////////////////////////////////////////////////////////////////////////

const core = require('./core');
const backend = require('./backend');

// non-printable null character for internal parsing
const SPACE_DELIM = '\x00';

// time suffix translation into multipliers
const TIME_SUFFIX_DICT = {'': 1, 's': 1, 'm': 60, 'h': 60 * 60};

// beep controllers for stopping beepers
let beep_controllers = [];

// task monitors for debugging
let task_monitors = {};

////////////////////////////////////////////////////////////////////////////////
// explore supabase object for development purposes
////////////////////////////////////////////////////////////////////////////////

const explore = async () => {
  if (core.Session.authenticated) {
    const { data, error } = await core.Session.supabase.auth.getSession();
    if (error) {
      core.handle_error('dev explore', error);
    } else {
      core.writeln(data);
    }
  } else {
    core.writeln('login?');
  }
};

////////////////////////////////////////////////////////////////////////////////
// parse dev command-line statement
////////////////////////////////////////////////////////////////////////////////

// edge
const edge = async (args) => {
  let pa = parse_args(args);
  if (pa.length == 0) {
    core.writeln('url?');
    return;
  }
  if (pa.length == 1) {
    core.writeln('payload?');
    return;
  }
  let endpoint = pa[0];
  let payload_str = pa[1].replace(SPACE_DELIM, ' ');
  let payload;
  try {
    payload = JSON.parse(payload_str);
  } catch {
    payload = {};
  }
  let url = `${core.Session.config['url']}/functions/v1/${endpoint}`;
  await backend.edge_function(url, payload);
};

// ping
const ping = async (args) => {
  core.writeln(`ping ${args}`);
};

// subscribe to channel
const sub = async (args) => {
  const channel_name = args.trim();
  const channel = await backend.subscribe_channel(channel_name);
  backend.register_channel(channel_name, channel);
};

// unsubscribe from channel
const unsub = async (args) => {
  const channel_name = args.trim();
  await backend.unsubscribe_channel(channel_name);
};

// list channels
const lschan = async () => {
  await backend.list_channels();
};

// listen to broadcast channel
const lchan = async (args) => {
  const arg_strings = parse_args(args);
  const channel_name = arg_strings[0];
  const event = arg_strings.length > 1 ? arg_strings[1] : 'test';
  await backend.listen_to_broadcast_channel(channel_name, event);
};

// send to broadcast channel
const schan = async (args) => {
  const arg_strings = parse_args(args);
  const channel_name = arg_strings[0];
  const event = arg_strings.length > 2 ? arg_strings[1] : 'test';
  const message = arg_strings[arg_strings.length - 1];
  await backend.send_to_broadcast_channel(channel_name, event, message);
};

// sync and track presence state
const tpres = async (args) => {
  const channel_name = args.trim();
  backend.sync_track_presence(channel_name);
};

// send presence state
const spres = async (args) => {
  const channel_name = args.trim();
  backend.send_presence(channel_name);
};

// stop tracking presence state
const stpres = async (args) => {
  const channel_name = args.trim();
  backend.stop_presence(channel_name);
};

// listen to table
const ldb = async (args) => {
  await backend.listen_to_table(args.trim());
};

// beep
function beeping(beep_id, status = null) {
  if (beep_id !== null && status !== null) {
    core.Session.config['beeping'][beep_id] = status;
  } else if (beep_id === null) {
    for (const key in core.Session.config.beeping) {
      if (core.Session.config.beeping.hasOwn(key)) {
        core.Session.config.beeping[key] = false;
      }
    }
  } else {
    status = core.Session.config.beeping[beep_id];
  }
  return status;
}

function start_beeping() {
  if (!('beeping' in core.Session.config)) {
    core.Session.config['beeping'] = {};
  }
  let beep_id = 0;
  while (true) {
    if (!(beep_id in core.Session.config['beeping'])) {
      break;
    }
    beep_id += 1;
  }
  beep_controllers[beep_id] = new AbortController();
  return beep_id;
}

function stop_beeping(beep_id) {
  beeping(beep_id, false);
  if (beep_id in core.Session.config['beeping']) {
    delete core.Session.config['beeping'][beep_id];
  }
  beep_controllers[beep_id].abort();
}

function stop_beeping_all() {
  for (let beep_id in core.Session.config['beeping']) {
    stop_beeping(beep_id);
  }
}

function print_beep(beep_id, beep_seq, beep_message) {
  core.writeln(`\r${beep_id}: beep_seq=${beep_seq} ${beep_message}`);
}

function run_beep(beep_id, beep_message, beep_interval) {
  let task_id = register_task('run_beep');
  set_task_key(task_id, 'beep_id', beep_id);
  set_task_key(task_id, 'beep_message', beep_message);
  set_task_key(task_id, 'beep_interval', beep_interval);
  let beep_seq = 1;
  print_beep(beep_id, beep_seq, beep_message);
  const beeper = setInterval(() => {
    if (beeping(beep_id)) {
      beep_seq++;
      print_beep(beep_id, beep_seq, beep_message);
    } else {
      clearInterval(beeper);
      deregister_task(task_id);
    }
  }, beep_interval * 1000);

  // listen for abort signal
  beep_controllers[beep_id].signal.addEventListener('abort', () => {
    clearInterval(beeper);
    deregister_task(task_id);
  });
}

function beep_sleep(beep_id, beep_duration) {
  let task_id = register_task('beep_sleep');
  set_task_key(task_id, 'beep_id', beep_id);
  set_task_key(task_id, 'beep_duration', beep_duration);
  return new Promise((resolve) => {
    const timeoutId = setTimeout(() => {
      resolve();
      deregister_task(task_id);
    }, beep_duration * 1000);

    // Listen for abort events
    beep_controllers[beep_id].signal.addEventListener('abort', () => {
      clearTimeout(timeoutId);
      deregister_task(task_id);
    });
  });
}

const beep = async (args) => {
  // check for beep stop
  args = args.trim();
  let m;
  m = args.match(/^stop (\d*)$/);
  if (m != null) {
    let beep_id = parseInt(m[1]);
    stop_beeping(beep_id);
    return;
  }
  if (args == 'stop') {
    stop_beeping_all();
    return;
  }

  // get beep parameters
  let beep_id = start_beeping();
  beeping(beep_id, true);
  let beep_interval = '1';
  let beep_duration = '10';
  let beep_message = 'beep';
  let float_regex = '(\\d+(\\.\\d+)?|\\.\\d+)'; // match an int string or a float string
  let time_suffix_regex = '[smhSMH]?';
  m = args.match(`^(${float_regex}${time_suffix_regex})\\s+(${float_regex}${time_suffix_regex})\\s+(\\S.*)$`);
  if (m != null) {
    beep_interval = m[1];
    beep_duration = m[4];
    beep_message = m[7];
  } else {
    m = args.match(`^(${float_regex}${time_suffix_regex})\\s+(${float_regex}${time_suffix_regex})$`);
    if (m != null) {
      beep_interval = m[1];
      beep_duration = m[4];
    } else {
      m = args.match(`^(${float_regex}${time_suffix_regex})\\s+([^\\d\\s].*)$`);
      if (m != null) {
        beep_interval = m[1];
        beep_message = m[4];
      } else {
        m = args.match(`^(${float_regex}${time_suffix_regex})$`);
        if (m != null) {
          beep_interval = m[1];
        }
      }
    }
  }

  // parse beep time suffixes
  m = beep_interval.match(`^(\\d*)(${time_suffix_regex})$`);
  let time_suffix;
  if (m != null) {
    time_suffix = m[2];
    beep_interval = parseFloat(m[1]) * TIME_SUFFIX_DICT[time_suffix];
  }
  m = beep_duration.match(`^(\\d*)(${time_suffix_regex})$`);
  if (m != null) {
    time_suffix = m[2];
    beep_duration = parseFloat(m[1]) * TIME_SUFFIX_DICT[time_suffix];
  }

  // start beeping
  run_beep(beep_id, beep_message, beep_interval);
  
  // sleep while beeping
  if (beeping(beep_id)) {
    await beep_sleep(beep_id, beep_duration);
    stop_beeping(beep_id);
  }
};

// dev
const dev = async (args) => {
  if (args == '') {
    core.writeln('dev?');
    core.writeln('   explore [args]');
    core.writeln('   ping [args]');
    return;
  }
  let experiment = '';
  const m = args.match(/(\S*)(.*)$/);
  if (m) {
    experiment = m[1];
    args = m[2];
  }
  if (experiment == 'explore') {
    await explore(args);
  } else if (experiment == 'beep') {
    await beep(args);
  } else if (experiment == 'edge') {
    await edge(args);
  } else if (experiment == 'subscribe' || experiment == 'sub') {
    await sub(args);
  } else if (experiment == 'unsubscribe' || experiment == 'unsub') {
    await unsub(args);
  } else if (experiment == 'listchannels' || experiment == 'lschan') {
    await lschan();
  } else if (experiment == 'listenchan' || experiment == 'lchan') {
    await lchan(args);
  } else if (experiment == 'sendchan' || experiment == 'schan') {
    await schan(args);
  } else if (experiment == 'trackpresence' || experiment == 'tpres') {
    await tpres(args);
  } else if (experiment == 'sendpresence' || experiment == 'spres') {
    await spres(args);
  } else if (experiment == 'stoptrackpresence' || experiment == 'stpres') {
    await stpres(args);
  } else if (experiment == 'listendb' || experiment == 'ldb') {
    await ldb(args);
  } else if (experiment == 'ping') {
    await ping(args);
  } else {
    core.writeln(`${experiment}?`);
  }
};

// parse_args
function parse_args(args) {
  if (args == '') {
    return '';
  }
  const regex = /(?:[^\s"']+|"([^"]*)"|'([^']*)')+/g;
  const matches = args.match(regex);
  if (!matches) {
    return args.split(' ');
  } else {
    return matches.map(match => {
      return match.replace(/^['"]|['"]$/g, '');
    });
  }
}

////////////////////////////////////////////////////////////////////////////////
// task monitoring for debugging purposes
////////////////////////////////////////////////////////////////////////////////

function new_task_id() {
  if (typeof core.next_task_id === 'undefined') {
    core.next_task_id = 0;
  } else {
    core.next_task_id++;
  }
  return core.next_task_id;
}

function register_task(name) {
  let task_id = new_task_id();
  let task_monitor = {
    'name': name,
  };
  task_monitors[task_id] = task_monitor;
  return task_id;
}

function set_task_key(task_id, key, value) {
  let task_monitor = task_monitors[task_id];
  task_monitor[key] = value;
}

function show_tasks() {
  for (let key in task_monitors) {
    show_task(key);
  }
}

function show_task(task_id) {
  let task_monitor = task_monitors[task_id];
  core.writeln(`  ${task_id}:`);
  for (let key in task_monitor) {
    core.writeln(`    ${key}: ${task_monitor[key]}`);
  }
}

function deregister_task(name) {
  delete task_monitors[name];
}

////////////////////////////////////////////////////////////////////////////////
// debug function to inspect important values
////////////////////////////////////////////////////////////////////////////////

function debug(args) {
  if (args == null) {
    args = '';
  }
  let filter_list = args.trim() ? args.split(' ') : [];
  let no_filters = filter_list.length == 0;
  if (filter_list.includes('url') || no_filters) {
    core.writeln(`url = ${core.Session.url}`);
  }
  if (filter_list.includes('api_key') || no_filters) {
    core.writeln(`api_key = ${'api_key' in core.Session.config ? core.Session.config['api_key'] : null}`);
  }
  if (filter_list.includes('email') || no_filters) {
    core.writeln(`email = ${'email' in core.Session.config ? core.Session.config['email'] : null}`);
  }
  if (filter_list.includes('jwt_token') || filter_list.includes('jwt') || no_filters) {
    core.writeln(`jwt_token = ${core.Session.jwt_token}`);
  }
  if (filter_list.includes('authenticated') || no_filters) {
    core.writeln(`authenticated = ${core.Session.authenticated}`);
  }
  if (filter_list.includes('config') || no_filters) {
    core.writeln('config:');
    core.print_item(core.Session.config, '   ');
  }
  if (filter_list.includes('tasks')) {
    core.writeln('Tasks:');
    show_tasks();
  }
}

module.exports.dev = dev;
module.exports.explore = explore;
module.exports.debug = debug;
