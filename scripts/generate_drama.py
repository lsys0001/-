from __future__ import annotations

import argparse
import os
import re
import tempfile
from pathlib import Path

from openai import OpenAI
from pydantic import BaseModel, Field


class DramaPackage(BaseModel):
    script: str = Field(description="可拍摄的中文单集剧本 Markdown")
    visual_design: str = Field(description="人物、造型、地点、道具与连续性的视觉设定 Markdown")
    storyboard: str = Field(description="含镜头 ID、时长、调度和冻结关键帧的分镜 Markdown")
    image_prompts: str = Field(description="资产和关键帧图片提示词 Markdown")
    video_prompts: str = Field(description="逐镜视频提示词 Markdown")


ROOT = Path(__file__).resolve().parents[1]
INPUT_ROOT = (ROOT / "输入" / "故事").resolve()
OUTPUT_ROOT = (ROOT / "项目").resolve()
MAX_SOURCE_BYTES = 200_000


def safe_slug(value: str) -> str:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "-", value).strip(".-")
    if not value:
        raise ValueError("无法从输入文件名生成安全的项目名")
    return value[:80]


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
    ) as handle:
        handle.write(text.rstrip() + "\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--episode", default="EP001")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--target-seconds", type=int, default=60)
    parser.add_argument("--aspect-ratio", default="9:16")
    args = parser.parse_args()

    source = (ROOT / args.source).resolve()
    if INPUT_ROOT not in source.parents:
        raise ValueError("输入文件必须位于 输入/故事/ 目录中")
    if source.suffix.lower() not in {".md", ".txt"} or not source.is_file():
        raise ValueError("输入必须是存在的 .md 或 .txt 文件")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise ValueError(f"输入文件超过 {MAX_SOURCE_BYTES} 字节限制")
    if not re.fullmatch(r"EP\d{3}", args.episode):
        raise ValueError("集号必须使用 EP001 形式")
    if not 15 <= args.target_seconds <= 600:
        raise ValueError("单集时长必须在 15 到 600 秒之间")
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("缺少 OPENAI_API_KEY；请在仓库 Actions Secret 中配置")

    story = source.read_text(encoding="utf-8-sig").strip()
    if not story:
        raise ValueError("故事输入不能为空")

    instructions = """你是中文 AI 短剧制作总监。根据用户提供的故事，只生成指定单集的五份创作者可读 Markdown。
严格保留原故事的核心人物、因果、对白意图和连续性；没有依据时不要虚构文件名、参考图 ID 或已生成资产。
剧本要可拍摄且在目标时长内；视觉设定拆清人物、造型、地点、道具和状态；分镜必须包含稳定镜头 ID、镜头职责、时长、景别、机位、表演、声音和冻结关键帧；图片提示词使用英文主体并保留原语言画内文字；视频提示词逐镜说明动作、表演、运镜、环境运动、时长、起止状态、口型与声音边界。
这一步只生成文本策划，不声称图片、视频、配音、音乐或成片已经生产。"""
    prompt = f"""项目来源：{source.name}
目标集号：{args.episode}
目标时长：{args.target_seconds} 秒
画幅：{args.aspect_ratio}

故事原文：
---
{story}
---
"""

    client = OpenAI()
    response = client.responses.parse(
        model=args.model,
        instructions=instructions,
        input=prompt,
        text_format=DramaPackage,
    )
    package = response.output_parsed
    if package is None:
        raise RuntimeError("模型未返回可解析的短剧文档")

    project = OUTPUT_ROOT / safe_slug(source.stem) / "剧集" / args.episode
    documents = {
        "剧本.md": package.script,
        "视觉设定.md": package.visual_design,
        "分镜.md": package.storyboard,
        "图片提示词.md": package.image_prompts,
        "视频提示词.md": package.video_prompts,
    }
    for filename, content in documents.items():
        atomic_write(project / filename, content)

    print(f"已生成 {len(documents)} 份文档：{project.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

