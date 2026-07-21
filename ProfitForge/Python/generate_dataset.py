# generate_dataset.py (финальная жирная версия)
# Цель: 30+ MB purchases.csv, реалистичная модель
# Увеличены: база игроков до 10000, период до 2026 (72 мес), retention до 0.92, лимиты покупок

from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ------------------------------
# 1. ДИНАМИЧЕСКИЕ ПУТИ
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "Сырые данные"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ------------------------------
# 2. ПАРАМЕТРЫ ГЕНЕРАЦИИ (ФИНАЛЬНЫЕ ЖИРНЫЕ)
# ------------------------------
START_DATE = datetime(2020, 1, 1)
END_DATE = datetime(2026, 1, 1)            # 72 месяца
TOTAL_MONTHS = 72
BASE_PLAYERS = 10000                       # увеличено до 10000

# Сезонные веса установок
MONTHLY_WEIGHTS = np.array([1.0, 0.8, 0.9, 1.1, 0.6, 1.4, 1.6, 1.5, 0.5, 0.9, 0.7, 0.3])
MONTHLY_WEIGHTS = MONTHLY_WEIGHTS / MONTHLY_WEIGHTS.sum() * 12

# Цены подписок
BASIC_PRICE, PREMIUM_PRICE = 200, 500
BASIC_DISCOUNT, PREMIUM_DISCOUNT = 0.05, 0.10

# Категории товаров
CATEGORIES = ['consumable', 'booster', 'skin']
CAT_PROBS = np.array([0.7, 0.15, 0.02])
CAT_PROBS = CAT_PROBS / CAT_PROBS.sum()
PRICE_RANGES = [(20,400), (40,700), (300,2000)]

# Поведение (максимально приближено к реальности, но с большим объёмом)
RETENTION_RATE = 0.92          # высокий retention = больше активных месяцев
RETENTION_JITTER = (0.88, 1.11)
REACTIVATION_RATE = 0.03
UPGRADE_FREE_TO_BASIC = 0.05   # чуть больше платящих
UPGRADE_BASIC_TO_PREMIUM = 0.015
MAX_PURCHASES_PAYING = 40      # очень много покупок у платящих
MAX_PURCHASES_FREE = 10        # и у бесплатных

# Ивенты
EVENT_PROB = 1/5
EVENT_INSTALL_MULT = (1.5, 3.0)
EVENT_RET_FACTOR = (0.7, 0.9)

# Маркетинг
CHANNELS = ['Organic', 'Ads', 'Referral']
CHANNEL_WEIGHTS = [0.5, 0.35, 0.15]
CHANNEL_COST = {'Organic': 0, 'Ads': 150, 'Referral': 50}

# ------------------------------
# 3. ГЕНЕРАЦИЯ ИГРОКОВ
# ------------------------------
np.random.seed(42)

# Месяцы для каждого дня периода
date_range = pd.date_range(START_DATE, END_DATE, freq='D')[:-1]
day_weights = MONTHLY_WEIGHTS[date_range.month - 1]
day_weights = day_weights / day_weights.sum()
install_dates_base = np.random.choice(date_range, size=BASE_PLAYERS, p=day_weights)
install_dates_base = np.sort(install_dates_base)

# Ивентовые игроки
extra = []
for y in range(2020, 2026):
    for m in range(1, 13):
        if np.random.random() < EVENT_PROB:
            mult = np.random.uniform(*EVENT_INSTALL_MULT)
            ret_f = np.random.uniform(*EVENT_RET_FACTOR)
            base_in_month = int(BASE_PLAYERS * MONTHLY_WEIGHTS[m-1] / MONTHLY_WEIGHTS.sum())
            extra_n = int(base_in_month * (mult - 1))
            for _ in range(extra_n):
                d = datetime(y, m, np.random.randint(1, 28))
                extra.append((d, ret_f))

extra_dates = [e[0] for e in extra]
extra_ret = [e[1] for e in extra]

all_dates = list(install_dates_base) + extra_dates
all_dates = sorted(all_dates)
N = len(all_dates)
player_ids = np.arange(1, N + 1)
install_dates = np.array(all_dates)

install_dates_pd = pd.DatetimeIndex(install_dates)
install_month_idx = (install_dates_pd.year - 2020) * 12 + install_dates_pd.month - 1
install_month_idx = install_month_idx.values

is_event = np.array([False] * BASE_PLAYERS + [True] * len(extra))
retention_factor = np.array([1.0] * BASE_PLAYERS + extra_ret)

channels = np.random.choice(CHANNELS, size=N, p=CHANNEL_WEIGHTS)
countries = np.random.choice(['RU', 'US', 'DE', 'BR', 'JP'], size=N, p=[0.5, 0.2, 0.1, 0.1, 0.1])

players_df = pd.DataFrame({
    'player_id': player_ids,
    'install_date': install_dates_pd,
    'acquisition_channel': channels,
    'country': countries
})

# ------------------------------
# 4. БЫСТРАЯ СИМУЛЯЦИЯ
# ------------------------------
plan = np.zeros(N, dtype=np.int8)
sub_end_month = np.full(N, -1, dtype=np.int16)
is_retained = np.ones(N, dtype=bool)
retention_mult = np.ones(N, dtype=np.float32)

subs_list = []
purch_list = []

base_ret = RETENTION_RATE * retention_factor

