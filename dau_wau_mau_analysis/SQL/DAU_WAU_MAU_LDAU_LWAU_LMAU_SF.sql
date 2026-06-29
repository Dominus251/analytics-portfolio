-- Лояльные пользователи: пригласили >=3 друзей, из которых хотя бы один зарегистрировался
WITH loyal_users AS (
    SELECT id_user
    FROM skygame.referral
    GROUP BY id_user
    HAVING COUNT(*) >= 3 AND SUM(ref_reg) >= 1
),

-- Все дни диапазона
all_day AS (
    SELECT generate_series('2022-07-02'::date, '2023-03-07'::date, '1 day')::date AS day
)

SELECT 
    ad.day,
    COALESCE(a."DAU", 0) AS "DAU",
    COALESCE(a."LDAU", 0) AS "LDAU",
    COALESCE(b."WAU", 0) AS "WAU",
    COALESCE(b."LWAU", 0) AS "LWAU",
    COALESCE(c."MAU", 0) AS "MAU",
    COALESCE(c."LMAU", 0) AS "LMAU",
    TO_CHAR(COALESCE(a."DAU", 0)::float / NULLIF(COALESCE(b."WAU", 0), 0) * 100, 'FM990.00') || '%' AS "SF(week)",
    TO_CHAR(COALESCE(a."DAU", 0)::float / NULLIF(COALESCE(c."MAU", 0), 0) * 100, 'FM990.00') || '%' AS "SF(month)"
FROM all_day ad
LEFT JOIN LATERAL (
    SELECT 
        COUNT(DISTINCT gsa.id_user) AS "DAU",
        COUNT(DISTINCT lua.id_user) AS "LDAU"
    FROM skygame.game_sessions gsa
    LEFT JOIN loyal_users lua ON gsa.id_user = lua.id_user
    WHERE ad.day = gsa.start_session::date
      AND gsa.end_session IS NOT NULL
) a ON true
LEFT JOIN LATERAL (
    SELECT 
        COUNT(DISTINCT gsb.id_user) AS "WAU",
        COUNT(DISTINCT lub.id_user) AS "LWAU"
    FROM skygame.game_sessions gsb
    LEFT JOIN loyal_users lub ON gsb.id_user = lub.id_user
    WHERE gsb.start_session::date BETWEEN ad.day - INTERVAL '6 day' AND ad.day
      AND gsb.end_session IS NOT NULL
) b ON true
LEFT JOIN LATERAL (
    SELECT 
        COUNT(DISTINCT gsc.id_user) AS "MAU",
        COUNT(DISTINCT luc.id_user) AS "LMAU"
    FROM skygame.game_sessions gsc
    LEFT JOIN loyal_users luc ON gsc.id_user = luc.id_user
    WHERE gsc.start_session::date BETWEEN ad.day - INTERVAL '29 day' AND ad.day
      AND gsc.end_session IS NOT NULL
) c ON true
ORDER BY ad.day;