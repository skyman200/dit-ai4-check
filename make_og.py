#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 카톡/오픈그래프 미리보기용 OG 이미지(1200x630) 생성 — Pretendard.
import pathlib
from PIL import Image, ImageDraw, ImageFont

HERE = pathlib.Path(__file__).resolve().parent
FONT = HERE.parent / "suite/nds-dit-mcp/_fonts"

W, H = 1200, 630
NAVY = (27, 42, 74)
NAVY2 = (40, 64, 110)
ORANGE = (226, 115, 31)
WHITE = (255, 255, 255)
SOFT = (232, 238, 248)
GREEN = (31, 122, 87)


def F(name, size):
    return ImageFont.truetype(str(FONT / name), size)


def center(draw, cx, y, text, font, fill):
    b = draw.textbbox((0, 0), text, font=font)
    w = b[2] - b[0]
    draw.text((cx - w / 2, y), text, font=font, fill=fill)
    return b[3] - b[1]


def main():
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)

    # 배경 그라데이션(수직 네이비 → 진네이비)
    for y in range(H):
        t = y / H
        r = int(NAVY[0] * (1 - t) + 12 * t)
        g = int(NAVY[1] * (1 - t) + 22 * t)
        b = int(NAVY[2] * (1 - t) + 42 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))

    # 상단 오렌지 액센트 바
    d.rectangle([0, 0, W, 12], fill=ORANGE)

    # 좌상단 대학 라벨
    d.text((60, 54), "동의과학대학교 · AID 사업", font=F("Pretendard-SemiBold.ttf", 30), fill=SOFT)

    # 메인 타이틀
    center(d, W / 2, 150, "강의계획서 AI 4주 적용", F("Pretendard-Bold.ttf", 82), WHITE)
    center(d, W / 2, 250, "학과 온라인 체크", F("Pretendard-Bold.ttf", 82), ORANGE)

    # 서브 카피
    center(d, W / 2, 372, "우리 학과 전 과목의 AI 적용 여부를 클릭 한 번으로 확인·확정",
           F("Pretendard-Medium.ttf", 34), SOFT)

    # 하단 배지들
    chips = [("● 25개 학과", GREEN), ("● 클릭 체크", ORANGE), ("● 결과 자동 저장", NAVY2)]
    cx = W / 2
    total = 0
    fchip = F("Pretendard-SemiBold.ttf", 30)
    widths = []
    for txt, _ in chips:
        b = d.textbbox((0, 0), txt, font=fchip)
        widths.append(b[2] - b[0] + 56)
    total = sum(widths) + 24 * (len(chips) - 1)
    x = cx - total / 2
    for (txt, col), wch in zip(chips, widths):
        d.rounded_rectangle([x, 462, x + wch, 528], radius=33, fill=(255, 255, 255))
        b = d.textbbox((0, 0), txt, font=fchip)
        d.text((x + 28, 462 + (66 - (b[3] - b[1])) / 2 - 6), txt, font=fchip, fill=col)
        x += wch + 24

    # 하단 안내
    center(d, W / 2, 566, "카카오톡 링크를 눌러 바로 시작하세요",
           F("Pretendard-Medium.ttf", 26), (150, 165, 190))

    out = HERE / "og.png"
    img.save(out, "PNG")
    print("OG 이미지 생성:", out, img.size)


if __name__ == "__main__":
    main()
