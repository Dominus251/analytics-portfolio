-- 1. Справочники
CREATE TABLE genres (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE developers (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE publishers (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE platforms (
    id INTEGER PRIMARY KEY,
    name TEXT
);

CREATE TABLE categories (
    id INTEGER PRIMARY KEY,
    name TEXT
);

-- 2. Основная таблица приложений
CREATE TABLE applications (
    appid INTEGER PRIMARY KEY,
    name TEXT,
    type TEXT,
    is_free BOOLEAN,
    release_date DATE,
    required_age TEXT, -- тип TEXT выбран ввиду наличия анаомалий, далее INTEGER
    supported_languages TEXT,
    recommendations_total INTEGER,
    mat_supports_windows BOOLEAN,
    mat_supports_mac BOOLEAN,
    mat_supports_linux BOOLEAN,
    mat_initial_price INTEGER,      -- цена в центах
    mat_final_price INTEGER,        -- цена в центах
    mat_currency TEXT
);

-- 3. Связующие таблицы (many-to-many)
CREATE TABLE application_genres (
    appid INTEGER,
    genre_id INTEGER
);

CREATE TABLE application_developers (
    appid INTEGER,
    developer_id INTEGER
);

CREATE TABLE application_publishers (
    appid INTEGER,
    publisher_id INTEGER
);

CREATE TABLE application_categories (
    appid INTEGER,
    category_id INTEGER
);

CREATE TABLE application_platforms (
    appid INTEGER,
    platform_id INTEGER
);

-- 4. Таблица отзывов (точная структура)
CREATE TABLE reviews (
    recommendationid INTEGER PRIMARY KEY,
    appid INTEGER,
    author_steamid BIGINT,
    author_num_reviews INTEGER,
    author_playtime_forever INTEGER,   -- в минутах
    language TEXT,
    voted_up BOOLEAN,
    written_during_early_access BOOLEAN
);

