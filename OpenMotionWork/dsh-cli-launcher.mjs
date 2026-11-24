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
//
// 本文件不写死任何机器路径（每台电脑安装位置不同）。解析顺序：
//   1. 环境变量 DSH_HARNESS_EXE / DSH_HARNESS_CLI / DSH_HARNESS_DIR
//   2. 同目录下 bootstrap.mjs 生成的 dsh-harness.json
//   3. 都取不到 → 明确报错，绝不猜一个可能存在的路径
import { existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));

function resolveHarness() {
  let fromFile = {};
  const configFile = path.join(here, 'dsh-harness.json');
  if (existsSync(configFile)) {
    try {
      fromFile = JSON.parse(readFileSync(configFile, 'utf8'));
    } catch {
      fromFile = {};
    }
  }
  const dir = process.env.DSH_HARNESS_DIR || fromFile.dir || '';
  const exe = process.env.DSH_HARNESS_EXE || fromFile.exe
    || (dir ? path.join(dir, 'DeepSeek Harness.exe') : '');
  const cli = process.env.DSH_HARNESS_CLI || fromFile.cli
    || (dir ? path.join(dir, 'resources', 'app.asar', 'dsh', 'node_modules',
      '@deepseek-ai', 'dsh-desktop-host', 'lib', 'cli.js') : '');
  return { exe, cli };
}

const { exe, cli } = resolveHarness();

if (!exe || !cli || !existsSync(exe) || !existsSync(cli)) {
  process.stderr.write([
    '找不到 DeepSeek Harness 的 CLI，dsh-cli-launcher.mjs 无法工作。',
    `  exe: ${exe || '(未配置)'}`,
    `  cli: ${cli || '(未配置)'}`,
    '',
    '设置方式（任选其一），然后重试：',
    '  1) 在 OpenMotionWork/ 里执行：',
    '       node ../bootstrap.mjs --rebind --harness "<DeepSeek Harness 安装目录>"',
    '  2) 设置环境变量 DSH_HARNESS_DIR=<DeepSeek Harness 安装目录>',
    '',
    '安装目录指包含 "DeepSeek Harness.exe" 的那一层。',
  ].join('\n') + '\n');
  process.exit(1);
}

const result = spawnSync(exe, ['--expose-internals', cli, ...process.argv.slice(2)], {
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
