import json
import webbrowser
import os
import time
from bs4 import BeautifulSoup
from Heuristic import get_genuine, LayoutError, TitleTypeError, DataTypeError
from Table import Table

def create_error_report(record_name, html_text, mismatch_info):
    """Создает HTML-файл для отчета об ошибке."""
    report_html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <title>Отчет о несоответствии</title>
        <style>
            body {{ font-family: sans-serif; padding: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #d9534f; }}
            pre {{ background: #eee; padding: 15px; border-radius: 4px; white-space: pre-wrap; word-wrap: break-word; font-family: monospace; }}
            table, th, td {{ border: 1px solid #ddd; border-collapse: collapse; }}
            th, td {{ padding: 8px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Обнаружено несоответствие в записи: {record_name}</h1>
            <hr>
            <h2>Информация о несоответствии:</h2>
            <pre>{mismatch_info}</pre>
            <h2>Содержимое таблицы:</h2>
            <div>{html_text}</div>
        </div>
    </body>
    </html>
    """
    report_filename = "mismatch_report.html"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_html)
    return report_filename

def calculate_f_score(tp, tn, fp, fn):
    """Расчет точности, полноты и F1-меры."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return precision, recall, f1_score

def audit_dataset(json_file_path):
    """Основная функция-аудитор."""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{json_file_path}' не найден.")
        return
    except json.JSONDecodeError:
        print(f"Ошибка: Не удалось прочитать JSON из файла '{json_file_path}'.")
        return

    tp, tn, fp, fn = 0, 0, 0, 0

    print("Начинаем аудит набора данных...")
    
    sorted_keys = sorted(data.keys(), key=int)

    for key in sorted_keys:
        record = data[key]
        record_name = record.get('name', f'Запись {key}')
        html_text = record.get('html_text', '')
        human_verification = record.get('verification', 'None')

        if not html_text or human_verification == 'None':
            continue

        program_thinks_genuine = False
        program_error_details = None
        
        try:
            soup = BeautifulSoup(html_text, "html.parser")
            table_element = soup.find("table")
            
            if table_element:
                table_original = Table(table_element)
                
                program_thinks_genuine = True
                table = get_genuine(table_original) # Если не будет ошибки, значит, genuine
            else:
                raise LayoutError("Тег <table> не найден в html_text.")

        except (TitleTypeError, DataTypeError, LayoutError) as e:
            program_thinks_genuine = False
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Сохраняем и тип ошибки, и ее текст
            program_error_details = f"{e.__class__.__name__}: {e}"

        human_thinks_genuine = (human_verification == 'genuine')

        mismatch = False
        mismatch_info = ""

        if human_thinks_genuine and program_thinks_genuine:
            tp += 1
        elif not human_thinks_genuine and not program_thinks_genuine:
            tn += 1
        elif not human_thinks_genuine and program_thinks_genuine:
            fp += 1
            mismatch = True
            mismatch_info = (
                f"Человек разметил как 'no genuine', но эвристика get_genuine УСПЕШНО отработала.\n"
                f"Это ложноположительное срабатывание (FP)."
            )
        elif human_thinks_genuine and not program_thinks_genuine:
            fn += 1
            mismatch = True
            # --- И ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Добавляем детали ошибки в отчет
            mismatch_info = (
                f"Человек разметил как 'genuine', но эвристика get_genuine ВЫЗВАЛА ОШИБКУ.\n"
                f"Детали ошибки: {program_error_details}\n"
                f"Это ложноотрицательное срабатывание (FN)."
            )
        
        if mismatch:
            print(f"\n!!! Найдено несоответствие в записи: {record_name} !!!")
            print(mismatch_info)
            
            report_file = create_error_report(record_name, html_text, mismatch_info)
            
            webbrowser.open('file://' + os.path.realpath(report_file))
            print(f"Отчет '{report_file}' был создан и открыт в браузере.")
            
            input("Нажмите Enter, чтобы продолжить аудит следующих записей...")
            print("-" * 50)

    print("\n\n" + "="*25 + " Аудит завершен " + "="*25)
    total_verified = tp + tn + fp + fn
    if total_verified == 0:
        print("Не найдено ни одной записи, проверенной вручную (кроме 'None'). Метрики не могут быть рассчитаны.")
        return

    print(f"Всего обработано записей с ручной разметкой: {total_verified}")
    print(f"  - Истинно положительные (TP): {tp}")
    print(f"  - Истинно отрицательные (TN): {tn}")
    print(f"  - Ложноположительные (FP):  {fp}")
    print(f"  - Ложноотрицательные (FN):  {fn}")
    
    precision, recall, f1_score = calculate_f_score(tp, tn, fp, fn)
    
    print("\n" + "-"*20 + " Итоговые метрики " + "-"*20)
    print(f"  - Точность (Precision): {precision:.2%}")
    print(f"  - Полнота (Recall):    {recall:.2%}")
    print(f"  - F1-мера (F1-Score):  {f1_score:.2%}")
    print("="*68)


if __name__ == '__main__':
    dataset_file = 'verified_dataset.json' 
    audit_dataset(dataset_file)
