from pathlib import Path
import pandas as pd

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR.parent.parent / "Очищенные данные"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_PATH = BASE_DIR.parent.parent / "Сырые данные" 
FILE_PATH.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(FILE_PATH / "store_data.csv")

# Разделители.
SEP = "=" * 80
SUBSEP = "-" * 80


print(SEP) # ---------------------------------
# Первичный анализ.
print(df.head(20))

print(SEP) # ---------------------------------
#Информация о столбцах и пропусках.
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
# Дубликаты в ID.
print(f"Поторяющиеся stotr_id: {df.duplicated(subset=["store_id"]).sum()}")

print(SUBSEP)  # ---------------------------------
# Выявление аномальных значений.
print("Анализ аномальных значений:")
print(df.describe())


print(SUBSEP) # ---------------------------------
# Наличие опечаток
print("Анализ уникальных наименований")
print(df["store_name"].value_counts())
print("Анализ уникальных наименований")
print(df["region"].value_counts())
print(SEP) # ---------------------------------

OUTPUT_PATH = OUTPUT_DIR / "cleaned_store_data.csv"
df.to_csv (OUTPUT_PATH, index=False)
print(f"Очищенные данные сохранены в {OUTPUT_PATH}")