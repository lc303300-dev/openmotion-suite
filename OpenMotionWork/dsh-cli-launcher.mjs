#!/usr/bin/env node
// Launcher adapter for the OpenMotion installer.
//
// Why this exists:
// OpenMotion's `scripts/npm-hosts.mjs` -> resolveHostCommand() treats a plain
// `.exe` as directly executable (`{ command: file, args: [] }`). The DeepSeek
// Harness desktop build is an Electron binary, so running
//   "DeepSeek Harness.exe" plugin --profile desktop add ...
// makes Electron try to `require('plugin')` and crash with MODULE_NOT_FOUND.
//
// resolveHostCommand()'s first rule is: a path ending in .js/.mjs/.cjs is run
// with the current node (`{ command: process.execPath, args: [file] }`).
// So the installer is pointed at this file instead, and we forward argv to the
// real host CLI the same way the bundled dsh.cmd shim does.
import { spawnSync } from 'node:child_process';

const HOST_EXE = 'F:\\LiuCan\\AI\\DSH\\DeepSeek Harness\\DeepSeek Harness.exe';
const HOST_CLI = 'F:\\LiuCan\\AI\\DSH\\DeepSeek Harness\\resources\\app.asar\\dsh\\node_modules\\@deepseek-ai\\dsh-desktop-host\\lib\\cli.js';

const result = spawnSync(HOST_EXE, ['--expose-internals', HOST_CLI, ...process.argv.slice(2)], {
  encoding: 'utf8',
  windowsHide: true,
  env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' },
});

if (result.error) {
  process.stderr.write(String(result.error) + '\n');
  process.exit(1);
}
if (result.stdout) process.stdout.write(result.stdout);
if (result.stderr) process.stderr.write(result.stderr);
process.exit(result.status ?? 1);
