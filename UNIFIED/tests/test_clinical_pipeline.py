from sites.head_neck.engine import evaluate_sampled_metrics


def test_hn_case_uses_eval_v105_and_oar_metrics():
    result = evaluate_sampled_metrics(
        {
            "PTV_High": {
                "V100Rx_%": 98,
                "V95Rx_%": 100,
                "V105Rx_%": 4,
                "Dmin_%Rx": 90,
            },
            "PTV_Low": {
                "V100Rx_%": 96,
                "V95Rx_%": 99,
                "V105Rx_%": 40,
                "Dmin_%Rx": 85,
            },
            "PTV_Low_eval": {
                "V105Rx_%": 8,
            },
            "SpinalCord": {
                "D0.03cc_Gy": 42,
            },
            "Mandible": {
                "D0.03cc_Gy": 69,
            },
        },
        plan_prescription_gy=70,
    )

    metric_pairs = {
        (row["structure"], row["metric"])
        for row in result["metrics"]
    }

    assert ("PTV_Low_eval", "V105Rx_%") in metric_pairs
    assert ("SpinalCord", "D0.03cc_Gy") in metric_pairs
    assert ("Mandible", "D0.03cc_Gy") in metric_pairs
    assert result["missing_eval"] is False


def test_missing_lower_dose_eval_is_flagged():
    result = evaluate_sampled_metrics(
        {
            "PTV_High": {
                "V100Rx_%": 98,
                "V95Rx_%": 100,
                "V105Rx_%": 4,
                "Dmin_%Rx": 90,
            },
            "PTV_Low": {
                "V100Rx_%": 96,
                "V95Rx_%": 99,
                "V105Rx_%": 40,
                "Dmin_%Rx": 85,
            },
        },
        plan_prescription_gy=70,
    )
    assert result["missing_eval"] is True
