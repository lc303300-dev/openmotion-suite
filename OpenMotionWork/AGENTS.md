# OpenMotionWork · 视频工作区专用指令

本目录（当前工作区根）是 **OpenMotion 0.2.1 单机版**的视频制作工作区。
在此目录新开的对话，直接按本文件执行：**不要重新调研安装方式、不要重装、不要装 Docker**。

> **路径口径**：本文所有路径都相对于本工作区根目录，不写死任何机器盘符。
> 每台机器的绝对路径由 `bootstrap.mjs` 写入 `.openmotion-home/install.json` 与 `dsh-harness.json`；
> 要核对实际位置，读这两个文件，或在 DSH 里调 `openmotion_get_project` 看返回的 `dataDirectory`。

配套目录：

| 目录 | 作用 |
| --- | --- |
| `OpenMotionWork/`（本工作区根） | **本工作区**：OpenMotion 运行时 + 工程数据 + 本指令 |
| `../OpenMotion/`（与本工作区同级） | **只读**：OpenMotion 上游源码副本（git submodule）。仅供查实现，不参与运行 |

---

## 0. 事实表（先读，省掉所有探测）

| 项 | 值 |
| --- | --- |
| 版本 | `0.2.1`，npm 单机形态，stable / prod 模板环境 |
| 形态 | **不需要 Docker / PostgreSQL / Redis / S3** |
| 运行时 | `.openmotion-home\`（appRoot 在里面的 `apps\0.2.1-*\`） |
| 工程数据 | `data\`（工程、素材、导出的唯一真实来源） |
| Studio | `http://localhost:4173`（由 MCP 按需拉起，不常驻） |
| MCP 服务名 | `openmotion`，工具前缀 `mcp__openmotion__` |
| 原生组件 | browser / media(FFmpeg) / vision(OpenCV) |
| 宿主 profile | DSH `desktop` |
| 宿主 CLI 启动器 | `dsh-cli-launcher.mjs`（重装/升级必需，**勿删**） |

自检一条就够：`openmotion_get_project` 返回的 `dataDirectory` 必须等于本工作区下的 `data\` 目录
（绝对路径以 `bootstrap.mjs` 写入的 `.openmotion-home/install.json` 为准）。
不等于就说明 MCP 连到了别的安装，**停下来报告，不要写工程**。

---

## 1. 铁律：生成与合成分离

违反这条会大量返工。

- **素材生成不在 OpenMotion 里做**
- **OpenMotion 只负责合成与渲染**

原因：它的媒体适配器只支持同步的**图片 / TTS / 语音转录**，**明确不支持异步视频端点**。
它的强项是把素材编排成片子（HTML/CSS/JS + GSAP → 渲染 MP4），不是素材工厂。

```
图片  ←  宿主 DSH 出图（Comfly）或用户提供
视频  ←  宿主 DSH 即梦 CLI（seedance 2.5）或用户提供
音乐  ←  参考片原声 / 用户素材
                 ↓ openmotion_import_assets（image / video / audio，单文件 ≤500MB）
         OpenMotion 工程：时间轴 + 动效 + 文字排版 + 字幕 + 转场
                 ↓ 渲染
         MP4 + 可编辑工程源码
```

`openmotion_media_use` 显示 provider 未配置**不是故障**，素材走导入即可。

---

## 2. 素材来源（按优先级）

1. **用户直接提供的文件**（最可靠）
2. **宿主 DSH 媒体工具**：`generate_image` / `batch_image` / `generate_video`（若会话可见）
3. **Comfly**：`https://ai.comfly.org/v1`，key 名 `COMFLY_API_KEY`，代理 `127.0.0.1:7897`
4. **即梦画布 CLI**：seedance 2.5 / 480p
5. **火山方舟 Ark**：`https://ark.cn-beijing.volces.com/api/v3`，key 名 `VOLCANO_ENGINE_API_KEY`

端点实测**直连可达**（返回 401 而非超时）。

### 可选：把 Comfly 接进 OpenMotion

只有需要它内部直接出图 / TTS / 字幕时才做：

