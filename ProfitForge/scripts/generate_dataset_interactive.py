# generate_dataset_interactive.py
# Интерактивный генератор данных для Profit Forge Online.
# Версия 2.0: добавлены сессии, убраны страны, управление частотой сессий.

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ============================================================
# 1. ДИНАМИЧЕСКИЕ ПУТИ
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 2. ЗАПРОС ПАРАМЕТРОВ У ПОЛЬЗОВАТЕЛЯ
# ============================================================
print("=" * 60)
print("ГЕНЕРАТОР ДАННЫХ ДЛЯ МОБИЛЬНОЙ ИГРЫ")
print("Версия 2.0 (с сессиями)")
print("=" * 60)

# --- Основные параметры ---
BASE_PLAYERS = int(input("Сколько игроков создать? (например, 2000): ") or "2000")
RETENTION_RATE = float(input("Базовый Retention Rate (0.1-1.0, например 0.85): ") or "0.85")
MAX_PURCHASES_PAYING = int(input("Максимум покупок у платящих в месяц (например, 25): ") or "25")
MAX_PURCHASES_FREE = int(input("Максимум покупок у бесплатных в месяц (например, 6): ") or "6")
BASIC_PRICE = int(input("Цена подписки Basic (руб.): ") or "200")
PREMIUM_PRICE = int(input("Цена подписки Premium (руб.): ") or "500")

START_DATE = input("Дата начала периода (ГГГГ-ММ-ДД, по умолчанию 2020-01-01): ") or "2020-01-01"
END_DATE = input("Дата окончания периода (ГГГГ-ММ-ДД, по умолчанию 2024-01-01): ") or "2024-01-01"

# --- Сезонность ---
print("\nЗадайте веса сезонности для каждого месяца (через пробел, 12 чисел, по умолчанию: 1.0 0.8 0.9 1.1 0.6 1.4 1.6 1.5 0.5 0.9 0.7 0.3):")
MONTHLY_WEIGHTS_INPUT = input("Веса: ") or "1.0 0.8 0.9 1.1 0.6 1.4 1.6 1.5 0.5 0.9 0.7 0.3"
MONTHLY_WEIGHTS = [float(x) for x in MONTHLY_WEIGHTS_INPUT.split()]

# --- Скидки ---
print("\nЗадайте скидки для подписчиков (доли, например 0.05 = 5%):")
BASIC_DISCOUNT = float(input("Скидка Basic: ") or "0.05")
PREMIUM_DISCOUNT = float(input("Скидка Premium: ") or "0.10")

# --- Товары ---
print("\nНастройки товаров. Для каждой категории введите диапазон цен и вероятность (через пробел).")
print("Расходники (consumable):")
cons_low, cons_high, cons_prob = map(float, input("Мин Макс Вероятность (по умолчанию 20 400 0.7): ") or "20 400 0.7".split())
print("Бустеры (booster):")
boost_low, boost_high, boost_prob = map(float, input("Мин Макс Вероятность (по умолчанию 40 700 0.15): ") or "40 700 0.15".split())
print("Скины (skin):")
skin_low, skin_high, skin_prob = map(float, input("Мин Макс Вероятность (по умолчанию 300 2000 0.02): ") or "300 2000 0.02".split())

ITEM_CATEGORIES = {
    "consumable": {"price_range": (cons_low, cons_high), "prob": cons_prob},
    "booster":    {"price_range": (boost_low, boost_high), "prob": boost_prob},
    "skin":       {"price_range": (skin_low, skin_high), "prob": skin_prob}
}

# --- Поведенческие вероятности ---
print("\nПоведенческие вероятности (доли, по умолчанию нажмите Enter):")
REACTIVATION_RATE = float(input("Шанс возврата (по умолчанию 0.03): ") or "0.03")
UPGRADE_FREE_TO_BASIC = float(input("Шанс апгрейда Free->Basic (по умолчанию 0.03): ") or "0.03")
UPGRADE_BASIC_TO_PREMIUM = float(input("Шанс апгрейда Basic->Premium (по умолчанию 0.015): ") or "0.015")
NEW_SUB_CHANCE = float(input("Шанс старта подписки для Free (по умолчанию 0.05): ") or "0.05")

