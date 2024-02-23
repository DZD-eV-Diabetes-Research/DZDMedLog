SELECT
    generic_sql_drug_search_cache.pzn,
    (
        CASE
            WHEN (
                lower(generic_sql_drug_search_cache.index_content) LIKE '%' || lower(:index_content_1) || '%'
            ) THEN :param_1
            WHEN (
                generic_sql_drug_search_cache.index_content LIKE '%' || :index_content_2 || '%'
            ) THEN :param_2
            ELSE :param_3
        END + CASE
            WHEN (
                lower(generic_sql_drug_search_cache.index_content) LIKE '%' || lower(:index_content_3) || '%'
            ) THEN :param_4
            WHEN (
                generic_sql_drug_search_cache.index_content LIKE '%' || :index_content_4 || '%'
            ) THEN :param_5
            ELSE :param_6
        END
    ) + CASE
        WHEN (
            lower(generic_sql_drug_search_cache.index_content) LIKE '%' || lower(:index_content_5) || '%'
        ) THEN :param_7
        WHEN (
            generic_sql_drug_search_cache.index_content LIKE '%' || :index_content_6 || '%'
        ) THEN :param_8
        ELSE :param_9
    END AS score
FROM
    generic_sql_drug_search_cache
ORDER BY
    score DESC
LIMIT
    :param_10