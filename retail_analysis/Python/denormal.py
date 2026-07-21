from pathlib import Path
import pandas as pd

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent

OUTPUT_DIR = BASE_DIR.parent/ "Денормализация"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILE_PATH = BASE_DIR.parent / "Очищенные данные"

# Загрузка всех CSV
df = pd.read_csv(FILE_PATH / "cleaned_customer_data.csv")
products = pd.read_csv(FILE_PATH / "cleaned_product_data.csv")
transactions = pd.read_csv(FILE_PATH / "cleaned_sales_data.csv")
stores = pd.read_csv(FILE_PATH / "cleaned_store_data.csv")

# Создание витрины промежуточными переменными
step1 = df.merge(transactions, on = "customer_id", how = "inner")
print(f"Проверка слияния: {step1.shape[0]} строк")
      
step2 = step1.merge(products, on = "product_id", how = "inner")
print(f"Проверка слияния: {step2.shape[0]} строк")

final = step2.merge(stores, on = "store_id", how = "inner")

# Исключение из витрины ненужных колонок
col_drop = ["missing_customer", "missing_product", "missing_store"]
final = final.drop(columns=col_drop)

# Приведение даты к правильному типу (после чтения CSV она стала строкой)
final["date"] = pd.to_datetime(final["date"])

# ОЦЕНОЧНАЯ выручка (на основе list_price и скидки, фактическая цена продажи неизвестна)
# Допущение: list_price не менялся в течение периода, скидка применялась к list_price.
final["estimated_revenue"] = final["quantity"] * final["list_price"] * (1 - final["discount"])

# Финальная проверка
print(f"Проверка финального слияния: {final.shape[0]} строк, {final.shape[1]} столбца")
final.info()

OUTPUT_PATH = OUTPUT_DIR / "denormal.csv"
final.to_csv (OUTPUT_PATH, index=False)
print(f"Витрина сохранена в {OUTPUT_PATH}")