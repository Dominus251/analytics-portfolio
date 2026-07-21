from pathlib import Path
import pandas as pd

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR.parent.parent / "Очищенные данные"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_PATH = BASE_DIR.parent.parent / "Сырые данные" 
FILE_PATH.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(FILE_PATH / "sales_data.csv")
products = pd.read_csv(OUTPUT_DIR / "cleaned_product_data.csv")
customers = pd.read_csv(OUTPUT_DIR / "cleaned_customer_data.csv")
stores = pd.read_csv(OUTPUT_DIR / "cleaned_store_data.csv")

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
print(f"Поторяющиеся trandsction_id: {df.duplicated(subset=["transaction_id"]).sum()}")

print(SUBSEP)  # ---------------------------------
# Флаги целостности ключей (True = проблема, ключ отсутствует в справочнике)
df["missing_customer"] = ~df["customer_id"].isin(customers["customer_id"])
df["missing_product"]  = ~df["product_id"].isin(products["product_id"])
df["missing_store"]    = ~df["store_id"].isin(stores["store_id"])

print("Замечания по качеству данных (флаги созданы):")
print(f"- Транзакций с отсутствующим customer_id: {df['missing_customer'].sum()}")
print(f"- Транзакций с отсутствующим product_id : {df['missing_product'].sum()}")
print(f"- Транзакций с отсутствующим store_id   : {df['missing_store'].sum()}")

print(SUBSEP)  # ---------------------------------
# Выявление аномальных значений.
print("Анализ на аномальные продажи:")
print(df["quantity"].describe())
print("\n")
print("Анализ аномальных скидок:")
print(df["discount"].describe().round(4))


print("\n")
print(SEP) # ---------------------------------
## Битые ключи я оставляю намеренно, так как при создании витрины они будут исключены автоматически, но создаю флаги, для быстрого включения в анализ в случае нужды.
# Исправление NaN в столбце "discount" и добавление флага если скидка была неизвестна.
df["discount_missing"] = df["discount"].isnull()
df["discount"] = df["discount"].fillna(0)

#Приведение даты к типу 
df["date"] = pd.to_datetime(df["date"], errors="coerce")

df.info()
print("\n")
print(df.isnull().sum())

print(SEP) # ---------------------------------

OUTPUT_PATH = OUTPUT_DIR / "cleaned_sales_data.csv"
df.to_csv (OUTPUT_PATH, index=False)
print(f"Очищенные данные сохранены в {OUTPUT_PATH}")