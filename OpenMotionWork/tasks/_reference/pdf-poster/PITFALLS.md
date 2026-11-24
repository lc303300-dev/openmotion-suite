# PDF 画板转动效 · 踩坑清单

> 来源：`20261125-0112-jmhb-poster-mg`（保利 POLY RARE 6s 9:16）实战。
> 本次在 PDF 解析、字体、工程交付三条线上都踩过坑，返工成本很高。这里是逐条复盘，
> 每条按「症状 → 根因 → 正确做法」写，配可直接抄的代码或命令。

---

## A. PowerShell / 编码（最耗时间的一类）

### A1. 内联 Python 一定翻车
- **症状**：`表达式或语句中包含意外的标记`、`字符串缺少终止符`，或者命令根本没执行。
- **根因**：PowerShell 先解析一遍引号，Python 再解析一遍；`python -c "..."` 里的
  `f"{x}"`、`'`、`>`、`$` 都会被 pwsh 提前吃掉。heredoc（`python - <<EOF`）在 pwsh 里也不存在。
- **正确做法**：**任何超过一行的 Python 都写成 `.py` 文件再执行**。
  ```powershell
  # 错
  python -c "for a,b in [('x','y')]: print(f'{a}{b}')"
  # 对
  python tasks\xxx\03-work\do_thing.py
  ```

### A2. 用 PowerShell 改写 UTF-8 源文件会静默毁文件
- **症状**：脚本里原本好好的中文路径变成 `鐢绘澘 16(1).pdf`，`pymupdf.FileNotFoundError`。
- **根因**：`Get-Content -Raw | Set-Content -Encoding utf8` 在 Windows PowerShell 5.1 下
  按 ANSI 解码再按 UTF-8 写回，中文全毁。而且**不会报错**。
- **正确做法**：改文件只走两条路——`edit`/`write` 工具，或一个**专门写文件的 .py**。
  永远不要用 pwsh 管道重写含中文的源码。

### A3. 中文报错在终端是乱码
- **症状**：`����λ�� ��:9 �ַ�: 87`，看不出错在哪。
- **根因**：pwsh 与 Python 的 stderr 编码不一致。
- **正确做法**：所有分析脚本开头固定
  ```python
  sys.stdout.reconfigure(encoding="utf-8")
  ```
  并且**不要依赖 pwsh 回显错误文本**——把结果写进文件再用 `read` 工具看。

### A4. `| Select-Object -First N` 会让命令"假失败"
- **症状**：命令明明成功，`[exit code: 1]`。
- **根因**：下游截断管道，上游进程收到管道关闭。
- **正确做法**：先落盘再读。
  ```powershell
  python draw.py > out.txt 2>&1
  ```
  或 `2>&1 | Select-String -Pattern '需要的行'`（Select-String 会读完整流）。

### A5. `&node $cli check $dir --json 2>$null | Out-File -Encoding utf8`
- **症状**：JSON 带 BOM，`json.load` 报 `Unexpected UTF-8 BOM`。
- **正确做法**：`json.load(open(p, encoding="utf-8-sig"))`。

---

## B. PDF 解析

### B1. y-up → y-down 的矩阵换算，符号错一次就全歪
- **症状**：算出来的 bbox 出现负数（`center=(-206.71, 510.63)`），元素跑到画布外。
- **根因**：PDF 内容流 `cm` 是 y 向上、原点左下；浏览器是 y 向下、原点左上。
  而且 **PDF 图像的 unit square 里 v 向上、栅格数据 v 向下**，还要再翻一次。
- **正确做法**（已实测与 fitz 的 `get_image_info().transform` 完全一致）：
  ```python
  def pdf_cm_to_fitz(a, b, c, d, e, f, page_h):
      return (a, -b, -c, d, c + e, page_h - d - f)
  ```
  **更好：别自己抄 cm**。`page.get_image_info()` 直接给 y-down 的 `transform`，
  而且按绘制顺序返回（= z 序）。

