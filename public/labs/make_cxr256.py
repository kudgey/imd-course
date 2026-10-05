#!/usr/bin/env python3
"""Копії рентгенограм Montgomery і Shenzhen зі стороною 256 px — для контролю якості.

Набори NLM (Jaeger et al., 2014) не публікуються на сайті й не поширюються як похідні:
цей скрипт лише будує локальний кеш у data/ (поза git і поза сайтом).

Спосіб зменшення (детермінований, без випадковості):
  1. PNG читається Pillow і переводиться в 8-бітний сірий режим «L»: у Montgomery файли вже
     «L»; у Shenzhen 635 палітрових PNG з сірою палітрою (R = G = B) і 27 RGB-файлів з трьома
     однаковими каналами — для обох типів convert("L") точно відтворює значення сірого;
  2. пропорції кадру зберігаються: довша сторона стає 256 px, коротша — round(256 · коротка /
     довга); без доповнення до квадрата й без обрізання — щоб статистики яскравості не
     змішувалися з чорними полями;
  3. фільтр Lanczos (Image.Resampling.LANCZOS) з reducing_gap=None — повне антиаліасингове
     зменшення без проміжного грубого кроку;
  4. результат — PNG «L» у data/nlm/cxr256/<набір>/<те саме ім’я файлу> і таблиця
     data/nlm/cxr256/sizes.csv: file, set, label, mode, width, height, w256, h256, sha1
     (sha1 — від пікселів копії; за ним --check перевіряє, що кеш не змінився).

Формат «256 px» для навчання моделей (квадрат, доповнення чи спотворення пропорцій) цей скрипт
НЕ визначає: це окреме рішення попередньої обробки. Кеш потрібен для контролю якості 800 знімків.

  python3 tools/make_cxr256.py          # побудувати кеш (≈ 1–3 хв на 8 процесах)
  python3 tools/make_cxr256.py --check  # перерахувати й звірити з кешем; код 1 — розбіжність
  python3 make_cxr256.py --root ПАПКА   # копії з ПАПКА/data/nlm/<Montgomery|Shenzhen>/CXR_png
                                        # у ПАПКА/data/nlm/cxr256/ (без --root — корінь курсу)
"""
import csv
import hashlib
import pathlib
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
SETS = ("Montgomery", "Shenzhen")
SIDE = 256
COLS = ["file", "set", "label", "mode", "width", "height", "w256", "h256", "sha1"]


def shrink(path):
    """Один знімок → (рядок таблиці, масив uint8 копії)."""
    with Image.open(path) as im:
        mode, (w, h) = im.mode, im.size
        g = im.convert("L")
    k = SIDE / max(w, h)
    size = (max(1, round(w * k)), max(1, round(h * k)))
    small = np.asarray(g.resize(size, Image.Resampling.LANCZOS, reducing_gap=None))
    row = {"file": path.name, "set": path.parent.parent.name, "label": path.stem[-1], "mode": mode,
           "width": w, "height": h, "w256": size[0], "h256": size[1],
           "sha1": hashlib.sha1(small.tobytes()).hexdigest()}
    return row, small


def sources(src):
    return sorted(p for s in SETS for p in (src / s / "CXR_png").glob("*.png"))


def main(argv):
    root = pathlib.Path(argv[argv.index("--root") + 1]).resolve() if "--root" in argv else ROOT
    src, out = root / "data/nlm", root / "data/nlm/cxr256"
    files = sources(src)
    # корінь курсу — рівно 800 знімків; у студента (--root) може бути лише один набір
    need_all = "--root" not in argv
    if (need_all and len(files) != 800) or not files:
        print(f"очікувалося {'800' if need_all else 'хоча б один'} PNG у "
              f"{src}/<Montgomery|Shenzhen>/CXR_png, знайдено {len(files)}")
        return 1
    counts = {s: sum(f.parent.parent.name == s for f in files) for s in SETS}
    print("знайдено:", ", ".join(f"{s} {n}" for s, n in counts.items()))
    with ProcessPoolExecutor(8) as ex:
        res = list(ex.map(shrink, files, chunksize=8))
    rows = [r for r, _ in res]
    if "--check" in argv:
        table = out / "sizes.csv"
        old = list(csv.DictReader(table.open(encoding="utf-8"))) if table.exists() else []
        new = [{k: str(v) for k, v in r.items()} for r in rows]
        bad = sum(a != b for a, b in zip(old, new, strict=False)) + abs(len(old) - len(new))
        for r, small in res:
            p = out / r["set"] / r["file"]
            if not p.exists() or not np.array_equal(np.asarray(Image.open(p)), small):
                bad += 1
        print(f"кеш 256 px: {len(new)} знімків, розбіжностей {bad}")
        return 1 if bad else 0
    for r, small in res:
        dst = out / r["set"] / r["file"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(small, "L").save(dst, optimize=True)
    with (out / "sizes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, COLS)
        w.writeheader()
        w.writerows(rows)
    mb = sum(p.stat().st_size for p in out.rglob("*.png")) / 1e6
    print(f"записано {len(rows)} копій у {out.relative_to(root)} ({mb:.1f} МБ) і sizes.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