1. 打开 `http://localhost:4173` → 侧栏「模型设置 / Model providers」
2. 添加**自定义 provider**：Base URL `https://ai.comfly.org/v1` + key
3. `openmotion_media_use(action=inspect)` 拿 `custom-*` ID
4. `action=models, provider=<该ID>, refresh=true` 拉模型目录
5. 给模型打 **Image** / **Audio** 能力标签
6. 之后才能 `action=generate`

注意：要求公网 HTTPS base URL，且**不走系统代理**。若 Comfly 必须经 7897，这条路不通，回退到「生成后导入」。

---

## 3. 工具地图

| 目的 | 工具 |
| --- | --- |
| 列 / 读工程 | `openmotion_get_project`（无参数=列出，带 projectId=详情） |
| 建工程 | `openmotion_create_project`（`natural_language` / `template` / `reference_video`） |
| 写工程 | `openmotion_edit_project`（必须带 revision + versionId） |
| 导入素材 | `openmotion_import_assets`（`items[]`：`itemId` + `sourcePath`） |
| 预览 | `openmotion_open_preview`（`action=open` / `begin`） |
| 导出 MP4 | `openmotion_export_request` → 轮询 `openmotion_get_project(exportJobId)` |
| 版本 | `openmotion_list_versions` / `openmotion_restore_version` |
| 模板 | `openmotion_list_templates` → `openmotion_get_template` |
| 素材生成 | `openmotion_media_use` / `openmotion_assets_use` |
| 工程管理 | `openmotion_manage_project` |
| 打包搬运 | `openmotion_project_archive` |

**Skill 分工**（按意图直接进，不必先过 production）：

| 意图 | Skill |
| --- | --- |
| 原创片、叙事/动效/声音重构 | `openmotion-director` |
| 复刻参考视频 | `openmotion-recreate` |
| 用模板库模板 | `openmotion-template-to-video` |
| 视频做成可复用模板 | `openmotion-video-to-template` |
| 既定方案下的修改/预览/排错/导出 | `openmotion-production` |
| 单独生成素材 | `openmotion-media` |

`openmotion-design`（HTML 设计）与 `openmotion-game`（小游戏）**不是视频**，不要混用。

---

## 4. 四种标准工作流

### A. 复刻参考视频（最常用）

1. 拿到**可解码的本地文件**。社媒链接常抓不到，优先让用户下载。
2. `ffprobe` 读时长/分辨率/帧率 → 按关键变化抽帧 → 逐帧看。
3. 先对齐预期：

| 参考片类型 | 可行性 | 说明 |
| --- | --- | --- |
| 动效/图文/UI 演示/数据图表/字幕动画 | 高 | 屏幕图形，代码可逐镜头重建 |
| 真人 + 字幕 + 动效 | 中 | 字幕/动效可重建；人物画面靠导入或生成 |
| 纯实拍 | 低 | 不是强项，只能套外壳 |

4. `openmotion_create_project`：有链接用 `reference_video` + `referenceUrl`；本地文件用 `natural_language`，路径与简报写进 `requirements`。
5. 用原生代码重建一切能重建的：文字、UI、图表、logo、字幕、形状、镜头运动、图层动画。
6. 重建不了的走第 2 节导入。
7. 声音默认保留参考片原声（抽 `.m4a` 导入并按新剪辑对时）。
8. 导出后**技术校验通过 ≠ 视觉验收**，分开陈述。

### B. 原创 → `openmotion-director`
### C. 用模板 → `openmotion_list_templates` 取本地 JSONL 索引 → 搜 ID → `openmotion_get_template` → `hasHtmlProject` 决定复用或复刻；**仅用户明确选定才建工程**
### D. 改已有工程 → 读 revision/versionId → 改；**永远不要重开新工程**

---

## 5. 调用纪律（违反会丢内容）

1. 任何写操作**先读工程**，拿 `revision` + `currentVersionId`。
2. 写操作必须带 `expectedRevision` + `expectedVersionId` + **稳定 `requestId`**（重试复用同一值）。
3. `openmotion_open_preview` **不会**隐式建工程。
4. 导出：`export_request` 拿 jobId，用 `get_project(projectId, exportJobId)` 轮询，不要重复提交。
5. 导入：`itemId` 与 `requestId` 稳定，重试不产生重复素材。
6. `sourcePath` 用绝对路径。
7. `dataDirectory` 不符立即停手。

---