### B2. `page.get_text("dict")` 里的 image bbox 对旋转图不可靠
- **症状**：便签图的 bbox 跟渲染图对不上。
- **正确做法**：几何一律用 `get_image_info()` 的 `transform`，`get_text("dict")` 只看文字。

### B3. 图片可能带 90° 旋转甚至斜切，不能反推成 rotate+scale
- **症状**：相纸框视觉是横的，但矩阵显示旋转 90°；强行按"视觉角度"摆，照片和框错位。
- **根因**：设计师把竖版相纸 PNG 转了 90° 使用，甚至可能带非等比/斜切。
- **正确做法**：**原样搬 matrix**。
  ```css
  /* 元素宽高 = 图像原始像素 W×H */
  transform: matrix(a/W, b/W, c/H, d/H, e, f);  /* unit 矩阵 → 像素基矩阵 */
  transform-origin: 0 0;
  ```
  判断是否斜切：两轴夹角 `((v_deg - u_deg) % 360)` 是否 ≈ 90°；`det < 0` 表示镜像。

### B4. 嵌套矩阵（照片放在相纸里）
- **症状**：照片跟着相纸一起动，但位置差 30–50px。
- **根因**：照片的矩阵是**页面坐标**的，放进相纸的局部坐标要左乘相纸矩阵的逆。
- **正确做法**：
  ```python
  M_local = mat_mul(mat_inv(M_frame_px), M_photo_px)
  ```
  再减去内窗原点的偏移（`.win` 的 left/top）。

### B5. PNG 素材在 PDF 里常常是"黑底 + 软蒙版"
- **症状**：导出的相纸框、邮戳是一块黑的。
- **根因**：`doc.extract_image()` 只给 RGB 数据，透明度在 `smask` 里。
- **正确做法**：把 smask 合成成 alpha 再存 PNG。
  ```python
  info = doc.extract_image(xref); sm = info.get("smask")
  if sm:
      mask = Image.open(io.BytesIO(doc.extract_image(sm)["image"])).convert("L")
      img = img.convert("RGBA"); img.putalpha(mask)
  ```

### B6. 找不到的图形，先怀疑它是"图片"而不是矢量
- **症状**：`get_drawings()` 里翻遍都没有那个金色邮戳，`get_drawings(extended=True)` 也没有。
- **根因**：它就是一张 333×161 的带 alpha PNG，`get_drawings` 永远看不到。
- **正确做法**：先列 `page.get_image_info()`，逐张导出看一眼；再谈"重绘"。

### B7. 页面外的图像会混进来
- **症状**：多出两张 1609×1121 的花卉图，bbox 在页面外。
- **正确做法**：按 bbox 与页面求交，过滤掉完全在页面外的实例（本次这两张就没用上）。

### B8. 底色不是一张图，是多次纯色填充
- **症状**：以为底色就是纸纹图的颜色。
- **正确做法**：统计 `get_drawings()` 里各填充色的覆盖面积，取最大者作为底色；
  纸纹图叠加在上层，最终颜色以纸纹图为准。

---

## C. 字体（中文项目必踩）

### C1. 子集 ttf 的 `cmap` 是空的
- **症状**：`cmap entries: 0`；导入后所有中文渲染成豆腐块。
- **根因**：PDF 用 CID 编码 + `ToUnicode` CMap，字体表里根本没有 unicode→glyph 映射。
- **正确做法**：从 `ToUnicode` 重建 cmap，**并假设 CID == GID**（`CIDToGIDMap` 为
  Identity 时成立；先检查 `doc.xref_get_key(fontxref, "CIDToGIDMap")`）。
  ```python
  pairs = parse_tounicode(cmap_stream_text)   # {cid: "字"}
  sub.cmap = {ord(uni): glyph_order[cid] for cid, uni in pairs.items()}
  ```

