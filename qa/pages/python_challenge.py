"""Page object for the graded Python challenge at the end of each course."""

from playwright.sync_api import Locator, Page, expect

# Pyodide is fetched and compiled on the first run, which is slow on a cold runner.
PYTHON_LOAD_TIMEOUT_MS = 90_000


class PythonChallenge:
    def __init__(self, page: Page, course_path: str) -> None:
        self.page = page
        self.course_path = course_path
        heading = page.get_by_role("heading", name="Desafio avaliado")
        self.section: Locator = page.locator("div").filter(has=heading).last
        self.editor = self.section.locator("textarea")
        self.run_button = self.section.get_by_role("button")
        self.summary = self.section.get_by_text("testes passaram.")
        # The function spec is also a list; only result lines say how many failed.
        self.hints = self.section.locator("li").filter(has_text="falharam")
        self.passed_badge = self.section.get_by_text("Já passaste neste desafio.")

    def open(self) -> "PythonChallenge":
        self.page.goto(self.course_path)
        self.editor.scroll_into_view_if_needed()
        expect(self.editor).to_be_editable()
        return self

    def submit(self, code: str) -> None:
        self.editor.fill(code)
        self.run_button.click()

    def wait_for_summary(self) -> str:
        expect(self.summary).to_be_visible(timeout=PYTHON_LOAD_TIMEOUT_MS)
        return self.summary.inner_text()

    def error_message(self, text: str) -> Locator:
        return self.section.get_by_text(text)

    def hint_for(self, function_name: str) -> str:
        return self.hints.filter(has_text=function_name).inner_text()
