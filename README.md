# OriginOne Demo

可运行的 OriginOneAI 示例仓库。

## 直接运行

复制下面这段命令即可跑通当前 demo：

```bash
git clone https://github.com/originoneai/originone-demo.git
cd originone-demo/OriginOne-Wiki
bash scripts/smoke_test.sh
```

这条命令不需要 Obsidian、不需要数据库、不需要外部 LLM API。

## 当前 Demo

- `OriginOne-Wiki/`：一个终端优先的 LLM-Wiki 0-1 构建案例，从 `raw/`、`wiki/`、`output/` 三个基础目录开始，逐步演进到数据开发场景和个人/项目知识库场景。

## 常用命令

```bash
cd originone-demo/OriginOne-Wiki
python3 scripts/llm_wiki_demo.py map
python3 scripts/llm_wiki_demo.py demo-all
python3 scripts/validate_design_package.py design-package
```

如果要重新生成文章截图：

```bash
cd originone-demo/OriginOne-Wiki
python3 -m pip install -r requirements.txt
bash scripts/regenerate_screenshots.sh
```

## 内容结构

- `OriginOne-Wiki/scripts/`：可运行脚本。
- `OriginOne-Wiki/assets/screenshots/`：终端截图与 transcript。
- `OriginOne-Wiki/article/`：面向新手的实操文章。
- `OriginOne-Wiki/design-package/`：LLM-Wiki 设计契约与验收材料。
