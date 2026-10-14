import unittest

from maintenance_ml.data import generate_dataset
from maintenance_ml.metrics import best_f1_threshold, classification_metrics
from maintenance_ml.model import LogisticRegression, Standardizer
from maintenance_ml.pipeline import evaluate


class DataTests(unittest.TestCase):
    def test_generation_is_deterministic_and_has_both_classes(self):
        self.assertEqual(generate_dataset(3, 10, 40), generate_dataset(3, 10, 40))
        labels = [r.label for r in generate_dataset(3, 10, 40)]
        self.assertIn(0, labels)
        self.assertIn(1, labels)

    def test_invalid_size_fails_clearly(self):
        with self.assertRaises(ValueError):
            generate_dataset(machines=2)


class ModelTests(unittest.TestCase):
    def test_logistic_regression_learns_separable_data(self):
        x = [[-2.0], [-1.0], [1.0], [2.0]]
        model = LogisticRegression(epochs=500).fit(x, [0, 0, 1, 1])
        probabilities = model.predict_proba(x)
        self.assertLess(probabilities[0], .5)
        self.assertGreater(probabilities[-1], .5)

    def test_scaler_uses_training_statistics(self):
        scaler = Standardizer().fit([(1.0, 10.0), (3.0, 10.0)])
        transformed = scaler.transform([(2.0, 10.0)])[0]
        self.assertAlmostEqual(transformed[0], 0)
        self.assertEqual(transformed[1], 0)


class MetricTests(unittest.TestCase):
    def test_metrics_and_threshold(self):
        labels, scores = [0, 0, 1, 1], [.1, .2, .8, .9]
        result = classification_metrics(labels, scores, best_f1_threshold(labels, scores))
        self.assertEqual(result["f1"], 1.0)
        self.assertEqual(result["pr_auc"], 1.0)
        self.assertEqual(result["roc_auc"], 1.0)


class PipelineTests(unittest.TestCase):
    def test_evaluation_repeats_and_splits_by_machine(self):
        first, predictions = evaluate(17)
        second, _ = evaluate(17)
        self.assertEqual(first, second)
        self.assertEqual(first["split"]["test_machines"], 24)
        self.assertTrue(predictions)
        self.assertGreater(first["logistic_regression"]["recall"], .5)


if __name__ == "__main__":
    unittest.main()
