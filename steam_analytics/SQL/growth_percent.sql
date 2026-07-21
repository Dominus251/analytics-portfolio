--Использование оконной функции (LAG)
--Чистый вывод за счет to_char
--Защита от деления на ноль NULLIF

with year_cnt as (
select date_trunc('year', release_date)::date as year,
count(*) filter (where is_free = true) as cnt_release
from applications  
where release_date >= '2000-01-01'
and release_date < '2026-01-01' 
group by year
order by year
)
select year,
cnt_release, 
to_char(coalesce((cnt_release::float-lag(cnt_release) over (order by year))
/nullif(lag(cnt_release) over (order by year),0),0)*100,'fm990.00')|| '%'
as growth_percent
from year_cnt
