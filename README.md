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
cd openmotion-suite/OpenMotion
npm install          # 然后按 OpenMotion/docs/install.md 完成首次 setup
```

`OpenMotionUser` 侧只需要改一处：**`OpenMotionWork/AGENTS.md` 里的绝对路径**
（原文写的是作者本机的 `F:\LiuCan\AI\DSH\OpenMotionWork` 与 `.../OpenMotion`），换成你本机的部署路径即可。

首次运行会自动生成两个目录，**都不入库**：

- `OpenMotionWork/.openmotion-home/` —— 托管运行时（约 1.4 GB）
- `OpenMotionWork/data/` —— 工程、素材、导出（体积随项目增长）

## 更新引擎（不动工作区）

```bash
git submodule update --remote OpenMotion
```

submodule 记录的是上游某个 commit，所以每次更新都能回退：`git checkout <old-commit> -- OpenMotion`。

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