# --- Ивенты ---
print("\nПараметры ивентов:")
EVENT_PROB = float(input("Шанс ивента в месяц (по умолчанию 0.1667 = 1/6): ") or "0.1667")
EVENT_INSTALL_MULT_LOW = float(input("Мин множитель установок в ивент (по умолчанию 1.5): ") or "1.5")
EVENT_INSTALL_MULT_HIGH = float(input("Макс множитель установок в ивент (по умолчанию 3.0): ") or "3.0")
EVENT_RET_FACTOR_LOW = float(input("Мин штраф к удержанию ивентовых игроков (по умолчанию 0.7): ") or "0.7")
EVENT_RET_FACTOR_HIGH = float(input("Макс штраф к удержанию ивентовых игроков (по умолчанию 0.9): ") or "0.9")
EVENT_INSTALL_MULT = (EVENT_INSTALL_MULT_LOW, EVENT_INSTALL_MULT_HIGH)
EVENT_RET_FACTOR = (EVENT_RET_FACTOR_LOW, EVENT_RET_FACTOR_HIGH)

# --- Каналы маркетинга ---
print("\nМаркетинговые каналы. Введите веса и стоимость за установку (CPI) для Organic, Ads, Referral:")
print("Веса (доли, сумма не обязана быть 1, будет отнормирована):")
org_weight = float(input("Organic вес (по умолчанию 0.5): ") or "0.5")
ads_weight = float(input("Ads вес (по умолчанию 0.35): ") or "0.35")
ref_weight = float(input("Referral вес (по умолчанию 0.15): ") or "0.15")
CHANNEL_WEIGHTS = [org_weight, ads_weight, ref_weight]
print("CPI (руб. за установку):")
CHANNEL_COST_PER_INSTALL = {
    "Organic": float(input("Organic CPI (по умолчанию 0): ") or "0"),
    "Ads": float(input("Ads CPI (по умолчанию 150): ") or "150"),
    "Referral": float(input("Referral CPI (по умолчанию 50): ") or "50")
}

# --- Сессии ---
print("\nНастройка сессий (частота игры):")
MIN_SESSIONS_FREE = int(input("Минимум сессий для бесплатного игрока в месяц (по умолчанию 1): ") or "1")
MAX_SESSIONS_FREE = int(input("Максимум сессий для бесплатного игрока в месяц (по умолчанию 10): ") or "10")
MIN_SESSIONS_PAYING = int(input("Минимум сессий для платящего игрока в месяц (по умолчанию 5): ") or "5")
MAX_SESSIONS_PAYING = int(input("Максимум сессий для платящего игрока в месяц (по умолчанию 25): ") or "25")
SUBSCRIBER_SESSION_MULTIPLIER = float(input("Коэффициент количества сессий для подписчиков (например 1.5 = +50%): ") or "1.5")

CHANNELS = ["Organic", "Ads", "Referral"]

print("\nГенерация началась, подождите...")

# ============================================================
# 3. ГЕНЕРАЦИЯ ИГРОКОВ (без стран)
# ============================================================
np.random.seed(42)
date_range = pd.date_range(START_DATE, END_DATE, freq="D")[:-1]
monthly_weights_norm = np.array(MONTHLY_WEIGHTS) / np.sum(MONTHLY_WEIGHTS)
day_weights = monthly_weights_norm[date_range.month - 1]
day_weights = day_weights / day_weights.sum()
install_dates_base = np.random.choice(date_range, size=BASE_PLAYERS, p=day_weights)
install_dates_base = np.sort(install_dates_base)

# Ивентовые игроки
extra = []
for y in range(pd.Timestamp(START_DATE).year, pd.Timestamp(END_DATE).year):
    for m in range(1, 13):
        if np.random.random() < EVENT_PROB:
            mult = np.random.uniform(*EVENT_INSTALL_MULT)
            ret_f = np.random.uniform(*EVENT_RET_FACTOR)
            base_in_month = int(BASE_PLAYERS * monthly_weights_norm[m-1])
            extra_n = int(base_in_month * (mult - 1))
            for _ in range(extra_n):
                d = datetime(y, m, np.random.randint(1, 28))
                extra.append((d, ret_f))

all_dates = list(install_dates_base) + [e[0] for e in extra]
all_dates = sorted(all_dates)
N = len(all_dates)
player_ids = np.arange(1, N + 1)
install_dates = np.array(all_dates)
install_dates_pd = pd.DatetimeIndex(install_dates)
install_month_idx = (install_dates_pd.year - pd.Timestamp(START_DATE).year) * 12 + install_dates_pd.month - 1
is_event = np.array([False] * BASE_PLAYERS + [True] * len(extra))
retention_factor = np.array([1.0] * BASE_PLAYERS + [e[1] for e in extra])
channels = np.random.choice(CHANNELS, size=N, p=np.array(CHANNEL_WEIGHTS)/np.sum(CHANNEL_WEIGHTS))

# Игроки теперь без стран
players_df = pd.DataFrame({
    "player_id": player_ids,
    "install_date": install_dates_pd,
    "acquisition_channel": channels
})

