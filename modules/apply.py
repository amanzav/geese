"""
Application Module for WaterlooWorks
Automates applying to jobs from the Geese (shortlist) section with rules:
- Skip jobs requiring extra documents beyond resume/cover letter
- Continue application on WaterlooWorks even if external apply is required, and report these at the end
- Handle pre-screening by waiting for user to click Next; resume automation afterwards
- Programmatically click the final Submit using provided selector
"""

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

from .utils import TIMEOUT, PAGE_LOAD


class WaterlooWorksApplicator:
    """Automate job applications on WaterlooWorks from the Geese jobs list."""

    def __init__(self, driver, cover_letters_folder="cover_letters", waterlooworks_folder="geese"):
        """
        Initialize applicator
        
        Args:
            driver: Selenium WebDriver instance
            cover_letters_folder: Folder containing cover letters (default: "cover_letters")
            waterlooworks_folder: WaterlooWorks folder name (default: "geese")
        """
        self.driver = driver
        self.cover_letters_folder = cover_letters_folder
        self.waterlooworks_folder = waterlooworks_folder
        
        # Initialize Gemini for smart document detection
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.llm = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.llm = None
            print("⚠️  Warning: GEMINI_API_KEY not found. Using regex fallback for document detection.")

    # ---------- Navigation helpers (borrowed pattern from cover_letter_generator) ----------
    def navigate_to_geese_jobs(self) -> bool:
        """Navigate to the specified WaterlooWorks folder (e.g., Geese Jobs, good shit, etc.)."""
        try:
            print(f"\n📁 Navigating to '{self.waterlooworks_folder}' folder...")
            self.driver.get(
                "https://waterlooworks.uwaterloo.ca/myAccount/co-op/full/jobs.htm"
            )
            time.sleep(PAGE_LOAD)

            stat_cards = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_all_elements_located(
                    (
                        By.CSS_SELECTOR,
                        ".simple--stat-card.border-radius--16.display--flex.flex--column.dist--between",
                    )
                )
            )

            target_card = None
            for card in stat_cards:
                if self.waterlooworks_folder.lower() in card.text.lower():
                    target_card = card
                    break

            if not target_card:
                print(f"   ✗ Could not find '{self.waterlooworks_folder}' folder")
                print(f"   Available folders:")
                for card in stat_cards:
                    folder_name = card.text.split('\n')[0] if '\n' in card.text else card.text
                    print(f"      - {folder_name}")
                return False

            link = target_card.find_element(By.TAG_NAME, "a")
            link.click()
            time.sleep(PAGE_LOAD)
            print(f"   ✓ '{self.waterlooworks_folder}' folder opened")
            return True
        except Exception as e:
            print(f"   ✗ Error navigating to '{self.waterlooworks_folder}' folder: {e}")
            return False

    def get_pagination_pages(self) -> int:
        """Get number of pages in the Geese jobs list."""
        try:
            pagination = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
            )
            page_buttons = len(pagination.find_elements(By.TAG_NAME, "li")) - 4
            return max(page_buttons, 1)
        except Exception:
            return 1

    def next_page(self):
        pagination = WebDriverWait(self.driver, TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagination"))
        )
        next_button = pagination.find_elements(By.TAG_NAME, "li")[-2]
        next_button.find_element(By.TAG_NAME, "a").click()
        time.sleep(PAGE_LOAD)

    def get_geese_jobs_from_page(self) -> List[Dict]:
        """Return basic job rows from current Geese page."""
        jobs: List[Dict] = []
        try:
            time.sleep(PAGE_LOAD)
            job_rows = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.table tbody tr"))
            )
            for idx, row in enumerate(job_rows, 1):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 4:
                        continue
                    job_title_elem = cells[0].find_element(By.TAG_NAME, "a")
                    job_title = job_title_elem.text.strip()
                    job_id = job_title_elem.get_attribute("href").split("=")[-1]
                    company = cells[1].text.strip()
                    jobs.append(
                        {
                            "job_id": job_id,
                            "job_title": job_title,
                            "company": company,
                            "title_element": job_title_elem,
                            "row_element": row,
                            "row_index": idx,
                        }
                    )
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
        Use Gemini LLM to intelligently detect if job requires extra documents beyond resume/cover letter.
        Falls back to regex if LLM is unavailable.
        """
        if not additional_info or additional_info == "N/A":
            return (False, None)
        
        # Use LLM if available
        if self.llm:
            try:
                prompt = f"""Analyze this job's additional information and determine if it requires documents OTHER than a resume or cover letter.

Additional Information:
{additional_info}

Documents we CAN provide (DO NOT flag these):
- Resume/CV
- Cover letter
- Transcripts (official or unofficial)


