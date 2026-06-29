-- Версия 1
-- Пример умения использования LATERAL и generate_series
-- Время выполнения: ~15 сек
with all_month as (select generate_series('2000-01-01'::date,'2020-01-01'::date,'1 month')::date as month)
select month
from all_month 
left join lateral (select count(*) filter (where type = 'game') cnt 
                     from applications 
                    where month = date_trunc('month', release_date)) 
                       on true
where cnt = 0;

-- Версия 2
-- Приведение запроса в надлежащий вид 
-- Прост для чтения
-- Время выполненеи: ~50 мс 
with all_month as (select generate_series('2000-01-01'::date,'2020-01-01'::date,'1 month')::date as month)
select month
from all_month 
left join applications a 
on month = date_trunc('month', release_date)
and type = 'game'
and release_date >= '2000-01-01'
and release_date < '2020-02-01'
where appid is null
order by month;

-- Версия 3
-- Лучше себя показывает на больших обьемах данных так как соеденяет только уникальные месяцы
-- Время выполнения: ~40 мс
with all_months as (
    select generate_series('2000-01-01'::date, '2020-01-01'::date, '1 month')::date as month
)
select month
from all_months 
left join (
    select date_trunc('month', release_date) as release_month
    from applications
    where type = 'game'
      and release_date >= '2000-01-01'
      and release_date < '2020-02-01' 
    group by release_month
) as releases on month = releases.release_month
where releases.release_month is null
order by month;