# ============================================================
# 4. СИМУЛЯЦИЯ (подписки, покупки, сессии)
# ============================================================
TOTAL_MONTHS = len(pd.date_range(START_DATE, END_DATE, freq="MS"))
plan = np.zeros(N, dtype=np.int8)
sub_end_month = np.full(N, -1, dtype=np.int16)
is_retained = np.ones(N, dtype=bool)
retention_mult = np.ones(N, dtype=np.float32)
subs_list = []
purch_list = []
sess_list = []
base_ret = RETENTION_RATE * retention_factor
START_DT = pd.Timestamp(START_DATE)

# Средний сезонный множитель
mean_monthly_weight = np.mean(MONTHLY_WEIGHTS)

for t in range(TOTAL_MONTHS):
    month_start = START_DT + pd.DateOffset(months=t)
    month_end = month_start + pd.DateOffset(months=1) - timedelta(days=1)
    month_number = month_start.month  # 1..12

    # Сезонный множитель сессий: отношение веса месяца к среднему весу
    seasonal_multiplier = MONTHLY_WEIGHTS[month_number - 1] / mean_monthly_weight

    # Обновление удержания
    mask_update = np.random.random(N) < 0.2
    retention_mult[mask_update] = np.random.uniform(0.88, 1.11, size=mask_update.sum())
    effective_ret = np.minimum(base_ret * retention_mult, 1.0)

    # Завершившиеся подписки
    ended = sub_end_month == t
    plan[ended] = 0
    sub_end_month[ended] = -1

    # Реактивация
    reactivate = (~is_retained) & (np.random.random(N) < REACTIVATION_RATE)
    is_retained[reactivate] = True

    active_mask = is_retained & (t >= install_month_idx)

    # --- Подписки ---
    free_mask = active_mask & (plan == 0)
    new_sub = free_mask & (np.random.random(N) < NEW_SUB_CHANCE)
    plan_type_new = np.random.choice(["Basic", "Premium"], p=[0.7, 0.3], size=new_sub.sum())
    durations = np.random.choice([1, 3, 6, 12], p=[0.3, 0.4, 0.2, 0.1], size=new_sub.sum())
    plan[new_sub] = np.where(plan_type_new == "Basic", 1, 2)
    sub_end_month[new_sub] = t + durations
    for i in np.where(new_sub)[0]:
        fee = BASIC_PRICE if plan[i] == 1 else PREMIUM_PRICE
        disc = BASIC_DISCOUNT if plan[i] == 1 else PREMIUM_DISCOUNT
        subs_list.append({
            "player_id": i + 1,
            "plan_type": "Basic" if plan[i] == 1 else "Premium",
            "start_date": month_start,
            "end_date": START_DT + pd.DateOffset(months=int(sub_end_month[i])),
            "monthly_fee": fee,
            "discount_pct": disc * 100
        })

    # Апгрейд Basic -> Premium
    basic_mask = active_mask & (plan == 1)
    upgrade = basic_mask & (np.random.random(N) < UPGRADE_BASIC_TO_PREMIUM)
    plan[upgrade] = 2
    durations_up = np.random.choice([1, 3, 6, 12], p=[0.3, 0.4, 0.2, 0.1], size=upgrade.sum())
    sub_end_month[upgrade] = t + durations_up
    for i in np.where(upgrade)[0]:
        subs_list.append({
            "player_id": i + 1,
            "plan_type": "Premium",
            "start_date": month_start,
            "end_date": START_DT + pd.DateOffset(months=int(sub_end_month[i])),
            "monthly_fee": PREMIUM_PRICE,
            "discount_pct": PREMIUM_DISCOUNT * 100
        })

    # --- Покупки ---
    disc_pct = np.where(plan == 1, BASIC_DISCOUNT, np.where(plan == 2, PREMIUM_DISCOUNT, 0.0))
    has_sub = (plan > 0)
    buy_prob = np.where(has_sub, 1.0, 0.4)
    buy_mask = active_mask & (np.random.random(N) < buy_prob)
    max_purch = np.where(has_sub, MAX_PURCHASES_PAYING, MAX_PURCHASES_FREE)
    num_purch = np.random.randint(0, max_purch + 1, size=N)
    num_purch[~buy_mask] = 0
    total_purch = num_purch.sum()
    if total_purch > 0:
        purch_player = np.repeat(np.arange(N), num_purch)
        cat_names = list(ITEM_CATEGORIES.keys())
        cat_probs = np.array([ITEM_CATEGORIES[c]["prob"] for c in cat_names])
        cat_probs = cat_probs / cat_probs.sum()
        purch_cat_idx = np.random.choice(len(cat_names), size=total_purch, p=cat_probs)
        base_prices = np.zeros(total_purch, dtype=np.float64)
        for ci, cat in enumerate(cat_names):
            mask_cat = purch_cat_idx == ci
            low, high = ITEM_CATEGORIES[cat]["price_range"]
            base_prices[mask_cat] = np.random.randint(low, high + 1, size=mask_cat.sum())
        discounts = disc_pct[purch_player]
        net_prices = np.round(base_prices * (1 - discounts), 2)
        days = np.random.randint(1, month_end.day + 1, size=total_purch)
        dates = [datetime(month_start.year, month_start.month, d) for d in days]
        for j in range(total_purch):
            purch_list.append({
                "player_id": purch_player[j] + 1,
                "purchase_date": dates[j],
                "item_category": cat_names[purch_cat_idx[j]],
                "base_price": base_prices[j],
                "discount_pct": discounts[j] * 100,
                "net_revenue": net_prices[j]
            })

    # --- Сессии ---
    # Определяем тип игрока для выбора диапазона сессий
    # Базовое количество сессий для каждого активного игрока
    has_purchase_this_month = (num_purch > 0)  # num_purch уже рассчитан
    has_sub_now = (plan > 0)

    # Диапазон по типу
    min_sess = np.where(has_purchase_this_month | has_sub_now, MIN_SESSIONS_PAYING, MIN_SESSIONS_FREE)
    max_sess = np.where(has_purchase_this_month | has_sub_now, MAX_SESSIONS_PAYING, MAX_SESSIONS_FREE)

    # Для активных игроков генерируем количество сессий
    sess_counts = np.zeros(N, dtype=int)
    for i in np.where(active_mask)[0]:
        if max_sess[i] >= min_sess[i]:
            count = np.random.randint(min_sess[i], max_sess[i] + 1)
        else:
            count = min_sess[i]
        # Применяем сезонный множитель
        count = int(round(count * seasonal_multiplier))
        # Дополнительный множитель для подписчиков
        if has_sub_now[i]:
            count = int(round(count * SUBSCRIBER_SESSION_MULTIPLIER))
        # Не может быть меньше 1, если игрок активен
        if count < 1:
            count = 1
        sess_counts[i] = count

    total_sessions = sess_counts.sum()
    if total_sessions > 0:
        sess_player = np.repeat(np.arange(N), sess_counts)
        # Генерируем случайные даты в месяце
        days = np.random.randint(1, month_end.day + 1, size=total_sessions)
        session_dates = [datetime(month_start.year, month_start.month, d) for d in days]
        # Создаём записи
        for j in range(total_sessions):
            sess_list.append({
                "session_id": len(sess_list) + 1,
                "player_id": sess_player[j] + 1,
                "session_date": session_dates[j]
            })

    # --- Отток ---
    churn = active_mask & (np.random.random(N) > effective_ret)
    is_retained[churn] = False

