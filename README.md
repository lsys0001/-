# AI 短剧自动化工厂

本仓库通过 GitHub Actions，把 `输入/故事/` 下的故事文本转换成单集 AI 短剧项目。每次运行生成五份 Markdown：

- `剧本.md`
- `视觉设定.md`
- `分镜.md`
- `图片提示词.md`
- `视频提示词.md`

生成结果写入 `项目/<故事名>/剧集/<EP>/` 并由 GitHub Actions 自动提交。

## 首次配置

1. 在 OpenAI Platform 创建项目 API Key。
2. 打开本仓库的 `Settings → Secrets and variables → Actions`。
3. 新建 Repository secret，名称必须是 `OPENAI_API_KEY`，值为 API Key。不要把密钥写入文件或提交记录。
4. 确认 `Settings → Actions → General → Workflow permissions` 允许工作流写入仓库内容。

## 使用

1. 把 `.md` 或 `.txt` 故事文件放进 `输入/故事/`。
2. 打开 `Actions → 自动生成 AI 短剧项目 → Run workflow`。
3. 填写故事路径、集号、目标时长、画幅和模型，运行工作流。
4. 成功后查看 `项目/` 下生成并提交的五份文档。

## 认证与安全

- OpenAI 调用只从 Actions Secret 读取 `OPENAI_API_KEY`，代码和生成文件不会保存密钥。
- 仓库提交使用 GitHub 为当前任务签发的短期 `GITHUB_TOKEN`，权限仅声明为 `contents: write`。
- 故事输入被限制在 `输入/故事/`，只接受 `.md`/`.txt`，最大 200,000 字节。
- 工作流只生成文本策划，不自动调用图片、视频、配音、音乐或 FFmpeg。媒体生产需要单独配置并明确确认。

## 目录

```text
输入/故事/                 故事源文件
scripts/generate_drama.py  生成器
项目/故事名/剧集/EP001/    五份创作文档
.github/workflows/         GitHub Actions 工作流
```