## 6. 已知坑

| 现象 | 处理 |
| --- | --- |
| `open_preview` 返回 `openedByHost:false` | **正常**。DSH 无右侧面板工具，把 `previewUrl` 给用户，不要反复重试或谎称已打开 |
| 视频生成在 OpenMotion 内不可用 | 设计如此，用宿主即梦生成后导入 |
| 组件安装 `EPERM ... rename` | 重跑 `openmotion prepare --home ".openmotion-home"`，第 2 次通常成功 |
| Studio 打不开 | 先调任意 `openmotion_*` 工具拉起服务；再看 `.openmotion-home\cache\native\win-x64\*.status.json` 的 `stage` |
| 重装报 `HOST_CLI_NOT_FOUND` / `UNSUPPORTED_SHIM` | `--dsh` 必须指向 `dsh-cli-launcher.mjs`，不要指 `.cmd` / `.exe` |
| MCP 连不上 | 先试一次 `openmotion_get_project`；仍失败查 profile 的 `package.json` 是否含 `dsh-plugin-openmotion-local` |
| 导出后文字**疯狂细微抖动**（预览正常） | 按序排查三处：①scene host 被写了 `data-hidden=""`；②文字层带 GPU 合成提示；③`mix-blend-mode: multiply` + 动态底图。详见 §6.1 |
| 导出画面**没有文字**但预览有 | 先查 scene host 的 `data-hidden` 属性，再查字符是否被 `gsap.set(opacity:0)` 隐藏后引擎未接管 |
| 导出/渲染报 `EPERM ... rename` 或 `ReplaceFileW EIO` | 文件被其他进程占用（播放器/预览窗格/Defender 实时扫描）。等几秒重试，或先关掉正在播放该文件的应用 |
| 字体导入报 `Cannot read properties of undefined (reading 'italicAngle')` | 子集字体缺 `post` 表。用 `tasks\_reference\pdf-poster\pdf2assets.py` 修（保留已有表，别整张替换） |
| 字体导入成功但渲染回退成系统字体 | 字体族名里有 `$`/`+`（如 `DKSPPM+Assassin$`）。清洗成纯 ASCII 再导入 |
| 中文全部渲染成豆腐块 | 子集字体的 `cmap` 是空的，需按 PDF `ToUnicode` 重建（同上脚本已处理） |
| 相纸/印章导出是一块黑板 | PNG 的透明度在 `smask` 里，`extract_image` 不会自动合成（同上脚本已处理） |
| 中文路径变成 `鐢绘澘` | 曾用 pwsh 管道重写过 UTF-8 源文件。禁止这样改文件，见 §6.2 |

### 6.1 文字层逐帧渲染坑（2026-11-24 实测，婚礼/书咖类纯文字动效必看）

**诊断方法**：抽连续帧（1/30s 间隔）比对**文字区**像素差异。正常应 `max ≤ 40`、`px>8 ≤ 100`；坏时 `max 130~170`、`px>8` 上万。

```
ffmpeg -y -i out.mp4 -vf "select='between(n,432,434)'" -fps_mode passthrough f%02d.png
```

**四个坑（按出现频率排序）**：

1. **`data-hidden=""` 出现在 scene host 上**（`<div data-composition-id="xxx" ... data-hidden="">`）
   - 来源：Studio/预览会话会往 `index.html` 写这个属性；一旦存在，`snapshot` 和 `render` 都**完全不渲染该 scene**。
   - 症状：预览有字、导出没字；或突然"抖动消失"其实是"字没了"。
   - 修：删掉 `data-hidden=""`。**每次导出前都应检查一遍**。

2. **文字层带 GPU 合成/字体平滑提示**：`will-change: transform`、`backface-visibility: hidden`、GSAP `force3D: true`、`-webkit-font-smoothing: antialiased`、`text-rendering: geometricPrecision`
   - 实时预览是优化，但逐帧截图（screenshot capture）会让字形**每帧重新栅格化**，边缘亚像素差 → 抖。
   - 实测：去掉后文字区帧间差异从 `px>8 11208` 降到 `16`。
   - 修：全部去掉。`transform-origin` 保留无妨。

