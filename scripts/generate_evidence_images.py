from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "data" / "logs.jsonl"
OUT_DIR = ROOT / "docs" / "evidence"


def load_font(size: int = 14) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("C:/Windows/Fonts/consola.ttf", size)
    except OSError:
        return ImageFont.load_default()


def pick_logs() -> tuple[list[str], list[str]]:
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    correlation: list[str] = []
    pii: list[str] = []
    by_cid: dict[str, list[str]] = {}

    for line in lines:
        if not line.strip():
            continue
        rec = json.loads(line)
        cid = rec.get("correlation_id")
        if cid and rec.get("service") == "api":
            by_cid.setdefault(cid, []).append(line)
        raw = line
        if "REDACTED" in raw:
            pii.append(raw)

    for cid, group in by_cid.items():
        if len(group) >= 2:
            correlation = group[:2]
            break

    return correlation, pii[-2:]


def format_correlation_evidence(lines: list[str]) -> list[str]:
    formatted: list[str] = []
    for line in lines:
        rec = json.loads(line)
        formatted.append(
            f'{rec["event"]:16} | correlation_id={rec["correlation_id"]} | session_id={rec.get("session_id", "-")}'
        )
    return formatted


def wrap_line(text: str, max_len: int = 118) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def render(title: str, command: str, body_lines: list[str], outfile: str) -> None:
    font = load_font(14)
    title_font = load_font(15)
    pad = 24
    line_h = 22
    width = 1400

    content = [f"PS D:\\AILearning\\2A202600979-NgoThiAnh-Day13> {command}", ""] + [
        wrap_line(line) for line in body_lines
    ]
    height = pad * 2 + line_h * (len(content) + 2)

    img = Image.new("RGB", (width, height), "#0c0c0c")
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), title, fill="#569cd6", font=title_font)

    y = pad + line_h + 10
    for i, line in enumerate(content):
        color = "#cccccc"
        if i == 0:
            color = "#ffffff"
        if "correlation_id" in line and "req-" in line:
            color = "#4ec9b0"
        if "REDACTED" in line:
            color = "#ce9178"
        draw.text((pad, y), line, fill=color, font=font)
        y += line_h

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(OUT_DIR / outfile)
    print(f"Saved {OUT_DIR / outfile}")


def main() -> None:
    correlation, pii = pick_logs()
    if len(correlation) < 2:
        raise SystemExit("Need at least 2 API log lines with same correlation_id")

    render(
        "Evidence: Correlation ID propagation",
        "Get-Content data/logs.jsonl -Tail 4",
        format_correlation_evidence(correlation),
        "correlation-id-log.png",
    )
    render(
        "Evidence: PII redaction in logs",
        'Select-String -Path data/logs.jsonl -Pattern "REDACTED" | Select-Object -Last 2',
        pii,
        "pii-redaction-log.png",
    )


if __name__ == "__main__":
    main()
