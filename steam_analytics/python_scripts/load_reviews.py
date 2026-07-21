import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Настройки подключения к PostgreSQL

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_NAME = os.getenv('DB_NAME')

# Путь к вашему CSV-файлу (проверьте, что путь правильный)
CSV_PATH = r'C:\Users\Admin\Desktop\Проект аналитика\Сырые данные\steam_dataset_2025_csv\reviews.csv'

# Колонки, которые нам нужны (в точности как в заголовке CSV)
expected_columns = [
    'recommendationid',
    'appid',
    'author_steamid',
    'author_num_reviews',
    'author_playtime_forever',
    'language',
    'voted_up',
    'written_during_early_access'
]

print("Чтение CSV...")

# Читаем CSV с явными параметрами
df = pd.read_csv(
    CSV_PATH,
    encoding='utf-8',
    quotechar='"',                 # кавычки, которыми обрамлены текстовые поля
    on_bad_lines='skip',           # пропускаем строки, которые не удаётся разобрать
    usecols=expected_columns,      # берём только нужные колонки
    engine='python'                # более гибкий парсер для сложных строк
)

# Удаляем строки, где recommendationid или appid отсутствуют (NULL)
df = df.dropna(subset=['recommendationid', 'appid'])

# Преобразуем типы данных для совместимости с PostgreSQL
df['recommendationid'] = df['recommendationid'].astype(int)
df['appid'] = df['appid'].astype(int)
df['author_steamid'] = df['author_steamid'].astype('int64')
df['author_num_reviews'] = df['author_num_reviews'].fillna(0).astype(int)
df['author_playtime_forever'] = df['author_playtime_forever'].fillna(0).astype(int)

print(f"Загружено строк: {len(df)} (после очистки)")

# Подключаемся к PostgreSQL
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

print("Загрузка в PostgreSQL...")
df.to_sql(
    'reviews',
    engine,
    if_exists='append',   # добавляем данные в существующую таблицу
    index=False,
    method='multi',
    chunksize=10000
)

print("Готово!")