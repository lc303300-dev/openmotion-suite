#!/usr/bin/env node
// OpenMotion Suite bootstrap — 让新机器上的 OpenMotionWork 能自己把「npm 单机形态 0.2.1」弄起来。
//
// 背景（为什么需要它）：
//   1. .openmotion-home/install.json 存的是绝对路径，整目录复制到新机器后全部失效；
//   2. .openmotion-home/run-mcp.mjs 直接 import(install.json.appRoot)，没有任何自举逻辑；
//   3. openmotion@0.2.1 不在 npm 上（E404），官方只提供 GitHub tag v0.2.1 源码；
//   4. docs/install.md 明确写着 "This is not an offline package."。
//
// 两种模式：
//   node bootstrap.mjs --rebind              已有 .openmotion-home（从旧机器拷来）→ 重写绝对路径，秒级
//   node bootstrap.mjs                       没有运行时 → 从 tag 构建 npm 包 → setup → prepare（慢，需网络）
//
// 常用参数：
//   --home DIR        安装目录，默认 <脚本目录>/OpenMotionWork/.openmotion-home
//   --data-dir DIR    工程数据目录，默认 <home 的父目录>/data
//   --tag v0.2.1      要构建的上游 tag
//   --tgz FILE        已构建好的 tgz，跳过 clone/build
//   --dsh FILE        传给 setup 的 --dsh（Harness 可执行文件或 launcher .mjs）
//   --profile NAME    Harness profile，默认 desktop
//   --harness DIR     DeepSeek Harness 安装目录（用于重写 dsh-cli-launcher.mjs）
//   --dry-run         只打印计划，不落盘
//   --force           允许覆盖已有 install.json（会先备份）

