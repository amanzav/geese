"""Application Module - Automates applying to jobs from the Geese section"""

from __future__ import annotations

import re
import time
from typing import Dict, List, Optional, Tuple
import os
import google.generativeai as genai
import winsound

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

from .utils import (
    TIMEOUT, PAGE_LOAD, SELECTORS,
    navigate_to_folder, get_pagination_pages, go_to_next_page,
    close_job_details_panel, get_jobs_from_page, sanitize_filename
)
from .database import get_db
from .config import load_app_config


class WaterlooWorksApplicator:
    """Automate job applications on WaterlooWorks from the Geese jobs list."""

    def __init__(self, driver, cover_letters_folder="cover_letters", waterlooworks_folder="geese", use_database=True):
        """
        Initialize applicator
        
        Args:
            driver: Selenium WebDriver instance
            cover_letters_folder: Folder containing cover letters (default: "cover_letters")
            waterlooworks_folder: WaterlooWorks folder name (default: "geese")
            use_database: Whether to track applications in database (default: True)
        """
        self.driver = driver
        self.cover_letters_folder = cover_letters_folder
        self.waterlooworks_folder = waterlooworks_folder
        self.use_database = use_database
        
        # Load config for LLM model names
        self.config = load_app_config()
        
        # Initialize agent factory for document classification
        from .agents import AgentFactory
        
        agent_config = {
            "document_classifier_agent": {
                "provider": self.config.agents.document_classifier_agent.get("provider", "groq"),
                "model": self.config.agents.document_classifier_agent.get("model", "llama-3.1-8b-instant")
            }
        }
        
        self.agent_factory = AgentFactory(
            config=agent_config,
            enable_tracking=self.config.agents.enable_token_tracking
        )
        
        self.classifier_agent = self.agent_factory.get_document_classifier_agent()
        print(f"✅ Document classifier initialized with {self.classifier_agent.provider}/{self.classifier_agent.model}")

    def track_application(self, job_id: str, status: str = "submitted", cover_letter_path: Optional[str] = None):
        """Track application in database
        
        Args:
            job_id: WaterlooWorks job ID
            status: Application status (e.g., "submitted", "draft", "failed")
            cover_letter_path: Optional path to cover letter file
        """
        if not self.use_database:
            return
        
        try:
            db = get_db()
            
            # Track cover letter if provided
            letter_id = None
            if cover_letter_path and os.path.exists(cover_letter_path):
                # Insert cover letter record
                with open(cover_letter_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                letter_id = db.insert_cover_letter(job_id, content, file_path=cover_letter_path)
                if status == "submitted":
                    db.mark_cover_letter_uploaded(letter_id)
            
            # Note: Applications table would be inserted here if we had the structure
            # For now, we're just tracking cover letters
            
        except Exception as e:
            print(f"   ⚠️  Warning: Could not track application in database: {e}")

    # ---------- Navigation helpers (borrowed pattern from cover_letter_generator) ----------
    def navigate_to_geese_jobs(self) -> bool:
        """Navigate to the specified WaterlooWorks folder"""
        print(f"\n📁 Navigating to '{self.waterlooworks_folder}' folder...")
        success = navigate_to_folder(self.driver, self.waterlooworks_folder)
        if success:
            print(f"   ✓ '{self.waterlooworks_folder}' folder opened")
        return success

    def get_geese_jobs_from_page(self) -> List[Dict]:
        """Return basic job rows from current Geese page"""
        jobs: List[Dict] = []
        try:
            job_rows = get_jobs_from_page(self.driver)
            for idx, row in enumerate(job_rows, 1):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 4:
                        continue
                    job_title_elem = cells[0].find_element(By.TAG_NAME, "a")
                    job_title = job_title_elem.text.strip()
                    job_id = job_title_elem.get_attribute("href").split("=")[-1]
                    company = cells[1].text.strip()
                    jobs.append({
                        "job_id": job_id,
                        "job_title": job_title,
                        "company": company,
                        "title_element": job_title_elem,
                        "row_element": row,
                        "row_index": idx,
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"   ✗ Error reading jobs on page: {e}")
        return jobs

    # ---------- Heuristics for job rules ----------
    EXTRA_DOC_KEYWORDS = [
        # things we cannot auto-attach today beyond resume/cover letter
        r"transcript",
        r"portfolio|github|behance|dribbble",
        r"writing sample|code sample|work sample|samples",
        r"references|reference letters|referees",
        r"security clearance|police check|background check",
        r"unofficial|official transcripts?",
        r"certificates|certification",
    ]

    EXTERNAL_APPLY_PATTERNS = [
        r"apply (directly|externally)",
        r"apply (on|via|through) (the )?(company|employer|website|site|portal)",
        r"(greenhouse|lever\.co|workday|myworkdayjobs|taleo|smartrecruiters|bamboohr|jobs\.)",
        r"use this link to apply|interested applicants must apply",
        r"employer will be contacting you directly",
        r"apply at http",
    ]

    def detect_additional_docs(self, additional_info: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Use DocumentClassifierAgent to detect if job requires extra documents beyond resume/cover letter.
        """
        if not additional_info or additional_info == "N/A":
            return (False, None)
        
        try:
            # Use agent's detection method
            requires, reason = self.classifier_agent.detect_additional_documents(additional_info)
            return (requires, reason)
        except Exception as e:
            print(f"      ⚠️  Agent detection failed ({e}), using regex fallback")
            # Regex fallback
            text = additional_info.lower()
            for pat in self.EXTRA_DOC_KEYWORDS:
                if re.search(pat, text):
                    return (True, pat)
            return (False, None)

    def detect_external_required(self, additional_info: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Use DocumentClassifierAgent to detect if external application is required.
        """
        if not additional_info or additional_info == "N/A":
            return (False, None)
        
        try:
            # Use agent's detection method
            requires, url = self.classifier_agent.detect_external_application(additional_info)
            return (requires, url)
        except Exception as e:
            print(f"      ⚠️  Agent detection failed ({e}), using regex fallback")
            # Regex fallback
            text = additional_info.lower()
            url_match = re.search(r"https?://\S+", additional_info)
            for pat in self.EXTERNAL_APPLY_PATTERNS:
                if re.search(pat, text):
                    return (True, url_match.group(0) if url_match else None)
            return (False, None)

    # ---------- Application flow ----------
    def open_job_details(self, title_element) -> bool:
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", title_element)
            time.sleep(0.2)
            self.driver.execute_script("window.scrollBy(0, -100);")
            time.sleep(0.2)
            title_element.click()
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "is--long-form-reading"))
            )
            time.sleep(0.5)
            return True
        except Exception as e:
            print(f"      ✗ Could not open job details: {e}")
            return False

    def start_application(self) -> bool:
        """Click the Apply button from the floating action bar in the job details panel."""
        try:
            buttons = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, ".floating--action-bar.color--bg--default button")
                )
            )
            if not buttons:
                print("      ✗ No floating action buttons found")
                return False
            # Heuristic: Apply is usually the first button
            self.driver.execute_script("arguments[0].click();", buttons[0])
            time.sleep(PAGE_LOAD)
            return True
        except Exception as e:
            print(f"      ✗ Error clicking Apply: {e}")
            return False

    def click_row_apply(self, row_element) -> Dict[str, Optional[str]]:
        """Click the Apply button directly from the job table row.

        Returns a dict:
          {
            'clicked': bool,
            'switched': bool,
            'new_handle': Optional[str],
            'prev_handle': Optional[str]
          }
        If a new tab/window opens, switches to it and records the handle.
        """
        context = {
            "clicked": False,
            "switched": False,
            "new_handle": None,
            "prev_handle": None,
        }
        try:
            # Ensure row in view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row_element)
            time.sleep(0.2)

            # Track window handles in case click opens a new tab/window
            handles_before = set(self.driver.window_handles)
            prev_handle = self.driver.current_window_handle
            context["prev_handle"] = prev_handle

            apply_button = WebDriverWait(row_element, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[aria-label='Apply']"))
            )
            self.driver.execute_script("arguments[0].click();", apply_button)
            context["clicked"] = True

            # Wait briefly for a new handle to appear
            deadline = time.time() + 5
            while time.time() < deadline:
                handles_after = set(self.driver.window_handles)
                new_handles = list(handles_after - handles_before)
                if new_handles:
                    new_handle = new_handles[-1]
                    self.driver.switch_to.window(new_handle)
                    context["switched"] = True
                    context["new_handle"] = new_handle
                    time.sleep(PAGE_LOAD)
                    break
                time.sleep(0.2)

            # If no new window opened, we remain in-place (same tab or modal)
            return context
        except Exception:
            print("      ℹ️  Already applied (no row-level Apply button)")
            return context

    def wait_for_prescreen_and_wizard(self, timeout_seconds: int = 600, skip_prescreening: bool = False) -> dict:
        """
        The apply form (#applyForm) is always present; content changes by step.
        We wait until the form is past the 'Pre-Screening Questions' step and shows
        'Application Options' (or an equivalent documents/package/Submit state) that we can automate.
        
        Returns:
            dict with 'success' (bool) and 'has_prescreen' (bool) keys
        """
        try:
            WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "applyForm"))
            )
        except Exception:
            print("      ✗ Apply form not found")
            return {"success": False, "has_prescreen": False}

        # Check if there are pre-screening questions
        try:
            form = self.driver.find_element(By.CSS_SELECTOR, "#applyForm")
            form_text = (form.text or "").lower()
            
            if "pre-screening questions" in form_text:
                if skip_prescreening:
                    print("      ⏭️  Pre-screening questions detected - skipping job")
                    return {"success": False, "has_prescreen": True}
                else:
                    print("      ⏱ Waiting for you to complete pre-screening... (will auto-resume)")
                    # Play notification sound to alert user
                    try:
                        # Play system beep (frequency=1000Hz, duration=500ms)
                        winsound.Beep(1000, 500)
                    except Exception:
                        pass  # Silently fail if sound doesn't work
        except Exception:
            pass

        start = time.time()
        while time.time() - start < timeout_seconds:
            try:
                form = self.driver.find_element(By.CSS_SELECTOR, "#applyForm")
                form_text = (form.text or "").lower()

                # If we see 'application options' or a Submit button, we're ready
                if "application options" in form_text:
                    return {"success": True, "has_prescreen": False}

                # Presence of a Submit button (by text) also indicates we're past pre-screen
                submit_buttons = [
                    b for b in form.find_elements(By.TAG_NAME, "button")
                    if (b.text or "").strip().lower() == "submit"
                ]
                if submit_buttons:
                    return {"success": True, "has_prescreen": False}

                # Otherwise, if we're on pre-screening step (detected by text), keep waiting
                if "pre-screening questions" in form_text:
                    if skip_prescreening:
                        print("      ⏭️  Pre-screening questions detected - skipping job")
                        return {"success": False, "has_prescreen": True}
                    # Still waiting for pre-screen completion
                    time.sleep(0.5)
                    continue

                # Fallback: detect doc/package-related selects/inputs
                selects = form.find_elements(By.TAG_NAME, "select")
                inputs = form.find_elements(By.TAG_NAME, "input")
                doc_related = [
                    el for el in selects + inputs
                    if any(
                        key in (el.get_attribute("id") or "").lower()
                        or key in (el.get_attribute("name") or "").lower()
                        for key in ["package", "resume", "cover"]
                    )
                ]
                if doc_related:
                    return {"success": True, "has_prescreen": False}
            except Exception:
                pass
            time.sleep(0.5)
        print("      ✗ Timed out waiting for pre-screening to complete")
        return {"success": False, "has_prescreen": False}

    def _sanitize_name(self, text: str) -> str:
        return re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")

    def _cover_letter_name(self, company: str, job_title: str) -> str:
        """Build expected cover letter document name matching the generator's sanitization"""
        company_clean = sanitize_filename(company)
        title_clean = sanitize_filename(job_title)
        return f"{company_clean}_{title_clean}"
    
    def _get_cover_letter_path(self, company: str, job_title: str) -> Optional[str]:
        """Get the full path to the cover letter PDF file"""
        cover_letter_name = self._cover_letter_name(company, job_title)
        pdf_path = os.path.join(self.cover_letters_folder, f"{cover_letter_name}.pdf")
        
        if os.path.exists(pdf_path):
            return pdf_path
        return None

    def fill_package_and_submit(
        self, organization: str, job_title: str, attempt_select_docs: bool = True
    ) -> bool:
        """Create a custom application package, pick resume, select existing cover letter, then submit.

        Notes:
          - Avoids 'Default Application Package' so cover letter can be attached.
          - Uses APPLICANT_NAME env var if provided to format package name, e.g., 'Aman Zaveri - {job_title}'.
        """
        try:
            form = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#applyForm"))
            )

            # 1) Choose 'Create Custom Application Package'
            try:
                radios = form.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                found_custom = False
                for r in radios:
                    try:
                        parent = r.find_element(By.XPATH, "..")
                        txt = (parent.get_attribute("innerText") or "").strip().lower()
                    except Exception:
                        txt = (r.get_attribute("value") or "").strip().lower()
                    if "create custom application package" in txt:
                        self.driver.execute_script("arguments[0].click();", r)
                        found_custom = True
                        break
                # If label is not directly on parent, try label elements
                if not found_custom:
                    labels = form.find_elements(By.TAG_NAME, "label")
                    for lab in labels:
                        if "create custom application package" in (lab.text or "").strip().lower():
                            self.driver.execute_script("arguments[0].click();", lab)
                            found_custom = True
                            break
            except Exception:
                pass

            time.sleep(0.5)

            # 2) Set Package Name (prefer #packageName if present)
            applicant = os.getenv("APPLICANT_NAME", "").strip()
            if applicant:
                pkg_name_val = f"{applicant} - {job_title}"
            else:
                pkg_name_val = f"{sanitize_filename(organization)} {sanitize_filename(job_title)} Package"
            try:
                pkg_input = None
                try:
                    pkg_input = form.find_element(By.ID, "packageName")
                except Exception:
                    pass
                if not pkg_input:
                    candidates = [
                        el for el in form.find_elements(By.TAG_NAME, "input")
                        if any(
                            key in (el.get_attribute("id") or "").lower()
                            or key in (el.get_attribute("name") or "").lower()
                            for key in ["package", "applicationpack", "packagename"]
                        ) and (el.get_attribute("type") or "text").lower() in ["text", ""]
                    ]
                    if candidates:
                        pkg_input = candidates[0]
                if pkg_input:
                    try:
                        pkg_input.clear()
                    except Exception:
                        pass
                    pkg_input.send_keys(pkg_name_val)
            except Exception:
                pass

            # 3) Choose Resume radio: exact match '<APPLICANT_NAME> Resume'
            try:
                resume_clicked = False
                radios = form.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                desired_resume = f"{applicant} Resume".strip().lower() if applicant else None
                # First pass: exact match
                if desired_resume:
                    for r in radios:
                        try:
                            parent = r.find_element(By.XPATH, "..")
                            txt = (parent.get_attribute("innerText") or "").strip().lower()
                        except Exception:
                            txt = (r.get_attribute("value") or "").strip().lower()
                        if txt == desired_resume:
                            self.driver.execute_script("arguments[0].click();", r)
                            resume_clicked = True
                            break
                # Fallback: any radio containing 'resume'
                if not resume_clicked:
                    for r in radios:
                        try:
                            parent = r.find_element(By.XPATH, "..")
                            txt = (parent.get_attribute("innerText") or "").strip().lower()
                        except Exception:
                            txt = (r.get_attribute("value") or "").strip().lower()
                        if "resume" in txt:
                            self.driver.execute_script("arguments[0].click();", r)
                            resume_clicked = True
                            break
            except Exception:
                pass

            # 4) Click 'Select Existing Cover Letter' button
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                if "Select Existing Cover Letter" in button.get_attribute("innerText"):
                    button.click()
                    print("      ✓ Clicked Select Existing Cover Letter")
                    break
            
            # 5) Choose cover letter from modal dropdown
            try:
                cover_letter_select = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, "select"))
                )[-1]
                
                time.sleep(0.5)
                
                cover_letter_name = f"{organization.replace(' ', '_')}_{job_title.replace(' ', '_')}"
                print(f"      ⏳ Selecting cover letter: {cover_letter_name}")
                Select(cover_letter_select).select_by_visible_text(cover_letter_name)
                
                # 6) Click modal 'Select' button to confirm
                modal_buttons = self.driver.find_elements(By.CLASS_NAME, "modal__inner")[-1].find_elements(By.TAG_NAME, "button")
                for button in modal_buttons:
                    if "Select" in button.get_attribute("innerText"):
                        button.click()
                        print("      ✓ Clicked modal Select button")
                        break

                # 7) Click Submit button
                time.sleep(1)
                submit_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in submit_buttons:
                    if "Submit" in button.get_attribute("innerText"):
                        button.click()
                        print("      ✓ Clicked Submit button")
                        break

                return True
            except Exception as e:
                print(f"      ⚠️  Cover letter not found: {cover_letter_name}")
                print(f"      ⏭️  Skipping - you'll need to apply manually")
                return False
        except Exception as e:
            print(f"      ✗ Error during package/doc step: {e}")
            return False

    # ---------- Public entrypoint ----------
    def apply_to_geese_jobs(
        self,
        cached_jobs: List[Dict],
        max_applications: int = 10,
        skip_prescreening: bool = False,
    ) -> Dict:
        """
        Apply to jobs in the Geese list, up to a maximum number.

        Args:
            cached_jobs: Full scraped jobs list to cross-reference metadata like additional_info
            max_applications: Max number of applications to submit this session
            skip_prescreening: If True, skip jobs that have pre-screening questions

        Returns:
            Stats dictionary with lists of outcomes
        """
        stats = {
            "attempted": 0,
            "applied": 0,
            "skipped_extra_docs": [],  # (job_id, company, title, reason)
            "skipped_prescreening": [],  # (job_id, company, title)
            "missing_cover_letter": [],  # (job_id, company, title)
            "external_required": [],  # (job_id, company, title, hint)
            "failed": [],  # (job_id, company, title, reason)
        }

        if not self.navigate_to_geese_jobs():
            return stats

        num_pages = get_pagination_pages(self.driver)
        total_applied = 0

        # Build a quick lookup by id for cached jobs
        by_id = {str(j.get("id")): j for j in (cached_jobs or [])}

        for page in range(1, num_pages + 1):
            jobs = self.get_geese_jobs_from_page()
            if not jobs:
                if page < num_pages:
                    go_to_next_page(self.driver)
                    continue
                break

            for job in jobs:
                if total_applied >= max_applications:
                    return stats

                job_id = str(job.get("job_id"))
                company = job.get("company", "")
                title = job.get("job_title", "")
                print(f"\n→ Applying: {title} @ {company} (ID {job_id})")

                # Cross-reference cached details
                cached = by_id.get(job_id)
                additional_info = cached.get("additional_info") if cached else None

                # Rule 1: skip if extra docs required
                skip, reason = self.detect_additional_docs(additional_info)
                # Do NOT skip for cover letter only
                if skip and not re.search(r"cover letter", (additional_info or "").lower()):
                    print("   ⏭️  Skipping (extra documents required)")
                    stats["skipped_extra_docs"].append((job_id, company, title, reason))
                    continue

                # Rule 2: track external application
                ext_flag, ext_hint = self.detect_external_required(additional_info)
                if ext_flag:
                    print("   ℹ️  Also requires external application")

                # Open details and start application
                # Preferred: click Apply directly on the row (faster, no panel)
                apply_ctx = self.click_row_apply(job["row_element"])
                if not apply_ctx.get("clicked"):
                    # Treat as already applied and skip silently
                    continue

                prescreen_result = self.wait_for_prescreen_and_wizard(skip_prescreening=skip_prescreening)
                if not prescreen_result["success"]:
                    # Close new tab if opened
                    if apply_ctx.get("switched") and apply_ctx.get("prev_handle"):
                        try:
                            time.sleep(1)
                            self.driver.close()
                            self.driver.switch_to.window(apply_ctx["prev_handle"])
                            print("      ✓ Closed tab and returned to job list")
                        except Exception:
                            pass
                    
                    if prescreen_result["has_prescreen"]:
                        stats["skipped_prescreening"].append((job_id, company, title))
                    else:
                        stats["failed"].append((job_id, company, title, "prescreen-timeout"))
                    continue

                if not self.fill_package_and_submit(company, title):
                    stats["missing_cover_letter"].append((job_id, company, title))
                    
                    # Play beep to alert user
                    print("      🔔 BEEP! Cover letter missing - complete manually")
                    try:
                        import winsound
                        winsound.Beep(1000, 500)  # 1000 Hz for 500ms
                    except Exception:
                        pass
                    
                    # Keep tab open and wait for user to manually close it
                    if apply_ctx.get("switched") and apply_ctx.get("prev_handle"):
                        print("      ⏳ Waiting for you to close the tab manually...")
                        prev_handle = apply_ctx["prev_handle"]
                        
                        # Wait until the tab is closed (user action)
                        while True:
                            try:
                                # Check if current window still exists
                                _ = self.driver.current_window_handle
                                current_handles = self.driver.window_handles
                                
                                # If we're back to single window (job list), user closed the tab
                                if len(current_handles) == 1 and current_handles[0] == prev_handle:
                                    self.driver.switch_to.window(prev_handle)
                                    print("      ✓ Tab closed, continuing...")
                                    break
                                
                                time.sleep(1)  # Check every second
                            except Exception:
                                # Window might have been closed
                                try:
                                    self.driver.switch_to.window(prev_handle)
                                    print("      ✓ Returned to job list")
                                    break
                                except Exception:
                                    break
                    continue

                total_applied += 1
                stats["attempted"] += 1
                stats["applied"] += 1
                if ext_flag:
                    stats["external_required"].append((job_id, company, title, ext_hint))
                
                # Track application in database
                cover_letter_path = self._get_cover_letter_path(company, title)
                self.track_application(job_id, status="submitted", cover_letter_path=cover_letter_path)

                # Close the tab and switch back to main window
                if apply_ctx.get("switched") and apply_ctx.get("prev_handle"):
                    try:
                        time.sleep(2)  # Wait for submission to process
                        self.driver.close()
                        self.driver.switch_to.window(apply_ctx["prev_handle"])
                        print("      ✓ Closed tab and returned to job list")
                    except Exception as e:
                        print(f"      ⚠️ Warning: could not close tab: {e}")

                if total_applied >= max_applications:
                    break

            if total_applied >= max_applications or page >= num_pages:
                break
            else:
                print(f"\n➡️  Moving to page {page + 1}...")
                go_to_next_page(self.driver)

        return stats
