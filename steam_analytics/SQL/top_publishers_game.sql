-- Версия 1 (без оптимизации)
-- Время выполнения: ~150 мс 

select p.name, COUNT(*) as cnt
from applications a  
join application_publishers ap on a.appid = ap.appid
join publishers p on ap.publisher_id = p.id
where DATE_PART('year', a.release_date) = 2024
  and type = 'game'
group by p.name
order by cnt desc
limit 10;

-- Версия 2 (оптимизированная)
-- Время выполнения: ~60 мс (ускорение в ~2.5 раза)
-- Почему быстрее?
-- Группировка по числовому publisher_id (вместо текстового name),
-- JOIN с publishers только после агрегации (для 10 строк вместо всех).
-- Диапазон дат для использования индекса по release_date

with top_publishers as (
		select ap.publisher_id , count(*) cnt
		from applications a  
		join application_publishers ap  
		on a.appid = ap.appid
		where a.release_date >= '2024-01-01'
		and a.release_date < '2025-01-01'
		and type = 'game'
		group by ap.publisher_id 
		order by cnt desc
		limit 10
)
select p.name, cnt
from top_publishers
join publishers p 
on publisher_id = id;