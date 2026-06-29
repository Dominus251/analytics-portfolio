--Использование последовательных CTE

with reviews_cnt as(
		select appid,
		count (*) cnt
		from reviews 
		group by appid
)
,genre_stats as (
		select ag.genre_id,
		sum(cnt) sum_reviews
		from applications a 
		join reviews_cnt rc on a.appid = rc.appid 
		join application_genres ag  on rc.appid = ag.appid
		where a.type = 'game'
		group by ag.genre_id 
)
select name, sum_reviews
from genre_stats
join genres g on genre_id = id
order by sum_reviews desc
limit 10;