Documents we CANNOT provide (FLAG these):
- Portfolios, GitHub links, Behance, Dribbble
- Writing samples, code samples, work samples
- References, reference letters
- Security clearance, police checks, background checks
- Certificates, certifications
- Any other documents beyond resume/cover letter

Respond with ONLY one of these:
- "SKIP: [reason]" if extra documents are required (e.g., "SKIP: transcript required")
- "OK" if only resume/cover letter are needed (or no specific documents mentioned)

Be strict: if there's any mention of documents we can't provide, flag it."""

                response = self.llm.generate_content(prompt)
                result = response.text.strip()
                
                if result.startswith("SKIP:"):
                    reason = result.replace("SKIP:", "").strip()
                    return (True, reason)
                else:
                    return (False, None)
            except Exception as e:
                print(f"      ⚠️  LLM detection failed ({e}), using regex fallback")
                # Fall through to regex fallback
        
        # Regex fallback
        text = additional_info.lower()
        for pat in self.EXTRA_DOC_KEYWORDS:
            if re.search(pat, text):
                return (True, pat)
        return (False, None)

    def detect_external_required(self, additional_info: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Use Gemini LLM to detect if external application is required.
        Falls back to regex if LLM is unavailable.
        """
        if not additional_info or additional_info == "N/A":
            return (False, None)
        
        # Use LLM if available
        if self.llm:
            try:
                prompt = f"""Analyze this job's additional information and determine if it requires applying externally (not through WaterlooWorks).

Additional Information:
{additional_info}

Look for indicators like:
- "Apply directly on company website"
- "Apply externally" 
- Links to external job portals (Greenhouse, Lever, Workday, Taleo, etc.)
- "Use this link to apply"
- "Employer will contact you directly"

Respond with ONLY one of these:
- "EXTERNAL: [url or hint]" if external application is required (e.g., "EXTERNAL: https://company.com/jobs" or "EXTERNAL: apply on company portal")
- "OK" if no external application is required

Be strict: if there's any clear indication of needing to apply elsewhere, flag it."""

                response = self.llm.generate_content(prompt)
                result = response.text.strip()
                
                if result.startswith("EXTERNAL:"):
                    hint = result.replace("EXTERNAL:", "").strip()
                    return (True, hint)
                else:
                    return (False, None)
            except Exception as e:
                print(f"      ⚠️  LLM detection failed ({e}), using regex fallback")
                # Fall through to regex fallback
        
        # Regex fallback
        text = additional_info.lower()
        url_match = re.search(r"https?://\S+", additional_info)
        for pat in self.EXTERNAL_APPLY_PATTERNS:
            if re.search(pat, text):
                return (True, url_match.group(0) if url_match else pat)
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
                """Build expected cover letter document name matching the generator's sanitization.

                Example: "Zomp Inc" + "Software Developer" -> "Zomp_Inc_Software_Developer"
                
                IMPORTANT: Must match the sanitization logic in cover_letter_generator.py
                to ensure we can find the generated cover letters.
                """
                def sanitize(text):
                    # Remove or replace Windows-invalid and problematic characters
                    text = text.replace('/', '_')
                    text = text.replace('\\', '_')
                    text = text.replace(':', '_')
                    text = text.replace('*', '_')
                    text = text.replace('?', '_')
                    text = text.replace('"', '')
                    text = text.replace('<', '')
                    text = text.replace('>', '')
                    text = text.replace('|', '_')
                    text = text.replace('(', '')
                    text = text.replace(')', '')
                    text = text.replace('[', '')
                    text = text.replace(']', '')
                    text = text.replace('{', '')
                    text = text.replace('}', '')
                    # Remove any other non-alphanumeric except spaces, hyphens, underscores
                    text = re.sub(r'[^\w\s-]', '', text)
                    # Replace multiple spaces with single space
                    text = re.sub(r'\s+', ' ', text)
                    # Replace spaces with underscores
                    text = text.strip().replace(' ', '_')
                    # Remove multiple underscores
                    text = re.sub(r'_+', '_', text)
                    return text.strip('_')
                
                company_clean = sanitize(company)
                title_clean = sanitize(job_title)
                return f"{company_clean}_{title_clean}"

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
                pkg_name_val = f"{self._sanitize_name(organization)} {self._sanitize_name(job_title)} Package"
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

    def close_job_details_panel(self):
        try:
            close_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, "[class='btn__default--text btn--default protip']"
            )
            if close_buttons:
                close_buttons[-1].click()
                time.sleep(1)
                return True
            return False
        except Exception:
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

        num_pages = self.get_pagination_pages()
        total_applied = 0

        # Build a quick lookup by id for cached jobs
        by_id = {str(j.get("id")): j for j in (cached_jobs or [])}

        for page in range(1, num_pages + 1):
            jobs = self.get_geese_jobs_from_page()
            if not jobs:
                if page < num_pages:
                    self.next_page()
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
                self.next_page()

        return stats