subs_df = pd.DataFrame(subs_list)
purch_df = pd.DataFrame(purch_list)
sess_df = pd.DataFrame(sess_list)

# ============================================================
# 5. МАРКЕТИНГ
# ============================================================
installs_by_month = players_df["install_date"].dt.to_period("M")
marketing = []
for period in pd.period_range(START_DATE, END_DATE, freq="M")[:-1]:
    month_start = period.start_time
    for ch in CHANNELS:
        mask = (installs_by_month == period) & (players_df["acquisition_channel"] == ch)
        n = mask.sum()
        marketing.append({
            "month": month_start,
            "channel": ch,
            "spend": n * CHANNEL_COST_PER_INSTALL[ch],
            "new_installs": n
        })
marketing_df = pd.DataFrame(marketing)

# ============================================================
# 6. СОХРАНЕНИЕ
# ============================================================
players_df.to_csv(DATA_DIR / "players.csv", index=False)
subs_df.to_csv(DATA_DIR / "subscriptions.csv", index=False)
purch_df.to_csv(DATA_DIR / "purchases.csv", index=False)
marketing_df.to_csv(DATA_DIR / "marketing_spend.csv", index=False)
sess_df.to_csv(DATA_DIR / "sessions.csv", index=False)

def file_size_mb(path):
    return path.stat().st_size / (1024 * 1024)

print("\n" + "=" * 60)
print(" ДАННЫЕ СГЕНЕРИРОВАНЫ! ")
print(f" Игроки: {len(players_df)}")
print(f" Подписки: {len(subs_df)}")
print(f" Покупки: {len(purch_df)}")
print(f" Сессии: {len(sess_df)}")
print(f" Маркетинговые записи: {len(marketing_df)}")
print("-" * 40)
print("Размеры файлов:")
for name in ["players.csv", "subscriptions.csv", "purchases.csv", "sessions.csv", "marketing_spend.csv"]:
    path = DATA_DIR / name
    if path.exists():
        print(f"  {name}: {file_size_mb(path):.2f} MB")
print("=" * 60)