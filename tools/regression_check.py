"""
Снятие контрольного среза результатов классификации.

Срез фиксирует поведение конвейера на размеченном наборе данных и позволяет
убедиться, что правки кода не сдвинули результат. Состоит из четырёх ступеней:

1. Эвристика -- вердикт ``Heuristic.get_genuine`` по каждой записи набора.
2. Признаки  -- вектор, который получает модель (``comparisonML.get_parameters``).
3. Модель    -- предсказания уже обученной модели из ``trained_model.pkl``.
4. Метрики   -- сводные показатели качества по ручной разметке.

Модель при снятии среза не переобучается: берётся готовый файл модели.
Благодаря этому любое расхождение в предсказаниях указывает на изменение
разбора таблицы, а не на случайность обучения.

Запуск:
    python tools/regression_check.py --out snapshot.json
"""

import argparse
import hashlib
import json
import os
import sys

# Модули программы лежат на уровень выше каталога tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import pandas as pd
from bs4 import BeautifulSoup

import comparisonML
from Heuristic import get_genuine, LayoutError, TitleTypeError, DataTypeError
from Table import Table

PROGRAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATASET = os.path.join(PROGRAM_DIR, "verified_dataset.json")
DEFAULT_MODEL = os.path.join(PROGRAM_DIR, "trained_model.pkl")

FEATURE_KEYS = ["numeric", "form", "string", "media", "other", "no_data", "link", "consistency"]
HEURISTIC_ERRORS = (LayoutError, TitleTypeError, DataTypeError)


def load_dataset(path):
    """Читает размеченный набор данных и возвращает записи в порядке номеров."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return sorted(data.items(), key=lambda item: int(item[0]))


def heuristic_verdict(html_text):
    """
    Прогоняет эвристику по одной таблице.

    Возвращает пару (вердикт, пояснение), где вердикт -- 'genuine' либо имя
    класса возбуждённого исключения. Пояснение содержит текст ошибки.
    """
    try:
        soup = BeautifulSoup(html_text, "html.parser")
        table_element = soup.find("table")
        if table_element is None:
            raise LayoutError("Тег <table> не найден в html_text.")
        get_genuine(Table(table_element))
        return "genuine", ""
    except HEURISTIC_ERRORS as e:
        return e.__class__.__name__, str(e)


def f_score(tp, tn, fp, fn):
    """Точность, полнота и F1-мера по счётчикам ошибок первого и второго рода."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def collect_heuristic(records):
    """Ступень 1: вердикты эвристики и метрики относительно ручной разметки."""
    verdicts = {}
    tp = tn = fp = fn = 0

    for key, record in records:
        html_text = record.get("html_text", "")
        human = record.get("verification", "None")
        if not html_text or human == "None":
            continue

        verdict, message = heuristic_verdict(html_text)
        verdicts[key] = {"verdict": verdict, "message": message}

        program_genuine = verdict == "genuine"
        human_genuine = human == "genuine"
        if human_genuine and program_genuine:
            tp += 1
        elif not human_genuine and not program_genuine:
            tn += 1
        elif not human_genuine and program_genuine:
            fp += 1
        else:
            fn += 1

    return verdicts, f_score(tp, tn, fp, fn)


