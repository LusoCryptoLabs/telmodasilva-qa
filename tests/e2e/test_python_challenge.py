"""The graded Python challenge of course 1, driven like a learner would.

The code runs in the learner's browser (Pyodide in a web worker) against 18 hidden tests.
These tests check the grading and the feedback it gives, without publishing an answer:
the passing solution comes from the CHALLENGE_SOLUTION environment variable (a CI secret).
"""

import os
from typing import Any

import pytest
from playwright.sync_api import Page, expect

from qa.pages.python_challenge import PYTHON_LOAD_TIMEOUT_MS, PythonChallenge

pytestmark = pytest.mark.e2e

COURSE = "/biblioteca/fundamentos-de-automacao-com-python"
FUNCTIONS = ("validar_telefone", "validar_versao", "validar_username")


def always(value: bool) -> str:
    return "\n\n".join(f"def {name}(valor):\n    return {value}" for name in FUNCTIONS)


@pytest.fixture
def challenge(page: Page) -> PythonChallenge:
    return PythonChallenge(page, COURSE).open()


def test_starter_code_fails_with_a_missing_return_hint(challenge: PythonChallenge) -> None:
    challenge.submit(challenge.editor.input_value())
    assert challenge.wait_for_summary() == "0 de 18 testes passaram."
    for name in FUNCTIONS:
        assert "não devolveu nada (falta um return?)" in challenge.hint_for(name)


def test_accepting_everything_is_reported_as_false_positives(challenge: PythonChallenge) -> None:
    challenge.submit(always(True))
    assert challenge.wait_for_summary() == "7 de 18 testes passaram."
    assert "4 aceitou um valor que devia rejeitar" in challenge.hint_for("validar_telefone")
    assert "4 aceitou um valor que devia rejeitar" in challenge.hint_for("validar_versao")
    assert "3 aceitou um valor que devia rejeitar" in challenge.hint_for("validar_username")


def test_rejecting_everything_is_reported_as_false_negatives(challenge: PythonChallenge) -> None:
    challenge.submit(always(False))
    assert challenge.wait_for_summary() == "11 de 18 testes passaram."
    assert "2 rejeitou um valor que devia aceitar" in challenge.hint_for("validar_telefone")
    assert "2 rejeitou um valor que devia aceitar" in challenge.hint_for("validar_versao")
    assert "3 rejeitou um valor que devia aceitar" in challenge.hint_for("validar_username")


def test_syntax_error_is_shown_to_the_learner(challenge: PythonChallenge) -> None:
    challenge.submit("def validar_telefone(valor)\n    return True")
    expect(challenge.error_message("Erro no teu código: SyntaxError")).to_be_visible(
        timeout=PYTHON_LOAD_TIMEOUT_MS
    )


def test_infinite_loop_is_stopped_after_five_seconds(challenge: PythonChallenge) -> None:
    challenge.submit("while True:\n    pass")
    expect(challenge.error_message("Demorou mais de 5 segundos")).to_be_visible(
        timeout=PYTHON_LOAD_TIMEOUT_MS
    )
    expect(challenge.run_button).to_be_enabled()


@pytest.mark.skipif(not os.environ.get("CHALLENGE_SOLUTION"), reason="CHALLENGE_SOLUTION not set")
def test_correct_solution_passes_and_is_remembered(
    challenge: PythonChallenge, page: Page, analytics_events: list[dict[str, Any]]
) -> None:
    challenge.submit(os.environ["CHALLENGE_SOLUTION"])
    assert challenge.wait_for_summary() == "18 de 18 testes passaram."
    expect(challenge.passed_badge).to_be_visible()
    assert {"path": COURSE, "ev": "desafio"}.items() <= next(
        (e for e in analytics_events if e.get("ev") == "desafio"), {}
    ).items(), "the pass was not recorded as a course milestone"

    page.reload()
    challenge.editor.scroll_into_view_if_needed()
    expect(challenge.passed_badge).to_be_visible()
