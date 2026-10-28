# 单细胞学习站（静态网站）

这是 `REPORT.md` 的“可操作版”：12 步 + 附录，每一步包含目标、命令、为什么、预期结果、解读、检查点和排错。

## 打开方式

直接双击 `index.html` 即可（无需服务器）。如果浏览器的 `file://` 限制了剪贴板/搜索，可以在项目根目录启动一个本地服务器：

```powershell
python -m http.server 8000 -d site
```

然后打开 `http://127.0.0.1:8000/`。

## 结构

```text
site/
├─ index.html            # 首页
├─ chapters/*.html       # 13 个章节（12 步 + 附录）
├─ glossary.html         # 58 个术语的完整列表 + 搜索
├─ code.html             # 代码与数据索引
├─ full-report.html      # 完整 REPORT.html 副本
├─ assets/style.css      # 视觉设计
├─ assets/app.js         # 进度、搜索、复制、移动端目录
├─ assets/glossary-data.js # 术语定义（tooltip 与术语表共用）
├─ assets/glossary.js    # 正文首次出现术语时自动加虚线与悬停注释
├─ assets/search-index.js# 自动生成的搜索索引
├─ content/*.md          # 课程源文件（可编辑）
├─ code/                 # 脚本副本 + DATA_README.md
├─ figures/              # 分析图副本
├─ downloads/            # 代码包 zip
└─ build_site.py         # 重新生成整站
```

## 术语悬停注释

正文中**第一次出现**的专业术语会自动加虚线下划线：鼠标悬停、键盘聚焦或点击即可看到
一句话解释；每页最多标记一次，避免满屏下划线。完整 58 条在 `glossary.html`，支持搜索。

定义在 `build_site.py` 的 `GLOSSARY` 列表中（term / aliases / category / definition）。
新增词条后重新运行 `python site/build_site.py`，tooltip 和术语表会一起更新。

## 重新生成

修改 `content/*.md` 或 `assets/style.css` 后：

```powershell
python site/build_site.py
```

脚本会复制 `figures/`、`code/`，重新生成章节、搜索索引和代码包。

## 说明

- 网站不包含原始 GEO 数据；按 `code/DATA_README.md` 下载。
- 学习进度保存在浏览器 `localStorage`，换浏览器/清缓存会重置。
- 关键数字来自 `results/` 的真实运行，不是示意值。
