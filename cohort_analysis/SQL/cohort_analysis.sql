/*
Когортный анализ игроков Skygame.

Цель:
- Оценить удержание (retention) по месяцам жизни когорты.
- Рассчитать монетарные метрики: ARPU, ARPPU, CARPU, CARPPU.
- Выявить динамику новых плательщиков по когортам.

Период: регистрации до 2023-02-01.
Глубина анализа: 3 месяца жизни когорты (месяцы 0, 1, 2).

Используемые таблицы:
- users — регистрации
- game_sessions — игровые сессии
- monetary — платежи
- log_prices — история цен
*/


-- 1. Когорты: месяц регистрации каждого пользователя
With cohorts as(Select Id_user, 
                       Date_trunc ('month', reg_date)::date as cohort_month
				  From skygame.users
			     where reg_date::date < '2023-02-01' )

-- 2. Размер когорт + все месяцы жизни (0, 1, 2) через generate_series
-- LATERAL используется для вычисления month_number без дублирования кода
,cohort_size_and_month_number as(Select Count (distinct id_user) total_users, 
                                        Cohort_month,
										month_number
							       From cohorts
					         Cross join LATERAL Generate_series (0,2) as gs(month_number)
							   Group by cohort_month, 
							            month_number)  

-- 3. Платежи с разбивкой по месяцам жизни когорты
--    month_number = 0 — месяц регистрации, 1 — следующий, 2 — через месяц     
,payments as(Select Cohort_month, 
                    m.Id_user,
                    date_trunc ('month', dtime_pay::date) month_payment, 
					(price*cnt_buy) as revenue, 
					cjl_pay.month_number,
					Min(cjl_pay.month_number) over (partition by m.id_user) as first_pay
			   From skygame.monetary m
               Join cohorts c
			     On m.id_user = c.id_user 
			   Join skygame.log_prices 
			     On id_item_buy = id_item 
			    And dtime_pay >= valid_from 
			    And dtime_pay < COALESCE (valid_to, '3000-01-01') 
		 Cross join LATERAL (select (Extract(year From age(date_trunc('month',dtime_pay::date),cohort_month))*12+
					extract(month from age(date_trunc('month', dtime_pay::date),cohort_month)))::int as month_number) as cjl_pay
			  Where dtime_pay >= cohort_month
			    And dtime_pay < cohort_month + interval '3 month') 

-- 4. Агрегация платежей по когортам и месяцам жизни    
,payments_users as(Select Cohort_month,
                          Month_number, 
						  Count (distinct id_user)  paying_users,
						  Count (distinct case when month_number =first_pay then id_user else null end) new_payers,
						  SUM (revenue) total_revenue 
					 From payments 
			     Group by Cohort_month, 
				          Month_number) 

-- 5. Активность (сессии) с разбивкой по месяцам жизни когорты      
,Play_users_month as(Select Cohort_month, 
                           gs.Id_user,
						   Date_trunc ('month', start_session::date) as month_playing, 
						   cjl_play.month_number  
                      From skygame.game_sessions gs 
					  Join cohorts c
					    On gs.id_user = c.id_user 
			    Cross join LATERAL (select (Extract (year From age(date_trunc('month', start_session::date), cohort_month))*12+extract(month from age(date_trunc('month', start_session::date), cohort_month)))::int as month_number) cjl_play
					 Where end_session is not null 
					   And start_session >= cohort_month
					   And start_session < cohort_month+ interval '3 month') 

-- 6. Агрегация активности по когортам и месяцам жизни    
,Play_users_count as(Select Cohort_month, 
                            Month_number, 
                            Count (distinct id_user) as Playing_users 
                       From play_users_month
				   Group by Cohort_month, 
				            Month_number) 
  
-- 7. Финальная витрина когортного анализа 
Select cza.Cohort_month, 
       cza.month_number, 
       COALESCE (Playing_users, 0) Playing_users, 
       COALESCE (Paying_users, 0) Paying_users, 
       COALESCE (Total_users, 0) Total_users,

	   -- Retention: доля активных пользователей
       TO_CHAR(COALESCE(playing_users, 0)::float /nullif(total_users,0) *100, 'fm990.00')||'%' as retention_percent, 

	   COALESCE(Total_revenue, 0) Total_revenue,

	    -- ARPU: доход на всех пользователей когорты 
       COALESCE(total_revenue, 0)/nullif(total_users,0) *1.0 ARPU,

	   -- CARPU: кумулятивный доход на всех пользователе
       SUM (COALESCE(total_revenue, 0)) over (partition by cza.cohort_month Order by cza.month_number)  
	   /nullif(total_users,0) *1.0 CARPU, 

	   -- ARPPU: доход на платящих пользователей
       COALESCE (total_revenue, 0)/nullif(paying_users,0)*1.0 ARPPU, 

	    -- Накопленное число новых плательщиков
       Nullif (sum(COALESCE (new_payers,0)) 
	   over (partition by cza.cohort_month Order by cza.month_number),0) as comul_new_payers,   

	   -- CARPPU: кумулятивный доход на платящих пользователей
       SUM (COALESCE(total_revenue, 0)) over (partition by cza.cohort_month Order by cza.month_number) 
	   /nullif (sum(COALESCE(new_payers,0)) 
	   over (partition by cza.cohort_month Order by cza.month_number), 0)*1.0 CARPPU 


  From cohort_size_and_month_number cza
  Left Join payments_users pu
         On cza.cohort_month = pu.cohort_month
        And cza.month_number = pu.month_number 
  Left Join Play_users_count puc
         On cza.cohort_month = puc.cohort_month 
        And cza.month_number = puc.month_number
  Order by cza.Cohort_month, cza.month_number