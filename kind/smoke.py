"""Browser check of Healthcheck Console's page: BASE=https://localhost:8443 python3 kind/smoke.py

Drives the page in headless Chrome with real clicks: starts an assessment and lands on the
application's assessment page in MTA, filters the respondents, and works the delete-all dialog.
E2E_CLEAR=1 confirms delete-all, which removes every respondent in the environment; without it
the check removes only the respondent it created.
"""

import os
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as expected
from selenium.webdriver.support.ui import WebDriverWait

BASE = os.environ.get("BASE", "https://localhost:8443")
ORGANISATION = "Smoke Test Ltd"


class Page(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--window-size=1512,900")
        # GitHub's runners name the directory of the chromedriver that matches their Chrome.
        driver = os.environ.get("CHROMEWEBDRIVER")
        service = Service(os.path.join(driver, "chromedriver")) if driver else Service()
        cls.browser = webdriver.Chrome(options=options, service=service)
        cls.wait = WebDriverWait(cls.browser, 60)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()

    def find(self, selector):
        return self.wait.until(expected.element_to_be_clickable((By.CSS_SELECTOR, selector)))

    def open_maintenance(self):
        self.browser.get(f"{BASE}/console/")
        tab = self.wait.until(
            expected.element_to_be_clickable((By.XPATH, "//button[@role='tab'][normalize-space()='Maintenance']"))
        )
        tab.click()
        self.wait.until(expected.visibility_of_element_located((By.ID, "respondent-page")))
        self.wait.until(lambda b: b.find_element(By.ID, "respondent-count").text)

    def rows(self):
        return self.browser.find_elements(By.CSS_SELECTOR, "#respondents tr")

    def test_1_start_opens_the_application_s_assessment_page(self):
        self.browser.get(f"{BASE}/console/")
        self.find("#organisation").send_keys(ORGANISATION)
        self.find("#email").send_keys("smoke@example.com")
        self.find("#start button").click()
        self.wait.until(expected.url_contains("/applications/assessment-actions/"))
        # The questionnaire's button: an assessment exists already, with the contact as its stakeholder.
        self.wait.until(expected.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Retake']")))

    def test_2_respondents_are_listed_and_filtered(self):
        self.open_maintenance()
        self.wait.until(lambda b: any(ORGANISATION in row.text for row in self.rows()))
        filter_box = self.find("#respondent-filter")
        filter_box.send_keys("smoke test")
        self.wait.until(lambda b: len(self.rows()) == 1)
        self.assertIn(ORGANISATION, self.rows()[0].text)
        self.assertEqual(self.browser.find_element(By.ID, "respondent-page").text, "1 to 1 of 1")
        filter_box.clear()
        filter_box.send_keys("no such organisation")
        self.wait.until(lambda b: not self.rows())
        self.assertEqual(self.browser.find_element(By.ID, "respondent-page").text, "No respondents match")

    def test_3_delete_all_dialog_answers_the_mouse(self):
        self.open_maintenance()
        dialog = self.browser.find_element(By.ID, "delete-all-modal")
        self.find("#delete-all").click()
        self.wait.until(lambda b: dialog.get_attribute("open"))
        self.find("#delete-all-cancel").click()
        self.wait.until(lambda b: not dialog.get_attribute("open"))
        if os.environ.get("E2E_CLEAR") == "1":
            self.find("#delete-all").click()
            self.find("#delete-all-confirm").click()
            self.wait.until(lambda b: "Deleted" in b.find_element(By.ID, "maintenance-status").text)
            self.wait.until(lambda b: not self.rows())
            self.assertEqual(self.browser.find_element(By.ID, "respondent-page").text, "No respondents")
        else:
            remove = next(r for r in self.rows() if ORGANISATION in r.text).find_element(By.CSS_SELECTOR, "button")
            remove.click()
            self.assertEqual(remove.text, "Confirm delete")
            remove.click()
            self.wait.until(lambda b: not any(ORGANISATION in r.text for r in self.rows()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
