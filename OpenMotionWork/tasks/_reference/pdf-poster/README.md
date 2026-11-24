# PDF 画板 → 动效 · 参考流水线

给「设计师给一张静态画板，要把它做成有动效的视频」这类任务用的固定套路。
本次实战产出：`tasks\20261125-0112-jmhb-poster-mg`（保利 POLY RARE 6s 9:16）。

核心原则：**版面靠读结构，不靠看图猜**。PDF 里有精确的变换矩阵、逐字坐标、内嵌字体，
把它们搬进 HTML，误差可以压到 1% 以内；靠眼睛摆，误差 5% 起步且返工无底。

---

## 目录

| 文件 | 作用 |
|---|---|
| `pdf2assets.py` | 一次跑完：底色、图像矩阵、位图（smask 合成）、可用字体、CFF 字形、逐字坐标、report |
| `pack_zip.py` | 把「已导入素材的工程」+「新源码」打包成 ZIP，走 `openmotion_project_archive import` |
| `verify_frames.py` | 渲染帧 vs 参考图的硬指标比对（meanDiff / 墨迹范围 / 差异热图） |
| `PITFALLS.md` | 踩坑清单（30 条，每条含症状、根因、正确做法） |

---

## 流水线（六步）

### 1. 读结构

```powershell
python tasks\_reference\pdf-poster\pdf2assets.py "源画板.pdf" "tasks\<id>\03-work\assets"
```

看 `report.md`：
- 页面尺寸、主底色
- 每个图像实例的 `bbox / 视觉尺寸 / 两轴角度 / 是否镜像 / 是否斜切`
- 字体清单（哪些能直接导入、哪些只能抽轮廓）
- 每行文字的 baseline、字号、颜色

**关键判断**：`sheared=true` 的元素只能用 `matrix()` 原样搬；`mirrored=true` 同理。

### 2. 建工程 + 导素材

```text
openmotion_create_project(projectType="natural_language", title, requirements, namingLanguage)
openmotion_import_assets(projectId, requestId, items=[{itemId, sourcePath}])   # 图 + 字体
```

字体一定要用 `pdf2assets.py` 修过的（cmap 重建 + post 补全 + 名称清洗），
否则会遇到 `italicAngle` 报错或渲染成豆腐。

### 3. 生成源码（本地，不进对话）

写一个 `gen_scene.py`，读 `matrix.json` + `trace.json`，生成 `index.html` 与
`compositions/scene-*.html`。要点：

- 画布 1080×1920（或按需求），内层 `#stage` 用设计稿原始尺寸（720×1280）+
  `transform: scale(1.5)`，这样所有坐标可以直接写 PDF 的 pt 值。
- 每个图层分两层：外层 `.fall`（GSAP 动 y/rotation/scale/opacity）、
  内层 `.sheet`（写死 `matrix(...)` 复刻版面）。
- 相纸这类"框 + 照片"结构：照片矩阵要左乘框矩阵的逆，再减去内窗原点。
- 逐字排 `<text>`，每个文字组加 `data-layout-allow-overlap`。

### 4. 本地快照自检（不消耗导出时间）

```powershell
node <hyperframes-cli> snapshot <project>\03-work\build-test --at 0.3,1.2,2.6,4.5,5.9 --output shots
python tasks\_reference\pdf-poster\verify_frames.py <参考页.png> shots\*.png
```

`meanDiff` 落在 3–8 且墨迹范围 shift ≤ 2px 就说明版面没问题，可以进下一步；
否则先修版面，别急着改动画。

### 5. 打包导入

```powershell
python tasks\_reference\pdf-poster\pack_zip.py ^
    "data\projects\<旧projectId>" "tasks\<id>\03-work\build" "tasks\<id>\03-work\out.zip"
```

```text
openmotion_project_archive(action="import", sourcePath="...out.zip", requestId)
openmotion_edit_project(... requirements, namingLanguage, assetNames)   # 补元数据，不传 files
openmotion_manage_project(action="trash", projectId=<旧工程>)
```

### 6. 贴链接（默认就到此为止）

```text
openmotion_open_preview({projectId, action:"open"})   # 跑 lint，返回 previewUrl
```

把 `previewUrl` 以可点击链接形式给用户，让他在 Studio 里自己看、自己拖时间轴。

**默认不提交 `export_request`。** 用户能预览就别渲染——渲染要等几十秒，预览是即时的。
改一次源码就重贴一次链接：ZIP 导入会生成新 `projectId`，旧链接会失效；旧工程记得 `trash`。

### 7. 出片（仅在用户明确要求时）

只有用户说「给我视频 / 出片 / 要文件 / 发给甲方 / 上平台」才走这步：

```text
openmotion_export_request     # audio="silent" 或 "required"
```

等 `data\exports\<jobId>\*.mp4` 落盘 → `ffprobe` 看规格 → 抽帧 →
`verify_frames.py` 比对 → 交付（工程 + MP4 + 限制说明）。
技术校验通过只代表文件没问题，不代表画面被接受——这两件事分开说。

---

## 动画设计上的经验

- **6 秒片的节奏**：0–0.2 纯色/留白 → 0.2–1.7 主视觉堆叠 → 1.7–2.5 点睛（盖章）→
  2.5–4.5 文字层 → 4.5–6.0 静置。文字层不要和主视觉抢时间。
- **"从画面外落下"**：起点 `y` 要大于「画布高 − 元素顶部」再加 100–200px，否则元素会
  一开始就露头，"从镜头外"的感觉就没了。
- **落地要有物理感**：`power3.in` 落下 + 落地瞬间 `scaleY 0.96 / scaleX 1.02` +
  `elastic.out(1, 0.5)` 回弹；旋转用更短的时长先归位，会有"甩正"的手感。
- **商标逐字入场**：`y: 26 → 0` + `opacity 0 → 1` + `stagger 0.048`；
  字距大的次级行用「从中心向外散开」（每个字初始 `x` 偏移 `(中心 − 字位) × 0.6`）。
- **打字**：逐字 `opacity 0 → 1` + `y: 3 → 0`，`stagger 0.036–0.05`，每字 0.15s。
  不要用宽度动画或真实光标——中文字宽固定，逐字闪现有"敲出来"的语义就够了。

---

## 什么时候不该走这条路

- 参考素材是**实拍视频**：走 `openmotion-recreate`，别硬拆。
- 需要**真 3D / 物理模拟**：HTML/CSS 撑不住，考虑生成素材再合成。
- 用户只要**静态图**：不用 OpenMotion。