3. **`mix-blend-mode: multiply` + 动态底图**
   - 文字颜色 = 字色 × 背景色；底图逐帧在动（猫、热气、树影）→ 文字逐帧变色 → 抖。
   - 静态底图可用；**动态底图严禁**。需要油墨质感就改用「静态纸纹层叠在文字上方」。

4. **不要用 `--workers 1` 去"修"抖动**
   - 本机实测：`--workers 1` 会让文字层整个不渲染（而且看起来"很稳"，实际是没字）。
   - 正确做法是修上面 1–3 项，渲染保持默认多 worker。

**收益参照**：修复后完全静止窗口应达到 `max ≤ 30、px>8 ≤ 5`，与"逐帧截图无差异"同一量级。

### 6.2 PDF 画板转动态（2026-11-25 实测，地产/品牌海报必看）

设计师给一张静态画板 PDF、要一套 6 秒左右的动效 —— 这是本工作区的高频任务。**别靠看图摆元素**，
PDF 里有精确的变换矩阵、逐字坐标和内嵌字体，搬过来误差可压到 1%。

**固定流水线见 `tasks\_reference\pdf-poster\README.md`，踩坑 30 条见同目录 `PITFALLS.md`。**

必须先记住的五条：

1. **一个命令打底**：`python tasks\_reference\pdf-poster\pdf2assets.py <pdf> <out>`，
   一次产出底色、图像矩阵（含旋转/镜像/斜切标记）、smask 合成后的位图、可导入字体
   （cmap 重建 + post 补全 + 名称清洗）、CFF 字形 JSON、逐字坐标、`report.md`。
2. **版面原样搬 matrix**，不要拆成 rotate + scale —— 相纸框常是竖版转 90° 使用，
   甚至带斜切。外层 `.fall` 给 GSAP 动，内层 `.sheet` 写死 `matrix(...)`，互不干扰。
3. **中文子集字体必须修过再用**：cmap 从 `ToUnicode` 重建（假设 CID==GID）、补 `post` 表
   （已有就保留，整张替换会导致 save 失败）、族名清洗成纯 ASCII。
4. **源码几十 KB 不要通过对话搬**：`pack_zip.py` 打包 → `openmotion_project_archive import`，
   导入后补一次 `edit_project`（只传 requirements + assetNames，不传 files）。
5. **禁手写 PowerShell 调 Python**：多行一律落成 `.py` 文件；**禁用 pwsh 管道重写含中文的
   源文件**（会静默变成 `鐢绘澘`）。中文结果写进文件再用 `read` 看。

验收口径：末帧与 PDF 3× 渲染 `meanDiff ≤ 8`、墨迹行范围 shift ≤ 2px，才算版面过关
（`verify_frames.py` 直接给这两个数）。

---

## 7. 目录纪律

- **视频工程只在 `data\`**，由 MCP 管理，不要手改。
- `.openmotion-home\` 是托管运行时，**不要手改**（除第 6 节已知修复）。
- `../OpenMotion/`（与本工作区同级的 submodule）是**只读源码副本**：不要在里面装东西、不要 `git clean`、不要当工作目录。
- 临时文件（抽帧、对比图）放 `data\_scratch\<taskId>\`，任务一结束即可删；任务产物不放这里（见 §9）。
- `dsh-cli-launcher.mjs` 不要删，重装需要它。

---

## 8. 交付规范

- 语言：**简体中文**（代码、路径、字段名保持原样）。
- **默认不出片。** 改完源码就把工程在 Studio 里打开，给一条**可点击的预览链接**，让用户在 web 端自己看、自己拖时间轴。
  用户能预览就别渲染 —— 一次渲染要等几十秒，而预览是即时的。
- **只有这些情况才 `openmotion_export_request`**：用户明确说「给我视频 / 出片 / 要文件 / 发给甲方 / 上平台」，或点名了 MP4 的规格、码率、平台适配。
  拿不准就先给预览链接，顺口问一句要不要出片；**不要在用户没要求时提前提交导出**。
- 出片时的交付物：**可编辑工程**（`data\` 内）+ **已校验 MP4** + **一句话说明改了什么、假设了什么、剩余限制**。
- 技术导出成功与视觉验收**分开陈述**。
- 缺口要明说，不要美化。
- 付费生成前一次性问清：几个素材、什么模型、大致花费，同意后再提交。

### 8.1 Studio 预览链接（默认交付形态）

开工和每次改完源码，**第一件事是拿链接、贴链接**，不要等用户来问。

1. 调 `openmotion_open_preview({projectId, action:"open"})`，它会跑 lint 并返回 `previewUrl`。
2. 在回复里以**蓝色链接**形式给出（Markdown `[Studio 预览](url)` 或裸 URL 都行）。
3. DSH 宿主没有右侧面板，`openedByHost:false` 是正常的 —— 把地址给用户，不要谎称已打开、不要用 `Start-Process` 去弹系统浏览器。
4. 链接形如：
   ```text
   http://localhost:4173/?session=<sessionId>&project=<projectId>&embed=1&tracking_context=<ctx>#project=<projectId>
   ```
   `#project=<id>` 与 `#project/<id>` 两种 hash 路由都可用；工具返回哪种就贴哪种，另一种留一句备选。

