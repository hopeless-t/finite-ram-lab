from pathlib import Path
import unittest


class Strata005WorkflowContractTests(unittest.TestCase):
    def test_systemd_trial_uses_absolute_spec_path(self) -> None:
        workflow = Path(
            ".github/workflows/strata-005-external-validity.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'SPEC="$GITHUB_WORKSPACE/specs/STRATA-005-EXTERNAL-VALIDITY-v1.json"',
            workflow,
        )
        self.assertIn('--spec "$SPEC"', workflow)

        panel = workflow.split("- name: Run five-arm panel with Recorder", 1)[1]
        panel = panel.split("- uses: actions/upload-artifact@v7", 1)[0]
        self.assertNotIn(
            "--spec specs/STRATA-005-EXTERNAL-VALIDITY-v1.json",
            panel,
        )


if __name__ == "__main__":
    unittest.main()
