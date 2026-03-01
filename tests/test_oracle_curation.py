"""Unit tests for oracle curation helpers in scripts/curate_oracle.py.

Covers the five new features added in the five-way bias mitigation commit:
  1. _classify_line_context
  2. _infer_file_tier
  3. generate_query_variations
  4. get_curation_queries  (priority chain, no LLM I/O)
  5. validate_oracle_quality
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.curate_oracle import (
    _classify_line_context,
    _infer_file_tier,
    generate_query_variations,
    get_curation_queries,
    validate_oracle_quality,
)


# ---------------------------------------------------------------------------
# _classify_line_context
# ---------------------------------------------------------------------------

class ClassifyLineContextTests(unittest.TestCase):

    # --- comment detection ---

    def test_c_line_comment(self):
        self.assertEqual(_classify_line_context("// This is a comment"), "comment")

    def test_hash_comment(self):
        self.assertEqual(_classify_line_context("# python comment"), "comment")

    def test_sql_comment(self):
        self.assertEqual(_classify_line_context("-- SELECT name FROM"), "comment")

    def test_block_comment_open(self):
        self.assertEqual(_classify_line_context("/* start of block */"), "comment")

    def test_block_comment_continuation(self):
        self.assertEqual(_classify_line_context(" * continuation line"), "comment")

    def test_html_comment(self):
        self.assertEqual(_classify_line_context("<!-- HTML comment -->"), "comment")

    def test_lisp_comment(self):
        self.assertEqual(_classify_line_context(";; lisp comment"), "comment")

    def test_comment_with_leading_whitespace(self):
        self.assertEqual(_classify_line_context("    // indented comment"), "comment")

    # --- string detection ---

    def test_string_assignment_double_quote(self):
        self.assertEqual(_classify_line_context('name = "ClusterRole"'), "string")

    def test_string_assignment_single_quote(self):
        self.assertEqual(_classify_line_context("kind: 'ClusterRole'"), "string")

    def test_string_field_colon(self):
        self.assertEqual(_classify_line_context('apiVersion: "rbac.authorization.k8s.io/v1"'), "string")

    # --- code ---

    def test_go_func_declaration(self):
        self.assertEqual(_classify_line_context("func NewClusterRole() *ClusterRole {"), "code")

    def test_python_class(self):
        self.assertEqual(_classify_line_context("class ClusterRoleBinding:"), "code")

    def test_rust_impl(self):
        self.assertEqual(_classify_line_context("impl Authorizer for RbacAuthorizer {"), "code")

    def test_java_method(self):
        self.assertEqual(_classify_line_context("public ClusterRole getClusterRole() {"), "code")

    def test_plain_code_usage(self):
        self.assertEqual(_classify_line_context("return clusterRole.rules"), "code")

    def test_empty_string_is_code(self):
        # Edge case: empty preview should not crash and defaults to code
        self.assertEqual(_classify_line_context(""), "code")


# ---------------------------------------------------------------------------
# _infer_file_tier
# ---------------------------------------------------------------------------

class InferFileTierTests(unittest.TestCase):

    def _match(self, preview: str, ctx: str = "code") -> dict:
        """Build a minimal lineMatches entry."""
        return {"preview": preview}

    # --- test/mock paths → always sufficient ---

    def test_test_path_suffix(self):
        tier = _infer_file_tier("pkg/auth/rbac_test.go", [self._match("func TestClusterRole(")])
        self.assertEqual(tier, "sufficient")

    def test_test_prefix_path(self):
        tier = _infer_file_tier("test_rbac.py", [self._match("def test_create_cluster_role():")])
        self.assertEqual(tier, "sufficient")

    def test_tests_directory(self):
        tier = _infer_file_tier("src/tests/auth_test.rs", [self._match("fn test_auth() {")])
        self.assertEqual(tier, "sufficient")

    def test_mock_path(self):
        tier = _infer_file_tier("internal/mock/rbac_mock.go", [self._match("func MockClusterRole(")])
        self.assertEqual(tier, "sufficient")

    def test_fixture_path(self):
        tier = _infer_file_tier("fixtures/cluster_role.yaml", [self._match("kind: ClusterRole")])
        self.assertEqual(tier, "sufficient")

    # --- all comment/string hits → sufficient ---

    def test_all_comment_hits(self):
        matches = [
            {"preview": "// ClusterRole is defined here"},
            {"preview": "// see ClusterRoleBinding"},
        ]
        tier = _infer_file_tier("docs/design.go", matches)
        self.assertEqual(tier, "sufficient")

    def test_all_string_hits(self):
        matches = [{"preview": 'kind = "ClusterRole"'}]
        tier = _infer_file_tier("config/defaults.go", matches)
        # String-assigned hit has no code context → sufficient
        self.assertEqual(tier, "sufficient")

    # --- definition pattern in code → required ---

    def test_func_definition(self):
        matches = [{"preview": "func NewClusterRole(name string) *ClusterRole {"}]
        tier = _infer_file_tier("pkg/auth/rbac.go", matches)
        self.assertEqual(tier, "required")

    def test_class_definition(self):
        matches = [{"preview": "class ClusterRole:"}]
        tier = _infer_file_tier("auth/models.py", matches)
        self.assertEqual(tier, "required")

    def test_struct_definition(self):
        matches = [{"preview": "type ClusterRole struct {"}]
        tier = _infer_file_tier("api/types.go", matches)
        self.assertEqual(tier, "required")

    def test_interface_definition(self):
        matches = [{"preview": "interface Authorizer {"}]
        tier = _infer_file_tier("pkg/auth/interface.go", matches)
        self.assertEqual(tier, "required")

    def test_java_public_method(self):
        matches = [{"preview": "public ClusterRole createRole() {"}]
        tier = _infer_file_tier("src/main/RbacService.java", matches)
        self.assertEqual(tier, "required")

    def test_upper_camel_assignment(self):
        matches = [{"preview": "ClusterRole = NewRole()"}]
        tier = _infer_file_tier("pkg/defaults.go", matches)
        self.assertEqual(tier, "required")

    # --- code usage (not definition) → required (any code hit counts) ---

    def test_code_usage_becomes_required(self):
        matches = [{"preview": "return authorizer.ClusterRoles()"}]
        tier = _infer_file_tier("pkg/handler.go", matches)
        self.assertEqual(tier, "required")

    # --- no line matches → sufficient ---

    def test_no_line_matches(self):
        tier = _infer_file_tier("pkg/auth/rbac.go", [])
        self.assertEqual(tier, "sufficient")

    # --- mixed hits: definition takes priority over test path for non-test paths ---

    def test_mixed_comment_and_definition(self):
        matches = [
            {"preview": "// ClusterRole is the main type"},
            {"preview": "type ClusterRole struct {"},
        ]
        tier = _infer_file_tier("pkg/types.go", matches)
        self.assertEqual(tier, "required")


# ---------------------------------------------------------------------------
# generate_query_variations
# ---------------------------------------------------------------------------

class GenerateQueryVariationsTests(unittest.TestCase):

    def test_single_term_returns_itself(self):
        result = generate_query_variations("ClusterRole", num_runs=3)
        self.assertIn("ClusterRole", result)

    def test_or_pattern_splits(self):
        result = generate_query_variations("ClusterRole OR ClusterRoleBinding", num_runs=3)
        self.assertIn("ClusterRole", result)
        self.assertIn("ClusterRoleBinding", result)

    def test_and_pattern_splits(self):
        result = generate_query_variations("heartbeat AND timeout", num_runs=3)
        self.assertIn("heartbeat", result)
        self.assertIn("timeout", result)

    def test_respects_num_runs_limit(self):
        result = generate_query_variations("a OR b OR c OR d OR e", num_runs=2)
        self.assertLessEqual(len(result), 2)

    def test_camelcase_mined_from_seed(self):
        # Search pattern is "sharedInformer"; seed has a DIFFERENT CamelCase term
        # (ResourceEventHandler) that should be mined as an extra variation.
        seed = "Implement SharedInformer with ResourceEventHandler callbacks"
        result = generate_query_variations("sharedInformer", seed_prompt=seed, num_runs=5)
        combined = " ".join(result)
        self.assertIn("ResourceEventHandler", combined)

    def test_camelcase_dedup_is_case_insensitive(self):
        # SharedInformer from seed has same lowercase as search_pattern sharedInformer
        # — deduplication must skip it, so we should NOT see it twice
        seed = "Implement SharedInformer for Kubernetes controller"
        result = generate_query_variations("sharedInformer", seed_prompt=seed, num_runs=5)
        lowered = [t.lower() for t in result]
        self.assertEqual(lowered.count("sharedinformer"), 1)

    def test_no_duplicates(self):
        result = generate_query_variations("foo OR foo", num_runs=5)
        self.assertEqual(len(result), len(set(result)))

    def test_empty_pattern(self):
        result = generate_query_variations("", num_runs=3)
        # Should not crash; may return empty list or list with empty string
        self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# get_curation_queries
# ---------------------------------------------------------------------------

class GetCurationQueriesTests(unittest.TestCase):

    def test_explicit_curation_queries_take_priority(self):
        params = {
            "search_pattern": "ClusterRole",
            "curation_queries": ["ClusterRoleBinding", "PolicyRule subjects", "rbac rules"],
        }
        queries, source = get_curation_queries(params, seed_prompt="", num_runs=4, use_llm=False)
        self.assertEqual(source, "task_spec_curation_queries")
        self.assertIn("ClusterRoleBinding", queries)

    def test_explicit_curation_queries_capped_at_num_runs(self):
        params = {"curation_queries": ["a", "b", "c", "d", "e"]}
        queries, _ = get_curation_queries(params, seed_prompt="", num_runs=3, use_llm=False)
        self.assertLessEqual(len(queries), 3)

    def test_falls_back_to_pattern_variation_when_no_llm(self):
        params = {"search_pattern": "ClusterRole OR ClusterRoleBinding"}
        queries, source = get_curation_queries(params, seed_prompt="", num_runs=3, use_llm=False)
        self.assertEqual(source, "pattern_variation")
        self.assertIn("ClusterRole", queries)

    def test_no_llm_flag_skips_llm(self):
        params = {"search_pattern": "foo"}
        # Even with an api_key present, use_llm=False must bypass LLM path
        queries, source = get_curation_queries(
            params, seed_prompt="some task", num_runs=3, use_llm=False, api_key="fake-key"
        )
        self.assertEqual(source, "pattern_variation")

    def test_empty_curation_queries_list_falls_through(self):
        params = {"search_pattern": "heartbeat", "curation_queries": []}
        queries, source = get_curation_queries(params, seed_prompt="", num_runs=3, use_llm=False)
        self.assertEqual(source, "pattern_variation")
        self.assertIn("heartbeat", queries)

    def test_missing_search_pattern_does_not_crash(self):
        params = {}
        queries, source = get_curation_queries(params, seed_prompt="", num_runs=3, use_llm=False)
        self.assertIsInstance(queries, list)


# ---------------------------------------------------------------------------
# validate_oracle_quality
# ---------------------------------------------------------------------------

class ValidateOracleQualityTests(unittest.TestCase):

    def _run(self, oracle_files, search_pattern="ClusterRole", repos=None):
        log: list = []
        validate_oracle_quality(
            oracle_files,
            search_pattern,
            repos or ["k8s/k8s"],
            log,
        )
        return log[-1]  # always appends one entry

    # --- no warnings on healthy oracle ---

    def test_healthy_oracle_no_warnings(self):
        files = [
            {"repo": "k8s/k8s", "path": f"pkg/auth/file{i}.go", "tier": "required"}
            for i in range(5)
        ]
        entry = self._run(files)
        self.assertEqual(entry["warnings"], [])

    # --- large oracle warning ---

    def test_large_oracle_warns(self):
        files = [
            {"repo": "k8s/k8s", "path": f"pkg/f{i}.go"}
            for i in range(16)
        ]
        entry = self._run(files)
        self.assertTrue(any("large oracle" in w for w in entry["warnings"]))

    def test_exactly_15_files_no_warning(self):
        files = [{"repo": "k8s/k8s", "path": f"pkg/f{i}.go"} for i in range(15)]
        entry = self._run(files)
        self.assertFalse(any("large oracle" in w for w in entry["warnings"]))

    # --- single-term over-population warning ---

    def test_single_term_many_files_per_repo_warns(self):
        files = [{"repo": "k8s/k8s", "path": f"pkg/f{i}.go"} for i in range(6)]
        # search_pattern has only 1 term (no OR/AND)
        entry = self._run(files, search_pattern="ClusterRole")
        self.assertTrue(any("single-term" in w for w in entry["warnings"]))

    def test_multi_term_no_over_population_warning(self):
        files = [{"repo": "k8s/k8s", "path": f"pkg/f{i}.go"} for i in range(6)]
        entry = self._run(files, search_pattern="ClusterRole OR ClusterRoleBinding")
        self.assertFalse(any("single-term" in w for w in entry["warnings"]))

    # --- zero required-tier warning ---

    def test_no_required_tier_warns(self):
        files = [
            {"repo": "k8s/k8s", "path": f"tests/f{i}.go", "tier": "sufficient"}
            for i in range(6)
        ]
        entry = self._run(files)
        self.assertTrue(any("required" in w for w in entry["warnings"]))

    def test_zero_required_below_threshold_no_warn(self):
        # Only 5 files total — threshold is n_files > 5
        files = [
            {"repo": "k8s/k8s", "path": f"tests/f{i}.go", "tier": "sufficient"}
            for i in range(5)
        ]
        entry = self._run(files)
        self.assertFalse(any("required" in w for w in entry["warnings"]))

    # --- tier imbalance warning ---

    def test_tier_imbalance_warns(self):
        required = [{"repo": "k8s/k8s", "path": "pkg/main.go", "tier": "required"}]
        sufficient = [
            {"repo": "k8s/k8s", "path": f"tests/f{i}.go", "tier": "sufficient"}
            for i in range(5)  # 5 sufficient vs 1 required → ratio 5:1 > 4:1
        ]
        entry = self._run(required + sufficient)
        self.assertTrue(any("imbalance" in w for w in entry["warnings"]))

    def test_four_to_one_ratio_no_imbalance_warning(self):
        required = [{"repo": "k8s/k8s", "path": "pkg/main.go", "tier": "required"}]
        sufficient = [
            {"repo": "k8s/k8s", "path": f"tests/f{i}.go", "tier": "sufficient"}
            for i in range(4)  # exactly 4:1 — not >4:1
        ]
        entry = self._run(required + sufficient)
        self.assertFalse(any("imbalance" in w for w in entry["warnings"]))

    # --- log entry structure ---

    def test_log_entry_has_expected_keys(self):
        entry = self._run([])
        for key in ("event", "n_files", "n_repos", "required_count", "sufficient_count", "warnings"):
            self.assertIn(key, entry)

    def test_log_entry_counts_tiers_correctly(self):
        files = [
            {"repo": "k8s/k8s", "path": "a.go", "tier": "required"},
            {"repo": "k8s/k8s", "path": "b.go", "tier": "required"},
            {"repo": "k8s/k8s", "path": "c.go", "tier": "sufficient"},
        ]
        entry = self._run(files)
        self.assertEqual(entry["required_count"], 2)
        self.assertEqual(entry["sufficient_count"], 1)
        self.assertEqual(entry["n_files"], 3)


if __name__ == "__main__":
    unittest.main()