def collect_features(records):
    """Ступень 2: матрица признаков и её контрольная сумма."""
    features = {}
    failures = {}

    for key, record in records:
        html_text = record.get("html_text", "")
        if not html_text:
            continue
        try:
            series = comparisonML.get_parameters(html_text)
            features[key] = [round(float(series[name]), 12) for name in FEATURE_KEYS]
        except Exception as e:
            failures[key] = f"{e.__class__.__name__}: {e}"

    canonical = json.dumps(features, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return features, failures, digest


def collect_predictions(records, features, model_path):
    """Ступень 3: предсказания готовой модели и метрики по ручной разметке."""
    if not os.path.exists(model_path):
        return {}, {"error": "файл модели не найден"}

    bundle = joblib.load(model_path)
    model = bundle["model"] if isinstance(bundle, dict) and "model" in bundle else bundle

    keys = list(features.keys())
    frame = pd.DataFrame([features[k] for k in keys], columns=FEATURE_KEYS, index=keys)
    labels = model.predict(frame)

    predictions = {key: str(label) for key, label in zip(keys, labels)}

    human_by_key = {key: record.get("verification", "None") for key, record in records}
    tp = tn = fp = fn = 0
    for key, label in predictions.items():
        human = human_by_key.get(key, "None")
        if human == "None":
            continue
        program_genuine = label == "genuine"
        human_genuine = human == "genuine"
        if human_genuine and program_genuine:
            tp += 1
        elif not human_genuine and not program_genuine:
            tn += 1
        elif not human_genuine and program_genuine:
            fp += 1
        else:
            fn += 1

    return predictions, f_score(tp, tn, fp, fn)


def collect_cv_metrics(records, features):
    """
    Ступень 4: перекрёстная проверка со случайным лесом.

    Повторяет схему, по которой построена сравнительная таблица моделей
    в отчёте: пятикратная стратифицированная проверка с фиксированными
    зёрнами, поэтому результат воспроизводим.
    """
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold
    from sklearn.preprocessing import LabelEncoder

    labelled = {key: record.get("verification") for key, record in records}
    keys = [k for k in features if labelled.get(k) in {"genuine", "no genuine"}]
    if not keys:
        return {}

    frame = pd.DataFrame([features[k] for k in keys], columns=FEATURE_KEYS, index=range(len(keys)))
    encoder = LabelEncoder()
    target = encoder.fit_transform(np.array([labelled[k] for k in keys]))

    forest = RandomForestClassifier(
        n_estimators=200, max_depth=15, min_samples_split=5, min_samples_leaf=2,
        max_features="sqrt", bootstrap=True, class_weight="balanced",
        random_state=42, n_jobs=-1, verbose=0,
    )
    wrapper = comparisonML.GenuineModelWrapper(forest, encoder)
    splitter = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    result = comparisonML.evaluate_model_with_cv(wrapper, frame, target, splitter, "Random Forest")
    # Время обучения меняется от запуска к запуску, для сверки оно бесполезно
    result.pop("Время (сек)", None)
    return {k: (round(float(v), 6) if isinstance(v, float) else v) for k, v in result.items()}


def build_snapshot(dataset_path, model_path, with_cv=False):
    """Собирает полный срез по всем ступеням конвейера."""
    records = load_dataset(dataset_path)

    print(f"Записей в наборе: {len(records)}")
    print("Ступень 1: эвристика...")
    verdicts, heuristic_metrics = collect_heuristic(records)

    print("Ступень 2: признаки...")
    features, feature_failures, digest = collect_features(records)

    print("Ступень 3: модель...")
    predictions, model_metrics = collect_predictions(records, features, model_path)

    cv_metrics = {}
    if with_cv:
        print("Ступень 4: перекрёстная проверка...")
        cv_metrics = collect_cv_metrics(records, features)

    return {
        "cv_metrics": cv_metrics,
        "dataset": os.path.basename(dataset_path),
        "records": len(records),
        "heuristic": verdicts,
        "heuristic_metrics": heuristic_metrics,
        "features": features,
        "feature_failures": feature_failures,
        "features_sha256": digest,
        "model_predictions": predictions,
        "model_metrics": model_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Снятие контрольного среза результатов классификации")
    parser.add_argument("--out", required=True, help="куда записать срез (JSON)")
    parser.add_argument("--dataset", default=DEFAULT_DATASET, help="размеченный набор данных")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="файл обученной модели")
    parser.add_argument("--cv", action="store_true", help="добавить перекрёстную проверку")
    args = parser.parse_args()

    snapshot = build_snapshot(args.dataset, args.model, with_cv=args.cv)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=1, sort_keys=True)

    print()
    print(f"Срез сохранён: {args.out}")
    print(f"Контрольная сумма признаков: {snapshot['features_sha256']}")
    print(f"Эвристика: {snapshot['heuristic_metrics']}")
    print(f"Модель:    {snapshot['model_metrics']}")
    if snapshot.get("cv_metrics"):
        print(f"Проверка:  {snapshot['cv_metrics']}")


if __name__ == "__main__":
    main()
