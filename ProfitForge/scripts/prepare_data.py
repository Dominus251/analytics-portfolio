from pathlib import Path
import pandas as pd
import numpy as np 

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent / 'Showcase'
DATA_DIR = BASE_DIR.parent / 'data'

# Разделители.
SEP = '=' * 80
SUBSEP = '-' * 80

# Загрузка исходных данных из CSV.
marketing = pd.read_csv(DATA_DIR / 'marketing_spend.csv')
players = pd.read_csv(DATA_DIR / 'players.csv')
purchases = pd.read_csv(DATA_DIR / 'purchases.csv')
subscriptions = pd.read_csv(DATA_DIR / 'subscriptions.csv')
sessions = pd.read_csv(DATA_DIR / 'sessions.csv')

#=================================================================================
# 1. Генерация сетки месяцев (activity_month) для каждого игрока.
#    Каждый игрок присутствует в таблице с даты установки (cohorts_month)
#    до конца анализируемого периода (END_DATE).
#=================================================================================
players['install_date'] = pd.to_datetime(players['install_date'])
players['cohorts_month'] = players['install_date'].dt.to_period('M').dt.start_time

# Динамическое определение конечной даты периода
END_DATE = max(
    players['install_date'].max(),
    subscriptions['end_date'].max(),
    purchases['purchase_date'].max(),
    sessions['session_date'].max()
)

def month_range(start, end):
    """Возвращает список первых чисел всех месяцев от start до end включительно."""
    return pd.date_range(start, end, freq='MS').tolist()

# Для каждого игрока создаём список месяцев от когорты до конца периода.
players['activity_month'] = players.apply(
    lambda x: month_range(x['cohorts_month'], END_DATE), axis=1
)

# "Разворачиваем" списки месяцев в отдельные строки (получаем сетку player_id × месяц).
grid = players.explode('activity_month', ignore_index=True)[
    ['player_id', 'cohorts_month', 'acquisition_channel', 'activity_month']
]

#=================================================================================
# 2. Обработка подписок: разворачиваем каждую подписку на месяцы её действия.
#=================================================================================
subscriptions['start_date'] = pd.to_datetime(subscriptions['start_date'])
subscriptions['end_date'] = pd.to_datetime(subscriptions['end_date'])

subscriptions['activity_month'] = subscriptions.apply(
    lambda x: month_range(x['start_date'], x['end_date']),
    axis=1
)

subs_expanded = subscriptions.explode('activity_month', ignore_index=True)[
    ['player_id', 'plan_type', 'activity_month', 'monthly_fee', 'discount_pct']
]

# Агрегируем подписки по игроку и месяцу.
subs_agg = subs_expanded.groupby(['player_id', 'activity_month']).agg(
    sub_revenue=('monthly_fee', 'sum'),
    plan_type=('plan_type', 'max'),
    discount_pct=('discount_pct', 'max')
).reset_index()

#=================================================================================
# 3. Обработка покупок.
#=================================================================================
purchases['purchase_date'] = pd.to_datetime(purchases['purchase_date'])
purchases['activity_month'] = purchases['purchase_date'].dt.to_period('M').dt.start_time

purchases_agg = purchases.groupby(['player_id', 'activity_month']).agg(
    purchase_revenue=('net_revenue', 'sum'),
    items_bought=('net_revenue', 'count')
).reset_index()

#=================================================================================
# 4. Обработка сессий.
#=================================================================================
sessions['session_date'] = pd.to_datetime(sessions['session_date'])
sessions['activity_month'] = sessions['session_date'].dt.to_period('M').dt.start_time

sessions_agg = sessions.groupby(['player_id', 'activity_month']).agg(
    session_count=('session_id', 'count')
).reset_index()

#=================================================================================
# 5. Сборка единой витрины активности: сетка + покупки + подписки + сессии.
#=================================================================================
activity = grid.merge(purchases_agg, on=['player_id', 'activity_month'], how='left')
activity = activity.merge(subs_agg, on=['player_id', 'activity_month'], how='left')
activity = activity.merge(sessions_agg, on=['player_id', 'activity_month'], how='left')

# Заполняем пропуски.
activity = activity.fillna({
    'purchase_revenue': 0.0,
    'items_bought': 0,
    'sub_revenue': 0.0,
    'discount_pct': 0.0,
    'plan_type': 'Free',
    'session_count': 0
})

# Флаги.
activity['is_active'] = activity['session_count'] > 0
activity['has_subscription'] = activity['plan_type'] != 'Free'
activity['has_purchase'] = activity['purchase_revenue'] > 0
activity['is_paying'] = activity['has_subscription'] | activity['has_purchase']

# Округляем денежные значения.
activity['purchase_revenue'] = activity['purchase_revenue'].round(2)
activity['sub_revenue'] = activity['sub_revenue'].round(2)

print(activity.head(20))

#=================================================================================
# 6. Расчёт когортных метрик.
#=================================================================================
activity['life_month'] = (
    (activity['activity_month'].dt.year - activity['cohorts_month'].dt.year) * 12 +
    (activity['activity_month'].dt.month - activity['cohorts_month'].dt.month)
)

# Агрегируем по когорте и месяцу жизни.
cohort_data = activity.groupby(['cohorts_month', 'life_month']).agg(
    active_players=('is_active', 'sum'),          # игроки с хотя бы одной сессией
    paying_players=('is_paying', 'sum'),          # игроки с покупкой или подпиской
    active_subscribers=('has_subscription', 'sum'),# игроки с активной подпиской
    total_sub_revenue=('sub_revenue', 'sum'),
    total_purchase_revenue=('purchase_revenue', 'sum'),
    total_items_bought=('items_bought', 'sum')
).reset_index()

# Размер когорты: уникальные игроки в нулевом месяце жизни.
cohort_sizes = activity[activity['life_month'] == 0] \
    .groupby('cohorts_month')['player_id'].nunique() \
    .reset_index(name='cohort_size')

cohort_data = cohort_data.merge(cohort_sizes, on='cohorts_month', how='left')
cohort_data['retention_rate'] = cohort_data['active_players'] / cohort_data['cohort_size']

print(cohort_data.head(30))

#=================================================================================
# 7. Сохранение витрины.
#=================================================================================
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
cohort_data.to_csv(OUTPUT_DIR / 'cohort_data.csv', index=False)

print(SEP)
print("Когортная витрина сохранена в", OUTPUT_DIR / 'cohort_data.csv')
print("Готово!")

#=================================================================================
# 8. Диагностика качества данных.
#=================================================================================
print("Доля активных месяцев:", activity['is_active'].mean().round(2))

active_months_per_player = activity.groupby('player_id')['is_active'].sum()
print("Среднее число активных месяцев на игрока:", active_months_per_player.mean().round(1))
print("Максимум:", active_months_per_player.max(), "Минимум:", active_months_per_player.min())

inactive_ever = (active_months_per_player < activity.groupby('player_id').size()).mean()
print(f"Доля игроков с хотя бы одним неактивным месяцем: {inactive_ever:.2%}")