import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import f1_score, accuracy_score
from sklearn.inspection import permutation_importance
from bs4 import BeautifulSoup
from Table import Table
from CellType import DataType
import Heuristic
import warnings
import os
import time

warnings.filterwarnings('ignore')


def get_parameters(str: str) -> pd.Series:
    """Извлечение признаков из HTML-таблицы"""
    soup = BeautifulSoup(str, "html.parser")
    table_soup = soup.find_all("table", recursive=True)[0]
    table = Table(table_soup)

    index_keys = ['numeric', 'form', 'string', 'media', 'other', 'no_data', 'link', 'consistency']
    series = pd.Series(data=0, index=index_keys, dtype=float)
    table_value = table.table
    sum_type = 0

    for i in range(len(table_value)):
        for j in range(len(table_value[i])):
            sum_type += 1
            match table_value[i][j].type:
                case DataType.NO_DATA:
                    series['no_data'] += 1
                case DataType.LINK:
                    series['link'] += 1
                case DataType.GENUINE:
                    series['numeric'] += 1
                case DataType.STRING:
                    series['string'] += 1
                case DataType.OTHER:
                    series['other'] += 1
                case DataType.FORM:
                    series['form'] += 1
                case DataType.MEDIA:
                    series['media'] += 1

    if sum_type > 0:
        series = series / sum_type
    else:
        series[:] = -1

    try:
        Heuristic.get_genuine(table)
        series['consistency'] = 1
    except (Heuristic.TitleTypeError, Heuristic.DataTypeError, Heuristic.LayoutError):
        series['consistency'] = -1

    return series


class GenuineModelWrapper:
    """Обертка модели с логикой обработки consistency"""

    def __init__(self, model, label_encoder, no_genuine_label='no genuine'):
        self.model = model
        self.label_encoder = label_encoder
        self.no_genuine_label = no_genuine_label
        self.use_features = ['numeric', 'form', 'string', 'media', 'other', 'no_data', 'link']

    def fit(self, X, y):
        """Обучение только на данных с consistency == 1"""
        mask = X['consistency'] == 1
        X_train = X.loc[mask, self.use_features]
        y_train = y[mask]
        self.model.fit(X_train, y_train)
        return self

    def predict(self, X):
        """Предсказание с учетом consistency"""
        predictions = np.empty(len(X), dtype=object)
        mask = X['consistency'] == 1

        # Для consistency == 1 делаем обычное предсказание
        if mask.sum() > 0:
            X_predict = X.loc[mask, self.use_features]
            pred_encoded = self.model.predict(X_predict)
            pred_labels = self.label_encoder.inverse_transform(pred_encoded)
            predictions[mask] = pred_labels

        # Для consistency != 1 возвращаем "no genuine"
        predictions[~mask] = self.no_genuine_label

        return predictions

    def get_feature_data(self, X):
        """Получить данные для расчета важности признаков"""
        mask = X['consistency'] == 1
        return X.loc[mask, self.use_features]


def evaluate_model_with_cv(wrapper, X, y, cv, model_name):
    """Кросс-валидация с учетом consistency"""
    f1_weighted_scores = []
    f1_macro_scores = []
    accuracy_scores = []
    fit_times = []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Измеряем время обучения
        start_time = time.time()
        wrapper.fit(X_train, y_train)
        fit_time = time.time() - start_time
        fit_times.append(fit_time)

        # Предсказание
        predictions = wrapper.predict(X_test)
        y_test_labels = wrapper.label_encoder.inverse_transform(y_test)

        # Кодируем для расчета метрик
        all_labels = list(set(y_test_labels) | set(predictions))
        le_temp = LabelEncoder()
        le_temp.fit(all_labels)

        y_true_encoded = le_temp.transform(y_test_labels)
        y_pred_encoded = le_temp.transform(predictions)

        # Расчет метрик для данного фолда
        f1_w = f1_score(y_true_encoded, y_pred_encoded, average='weighted', zero_division=0)
        f1_m = f1_score(y_true_encoded, y_pred_encoded, average='macro', zero_division=0)
        acc = accuracy_score(y_true_encoded, y_pred_encoded)

        f1_weighted_scores.append(f1_w)
        f1_macro_scores.append(f1_m)
        accuracy_scores.append(acc)

    return {
        'Модель': model_name,
        'F1 (weighted)': np.mean(f1_weighted_scores),
        'F1_weighted_std': np.std(f1_weighted_scores),
        'F1 (macro)': np.mean(f1_macro_scores),
        'F1_macro_std': np.std(f1_macro_scores),
        'Accuracy': np.mean(accuracy_scores),
        'Accuracy_std': np.std(accuracy_scores),
        'Время (сек)': np.mean(fit_times)
    }


