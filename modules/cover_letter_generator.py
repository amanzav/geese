"""Cover Letter Generator Module"""

import os
import re
import time
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx2pdf import convert
import pythoncom
import google.generativeai as genai
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from .utils import (
    TIMEOUT, PAGE_LOAD,
    navigate_to_folder, get_pagination_pages, go_to_next_page,
    get_jobs_from_page, sanitize_filename
)


class CoverLetterGenerator:
    """Generate and manage cover letters for job applications"""

    def __init__(self, driver, resume_text, prompt_template, api_key=None, cover_letters_folder="cover_letters"):
        """
        Initialize cover letter generator
        
        Args:
            driver: Selenium WebDriver instance
            resume_text: User's resume text for context
            prompt_template: Template for LLM prompt
            api_key: Google API key for Gemini
            cover_letters_folder: Folder to save cover letters (default: "cover_letters")
        """
        self.driver = driver
        self.resume_text = resume_text
        self.prompt_template = prompt_template
        self.cover_letters_dir = Path(cover_letters_folder)
        self.cover_letters_dir.mkdir(exist_ok=True)
        
        # Configure Gemini
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash-lite")
        else:
            self.model = None
        
    def get_document_name(self, company, job_title):
        """Generate standardized document name"""
        company_clean = sanitize_filename(company)
        title_clean = sanitize_filename(job_title)
        return f"{company_clean}_{title_clean}"
    
    def cover_letter_exists(self, company, job_title):
        """
        Check if cover letter already exists
        
        Args:
            company: Company name
            job_title: Job title
            
        Returns:
            True if PDF exists, False otherwise
        """
        doc_name = self.get_document_name(company, job_title)
        pdf_path = self.cover_letters_dir / f"{doc_name}.pdf"
        return pdf_path.exists()
    
    def navigate_to_geese_jobs(self):
        """Navigate to the Geese Jobs (shortlisted) section"""
        print("\n🦢 Navigating to Geese Jobs section...")
        success = navigate_to_folder(self.driver, "geese")
        if success:
            print("   ✓ Successfully navigated to Geese Jobs")
        return success
    
    def get_pagination_pages(self):
        """Get the number of pages in the current view"""
        return get_pagination_pages(self.driver)
    
    def next_page(self):
        """Go to the next page in pagination"""
        go_to_next_page(self.driver)
    
    def get_geese_jobs_from_page(self):
        """Get all job listings from the current Geese Jobs page"""
        jobs = []
        try:
            job_rows = get_jobs_from_page(self.driver)
            print(f"   Found {len(job_rows)} job listings on this page")
            
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
                        "row_index": idx
                    })
                except Exception as e:
                    print(f"   ⚠ Error extracting job {idx}: {e}")
                    continue
            
            return jobs
        except Exception as e:
            print(f"   ✗ Error getting jobs from page: {e}")
            return []
    
    def get_job_details(self, job_basic_info, cached_jobs=None):
        """
        Get full job details from cache ONLY
        
        Args:
            job_basic_info: Dictionary with job_id, job_title, company
            cached_jobs: List of previously scraped jobs
            
        Returns:
            Dictionary with full job details or None
        """
        job_id = job_basic_info["job_id"]
        
        # ONLY use cached data - don't try to scrape
        if cached_jobs:
            for cached_job in cached_jobs:
                # Match by ID or by company+title
                if (cached_job.get("id") == job_id or 
                    cached_job.get("job_id") == job_id or
                    (cached_job.get("company") == job_basic_info["company"] and 
                     cached_job.get("title") == job_basic_info["job_title"])):
                    print(f"      ✓ Using cached data")
                    
                    # Combine all relevant fields into description
                    description_parts = []
                    
                    if cached_job.get("summary"):
                        description_parts.append(f"Job Summary:\n{cached_job['summary']}")
                    
                    if cached_job.get("responsibilities"):
                        description_parts.append(f"\nResponsibilities:\n{cached_job['responsibilities']}")
                    
                    if cached_job.get("skills"):
                        description_parts.append(f"\nRequired Skills:\n{cached_job['skills']}")
                    
                    if cached_job.get("additional_info") and cached_job["additional_info"] != "N/A":
                        description_parts.append(f"\nAdditional Info:\n{cached_job['additional_info']}")
                    
                    full_description = "\n".join(description_parts)
                    
                    return {
                        "job_id": job_id,
                        "job_title": cached_job.get("title", job_basic_info["job_title"]),
                        "company": cached_job.get("company", job_basic_info["company"]),
                        "description": full_description
                    }
        
        # Not in cache - skip this job
        print(f"      ✗ Not in cache, skipping (scraping disabled)")
        return None
    
    def generate_cover_letter_text(self, company, job_title, description):
        """
        Generate cover letter text using LLM
        
        Args:
            company: Company name
            job_title: Job title
            description: Job description
            
        Returns:
            Generated cover letter text or None
        """
        if not self.model:
            print(f"      ✗ No LLM model configured")
            return None
            
        try:
            output = ""
            
            # Keep trying until we get appropriate length (100-400 words)
            attempts = 0
            max_attempts = 3
            
            while (len(output.split()) > 400 or len(output.split()) < 100) and attempts < max_attempts:
                attempts += 1
                
                try:
                    prompt = f"""{self.prompt_template}

{self.resume_text}

Job Information:
Organization: {company}
Position: {job_title}
Job Description: {description}

CRITICAL INSTRUCTIONS - READ CAREFULLY:
Write a professional cover letter (100-400 words) that is COMPLETELY FINISHED and READY TO SUBMIT.

ABSOLUTELY NO:
- Placeholders like [Your Name], [Company Name], [Position], etc.
- Square brackets [] with anything to fill in
- Blank spaces or underscores _____ to complete
- Notes like "customize this section" or "add details here"
- Any TODO items or suggestions for edits
- Special Unicode symbols, emojis, or decorative characters
- Smart quotes/apostrophes (use straight quotes: " and ')
- Em dashes or en dashes (use regular hyphens: -)
- Bullet points with special symbols (use plain text only)
- Any symbols that might not render properly in PDF

REQUIRED:
1. Use ONLY real information from the resume provided above
2. Reference the specific company name: {company}
3. Reference the specific position: {job_title}
4. Show genuine enthusiasm for THIS specific role at THIS specific company
5. Highlight 2-3 relevant experiences or skills from the resume that match the job description
6. Explain concretely why I'm a great fit based on my actual experience
7. Keep a professional but personable tone
8. Make every sentence complete and specific - no generic statements
9. Use only standard ASCII characters and basic punctuation (periods, commas, colons, semicolons, hyphens, parentheses)
10. Write in clear paragraphs with proper spacing

The cover letter will be exported as PDF and must be 100% ready to submit without any edits.

Start with "Dear Hiring Manager," and end with "Aman Zaveri"."""

                    response = self.model.generate_content(prompt)
                    output = self._filter_text(response.text)
                    
                    if len(output.split()) >= 100:
                        break
                        
                except Exception as e:
                    print(f"      ⚠ LLM attempt {attempts} failed: {str(e)[:80]}")
                    if attempts >= max_attempts:
                        raise
                    time.sleep(2)  # Wait before retry
            
            if len(output.split()) < 100:
                print(f"      ⚠ Generated text too short ({len(output.split())} words)")
                return None
            
            return output.strip()
            
        except Exception as e:
            print(f"      ✗ Error generating cover letter: {str(e)[:100]}")
            return None
    
    def _filter_text(self, output: str) -> str:
        """
        Filter and clean the generated text
        
        Args:
            output: Raw LLM output
            
        Returns:
            Cleaned text
        """
        # Remove citation markers like [[1]]
        pattern = r"\[\[\d+\]\]"
        output = re.sub(pattern, "", output)
        
        # Extract text between markers
        start = "Dear Hiring Manager,"
        end = "Aman Zaveri"
        
        idx1 = output.find(start)
        idx2 = output.find(end)
        
        if idx1 == -1 or idx2 == -1:
            # Markers not found, return cleaned output
            return output.strip()
        
        final_output = output[idx1 + len(start) + 1 : idx2]
        final_output = bytes(final_output, "utf-8").decode("unicode_escape")
        return final_output.strip()
    
    def save_cover_letter(self, company, job_title, cover_text, template_path="template.docx"):
        """
        Save cover letter as PDF
        
        Args:
            company: Company name
            job_title: Job title
            cover_text: Generated cover letter text
            template_path: Path to Word template
            
        Returns:
            True if successful, False otherwise
        """
        doc_name = self.get_document_name(company, job_title)
        
        try:
            # Load template
            document = Document(template_path)
            
            # Add generated text
            generated_text = document.add_paragraph().add_run(
                f"""Dear Hiring Manager,
        
{cover_text}

Aman Zaveri"""
            )
            
            generated_text.font.size = Pt(11)
            generated_text.font.name = "Garamond"
            
            # Save as DOCX first
            docx_path = self.cover_letters_dir / f"{doc_name}.docx"
            document.save(str(docx_path))
            
            # Convert to PDF
            pythoncom.CoInitialize()
            convert(str(docx_path))
            pythoncom.CoUninitialize()
            
            # Remove DOCX file
            docx_path.unlink()
            
            print(f"      ✓ Saved: {doc_name}.pdf")
            return True
            
        except Exception as e:
            print(f"      ✗ Error saving cover letter: {e}")
            return False
    
    def generate_all_cover_letters(self, cached_jobs_path=None):
        """
        Main method to generate cover letters for all Geese Jobs
        
        Args:
            cached_jobs_path: Path to cached jobs JSON file (optional)
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_jobs": 0,
            "skipped_existing": 0,
            "generated": 0,
            "failed": 0
        }
        
        # Load cached jobs if available
        cached_jobs = None
        if cached_jobs_path and os.path.exists(cached_jobs_path):
            try:
                with open(cached_jobs_path, 'r', encoding='utf-8') as f:
                    cached_jobs = json.load(f)
                print(f"✓ Loaded {len(cached_jobs)} cached jobs")
            except Exception as e:
                print(f"⚠ Could not load cached jobs: {e}")
        
        # Navigate to Geese Jobs
        if not self.navigate_to_geese_jobs():
            return stats
        
        # Get number of pages
        num_pages = self.get_pagination_pages()
        print(f"\n📄 Found {num_pages} page(s) of jobs")
        
        # Collect jobs from all pages
        all_jobs = []
        for page in range(1, num_pages + 1):
            print(f"\n📊 Extracting jobs from page {page}/{num_pages}...")
            
            # Get jobs from current page
            jobs = self.get_geese_jobs_from_page()
            all_jobs.extend(jobs)
            
            print(f"   ✓ Extracted {len(jobs)} jobs from page {page}")
            
            # Go to next page if not the last one
            if page < num_pages:
                print(f"   ➡️  Going to page {page + 1}...")
                self.next_page()
        
        stats["total_jobs"] = len(all_jobs)
        
        if not all_jobs:
            print("No jobs found in Geese Jobs section")
            return stats
        
        print(f"\n🎯 Processing {len(all_jobs)} jobs total...")
        
        # Process each job
        for idx, job_basic in enumerate(all_jobs, 1):
            company = job_basic["company"]
            job_title = job_basic["job_title"]
            
            print(f"\n[{idx}/{len(all_jobs)}] {company} - {job_title}")
            
            # Check if cover letter already exists
            if self.cover_letter_exists(company, job_title):
                print(f"      ⏭ Cover letter already exists, skipping")
                stats["skipped_existing"] += 1
                continue
            
            # Get full job details
            job_details = self.get_job_details(job_basic, cached_jobs)
            
            if not job_details:
                print(f"      ⏭ Skipping (no cached data available)")
                stats["failed"] += 1
                continue
            
            # Check if we have a real description
            description = job_details.get("description", "")
            if not description or len(description) < 50:
                print(f"      ⏭ Skipping (description too short or missing)")
                stats["failed"] += 1
                continue
            
            # Generate cover letter text
            print(f"      🤖 Generating cover letter...")
            cover_text = self.generate_cover_letter_text(
                company,
                job_title,
                description
            )
            
            if not cover_text:
                stats["failed"] += 1
                continue
            
            # Save cover letter
            if self.save_cover_letter(company, job_title, cover_text):
                stats["generated"] += 1
            else:
                stats["failed"] += 1
        
        return stats


class CoverLetterUploader:
    """Upload cover letters to WaterlooWorks"""
    
    def __init__(self, driver, cover_letters_folder="cover_letters"):
        """
        Initialize uploader
        
        Args:
            driver: Selenium WebDriver instance
            cover_letters_folder: Folder containing cover letters (default: "cover_letters")
        """
        self.driver = driver
        self.cover_letters_dir = Path(cover_letters_folder)
    
    def navigate_to_upload_menu(self):
        """Navigate to document upload page"""
        try:
            print("\n📤 Navigating to upload menu...")
            
            # Go to home page
            home_button = WebDriverWait(self.driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "outerTemplateTabs_overview"))
            )
            home_button.click()
            time.sleep(2)
            
            # Open main menu
            # menu_button = WebDriverWait(self.driver, TIMEOUT).until(
            #     EC.element_to_be_clickable(
            #         (By.CSS_SELECTOR, "[aria-label='Toggle Main Menu']")
            #     )
            # )
            # menu_button.click()
            # time.sleep(1)
            
            # Click upload documents
            upload_button = WebDriverWait(self.driver, TIMEOUT).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "[data-pt-classes='tip--default']")
                )
            )
            upload_button.click()
            time.sleep(1)
            
            # Click internal upload button
            upload_buttons = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "[class='btn__default--text btn--info  display--flex align--middle']")
                )
            )
            upload_buttons[0].click()
            time.sleep(1)
            
            print("   ✓ Navigated to upload menu")
            return True
            
        except Exception as e:
            print(f"   ✗ Error navigating to upload menu: {e}")
            return False
    
    def upload_file(self, pdf_filename):
        """
        Upload a single PDF file
        
        Args:
            pdf_filename: Name of the PDF file (with extension)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract document name (without .pdf)
            doc_name = pdf_filename.replace(".pdf", "")
            
            # Write cover letter name
            name_input = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "docName"))
            )
            name_input.clear()
            name_input.send_keys(doc_name)
            
            # Select document type (66 = Cover Letter)
            select_element = self.driver.find_element(By.ID, "docType")
            select = Select(select_element)
            select.select_by_value("66")
            
            # Upload file
            file_path = str((self.cover_letters_dir / pdf_filename).absolute())
            file_input = WebDriverWait(self.driver, TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "fileUpload_docUpload"))
            )
            file_input.send_keys(file_path)
            time.sleep(3)  # Wait for file to upload
            
            # Submit
            submit_button = WebDriverWait(self.driver, TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "submitFileUploadFormBtn"))
            )
            submit_button.click()
            time.sleep(2)
            
            print(f"      ✓ Uploaded: {doc_name}")
            return True
            
        except Exception as e:
            print(f"      ✗ Error uploading {pdf_filename}: {e}")
            return False
    
    def get_uploaded_files_log(self):
        """
        Get the log file tracking already uploaded files
        
        Returns:
            Path to the log file
        """
        return Path("data") / "uploaded_cover_letters.json"
    
    def load_uploaded_files(self):
        """
        Load the list of already uploaded files
        
        Returns:
            Set of uploaded filenames
        """
        log_file = self.get_uploaded_files_log()
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get("uploaded_files", []))
        return set()
    
    def save_uploaded_file(self, filename):
        """
        Mark a file as uploaded
        
        Args:
            filename: Name of the uploaded file
        """
        log_file = self.get_uploaded_files_log()
        log_file.parent.mkdir(exist_ok=True)
        
        # Load existing
        uploaded = self.load_uploaded_files()
        uploaded.add(filename)
        
        # Save updated list
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump({"uploaded_files": sorted(list(uploaded))}, f, indent=2)
    
    def upload_all_cover_letters(self):
        """
        Upload all PDF files in the cover_letters directory that haven't been uploaded yet
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_files": 0,
            "uploaded": 0,
            "skipped_existing": 0,
            "failed": 0
        }
        
        # Get all PDF files
        pdf_files = list(self.cover_letters_dir.glob("*.pdf"))
        stats["total_files"] = len(pdf_files)
        
        if not pdf_files:
            print("No cover letters found to upload")
            return stats
        
        # Load already uploaded files
        uploaded_files = self.load_uploaded_files()
        
        # Filter out already uploaded files
        files_to_upload = [f for f in pdf_files if f.name not in uploaded_files]
        stats["skipped_existing"] = len(pdf_files) - len(files_to_upload)
        
        print(f"\n📤 Found {len(pdf_files)} total cover letters")
        if stats["skipped_existing"] > 0:
            print(f"   ⏭️  Skipping {stats['skipped_existing']} already uploaded")
        print(f"   📤 Uploading {len(files_to_upload)} new files")
        
        if not files_to_upload:
            print("\n✅ All cover letters already uploaded!")
            return stats
        
        # Navigate to upload menu once
        if not self.navigate_to_upload_menu():
            return stats
        
        # Upload each file
        for idx, pdf_path in enumerate(files_to_upload, 1):
            print(f"\n[{idx}/{len(files_to_upload)}] Uploading {pdf_path.name}...")
            
            if self.upload_file(pdf_path.name):
                stats["uploaded"] += 1
                # Mark as uploaded
                self.save_uploaded_file(pdf_path.name)
                
                # Navigate back to upload page for next file (except last one)
                if idx < len(files_to_upload):
                    if not self.navigate_to_upload_menu():
                        break
            else:
                stats["failed"] += 1
        
        return stats
