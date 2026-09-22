"""
Сверка двух контрольных срезов результатов классификации.

Показывает расхождения поимённо, а не только итоговые числа: для каждой
изменившейся записи выводится прежний и новый вердикт. Это позволяет отличить
осознанное изменение поведения от незамеченной регрессии.

Код возврата 0 -- расхождений нет, 1 -- есть.

Запуск:
    python tools/compare_snapshots.py было.json стало.json
"""

import argparse
import json
import sys


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_verdicts(before, after, limit):
    """Сравнивает повердиктный разбор эвристики."""
    keys = sorted(set(before) | set(after), key=int)
    changed = []
    for key in keys:
        was = before.get(key, {}).get("verdict", "<нет записи>")
        now = after.get(key, {}).get("verdict", "<нет записи>")
        if was != now:
            changed.append((key, was, now))

    print(f"Ступень 1, эвристика: изменилось записей -- {len(changed)} из {len(keys)}")
    for key, was, now in changed[:limit]:
        print(f"    запись {key}: {was} -> {now}")
    if len(changed) > limit:
        print(f"    ... и ещё {len(changed) - limit}")
    return changed


def compare_features(before, after, limit):
    """Сравнивает матрицу признаков покомпонентно."""
    if before.get("features_sha256") == after.get("features_sha256"):
        print("Ступень 2, признаки: контрольные суммы совпадают")
        return []

    fb, fa = before.get("features", {}), after.get("features", {})
    keys = sorted(set(fb) | set(fa), key=int)
    changed = [(k, fb.get(k), fa.get(k)) for k in keys if fb.get(k) != fa.get(k)]

    print(f"Ступень 2, признаки: контрольные суммы РАЗЛИЧАЮТСЯ, записей -- {len(changed)}")
    for key, was, now in changed[:limit]:
        print(f"    запись {key}:")
        print(f"        было : {was}")
        print(f"        стало: {now}")
    if len(changed) > limit:
        print(f"    ... и ещё {len(changed) - limit}")
    return changed


def compare_predictions(before, after, limit):
    """Сравнивает предсказания модели."""
    pb, pa = before.get("model_predictions", {}), after.get("model_predictions", {})
    keys = sorted(set(pb) | set(pa), key=int)
    changed = [(k, pb.get(k, "<нет>"), pa.get(k, "<нет>")) for k in keys if pb.get(k) != pa.get(k)]

    print(f"Ступень 3, модель: изменилось предсказаний -- {len(changed)} из {len(keys)}")
    for key, was, now in changed[:limit]:
        print(f"    запись {key}: {was} -> {now}")
    if len(changed) > limit:
        print(f"    ... и ещё {len(changed) - limit}")
    return changed


def compare_metrics(name, before, after):
    """Печатает метрики до и после с дельтой."""
    print(f"Метрики, {name}:")
    keys = ["tp", "tn", "fp", "fn", "precision", "recall", "f1",
            "F1 (weighted)", "F1_weighted_std", "F1 (macro)", "F1_macro_std",
            "Accuracy", "Accuracy_std"]
    changed = False
    for key in keys:
        was, now = before.get(key), after.get(key)
        if was is None or now is None:
            continue
        mark = ""
        if was != now:
            changed = True
            delta = now - was
            mark = f"   ({delta:+.6f})" if isinstance(delta, float) else f"   ({delta:+d})"
        print(f"    {key:<10} {was!s:<12} -> {now!s:<12}{mark}")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Сверка двух срезов результатов классификации")
    parser.add_argument("before", help="срез до изменений")
    parser.add_argument("after", help="срез после изменений")
    parser.add_argument("--limit", type=int, default=25, help="сколько расхождений печатать подробно")
    args = parser.parse_args()

    before, after = load(args.before), load(args.after)

    print(f"было : {args.before}")
    print(f"стало: {args.after}")
    print("-" * 70)

    verdicts = compare_verdicts(before.get("heuristic", {}), after.get("heuristic", {}), args.limit)
    print()
    features = compare_features(before, after, args.limit)
    print()
    predictions = compare_predictions(before, after, args.limit)
    print()
    m1 = compare_metrics("эвристика", before.get("heuristic_metrics", {}), after.get("heuristic_metrics", {}))
    print()
    m2 = compare_metrics("эвристика + модель", before.get("model_metrics", {}), after.get("model_metrics", {}))
    m3 = False
    if before.get("cv_metrics") or after.get("cv_metrics"):
        print()
        m3 = compare_metrics("перекрёстная проверка", before.get("cv_metrics", {}), after.get("cv_metrics", {}))
    print("-" * 70)

    differs = bool(verdicts or features or predictions or m1 or m2 or m3)
    print("ИТОГ: результаты различаются" if differs else "ИТОГ: результаты совпадают полностью")
    return 1 if differs else 0


if __name__ == "__main__":
    sys.exit(main())