### C2. 子集字体缺 `post` 表 → OpenMotion 导入报错
- **症状**：`Cannot read properties of undefined (reading 'italicAngle')`。
- **根因**：导入器读 `post.italicAngle`，子集字体被裁掉了 `post` 表。
- **正确做法**：补一张 `formatType 3.0` 的 post 表；**已有就保留**。
  ⚠️ 不要直接 `tt["post"] = newTable("post")` 替换——format 3.0 不存字形名，
  会导致 `getGlyphOrder()` 抛 `illegal use of getGlyphOrder()`，save 直接失败。
  先 `tt.getGlyphOrder()` 拿到顺序再决定，或在已有 post 上只改 italicAngle。

### C3. 字体族名里的 `$`、`+` 会让渲染端加载失败
- **症状**：`Fonts FAILED: DKSPPM+Assassin$ (400 normal)`，页面回退到系统字体。
- **正确做法**：清洗成纯 ASCII。
  ```python
  name = re.sub(r"^[A-Z]{6}\+", "", basefont)      # 去子集前缀
  name = re.sub(r"[^A-Za-z0-9_-]+", "_", name)     # 去 $ + 等
  ```
  同时改 `name` 表的 1/2/4/6 号记录，导入后 family 才是干净的。

### C4. CFF 字形：`CFFFontSet.decompile` 传文件句柄会崩
- **症状**：`ValueError: seek of closed file`。
- **根因**：CFF 是惰性解析，`with open(...)` 退出后再取字形就找不到文件。
- **正确做法**：`cff.decompile(io.BytesIO(data), None)`。

### C5. `T2CharStringPen` 没有 `getCommands()`
- **正确做法**：要 SVG path 就用 `fontTools.pens.svgPathPen.SVGPathPen`；
  两者的 import 路径也不同（`fontTools.pens.*`，不是 `fontTools.misc.psCharStrings`）。

### C6. 抽取的 CFF 往往只有 10–12 个字形
- 这是好事：LOGO 这种艺术字，`P O L Y R A E C N T R O` 正好够用。
  渲染时按 PDF 里的逐字 x 定位，用
  ```html
  <g transform="translate(x, baseline)">
    <g transform="scale(SX, -SY)"><path d="..."/></g>
  </g>
  ```
  `SX = 字号的 x 缩放 / 1000`，`SY = 字号的 y 缩放 / 1000`（注意 PDF 里 LOGO 常有
  非等比缩放，例如 x=64.74 / y=70.47，直接抄 Tm 的 a、d）。

### C7. 标点缺席
- 英文子集缺 `, - . /`，中文子集只含用到的字。
- **正确做法**：标点单独用 `@font-face { src: local("SimSun"), local("宋体"), local("Arial") }`
  兜底；或从另一个 CFF（本次是 AdobeSongStd）抽标点轮廓。

---

## D. OpenMotion / Hyperframes

### D1. 逐字排布会触发 lint 「文字重叠」
- **症状**：`layout` 报十几条 `Two text blocks overlap and may render unreadable`，导出被拦。
- **根因**：逐字 `<text>` 相邻字符的包围盒必然轻微相交。
- **正确做法**：给**每个**文字组加 `data-layout-allow-overlap`（不继承，要逐组加）。

### D2. `.clip` 元素不能被 GSAP 动 transform
- **症状**：`gsap_animates_clip_element`。
- **正确做法**：`.clip` 只做时间窗容器，动画层放子元素（`.fall` / `.inner`）。

### D3. 元素已有 CSS transform 时，GSAP 再管 transform 会打架
- **症状**：元素位置跳动、静态版式被覆盖。
- **正确做法**：**分层**。
  - 外层 `.fall`：GSAP 只动 `y / rotation / scale / opacity`，`transform-origin` 设成
    目标元素中心（GSAP 的旋转 / 缩放要绕自身中心才自然）。
  - 内层 `.sheet`：写死 `matrix(...)` 复刻版面，GSAP 不碰。
  这样"精确版式"和"动画"互不干扰。

