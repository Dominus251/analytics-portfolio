import csv

file_path = r'C:\Users\Admin\Desktop\Проект аналитика\Сырые данные\steam_dataset_2025_csv\reviews.csv'

with open(file_path, 'r', encoding='utf-8') as f:
    # Прочитаем первые 5 строк
    lines = []
    for i in range(5):
        line = f.readline()
        if not line:
            break
        lines.append(line)

# Покажем строки
for i, line in enumerate(lines, 1):
    print(f"Строка {i}: {repr(line)}")