import { readFile, writeFile, readdir, stat, mkdtemp, rm, copyFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import os from 'node:os';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const REPO = 'https://github.com/nexu-io/openmotion.git';

// 默认装到「当前窗口的工作区根」：在 openmotion-suite/ 下跑就找 OpenMotionWork/，
// 在 OpenMotionWork/ 里跑就直接用当前目录，别的一律回落到脚本同级的 OpenMotionWork/。
function defaultWorkspace() {
  const cwd = process.cwd();
  if (existsSync(path.join(cwd, 'OpenMotionWork'))) return path.join(cwd, 'OpenMotionWork');
  if (path.basename(cwd) === 'OpenMotionWork') return cwd;
  return path.join(scriptDir, 'OpenMotionWork');
}

function parseArgs(argv) {
  const opts = {
    home: path.join(defaultWorkspace(), '.openmotion-home'),
    dataDir: null,
    tag: 'v0.2.1',
    tgz: null,
    dsh: null,
    profile: 'desktop',
    harness: null,
    rebind: false,
    dryRun: false,
    force: false,
    node: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const next = () => {
      const value = argv[++i];
      if (!value || value.startsWith('--')) throw new Error(`${arg} 需要一个值`);
      return value;
    };
    switch (arg) {
      case '--home': opts.home = next(); break;
      case '--data-dir': opts.dataDir = next(); break;
      case '--tag': opts.tag = next(); break;
      case '--tgz': opts.tgz = next(); break;
      case '--dsh': opts.dsh = next(); break;
      case '--profile': opts.profile = next(); break;
      case '--harness': opts.harness = next(); break;
      case '--node': opts.node = path.resolve(next()); break;
      case '--rebind': opts.rebind = true; break;
      case '--dry-run': opts.dryRun = true; break;
      case '--force': opts.force = true; break;
      case '-h': case '--help': opts.help = true; break;
      default: throw new Error(`未知参数: ${arg}`);
    }
  }
  opts.home = path.resolve(opts.home);
  opts.dataDir = path.resolve(opts.dataDir ?? path.join(path.dirname(opts.home), 'data'));
  if (opts.tgz) opts.tgz = path.resolve(opts.tgz);
  if (opts.dsh) opts.dsh = path.resolve(opts.dsh);
  if (opts.harness) opts.harness = path.resolve(opts.harness);
  return opts;
}

const usage = `OpenMotion Suite bootstrap

  node bootstrap.mjs --rebind [--home DIR] [--data-dir DIR]
      已从旧机器复制 .openmotion-home，把这个路径重写成当前机器的。

  node bootstrap.mjs [--home DIR] [--tag v0.2.1] [--tgz FILE] [--dsh FILE] [--profile desktop]
      没有运行时，从上游 tag 构建 npm 单机包并安装（需要 git + node>=22.18 + 网络）。

  node bootstrap.mjs --dry-run ...
      只打印将要改动的字段。

参数：--home --data-dir --tag --tgz --dsh --profile --harness --node --rebind --dry-run --force`;

const readJson = async (file) => JSON.parse(await readFile(file, 'utf8'));
const posix = (p) => p.replaceAll('\\', '/');

async function writeJsonIfChanged(file, data, { dryRun }) {
  const next = JSON.stringify(data, null, 2) + '\n';
  const before = existsSync(file) ? await readFile(file, 'utf8') : null;
  if (before === next) return { file, changed: false };
  if (dryRun) return { file, changed: true };
  if (before !== null) await copyFile(file, `${file}.bak-bootstrap`);
  await writeFile(file, next, 'utf8');
  return { file, changed: true };
}

// launcher 本身不写死任何机器路径；本机 Harness 位置写进同目录的 dsh-harness.json。
async function writeHarnessConfig(launcherFile, harnessDir, opts) {
  const configFile = path.join(path.dirname(launcherFile), 'dsh-harness.json');
  const exe = path.join(harnessDir, 'DeepSeek Harness.exe');
  const cli = path.join(harnessDir, 'resources', 'app.asar', 'dsh', 'node_modules',
    '@deepseek-ai', 'dsh-desktop-host', 'lib', 'cli.js');
  if (!existsSync(exe)) throw new Error(`--harness 下找不到 DeepSeek Harness.exe：${exe}`);
  if (!existsSync(cli)) throw new Error(`--harness 下找不到 dsh-desktop-host 的 cli.js：${cli}`);
  return writeJsonIfChanged(configFile, { dir: harnessDir, exe, cli }, opts);
}

async function pickAppRoot(home) {
  const appsDir = path.join(home, 'apps');
  if (!existsSync(appsDir)) return null;
  const entries = await readdir(appsDir, { withFileTypes: true });
  const apps = entries.filter((e) => e.isDirectory() && /^0\.\d+\.\d+-[a-f0-9]+$/.test(e.name)).map((e) => e.name);
  if (apps.length === 0) return null;
  if (apps.length > 1) {
    throw new Error(`apps/ 下有多个运行时，请手动只保留一个：${apps.join(', ')}`);
  }
  return { name: apps[0], dir: path.join(appsDir, apps[0]) };
}

async function pickBundle(home) {
  const hostsDir = path.join(home, 'hosts');
  if (!existsSync(hostsDir)) return null;
  const entries = await readdir(hostsDir, { withFileTypes: true });
  const bundles = entries.filter((e) => e.isDirectory() && e.name.startsWith('deepseek')).map((e) => e.name);
  return bundles.length ? bundles[0] : null;
}

function profileConfigFile(profile) {
  const dshHome = process.env.DSH_HOME ?? path.join(os.homedir(), '.dsh');
  return path.join(dshHome, 'profiles', profile, 'package.json');
}

// ---------- 模式 A：重指向 ----------

async function rebind(opts) {
  const problems = [];
  const report = { mode: 'rebind', home: opts.home, dataDir: opts.dataDir, changes: [] };

  const installFile = path.join(opts.home, 'install.json');
  if (!existsSync(installFile)) {
    throw new Error(`找不到 ${installFile}。若这是全新机器且没有可复制的运行时，请去掉 --rebind，改用默认模式从 tag 构建。`);
  }
  const install = await readJson(installFile);
  const app = await pickAppRoot(opts.home);
  if (!app) throw new Error(`${opts.home}/apps 下没有 0.${''}x.x-<hash> 运行时目录`);
  const bundle = await pickBundle(opts.home);

  const next = {
    ...install,
    appRoot: app.dir,
    dataDirectory: opts.dataDir,
    launcher: path.join(opts.home, 'run-mcp.mjs'),
  };
  const host = install.hosts?.deepseek;
  if (host) {
    next.hosts = {
      ...install.hosts,
      deepseek: {
        ...host,
        skillsDirectory: bundle ? path.join(opts.home, 'hosts', bundle, 'skills') : host.skillsDirectory,
        bundleDirectory: bundle ? path.join(opts.home, 'hosts', bundle) : host.bundleDirectory,
        configFile: profileConfigFile(host.profile ?? opts.profile),
        profile: host.profile ?? opts.profile,
      },
    };
  }
  report.changes.push(await writeJsonIfChanged(installFile, next, opts));

  // .npm-install.json：cacheDirectory 决定原生组件缓存位置，必须是绝对路径
  const npmInstallFile = path.join(app.dir, '.npm-install.json');
  if (existsSync(npmInstallFile)) {
    const npmInstall = await readJson(npmInstallFile);
    const updated = {
      ...npmInstall,
      installHome: opts.home,
      cacheDirectory: path.join(opts.home, 'cache', 'native'),
    };
    report.changes.push(await writeJsonIfChanged(npmInstallFile, updated, opts));
  } else {
    problems.push(`${npmInstallFile} 不存在（原生组件会退回系统 ffmpeg/browser）`);
  }

  // dsh-cli-launcher.mjs 通过同目录 dsh-harness.json 取本机 Harness 位置
  const launcherFile = path.join(path.dirname(opts.home), 'dsh-cli-launcher.mjs');
  if (opts.harness) {
    report.changes.push(await writeHarnessConfig(launcherFile, opts.harness, opts));
  } else {
    const harnessConfig = path.join(path.dirname(opts.home), 'dsh-harness.json');
    if (!existsSync(harnessConfig) && !process.env.DSH_HARNESS_DIR) {
      problems.push(`未配置 Harness 位置（重装/升级会失败）：加 --harness "<DeepSeek Harness 安装目录>" 生成 dsh-harness.json`);
    }
  }

  // DSH profile 里指向 host bundle 的 link: 依赖
  const profileFile = profileConfigFile(opts.profile);
  if (existsSync(profileFile) && bundle) {
    const pkg = await readJson(profileFile);
    const deps = pkg.dependencies ?? {};
    const target = posix(path.join(opts.home, 'hosts', bundle));
    let touched = false;
    for (const [key, value] of Object.entries(deps)) {
      if (typeof value !== 'string' || !value.startsWith('link:')) continue;
      if (!/openmotion/i.test(key)) continue;
      const wanted = `link:${target}`;
      if (value === wanted) continue;
      deps[key] = wanted;
      touched = true;
    }
    if (touched) report.changes.push(await writeJsonIfChanged(profileFile, { ...pkg, dependencies: deps }, opts));
  } else if (!existsSync(profileFile)) {
    problems.push(`profile 配置不存在：${profileFile}（先启动一次 DSH，或确认 --profile）`);
  }

  // host bundle 里的两个注册文件，才是 MCP 实际启动用的东西（比 install.json 更靠前）
  if (bundle) {
    const bundleDir = path.join(opts.home, 'hosts', bundle);

    const scopeFile = path.join(bundleDir, 'scope.json');
    if (existsSync(scopeFile)) {
      const scope = await readJson(scopeFile);
      report.changes.push(await writeJsonIfChanged(scopeFile, {
        ...scope,
        installHome: opts.home,
        runtimeRoot: app.dir,
        dataDirectory: opts.dataDir,
        configFile: profileConfigFile(scope.profile ?? opts.profile),
      }, opts));
    }

    // cordis.patch.yml 的文件名叫 .yml，内容其实是 JSON 数组
    const patchFile = path.join(bundleDir, 'cordis.patch.yml');
    if (existsSync(patchFile)) {
      const patches = JSON.parse(await readFile(patchFile, 'utf8'));
      const runMcp = path.join(opts.home, 'run-mcp.mjs');
      const skillsDir = path.join(bundleDir, 'skills');
      let touched = false;
      for (const patch of patches) {
        for (const entry of patch?.insert ?? []) {
          if (entry?.id === 'mcp-openmotion' && entry.config) {
            entry.config.args = [runMcp];
            entry.config.cwd = opts.home;
            if (opts.node) entry.config.command = opts.node;
            touched = true;
          }
          if (entry?.id === 'openmotion-skills' && entry.config) {
            entry.config.customSkillDirs = [skillsDir];
            touched = true;
          }
        }
      }
      if (touched) {
        const next = JSON.stringify(patches, null, 2) + '\n';
        const before = await readFile(patchFile, 'utf8');
        if (before !== next) {
          if (!opts.dryRun) {
            await copyFile(patchFile, `${patchFile}.bak-bootstrap`);
            await writeFile(patchFile, next, 'utf8');
            // 备份文件会干扰 JSON 解析之外的工具，但保留以便回滚
          }
          report.changes.push({ file: patchFile, changed: true });
        } else {
          report.changes.push({ file: patchFile, changed: false });
        }
      }
    }
  }

  report.problems = problems;
  report.changed = report.changes.some((c) => c.changed);
  report.planned = next; // dry-run 校验用它，而不是磁盘上的旧值
  return report;
}

// ---------- 模式 B：从官方 tag 构建安装 ----------

function run(command, args, options = {}) {
  console.log(`\n$ ${command} ${args.join(' ')}`);
  const result = spawnSync(command, args, { stdio: 'inherit', shell: process.platform === 'win32', ...options });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(`${command} 退出码 ${result.status}`);
  return result;
}

async function findTgz(root) {
  const out = [];
  async function walk(dir, depth) {
    if (depth > 3) return;
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      if (entry.name === 'node_modules' || entry.name === '.git') continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) await walk(full, depth + 1);
      else if (entry.name.endsWith('.tgz')) out.push(full);
    }
  }
  await walk(root, 0);
  return out;
}