for t in range(TOTAL_MONTHS):
    month_start = START_DATE + pd.DateOffset(months=t)
    month_end = month_start + pd.DateOffset(months=1) - timedelta(days=1)

    # Обновление множителя удержания
    mask_update = np.random.random(N) < 0.2
    retention_mult[mask_update] = np.random.uniform(*RETENTION_JITTER, size=mask_update.sum())
    effective_ret = np.minimum(base_ret * retention_mult, 1.0)

    # Завершившиеся подписки
    ended = sub_end_month == t
    plan[ended] = 0
    sub_end_month[ended] = -1

    # Реактивация
    reactivate = (~is_retained) & (np.random.random(N) < REACTIVATION_RATE)
    is_retained[reactivate] = True

    active_mask = is_retained & (t >= install_month_idx)

    # --------- ПОДПИСКИ ---------
    free_mask = active_mask & (plan == 0)
    new_sub = free_mask & (np.random.random(N) < 0.07)  # шанс начать подписку 7%
    plan_type_new = np.random.choice(['Basic', 'Premium'], p=[0.7, 0.3], size=new_sub.sum())
    durations = np.random.choice([1, 3, 6, 12], p=[0.3, 0.4, 0.2, 0.1], size=new_sub.sum())
    plan[new_sub] = np.where(plan_type_new == 'Basic', 1, 2)
    sub_end_month[new_sub] = t + durations
    for i in np.where(new_sub)[0]:
        fee = BASIC_PRICE if plan[i] == 1 else PREMIUM_PRICE
        disc = BASIC_DISCOUNT if plan[i] == 1 else PREMIUM_DISCOUNT
        subs_list.append({
            'player_id': i + 1,
            'plan_type': 'Basic' if plan[i] == 1 else 'Premium',
            'start_date': month_start,
            'end_date': START_DATE + pd.DateOffset(months=int(sub_end_month[i])),
            'monthly_fee': fee,
            'discount_pct': disc * 100
        })

    # Апгрейд Basic -> Premium
    basic_mask = active_mask & (plan == 1)
    upgrade = basic_mask & (np.random.random(N) < UPGRADE_BASIC_TO_PREMIUM)
    plan[upgrade] = 2
    durations_up = np.random.choice([1, 3, 6, 12], p=[0.3, 0.4, 0.2, 0.1], size=upgrade.sum())
    sub_end_month[upgrade] = t + durations_up
    for i in np.where(upgrade)[0]:
        subs_list.append({
            'player_id': i + 1,
            'plan_type': 'Premium',
            'start_date': month_start,
            'end_date': START_DATE + pd.DateOffset(months=int(sub_end_month[i])),
            'monthly_fee': PREMIUM_PRICE,
            'discount_pct': PREMIUM_DISCOUNT * 100
        })

    # --------- ПОКУПКИ ---------
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
        purch_cat = np.random.choice(len(CATEGORIES), size=total_purch, p=CAT_PROBS)
        base_prices = np.zeros(total_purch, dtype=np.float64)
        for ci in range(len(CATEGORIES)):
            mask_cat = purch_cat == ci
            low, high = PRICE_RANGES[ci]
            base_prices[mask_cat] = np.random.randint(low, high + 1, size=mask_cat.sum())
        discounts = disc_pct[purch_player]
        net_prices = np.round(base_prices * (1 - discounts), 2)
        days = np.random.randint(1, month_end.day + 1, size=total_purch)
        dates = [datetime(month_start.year, month_start.month, d) for d in days]

        for j in range(total_purch):
            purch_list.append({
                'player_id': purch_player[j] + 1,
                'purchase_date': dates[j],
                'item_category': CATEGORIES[purch_cat[j]],
                'base_price': base_prices[j],
                'discount_pct': discounts[j] * 100,
                'net_revenue': net_prices[j]
            })

    # --------- ОТТОК ---------
    churn = active_mask & (np.random.random(N) > effective_ret)
    is_retained[churn] = False

# ------------------------------
# 5. СОХРАНЕНИЕ В CSV
# ------------------------------
subs_df = pd.DataFrame(subs_list)
purch_df = pd.DataFrame(purch_list)

# Маркетинг
installs_by_month = players_df['install_date'].dt.to_period('M')
marketing = []
for period in pd.period_range(START_DATE, END_DATE, freq='M')[:-1]:
    month_start = period.start_time
    for ch in CHANNELS:
        mask = (installs_by_month == period) & (players_df['acquisition_channel'] == ch)
        n = mask.sum()
        marketing.append({
            'month': month_start,
            'channel': ch,
            'spend': n * CHANNEL_COST[ch],
            'new_installs': n
        })
marketing_df = pd.DataFrame(marketing)

# Запись с выводом размеров
players_df.to_csv(DATA_DIR / 'players.csv', index=False)
subs_df.to_csv(DATA_DIR / 'subscriptions.csv', index=False)
purch_df.to_csv(DATA_DIR / 'purchases.csv', index=False)
marketing_df.to_csv(DATA_DIR / 'marketing_spend.csv', index=False)

def file_size_mb(path):
    return path.stat().st_size / (1024 * 1024)

print("=" * 80)
print(" ДАННЫЕ СГЕНЕРИРОВАНЫ (ФИНАЛЬНАЯ ЖИРНАЯ ВЕРСИЯ) ")
print(f" Игроки: {len(players_df)}")
print(f" Подписки: {len(subs_df)}")
print(f" Покупки: {len(purch_df)}")
print(f" Маркетинговые записи: {len(marketing_df)}")
print("-" * 40)
print("Размеры файлов:")
for name in ['players.csv', 'subscriptions.csv', 'purchases.csv', 'marketing_spend.csv']:
    path = DATA_DIR / name
    if path.exists():
        print(f"  {name}: {file_size_mb(path):.2f} MB")
print("=" * 80)