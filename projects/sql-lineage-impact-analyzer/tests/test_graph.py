from lineage_guard.errors import DuplicateModelError, UnknownModelError
from lineage_guard.graph import ParsedModel, build_impact, build_report


def sample_report():
    return build_report(
        [
            ParsedModel("raw_orders", "raw_orders.sql", ("landing.orders",)),
            ParsedModel("stg_orders", "stg_orders.sql", ("raw_orders",)),
            ParsedModel("dim_customers", "dim_customers.sql", ("landing.customers",)),
            ParsedModel(
                "mart_revenue",
                "mart_revenue.sql",
                ("stg_orders", "dim_customers"),
            ),
        ],
        "postgres",
    )


def test_internal_and_external_dependencies_are_separated():
    report = sample_report()
    by_name = {model.name: model for model in report.models}
    assert by_name["stg_orders"].dependencies == ("raw_orders",)
    assert by_name["raw_orders"].external_dependencies == ("landing.orders",)
    assert by_name["mart_revenue"].dependencies == ("dim_customers", "stg_orders")
    assert len(report.edges) == 3


def test_topological_order_places_dependencies_before_consumers():
    report = sample_report()
    positions = {name: index for index, name in enumerate(report.topological_order)}
    for edge in report.edges:
        assert positions[edge["upstream"]] < positions[edge["downstream"]]


def test_impact_is_transitive_and_distance_ordered():
    report = sample_report()
    impact = build_impact(report, ["raw_orders"])
    assert [(item.model, item.distance) for item in impact.affected] == [
        ("stg_orders", 1),
        ("mart_revenue", 2),
    ]


def test_multiple_changes_do_not_duplicate_affected_models():
    impact = build_impact(sample_report(), ["raw_orders", "dim_customers"])
    assert impact.changed == ("dim_customers", "raw_orders")
    assert [item.model for item in impact.affected] == ["mart_revenue", "stg_orders"]
    assert all(item.distance == 1 for item in impact.affected)


def test_cycles_are_detected_and_order_is_incomplete():
    report = build_report(
        [
            ParsedModel("alpha", "alpha.sql", ("beta",)),
            ParsedModel("beta", "beta.sql", ("alpha",)),
            ParsedModel("independent", "independent.sql", ()),
        ],
        "postgres",
    )
    assert report.cycles == (("alpha", "beta", "alpha"),)
    assert report.topological_order == ("independent",)


def test_duplicate_model_names_are_rejected_case_insensitively():
    models = [
        ParsedModel("Orders", "one/Orders.sql", ()),
        ParsedModel("orders", "two/orders.sql", ()),
    ]
    try:
        build_report(models, "postgres")
    except DuplicateModelError as exc:
        assert "Duplicate model name" in str(exc)
    else:
        raise AssertionError("Expected duplicate model name to fail")


def test_unknown_changed_model_is_an_error():
    try:
        build_impact(sample_report(), ["does_not_exist"])
    except UnknownModelError as exc:
        assert "does_not_exist" in str(exc)
    else:
        raise AssertionError("Expected unknown model to fail")
