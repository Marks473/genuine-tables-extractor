from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import comparisonML
import Heuristic
from CellType import DataType
import joblib
import pandas as pd
from Table import Table

def train_and_save_model(model_name='RandomForest', save_path='trained_model.pkl', json_path='verified_dataset.json'):
    """
    Обучение модели и сохранение на диск

    Args:
        model_name: Название модели для обучения
        save_path: Путь для сохранения модели
     """
    df = pd.read_json(json_path).T
    X = df.html_text
    y = df.verification

    X_parameters = X.apply(comparisonML.get_parameters)

    # Кодирование меток
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Создание модели
    if model_name == 'RandomForest':
        base_model = RandomForestClassifier(
            n_estimators=200, max_depth=15, min_samples_split=5,
            min_samples_leaf=2, max_features='sqrt', bootstrap=True,
            class_weight='balanced', random_state=42, n_jobs=-1, verbose=0
        )
    elif model_name == 'XGBoost':
        from xgboost import XGBClassifier
        class_counts = pd.Series(y_encoded).value_counts()
        class_ratio = class_counts.max() / class_counts.min()
        base_model = XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=class_ratio,
            random_state=42, n_jobs=-1, eval_metric='logloss',
            use_label_encoder=False
        )
    elif model_name == 'LightGBM':
        from lightgbm import LGBMClassifier
        class_counts = pd.Series(y_encoded).value_counts()
        class_ratio = class_counts.max() / class_counts.min()
        base_model = LGBMClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.1,
            subsample=0.8, colsample_bytree=0.8, scale_pos_weight=class_ratio,
            random_state=42, n_jobs=-1, verbose=-1
        )
    else:
        raise ValueError(f"Неизвестная модель: {model_name}")

    # Создание обертки
    wrapper = comparisonML.GenuineModelWrapper(base_model, le)

    # Обучение
    wrapper.fit(X_parameters, y_encoded)

    # Сохранение
    joblib.dump(wrapper, save_path)

    return wrapper

class MLVerification:
    def __init__(self, model_path='trained_model.pkl'):
        self.wrapper = self.install_model(model_path)

    def install_model(self, model_path='trained_model.pkl'):
        wrapper = joblib.load(model_path)
        return wrapper

    def predict(self, table :Table) -> str:
        # Извлекаем признаки
        features = get_parameters_from_table(table)
        features_df = pd.DataFrame([features])
        prediction = self.wrapper.predict(features_df)[0]
        return prediction

def get_parameters_from_table(table: Table) -> pd.Series:
    """Извлечение признаков из объекта Table"""
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

    # Сначала эвристика: не прошедшую проверку структуры таблицу модель
    # не классифицирует, GenuineModelWrapper сразу отвечает "no genuine".
    # Проверяется копия: разбор меняет классы ячеек и объединения
    series['consistency'] = 1 if Heuristic.is_genuine(table.copy) else -1

    return series


if __name__ == "__main__":
    from bs4 import BeautifulSoup

    train_and_save_model()
    html_example = """
    <table>
        <tr><th>Продукт</th><th>Цена</th></tr>
        <tr><td>Яблоко</td><td>100</td></tr>
        <tr><td>Молоко</td><td>80</td></tr>
    </table>
    """
    verifier = MLVerification(model_path='trained_model.pkl')
    soup = BeautifulSoup(html_example, "html.parser")
    table_soup = soup.find_all("table", recursive=True)[0]
    my_table_object = Table(table_soup)
    result = verifier.predict(my_table_object)
    print("\n" + "=" * 40)
    print("Результат предсказания:")
    print(f"Класс таблицы: {result}")
    print("=" * 40)
