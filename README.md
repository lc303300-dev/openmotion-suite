# OpenMotion Suite

OpenMotion 视频制作环境的**部署包**。一个根目录，下面两个各自独立演进的子目录：

```
openmotion-suite/
├── OpenMotion/        # 渲染引擎 + Studio（git submodule，跟随上游）
└── OpenMotionWork/    # 工作区：任务台账、脚本、口径与踩坑
```

## 为什么分两层

| | `OpenMotion/` | `OpenMotionWork/` |
|---|---|---|
| 是什么 | 视频合成引擎与 Studio 编辑器 | 你的项目现场 |
| 谁维护 | 上游 [`nexu-io/openmotion`](https://github.com/nexu-io/openmotion) | 你自己 |
| 怎么更新 | `git submodule update --remote OpenMotion` | `git pull` |
| 更新时会不会动到你的东西 | 整目录替换 | 完全不受影响 |

引擎当依赖、工作区当数据。**升级引擎永远不碰你的任务、脚本、口径文档。**

## 首次部署

```bash
git clone --recurse-submodules <本仓库地址> openmotion-suite
cd openmotion-suite
node bootstrap.mjs --profile desktop
```

`bootstrap.mjs` 负责把运行时装起来，因为**没有任何一条命令能直接装着走**：

- `openmotion@0.2.1` **不在 npm 上**（`npm view openmotion@0.2.1` 返回 404），公开版本只到 `0.1.1`；官方只有 GitHub tag **`v0.2.1`（commit `34df9b1a`）**。
- 安装器要用的 `payload/release-npm.json` 是构建产物、不入库（仓库里请求 `payload/` 是 404），所以只能从源码打。
- 上游 `docs/install.md` 自己写着 **"This is not an offline package."** —— 安装器不会自举。

所以它按官方路径走一遍：`git clone --depth 1 --branch v0.2.1` → `npm ci` → `npm run package:npm` → `openmotion setup --host deepseek` → `openmotion prepare --home`。需要 Node ≥ 22.18 和网络，首次构建约十几分钟（含 Studio 构建与原生组件下载）。

### 已有一份 `.openmotion-home`（换机器 / 搬目录）

```bash
node bootstrap.mjs --rebind --harness "D:\path\to\DeepSeek Harness" --dry-run   # 先看计划
node bootstrap.mjs --rebind --harness "D:\path\to\DeepSeek Harness"
```

把 `.openmotion-home` 和 `data` 整目录复制到新位置后跑它。它改写的是**运行时里的硬编码绝对路径**，共五处：

| 文件 | 字段 | 不改的后果 |
|---|---|---|
| `.openmotion-home/install.json` | `appRoot` / `dataDirectory` / `launcher` / `hosts.*` | `run-mcp.mjs` 直接 `import` 老 `appRoot`，ENOENT 崩 |
| `hosts/*/cordis.patch.yml` | MCP 的 `args` / `cwd` / `node` 命令 / `customSkillDirs` | **最容易漏**：它决定 MCP 实际启动哪个 `run-mcp.mjs`，不改就还连老安装 |
| `hosts/*/scope.json` | `installHome` / `runtimeRoot` / `dataDirectory` | 插件作用域指向老目录 |
| `apps/*/.npm-install.json` | `installHome` / `cacheDirectory` | 原生组件（ffmpeg/browser/python）缓存错位 |
| `dsh-cli-launcher.mjs` | `HOST_EXE` / `HOST_CLI` | 重装/升级时报 `HOST_CLI_NOT_FOUND` |

另外会同步 DSH profile `package.json` 里 `dsh-plugin-openmotion-local` 的 `link:` 路径。跑完必须**重启 DSH**（或新开会话）让 MCP 重连，再用 `openmotion_get_project` 核对返回的 `dataDirectory` 是否等于 `OpenMotionWork/data`。

`OpenMotionWork/AGENTS.md` 里的说明性绝对路径（文档举例，不是运行时）需要自己替换成本机路径。

首次运行会自动生成两个目录，**都不入库**：

- `OpenMotionWork/.openmotion-home/` —— 托管运行时（约 1.4 GB）
- `OpenMotionWork/data/` —— 工程、素材、导出（体积随项目增长）

## 更新引擎（不动工作区）

```bash
git submodule update --remote OpenMotion
```

submodule 记录的是上游某个 commit，所以每次更新都能回退：`git checkout <old-commit> -- OpenMotion`。

> **注意：更新 submodule 不会更新正在跑的运行时。**
> 运行时版本由 `bootstrap.mjs --tag` 决定（本机当前为 `v0.2.1` / `34df9b1a`），而 submodule 跟的是 `main`。两条线并不一致——上游在 2026-11 把版本序列重置过：`v0.2.1` 之后 `main` 的 `package.json` 是 `0.0.1`，新系列的 tag 已经跑到 `v0.6.8-test.*`。所以 submodule 只当源码参考，别指望它和运行时同版本。

## `OpenMotionWork` 里有什么

| 路径 | 内容 |
|---|---|
| `AGENTS.md` | 工作区纪律：三区划分、任务目录规范、交付规范、已知坑（含文字层抖动、PDF 画板流水线） |
| `TASKS.md` | 任务总账，一行一个任务 |
| `tasks/_template/` | 新建任务时复制的模板 |
| `tasks/_reference/pdf-poster/` | PDF 画板 → 动效 的固定流水线：`pdf2assets.py`（一次提取底色/矩阵/字体/字形/逐字坐标）、`pack_zip.py`、`verify_frames.py`，以及 `PITFALLS.md`（30 条实测踩坑） |
| `tasks/<taskId>/` | 每个任务的 `00-brief.md`、`task.json`、以及 `03-work/` 下的脚本 |

**不入库的东西**：客户素材、成片、工程数据、运行时。仓库只保留可复用资产 —— 换台机器 clone 下来就能接着干，但具体项目要自己带素材。

## 配套技能（不在本仓库）

`openmotion-to-ae`：把 OpenMotion 工程转成可编辑的 After Effects 工程（保留图层、Null 父级、遮罩和贝塞尔关键帧）。装在 DSH 的技能目录 `~/.dsh/skills/`，因为它依赖 AE 2025 且与宿主集成。

## 约定

- 引擎问题去上游仓库提，不要在本仓库改 `OpenMotion/`
- 工作区自己的经验写进 `AGENTS.md` 和 `tasks/_reference/`，下一台机器 clone 下来就带着走