def calculate_permutation_importance(wrapper, X, y, cv, model_name):
    """Расчет permutation importance на кросс-валидации"""
    use_features = ['numeric', 'form', 'string', 'media', 'other', 'no_data', 'link']
    importances_list = []

    for train_idx, test_idx in cv.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Обучаем на consistency == 1
        wrapper.fit(X_train, y_train)

        # Важность на тестовых данных с consistency == 1
        mask_test = X_test['consistency'] == 1
        if mask_test.sum() > 0:
            X_test_consistent = X_test.loc[mask_test, use_features]
            y_test_consistent = y_test[mask_test]

            imp = permutation_importance(
                wrapper.model, X_test_consistent, y_test_consistent,
                n_repeats=10, scoring='f1_weighted', random_state=42, n_jobs=-1
            )
            importances_list.append(imp.importances_mean)

    if importances_list:
        return np.mean(importances_list, axis=0)
    else:
        return np.zeros(len(use_features))


if __name__ == "__main__":
    # Градиентный бустинг и графики нужны только при сравнительном прогоне,
    # поэтому импортируются здесь: разбор таблиц от них не зависит
    import matplotlib.pyplot as plt
    import seaborn as sns
    from catboost import CatBoostClassifier
    from lightgbm import LGBMClassifier
    from xgboost import XGBClassifier

    # Загрузка данных
    df = pd.read_json('verified_dataset.json').T
    X = df.html_text
    y = df.verification

    # Извлечение признаков
    X_parameters = X.apply(get_parameters)

    # Кодирование меток
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Вычисление соотношения классов
    class_counts = pd.Series(y_encoded).value_counts()
    class_ratio = class_counts.max() / class_counts.min()

    # Создание директории для CatBoost
    os.makedirs('./catboost_temp', exist_ok=True)

    # Базовые модели
    base_models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_split=5, min_samples_leaf=2,
            max_features='sqrt', bootstrap=True, class_weight='balanced',
            random_state=42, n_jobs=-1, verbose=0
        ),
        'XGBoost': XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8,
            colsample_bytree=0.8, scale_pos_weight=class_ratio, random_state=42,
            n_jobs=-1, eval_metric='logloss', use_label_encoder=False
        ),
        'LightGBM': LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8,
            colsample_bytree=0.8, scale_pos_weight=class_ratio, random_state=42,
            n_jobs=-1, verbose=-1
        ),
        'CatBoost': CatBoostClassifier(
            iterations=200, depth=6, learning_rate=0.1, auto_class_weights='Balanced',
            random_state=42, verbose=False, thread_count=-1, train_dir='./catboost_temp',
            allow_writing_files=True
        ),
        'SVM (RBF)': SVC(
            C=1.0, kernel='rbf', gamma='scale', class_weight='balanced',
            random_state=42, probability=True
        ),
        'Logistic Regression': LogisticRegression(
            C=1.0, penalty='l2', solver='lbfgs', class_weight='balanced',
            max_iter=1000, random_state=42, n_jobs=-1
        )
    }

    # Создание оберток для каждой модели
    model_wrappers = {
        name: GenuineModelWrapper(model, le)
        for name, model in base_models.items()
    }

    # Кросс-валидация
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # 1. ОЦЕНКА МОДЕЛЕЙ
    print("\n" + "=" * 120)
    print("\n📊 КРОСС-ВАЛИДАЦИЯ МОДЕЛЕЙ")
    print("\n" + "=" * 120)

    results = []
    for model_name, wrapper in model_wrappers.items():
        print(f"\n⏳ Обучение модели: {model_name}...")
        result = evaluate_model_with_cv(wrapper, X_parameters, y_encoded, cv, model_name)
        results.append(result)

    results_df = pd.DataFrame(results).sort_values('F1 (weighted)', ascending=False).reset_index(drop=True)

    print(f"\n{'№':<3} {'Модель':<25} {'F1 (weighted)':<25} {'F1 (macro)':<25} {'Accuracy':<20} {'Время (сек)':<12}")
    print("-" * 120)
    for idx, row in results_df.iterrows():
        rank = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "  "
        print(
            f"{rank} {idx + 1:<2} "
            f"{row['Модель']:<25} "
            f"{row['F1 (weighted)']:.4f} ± {row['F1_weighted_std']:.4f}      "
            f"{row['F1 (macro)']:.4f} ± {row['F1_macro_std']:.4f}      "
            f"{row['Accuracy']:.4f} ± {row['Accuracy_std']:.4f}   \t"
            f"{row['Время (сек)']:.2f}"
        )

    # 2. PERMUTATION IMPORTANCE
    print("\n" + "=" * 120)
    print("\n🔍 ПЕРМУТАЦИОННАЯ ВАЖНОСТЬ ПРИЗНАКОВ НА КРОСС-ВАЛИДАЦИИ")
    print("\n" + "=" * 120)

    use_features = ['numeric', 'form', 'string', 'media', 'other', 'no_data', 'link']

    # Собираем все важности в словарь
    importance_data = {}

    for model_name, wrapper in model_wrappers.items():
        print(f"\n⏳ Расчет важности для: {model_name}...")
        importances = calculate_permutation_importance(
            wrapper, X_parameters, y_encoded, cv, model_name
        )
        importance_data[model_name] = importances

        print(f"\n{model_name}:")
        for feat, score in zip(use_features, importances):
            bar = "█" * int(score * 100)
            print(f"  {feat:<10}: {score:.5f} {bar}")

    # Создаем DataFrame для таблицы важности
    importance_df = pd.DataFrame(importance_data, index=use_features).T

    print("\n" + "=" * 120)
    print("\n📋 ТАБЛИЦА ПЕРМУТАЦИОННОЙ ВАЖНОСТИ ПРИЗНАКОВ")
    print("\n" + "=" * 120)
    print("\n", importance_df.round(5))

    # Визуализация таблицы важности с градиентом
    print("\n" + "=" * 120)
    print("\n🎨 СОЗДАНИЕ ВИЗУАЛИЗАЦИИ ВАЖНОСТИ ПРИЗНАКОВ")
    print("\n" + "=" * 120)

    # Создаем heatmap
    plt.figure(figsize=(12, 8))
    sns.heatmap(
        importance_df,
        annot=True,
        fmt='.4f',
        cmap='YlOrRd',  # Желто-оранжево-красный градиент
        linewidths=1,
        linecolor='white',
        cbar_kws={'label': 'Важность признака'},
        vmin=0,
        vmax=importance_df.max().max()
    )

    plt.title('Пермутационная важность признаков по моделям\n(на кросс-валидации, consistency=1)',
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Признаки (типы данных)', fontsize=12, fontweight='bold')
    plt.ylabel('Модели', fontsize=12, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()

    # Сохраняем
    plt.savefig('feature_importance_heatmap.png', dpi=300, bbox_inches='tight')
    print("\n✓ Heatmap важности сохранен в 'feature_importance_heatmap.png'")

    # Дополнительная визуализация: барплот для сравнения
    plt.figure(figsize=(14, 8))
    importance_df_melted = importance_df.reset_index().melt(
        id_vars='index',
        var_name='Признак',
        value_name='Важность'
    )
    importance_df_melted.rename(columns={'index': 'Модель'}, inplace=True)

    ax = sns.barplot(
        data=importance_df_melted,
        x='Признак',
        y='Важность',
        hue='Модель',
        palette='Set2'
    )

    plt.title('Сравнение важности признаков по моделям', fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Признаки (типы данных)', fontsize=12, fontweight='bold')
    plt.ylabel('Пермутационная важность', fontsize=12, fontweight='bold')
    plt.legend(title='Модель', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.tight_layout()

    plt.savefig('feature_importance_barplot.png', dpi=300, bbox_inches='tight')
    print("✓ Барплот важности сохранен в 'feature_importance_barplot.png'")

    # 3. КОРРЕЛЯЦИОННАЯ МАТРИЦА
    print("\n" + "=" * 120)
    print("\n📈 КОРРЕЛЯЦИОННАЯ МАТРИЦА ПРИЗНАКОВ")
    print("\n" + "=" * 120)

    # Берем только consistency == 1
    mask_consistent = X_parameters['consistency'] == 1
    X_consistent = X_parameters.loc[mask_consistent, use_features]

    correlation_matrix = X_consistent.corr()
    print("\n", correlation_matrix.round(3))

    # Визуализация корреляционной матрицы
    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, fmt='.3f', cmap='coolwarm',
                center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
    plt.title('Корреляционная матрица признаков (consistency=1)', fontsize=14, pad=20)
    plt.tight_layout()
    plt.savefig('correlation_matrix.png', dpi=300, bbox_inches='tight')
    print("\n✓ Корреляционная матрица сохранена в 'correlation_matrix.png'")

    print("\n" + "=" * 120)
    print("\n✅ ВСЕ РЕЗУЛЬТАТЫ УСПЕШНО СОХРАНЕНЫ:")
    print("   🖼️  feature_importance_heatmap.png - тепловая карта важности")
    print("   📊 feature_importance_barplot.png - барплот сравнения важности")
    print("   📈 correlation_matrix.png - корреляционная матрица")
    print("\n" + "=" * 120 + "\n")