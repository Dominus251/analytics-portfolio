from pathlib import Path
import pandas as pd

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR.parent.parent / "Очищенные данные"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_PATH = BASE_DIR.parent.parent / "Сырые данные" 
FILE_PATH.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(FILE_PATH / "customer_data.csv")

# Разделители.
SEP = "=" * 80
SUBSEP = "-" * 80


print(SEP) # ---------------------------------
# Первичный анализ.
print(df.head(10))

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

print(SUBSEP)  # ---------------------------------
# Наличие дубликатов ID.
print(f"Повторяющихся customer_id: {df.duplicated(subset=["customer_id"]).sum()}")

print(SUBSEP) # ---------------------------------
# Наличие аномалий в колонке возраста.
print("Статистика по возрасту:")
print(df["age"].describe())

print(SUBSEP) # ---------------------------------
# Наличие опечаток.
print("Уникальные города:")
print(df["city"].value_counts())
print("\n")
print("Уникальный гендер:")
print(df["gender"].value_counts())


print("\n")
print(SEP) # ---------------------------------
# Замена пропусков столбце "email" на "Unknown".
df["email"] = df["email"].fillna("Unknown")

# Заменя "???" в столбце "gender" на "Other"
df["gender"] = df["gender"].replace("???", "Other")

print("Проверка корректности заполнения пропусков и очистки данных:")
print("Анализ количества пропусков:")
print(df.isnull().sum())
print("\n")
print("Уникальный гендер:")
print(df["gender"].value_counts())

print(SEP) # ---------------------------------

OUTPUT_PATH = OUTPUT_DIR / "cleaned_customer_data.csv"
df.to_csv (OUTPUT_PATH, index=False)
print(f"Очищенные данные сохранены в {OUTPUT_PATH}")