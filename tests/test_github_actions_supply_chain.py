from __future__ import annotations
import unittest

from finite_ram_lab.github_actions_supply_chain import (
    audit_workflows,classify_use,lockfile_preflight,scan_workflow_text
)


class GitHubActionsSupplyChainTests(unittest.TestCase):
    def test_mutable_tag_is_unpinned(self):
        row=classify_use(".github/workflows/ci.yml",4,"actions/checkout@v7")
        self.assertEqual(row.kind,"GITHUB_ACTION")
        self.assertFalse(row.pinned)

    def test_exact_commit_sha_is_pinned(self):
        row=classify_use(
            ".github/workflows/ci.yml",4,
            "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        )
        self.assertTrue(row.pinned)

    def test_local_action_is_not_external_supply_chain(self):
        row=classify_use(".github/workflows/ci.yml",4,"./.github/actions/test")
        self.assertEqual(row.kind,"LOCAL")
        self.assertTrue(row.pinned)

    def test_docker_tag_is_not_silently_treated_as_pinned(self):
        row=classify_use(".github/workflows/ci.yml",4,"docker://alpine:3.20")
        self.assertFalse(row.pinned)
        digest=classify_use(
            ".github/workflows/ci.yml",4,
            "docker://alpine@sha256:"+"a"*64,
        )
        self.assertTrue(digest.pinned)

    def test_audit_finds_real_style_mutable_action_refs(self):
        text="""name: ci
jobs:
  test:
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
      - uses: ./.github/actions/local
"""
        row=audit_workflows(((".github/workflows/ci.yml",text),))
        self.assertEqual(row["external_use_count"],2)
        self.assertEqual(row["unpinned_external_count"],2)
        self.assertFalse(row["all_external_pinned"])
        self.assertFalse(row["workflow_rewrite_performed"])

    def test_preview_lock_schema_never_authorizes_rewrite(self):
        row=lockfile_preflight(lock_version="v0.0.3")
        self.assertEqual(row["status"],"PREVIEW_SCHEMA_RECOGNIZED")
        self.assertFalse(row["rewrite_authorized"])

    def test_missing_lockfile_is_explicit(self):
        row=lockfile_preflight(lock_version=None)
        self.assertEqual(row["status"],"MISSING")


if __name__=="__main__":
    unittest.main()
