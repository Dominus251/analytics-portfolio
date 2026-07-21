create table steam_mart as
with total_rev as(
        select r.appid,
        count(*) as total_reviews,
        round(avg(voted_up::int),2) AS positive_share
        from reviews r 
        group by r.appid 
)
, app_pub as(
select ap.appid,
        string_agg(distinct(name), ', ') publishers
        from application_publishers ap 
        join publishers p 
        on ap.publisher_id = p.id 
        group by ap.appid
)
,app_gen as(
select ag.appid,
        string_agg(distinct(name), ', ') genres
        from application_genres ag 
        join genres g 
        on ag.genre_id  = g.id 
        group by ag.appid
)
,app_dev as(
        select ad.appid,
        string_agg(distinct(name), ', ') developers
        from application_developers ad 
        join developers d  
        on ad.developer_id   = d.id 
        group by ad.appid
)
,app_cat as(
        select ac.appid,
        string_agg(distinct(name), ', ') categories
        from application_categories ac 
        join categories c  
        on ac.category_id   = c.id 
        group by ac.appid
)
,app_pla as(
        select ap.appid,
        string_agg(distinct(name), ', ') platforms
        from application_platforms ap 
        join platforms p 
        on ap.platform_id   = p.id 
        group by ap.appid
)
select  a.appid,
        a.name,
        a.type,
        a.is_free,
        a.release_date,
        a.required_age,
        a.supported_languages,
        coalesce(publishers,'') publishers,
        coalesce(genres,'') genres,
        coalesce(developers,'') developers,
        coalesce(categories,'') categories,
        coalesce(platforms,'') platforms,
        coalesce(total_reviews, 0) total_reviews,
        coalesce(positive_share, 0) positive_share
from applications a 
left join app_pub t1
    on t1.appid = a.appid
left join app_gen t2
    on t2.appid = a.appid 
left join app_dev t3
    on t3.appid = a.appid 
left join app_cat t4
    on t4.appid = a.appid 
left join app_pla t5
    on t5.appid = a.appid 
left join total_rev tr
    on tr.appid = a.appid 