import unittest
from pathlib import Path
from unittest.mock import patch

from explorer.research_audit import load_public_contract, OUT
from explorer.research_audit_data import prompt


class ResearchAuditTests(unittest.TestCase):
    def test_common_prompt_has_no_disallowed_nor_example_and_names_new_variable(self):
        meta = {'variables': ['x', 'y', 'z'], 'operators': ['AND', 'OR', 'NOT'], 'max_depth': 2,
                'mechanistic_opts': {'apply_commutativity': True, 'apply_idempotence_and_or': True, 'flatten_associativity': True}}
        text = prompt(meta, [{'inputs': {'x': 0, 'y': 1, 'z': 0}, 'output': 1}])
        self.assertIn('Use lowercase for variables: x, y, z', text)
        self.assertNotIn('Expression: NOR(', text)
        self.assertIn('2. Use ONLY these operators: AND, NOT, OR', text)

    @unittest.skipUnless((OUT / 'protocol.json').exists(), 'Prepare frozen audit first')
    def test_generation_contract_loads_without_reading_any_solution_file(self):
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            self.assertNotEqual(path.name, 'scoring_references.json')
            self.assertNotEqual(path.name, 'tasks.json')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', guarded):
            protocol, tasks = load_public_contract()
        self.assertEqual(protocol['budget'], 16)
        self.assertEqual(len(tasks), 38)
        self.assertTrue(all('reference_keys' not in t and 'reference_size' not in t for t in tasks))


if __name__ == '__main__':
    unittest.main()