async function buildFromRepo(opts) {
  const nodeMajor = Number(process.versions.node.split('.')[0]);
  const nodeMinor = Number(process.versions.node.split('.')[1]);
  if (nodeMajor < 22 || (nodeMajor === 22 && nodeMinor < 18)) {
    throw new Error(`需要 Node >= 22.18，当前 ${process.versions.node}`);
  }

  let tgz = opts.tgz;
  let work = null;
  if (!tgz) {
    work = await mkdtemp(path.join(os.tmpdir(), 'openmotion-build-'));
    console.log(`构建目录：${work}`);
    const clone = path.join(work, 'openmotion');
    run('git', ['clone', '--depth', '1', '--branch', opts.tag, REPO, clone]);
    run('npm', ['ci'], { cwd: clone });
    run('npm', ['run', 'package:npm'], { cwd: clone });
    const found = await findTgz(clone);
    if (!found.length) throw new Error('package:npm 没有产出 .tgz');
    tgz = found.sort((a, b) => b.length - a.length)[0];
    console.log(`产出包：${tgz}`);
  } else {
    console.log(`复用已有 tgz：${tgz}`);
  }

  const args = ['--yes', '--package', tgz, 'openmotion', 'setup', '--host', 'deepseek',
    '--home', opts.home, '--data-dir', opts.dataDir, '--profile', opts.profile];
  if (opts.dsh) args.push('--dsh', opts.dsh);
  run('npx', args);
  run('npx', ['--yes', '--package', tgz, 'openmotion', 'prepare', '--home', opts.home]);

  if (work) await rm(work, { recursive: true, force: true }).catch(() => {});
  return { mode: 'build', tgz, home: opts.home, dataDir: opts.dataDir };
}

