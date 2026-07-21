from pathlib import Path
import pandas as pd

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR.parent.parent / "Очищенные данные"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_PATH = BASE_DIR.parent.parent / "Сырые данные" 
FILE_PATH.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(FILE_PATH / "product_data.csv")


# Разделители.
SEP = "=" * 80
SUBSEP = "-" * 80


print(SEP) # ---------------------------------
# Первичный анализ.
print(df.head(20))

print(SEP) # ---------------------------------
#Информация о столбцах и пропусках
df.info()

print("\n")
print("Анализ количества пропусков:")
print(df.isnull().sum())
    
print(SUBSEP) # ---------------------------------
# Анализ дубликатов.
print("Полных дубликтов:")
print(df.duplicated().sum())
# print(df[df.duplicated()])


print(SUBSEP) # ---------------------------------
# Дубликаты в ID
print(f"Повторяющиеся product_id: {df.duplicated(subset=["product_id"]).sum()}")

print(SUBSEP)  # ---------------------------------
# Выявление аномальных значений
print("Анализ аномалий в ценах:")
print(df.describe())

print(SUBSEP) # ---------------------------------
# Наличие опечаток и несоответствий.
print("Уникальные категории:")
print(df["category"].value_counts())
print("\n")
print("Уникальные цвета:")
print(df["color"].value_counts())
print("\n")
print("Уникальные размеры:")
print(df["size"].value_counts())
print("\n")
print("Уникальные рекомендуемые сезоны:")
print(df["season"].value_counts())
print("\n")
print("Уникальные поставщики")
print(df["supplier"].value_counts())


print("\n")
print(SEP) # ---------------------------------
# Заменя "???" в столбце "category" на "Unknown"
df["category"] = df["category"].replace("???", "Unknown")

# Замена пропусков в столбце "color" на "Unknown"
df["color"] = df["color"].fillna("Unknown")

# Замена некорректного "Fall" в столбце "season" на "Autumn"
df["season"] = df["season"].replace("Fall", "Autumn")

print("Проверка корректности заполнения пропусков и очистки данных:")
print("Анализ количества пропусков:")
print(df.isnull().sum())
print("\n")
print("Уникальные категории:")
print(df["category"].value_counts())
print("\n")
print("Уникальные рекомендуемые сезоны:")
print(df["season"].value_counts())

print(SEP) # ---------------------------------

OUTPUT_PATH = OUTPUT_DIR / "cleaned_product_data.csv"
df.to_csv (OUTPUT_PATH, index=False)
print(f"Очищенные данные сохранены в {OUTPUT_PATH}")