import pytest

from lineage_guard.errors import ModelParseError
from lineage_guard.sql_parser import parse_model_sql


def test_ctes_and_aliases_are_not_reported_as_physical_tables():
    sql = """
    WITH recent AS (
        SELECT * FROM landing.orders
    ),
    totals AS (
        SELECT customer_id, COUNT(*) AS order_count FROM recent GROUP BY customer_id
    )
    SELECT t.customer_id
    FROM totals AS t
    JOIN analytics.customers AS c ON c.customer_id = t.customer_id
    """
    assert parse_model_sql(sql, "model.sql", "postgres") == {
        "landing.orders",
        "analytics.customers",
    }


def test_nested_query_references_are_found():
    sql = """
    SELECT q.id
    FROM (SELECT id FROM warehouse.events) AS q
    JOIN warehouse.accounts a ON a.id = q.id
    """
    assert parse_model_sql(sql, "nested.sql", "postgres") == {
        "warehouse.events",
        "warehouse.accounts",
    }


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "INSERT INTO target SELECT * FROM source",
        "SELECT * FROM source; SELECT * FROM other_source",
        "SELECT FROM",
    ],
)
def test_empty_non_query_multiple_statement_and_invalid_sql_are_rejected(sql):
    with pytest.raises(ModelParseError):
        parse_model_sql(sql, "bad.sql", "postgres")