// ---------- 校验 ----------

async function verify(opts, planned) {
  const installFile = path.join(opts.home, 'install.json');
  const problems = [];
  if (!planned && !existsSync(installFile)) return { ok: false, problems: ['install.json 不存在'] };
  const install = planned ?? await readJson(installFile);
  const check = (label, actual, expected) => {
    if (!actual) return problems.push(`${label} 未配置`);
    if (actual && path.resolve(actual) !== path.resolve(expected)) {
      return problems.push(`${label} 指向 ${actual}，期望 ${expected}`);
    }
    if (!existsSync(actual)) problems.push(`${label} 指向的路径不存在：${actual}`);
  };
  check('appRoot', install.appRoot, install.appRoot);
  check('dataDirectory', install.dataDirectory, opts.dataDir);
  if (install.appRoot && existsSync(install.appRoot) && !existsSync(path.join(install.appRoot, 'mcp.ts'))) {
    problems.push('appRoot 下缺 mcp.ts');
  }
  if (install.launcher && !existsSync(install.launcher)) problems.push(`launcher 不存在：${install.launcher}`);

  const bundle = await pickBundle(opts.home);
  if (bundle) {
    const patchFile = path.join(opts.home, 'hosts', bundle, 'cordis.patch.yml');
    if (existsSync(patchFile)) {
      try {
        const patches = JSON.parse(await readFile(patchFile, 'utf8'));
        for (const patch of patches) {
          for (const entry of patch?.insert ?? []) {
            if (entry?.id !== 'mcp-openmotion' || !entry.config) continue;
            const runMcp = entry.config.args?.[0];
            if (runMcp && !existsSync(runMcp)) problems.push(`cordis.patch.yml 的 run-mcp.mjs 不存在：${runMcp}`);
            if (entry.config.command && !existsSync(entry.config.command)) {
              problems.push(`cordis.patch.yml 的 node 命令不存在：${entry.config.command}（用 --node 指定）`);
            }
          }
        }
      } catch (error) {
        problems.push(`cordis.patch.yml 无法解析为 JSON：${error.message}`);
      }
    }
  }
  return { ok: problems.length === 0, problems, appRoot: install.appRoot, dataDirectory: install.dataDirectory };
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) { console.log(usage); return; }
  console.log(`home     = ${opts.home}`);
  console.log(`data-dir = ${opts.dataDir}`);
  console.log(`dry-run  = ${opts.dryRun}`);

  if (!existsSync(opts.home) && opts.rebind) {
    throw new Error(`--rebind 需要一个已存在的 home，${opts.home} 不存在`);
  }

  const hasInstall = existsSync(path.join(opts.home, 'install.json'));
  const report = opts.rebind || hasInstall
    ? await rebind(opts)
    : await buildFromRepo(opts);

  console.log('\n=== 结果 ===');
  console.log(JSON.stringify(report, null, 2));

  const check = await verify(opts, report.planned);
  console.log('\n=== 校验 ===');
  console.log(JSON.stringify(check, null, 2));

  if (opts.dryRun) {
    console.log('\n(--dry-run：以上均为计划，未写入任何文件)');
    return;
  }
  if (!check.ok) {
    console.error('\n校验未通过，先处理上面的问题再启动 DSH。');
    process.exitCode = 1;
    return;
  }
  console.log('\n下一步：');
  console.log('  1) 重启 DSH（或新开会话），让 MCP 重新加载插件与本安装；');
  console.log('  2) 调用一次 openmotion_get_project，确认返回的 dataDirectory 等于上方 data-dir；');
  console.log('  3) 若 Tools 缺失，在该会话执行 openmotion diagnose --home "<home>" 查看恢复建议。');
}

main().catch((error) => {
  console.error(`\n失败：${error.message}`);
  process.exitCode = 1;
});
