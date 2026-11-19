"""Pure-static safety contract for the standalone production E2E launcher.

No secrets, network calls, account mutations, or workflow executions.
"""
from pathlib import Path

WORKFLOW = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "papersignal-live-e2e.yml"
).read_text(encoding="utf-8")

AUDITED_SHA = "431059a1116a50f39fd56d565c35a1afc081b8fc"


def test_manual_only_main_branch_and_separate_confirmation_are_required():
    assert "on:\n  workflow_dispatch:\n" in WORKFLOW
    assert "\n  push:" not in WORKFLOW
    assert "\n  pull_request:" not in WORKFLOW
    assert "github.ref == 'refs/heads/main'" in WORKFLOW
    assert "inputs.target == 'papersignal-production'" in WORKFLOW
    assert "inputs.approve_mutations == true" in WORKFLOW
    assert "inputs.acknowledgment == 'RUN_SYNTHETIC_LIVE_E2E'" in WORKFLOW
    assert "inputs.approved_commit == '" + AUDITED_SHA + "'" in WORKFLOW


def test_source_is_immutable_and_token_permissions_are_read_only():
    assert "permissions:\n  contents: read\n" in WORKFLOW
    assert "persist-credentials: false" in WORKFLOW
    assert "cancel-in-progress: false" in WORKFLOW
    assert "group: papersignal-live-e2e-production" in WORKFLOW
    assert "          ref: " + AUDITED_SHA in WORKFLOW
    assert 'test "$(git rev-parse HEAD)" = ' + "'" + AUDITED_SHA + "'" in WORKFLOW
    assert "git checkout" not in WORKFLOW
    assert "git pull" not in WORKFLOW


def test_production_secrets_are_scoped_after_dependency_install():
    assert "Install reviewed Python requirements without privileged environment" in WORKFLOW
    assert "Check target allowlist and upgraded API without mutations" in WORKFLOW
    assert "Run approved two-account synthetic E2E" in WORKFLOW
    installation = WORKFLOW.index("Install reviewed Python requirements")
    first_secret = WORKFLOW.index("secrets.SUPABASE_SERVICE_ROLE_KEY")
    assert first_secret > installation
    assert "PAPERSIGNAL_E2E_APPROVED: RUN_SYNTHETIC_LIVE_E2E" in WORKFLOW
    assert "PAPERSIGNAL_E2E_ENABLED:" in WORKFLOW
    assert "PAPERSIGNAL_API_URL" in WORKFLOW
    assert "module._validate_live_e2e_target" in WORKFLOW
    assert "module._assert_server_ready_for_live_e2e" in WORKFLOW


def test_workflow_does_not_apply_database_migrations_or_rollout_code():
    assert "supabase db push" not in WORKFLOW
    assert "supabase migration" not in WORKFLOW
    assert "railway up" not in WORKFLOW
    assert "railway redeploy" not in WORKFLOW
    assert "vercel deploy" not in WORKFLOW
    assert "uses: actions/checkout@" in WORKFLOW
    assert "pytest -q backend/tests/test_live_e2e.py" in WORKFLOW
