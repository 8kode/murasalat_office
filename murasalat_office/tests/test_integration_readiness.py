from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_placeholder_doctype_integration_test_remains():
    path = ROOT / "murasalat_office/doctype/murasalat_user_organization_membership/test_murasalat_user_organization_membership.py"
    assert not path.exists()


def test_inbox_resolves_delegation_scope_without_implicit_cross_doctype_join():
    source = (ROOT / "murasalat_office/report/murasalat_inbox/murasalat_inbox.py").read_text()
    assert "correspondence.originating_organization" not in source
    assert "enrich_with_correspondence" in source
    assert '["correspondence", "in", scoped_names]' in source