### D4. 源码几十 KB，别通过对话搬
- **症状**：手工复制 32KB HTML 容易丢行、改错坐标；token 成本也高。
- **正确做法**：**打包 ZIP，走 `openmotion_project_archive(action="import")`**。
  ```text
  index.html + compositions/ + assets/(素材与字体) + hyperframes.json
  → zip → import → 新 projectId
  ```
  注意：导入后 `requirements` 为空、`assetNames` 变成 `Image 1..N`、`projectType`
  变 `legacy`，需要一次 `openmotion_edit_project` 补元数据（只传 assetNames +
  requirements，不传 files，就不会动源码）。
  旧的空壳工程用 `openmotion_manage_project(action="trash")` 回收。

### D5. `get_project` 的 `file` 参数是对象
- **症状**：`INVALID_ARGUMENT: arguments.file must be an object`。
- **正确用法**：`file: {path: "index.html", offset: 0, length: 2000}`。

### D6. 刚导入就查会 `VERSION_CONFLICT`
- 重试一次即可（导入是异步落盘）。

### D7. 导出进度别高频轮询
- `get_project(exportJobId=...)` 每次返回整个工程 JSON（十几 KB）。
- **正确做法**：看 `data/exports/<jobId>/` 下有没有 `.mp4` 落盘 + `ffprobe` 校验，
  确认后再查一次终态拿 verification 明细。

### D8. `open_preview` 在 DSH 返回 `openedByHost:false` 是正常的
- DSH 没有右侧面板工具。老老实实把 `previewUrl` 给用户，并 `record_display`
  记 `visibility:"unavailable"`，**不要谎称已打开**。

---

## E. 渲染与验收

### E1. `snapshot --at` 与 timeline 有约 0.1s 相位差
- **症状**：`--at 0.45` 抓到空帧，以为动画没跑。
- **正确做法**：判断"某元素何时出现"要抓密集帧（0.3/0.4/0.5/0.6），不要用单帧下结论。

### E2. 缩略拼图目测会误判
- **症状**：看 contact sheet 以为内容整体偏上/偏小，实际是对的。
- **正确做法**：用像素比对 + 墨迹行范围。
  ```python
  col = (rgb.mean(axis=2) < 200).sum(axis=1)   # 每行有多少"有内容"的像素
  rows = np.where(col > 3)[0]                  # 与参考对比 min/max
  ```
  本次末帧墨迹行 260–1639 vs 参考 260–1640，一眼确认无偏移。

### E3. 导出前的三件套检查（AGENTS.md §6.1 的坑）
1. `compositions/*.html` 里**不能有 `data-hidden=""`**（有就整场景不渲染）。
2. 文字层不要带 `will-change` / `backface-visibility` / `font-smoothing`。
3. 不要在动态底图上用 `mix-blend-mode: multiply`。
本次没有触发，但每次导出前都该 grep 一遍。

### E4. 相纸投影的"方向"
- PDF 的投影是**页面坐标向下**的独立图元；CSS `box-shadow` 是**元素本地坐标**。
  元素一旦旋转 90°，本地"向下"就变成页面"向右"。
- **正确做法**：把页面 (0,1) 逆转进元素本地，得到本地偏移，再除以元素缩放。
  ```python
  lx, ly = -c/det, a/det           # 页面 (0,1) 在元素本地的方向
  dist, blur = 9/scale, 19/scale   # 除以元素缩放，视觉上才等大
  ```

---

## 附：一条命令搞定前半程

```powershell
python tasks\_reference\pdf-poster\pdf2assets.py "源画板.pdf" "03-work\assets"
```

它会产出：底色、11 个图像实例的矩阵（含旋转/镜像/斜切标记）、位图（smask 已合成）、
可导入的字体（cmap + post + 命名已修）、CFF 字形 JSON、逐字位置、以及一份 `report.md`。
剩下要做的就是照着 `matrix.json` 写 CSS、照着 `trace.json` 排字。
