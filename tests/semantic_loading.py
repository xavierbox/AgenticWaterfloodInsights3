import unittest
from pathlib import Path

from StuffThatDidntWork.load_semantics import load_semantics


class TestSemanticLoading(unittest.TestCase):
    def test_load_semantics_models(self) -> None:
        catalog, idioms, context = load_semantics(Path('semantics'))

        self.assertGreaterEqual(len(catalog.tables), 1)
        self.assertGreaterEqual(len(catalog.query_catalog), 1)
        self.assertGreaterEqual(len(idioms.idioms), 1)

        table_names = {t.name for t in catalog.tables}
        self.assertIn('injectors', table_names)
        self.assertIn('producers', table_names)
        self.assertIn('locations', table_names)

        self.assertIsInstance(context.definitions, list)
        self.assertIsInstance(context.business_rules, list)
        self.assertIsInstance(context.domain_knowledge, list)


if __name__ == '__main__':
    unittest.main()
