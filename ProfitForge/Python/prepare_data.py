from pathlib import Path
import pandas as pd
import numpy as np 

# Динамический путь.
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent/ 'Витрина'
DATA_DIR = BASE_DIR.parent / 'Сырые данные'

# Разделители.
SEP = '=' * 80
SUBSEP = '-' * 80

#
marketing = pd.read_csv(DATA_DIR/'marketing_spend.csv')
players = pd.read_csv(DATA_DIR/'players.csv')
purchases = pd.read_csv(DATA_DIR/'purchases.csv')
subscriptions = pd.read_csv(DATA_DIR/'subscriptions.csv')


#=================================================================================
#
players['install_date'] = pd.to_datetime(players['install_date'])
players['cohorts_month'] = players['install_date'].dt.to_period('M').dt.start_time


#
END_DATE = pd.Timestamp('2023-01-01')

def monith_range(start, end):
    return pd.date_range(start, end, freq='MS').tolist()

players['activity_month']=players.apply(
    lambda x: monith_range(x['cohorts_month'], END_DATE), axis=1
)

grid = (players.explode('activity_month', ignore_index=True)
        [['player_id','cohorts_month', 'acquisition_channel', 'country', 'activity_month']]
)

subscriptions['start_date'] = pd.to_datetime(subscriptions['start_date'])
subscriptions['end_date'] = pd.to_datetime(subscriptions['end_date'])

subscriptions['activity_month'] = subscriptions.apply(
    lambda x: monith_range(x['start_date'], x['end_date']),
    axis=1
)
subs_expanded = (subscriptions.explode('activity_month', ignore_index=True)
                 [['player_id', 'plan_type','activity_month', 'monthly_fee', 'discount_pct']]
)


subs_agg = subs_expanded.groupby(['player_id', 'activity_month']).agg(
    sub_revenue = ('monthly_fee', 'sum'),
    plan_type = ('plan_type', 'max'),
    discount_pct = ('discount_pct', 'max')
).reset_index()

purchases = pd.read_csv(DATA_DIR / 'purchases.csv')
purchases['purchase_date'] = pd.to_datetime(purchases['purchase_date'])
purchases['activity_month'] = purchases['purchase_date'].dt.to_period('M').dt.start_time

purchases_agg = purchases.groupby(['player_id', 'activity_month']).agg(
    purchase_revenue = ('net_revenue', 'sum'),
    items_bought = ('net_revenue', 'count')
).reset_index()

activity = grid.merge(purchases_agg, on=['player_id', 'activity_month'], how='left')
activity = activity.merge(subs_agg, on=['player_id', 'activity_month'], how='left')

# 
activity = activity.fillna({
    'purchase_revenue': 0.0,
    'items_bought': 0,
    'sub_revenue': 0.0,
    'discount_pct': 0.0,
    'plan_type': 'Free'
})
activity['is_active'] = (activity['purchase_revenue'] + activity['sub_revenue']) > 0
activity['has_subscription'] = activity['plan_type'] != 'Free'

activity['purchase_revenue'] = activity['purchase_revenue'].round(2)
activity['sub_revenue'] = activity['sub_revenue'].round(2)

print(activity.head(20))

activity['life_month'] = (
    (activity['activity_month'].dt.year - activity['cohorts_month'].dt.year) * 12 +
    (activity['activity_month'].dt.month - activity['cohorts_month'].dt.month)
)

# Когортная агрегация (исправленная)
cohort_data = activity.groupby(['cohorts_month', 'life_month']).agg(
    active_players=('is_active', 'sum'),          # количество активных игроков
    paying_players=('has_subscription', 'sum'),
    total_sub_revenue=('sub_revenue', 'sum'),
    total_purchase_revenue=('purchase_revenue', 'sum'),
    total_items_bought=('items_bought', 'sum')
).reset_index()

# Размер когорты: общее количество уникальных игроков в месяце установки (life_month=0)
cohort_sizes = activity[activity['life_month'] == 0] \
    .groupby('cohorts_month')['player_id'].nunique() \
    .reset_index(name='cohort_size')

cohort_data = cohort_data.merge(cohort_sizes, on='cohorts_month', how='left')
cohort_data['retention_rate'] = cohort_data['active_players'] / cohort_data['cohort_size']

print(cohort_data.head(30))

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
cohort_data.to_csv(OUTPUT_DIR / 'cohort_data.csv', index=False)

print(SEP)
print("Когортная витрина сохранена в", OUTPUT_DIR / 'cohort_data.csv')
print("Готово!")


# Проверка активности: доля месяцев с is_active == True
print("Доля активных месяцев:", activity['is_active'].mean().round(2))

# Распределение количества активных месяцев на игрока
active_months_per_player = activity.groupby('player_id')['is_active'].sum()
print("Среднее число активных месяцев на игрока:", active_months_per_player.mean().round(1))
print("Максимум:", active_months_per_player.max(), "Минимум:", active_months_per_player.min())

# Доля игроков, у которых хоть раз был неактивный месяц
inactive_ever = (active_months_per_player < activity.groupby('player_id').size()).mean()
print(f"Доля игроков с хотя бы одним неактивным месяцем: {inactive_ever:.2%}")