**注意改源码会让链接失效。** 现在改动画是「ZIP 打包 → `archive import`」，每次导入会生成**新 projectId**，
所以链接会变。改完必须重新跑一次 `open_preview` 并把**新链接**贴出来，别让用户拿着旧链接刷不出内容。
（后续要优化的方向：把动画代码抽到 `assets/motion.js`，让 scene 用 `<script src>` 引，这样小改只需
`edit_project` 传那个小文件、projectId 不变 —— 先在下次任务里验证 OpenMotion 是否加载 scene 内的外部脚本。）

旧工程用 `openmotion_manage_project(action="trash")` 回收，避免用户点错。

---

## 9. 任务层级与目录规范（一个窗口 = 一个任务）

**这是硬约束。** 多个窗口并行干活时，没有任务边界的工作区一定会变成垃圾场。

### 9.1 三个区，各管各的

| 区 | 路径 | 谁能写 | 用途 |
| --- | --- | --- | --- |
| **任务区** | `tasks\<taskId>\` | 本任务窗口 | **唯一工作区**：参考、素材、脚本、交付物 |
| **运行时区** | `data\` | 只有 OpenMotion MCP | 工程、导入素材、导出；**不手改、不手建目录** |
| **临时区** | `data\_scratch\<taskId>\` | 本任务窗口 | 抽帧、对比图等一次性文件，随时可删 |

### 9.2 一个窗口 = 一个任务

- 每个新对话窗口默认**新建一个任务**；窗口内不做任务切换。
- 同一任务的后续修改、返工、追加需求，都在**原任务目录**里做：不开新任务、不建子任务、不另起工程。
- 只有用户明确说"接着做 / 继承 / 用上个窗口的素材 / 继续那个工程"时才关联旧任务（见 §9.6）。

### 9.3 目录骨架

```
OpenMotionWork\
├── AGENTS.md              # 本文件：运行时与任务纪律
├── TASKS.md               # 任务总账：一行一个任务
├── dsh-cli-launcher.mjs   # 勿删
├── tasks\
│   ├── _template\          # 任务模板（复制用，不在此工作）
│   ├── _reference\         # 跨任务复用的脚本与踩坑文档（只读，别在这儿干活）
│   │   └── pdf-poster\     # PDF 画板 → 动效 的固定流水线 + PITFALLS.md
│   ├── _archive\<YYYY-MM>\ # 归档任务
│   └── <taskId>\
│       ├── 00-brief.md     # 需求原话 + 我的理解 + 口径 + 交付结论
│       ├── task.json       # 机器可读状态：projectId / 继承 / 导出记录
│       ├── 01-ref\         # 参考片、抽帧、截图、继承素材
│       ├── 02-assets\      # 待导入工程的素材（图 / 音 / 字体 / 片段）
│       ├── 03-work\        # 脚本、分析产物、中间文件、交接文档
│       └── 04-deliver\     # 导出 MP4、对比图、交付说明
├── data\                   # OpenMotion 运行时数据（工程在此，见 §7）
└── .openmotion-home\       # 托管运行时，勿改
```

`_reference\` 只放**跨任务复用**的东西（脚本、踩坑清单、口径文档），一个任务专属的脚本仍然进
`03-work\`，不要往 `_reference\` 里塞一次性文件。

四个子目录职责**不许混用**：参考不进 assets、脚本不进 deliver、交付物不留在 work。

### 9.4 taskId 命名

`YYYYMMDD-HHMM-<slug>`

- `YYYYMMDD-HHMM`：任务创建时刻（本地时区，即会话开始时间）
- `slug`：2–4 个英文短词，kebab-case，一眼能看出内容（如 `wedding-invite-recreate`）
- 目录名**只用 ASCII**，不带空格；文件名可以用中文，但不要带空格
- `taskId` 必须与目录名完全一致，并写进 `task.json`

### 9.5 开场流程（每个窗口第一件事，5 步）

1. 读 `TASKS.md`。
2. 判断：用户是在继续某任务吗？—— 只有明确提到"接着 / 继承 / 上个窗口 / 那个工程 / 那片"才算。是 → 走第 4 步；否 → **新建任务**。
3. 新建：复制 `tasks\_template\` 为 `tasks\<taskId>\`，填 `00-brief.md`（用户原话逐字、我的理解、待确认项）与 `task.json`，并在 `TASKS.md` 活跃表加一行。
4. 打开已有任务：读该任务 `00-brief.md` + `task.json`，从中取 `projectId`，再用 `openmotion_get_project` 核对（`dataDirectory` 必须等于本工作区 `data`）。
5. 开工：所有新文件只写进本任务目录（或 `data\_scratch\<taskId>\`）。

### 9.6 继承规则（默认不继承）

- **默认从零开始**：新任务不自动继承任何旧任务的目录、素材或工程。
- 用户明确要求继承时：
  - 在 `task.json` 的 `inherits[]` 写 `{ "taskId": "...", "reason": "用户原话摘要" }`
  - 源任务目录**只读**：需要文件就**复制**到本任务 `01-ref\inherited-<源taskId>\`；不要跨目录写入、不要移动别人的文件
  - 继承**工程**时：不新建工程，复用 `projectId` 继续编辑（写操作带最新 revision + versionId）
- 继承了什么、为什么，写进 `00-brief.md` 的「关联」。

### 9.7 工程与任务的关系

- OpenMotion 工程只在 `data\`，由 MCP 创建管理；**任务目录里不复制工程**。
- 任务 ↔ 工程的映射唯一记录在 `task.json` 的 `openmotion.projectId`。
- **只认 `projectId`**：不要用工程标题、目录名或"最近打开的工程"猜工程；不确定就读 `TASKS.md` + `task.json`。
- 一个任务一个工程；需要在同一工程上分叉实验时用 `openmotion_manage_project(duplicate)`，不新建同标题工程。

### 9.8 收场流程（一个阶段结束或本次会话结束前）

1. 更新 `task.json`：`status`、`updatedAt`、`openmotion.*`、`exports`、`notes`（剩余限制）。
2. 更新 `TASKS.md` 对应行：状态、版本、最近更新。
3. 交付结论写进 `00-brief.md`，**必带 Studio 预览链接**；只有真出了片才把 MP4 放进 `04-deliver\`。
4. 清理 `data\_scratch\<taskId>\`（能删就删）。

### 9.9 状态机

`planning → building → previewed → delivered`；用户要片时中间插 `exported`（`previewed` 直接进 `delivered` 是常态）。
任一步卡住用 `blocked`（`notes` 写明卡在哪）；结束用 `archived`。

### 9.10 归档

- `delivered` 且 7 天无更新的任务：整目录移到 `tasks\_archive\<YYYY-MM>\<taskId>\`，`TASKS.md` 行移到「已归档」并写归档路径。
- 活跃任务 ≥ 10 个时提醒用户归档；**永不自动删任务目录**。

### 9.11 并发与冲突

- 多个窗口可能同时跑：**每个窗口只写自己的任务目录**，跨任务一律只读。
- 写 `TASKS.md` 前先重读，只改自己那一行。
- 两边冲突时以 `task.json` 为准（它是该任务的机器真源）。

### 9.12 根目录红线

根下**只允许**出现：`AGENTS.md`、`TASKS.md`、`dsh-cli-launcher.mjs`、`tasks\`、`data\`、`.openmotion-home\`。
临时文件、脚本、参考图、导出物、交接文档，一律进任务目录。发现根目录有散落文件，**先归位再干活**。
