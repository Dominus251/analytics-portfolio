CREATE TABLE steam_mart (
    appid Int32,
    name String,
    type String,
    is_free UInt8,
    release_date Date,
    required_age Int32,
    supported_languages String,
    publishers String,
    genres String,
    developers String,
    categories String,
    platforms String,
    total_reviews Int32,
    positive_share Float32
) ENGINE = MergeTree()
ORDER BY (release_date, appid);