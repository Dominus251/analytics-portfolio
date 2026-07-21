-- В таблице я намеренно оставил дубли.
-- Отобрал топ 100 чтобы визуально не перегружать графики

with reviews_total as(
        select r.appid,
        count(*) cnt_rev
        from reviews r
        group by r.appid
)
,top_publishers  as(
        select ap1.publisher_id,
        count(*) cnt
        from application_publishers ap1 
        group by ap1.publisher_id
        order by cnt desc
        limit 100
)
select  a.appid, 
        a.name,
        sum(rt.cnt_rev) tot_rev,
        a.type,
        a.is_free,
        a.release_date,
        a.required_age,
        a.mat_supports_windows,
        a.mat_supports_mac,
        a.mat_supports_linux,
        p.name
from applications a 
join application_publishers ap 
    on a.appid = ap.appid 
join top_publishers tp
    on tp.publisher_id = ap.publisher_id 
join publishers p 
    on tp.publisher_id = p.id 
join reviews_total rt
    on a.appid = rt.appid 
group by a.appid, 
         a.name,
         a.type,
         a.is_free,
         a.release_date,
         a.required_age,
         a.mat_supports_windows,
         a.mat_supports_mac,
         a.mat_supports_linux,
         p.name
