"""Command-line interface orchestration for the Waterloo Works Automator."""
from __future__ import annotations

import argparse
import json
import os
from typing import Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from modules.pipeline import JobAnalyzer

from modules.config import resolve_waterlooworks_credentials

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze WaterlooWorks jobs")
    parser.add_argument(
        "--mode",
        choices=["realtime", "batch", "analyze", "cover-letter", "upload-covers", "db-stats", "db-export"],
        default="batch",
        help=(
            "Operation mode: realtime (scrape+analyze live), batch (scrape then analyze), "
            "analyze (cached only), cover-letter (generate covers for Geese jobs), "
            "upload-covers (upload all covers to WW), "
            "db-stats (show database statistics), db-export (export database to markdown)"
        ),
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick mode (basic scraping, faster)",
    )
    parser.add_argument(
        "--force-rematch",
        action="store_true",
        help="Ignore cached matches and recalculate all job scores",
    )
    parser.add_argument(
        "--auto-save",
        action="store_true",
        help="Automatically save high-scoring jobs to WaterlooWorks folder",
    )
    parser.add_argument(
        "--jobs-path",
        default="data/jobs_scraped.json",
        help="Path to cached jobs JSON used by analyze mode.",
    )
    return parser


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def run_cli(argv: Optional[Sequence[str]] = None, analyzer: Optional["JobAnalyzer"] = None) -> None:
    args = parse_args(argv)
    if analyzer is None:
        from modules.pipeline import JobAnalyzer

        analyzer = JobAnalyzer()

    if args.mode == "realtime":
        from modules.auth import obtain_authenticated_session

        auth = obtain_authenticated_session()
        analyzer.run_realtime_pipeline(auto_save_to_folder=True, auth=auth)
        return

    if args.mode == "batch":
        analyzer.run_full_pipeline(
            detailed=not args.quick,
            force_rematch=args.force_rematch,
            auto_save_to_folder=args.auto_save,
        )
        return

    if args.mode == "analyze":
        _run_analyze_mode(analyzer, args.jobs_path, args.force_rematch)
        return

    if args.mode == "cover-letter":
        _run_cover_letter_mode(analyzer)
        return

    if args.mode == "upload-covers":
        _run_upload_covers_mode(analyzer)
        return

    if args.mode == "db-stats":
        _run_db_stats_mode()
        return

    if args.mode == "db-export":
        _run_db_export_mode()
        return

    raise ValueError(f"Unsupported mode: {args.mode}")


def _run_analyze_mode(analyzer: "JobAnalyzer", jobs_path: str, force_rematch: bool) -> None:
    print("📂 Using cached jobs...")
    if not os.path.exists(jobs_path):
        raise FileNotFoundError(f"Cached jobs not found at {jobs_path}")

    with open(jobs_path, "r", encoding="utf-8") as handle:
        jobs = json.load(handle)

    print(f"✅ Loaded {len(jobs)} jobs from cache\n")
    print("🔍 Analyzing jobs...")
    if force_rematch:
        print("⚠️  Force rematch enabled - ignoring cache")

    results = analyzer.matcher.batch_analyze(jobs, force_rematch=force_rematch)
    filtered = analyzer.apply_filters(results)
    analyzer.save_results(filtered)
    analyzer.show_summary(filtered)


def _run_cover_letter_mode(analyzer: "JobAnalyzer") -> None:
    from modules.auth import WaterlooWorksAuth
    from modules.cover_letter_generator import CoverLetterGenerator

    print("=" * 70)
    print("📝 COVER LETTER GENERATOR")
    print("=" * 70)
    print()

    print("🔐 Logging into WaterlooWorks...")
    username, password = resolve_waterlooworks_credentials()

    if not username or not password:
        print("❌ Error: Credentials not found in .env file")
        print("   Please set WATERLOOWORKS_USERNAME and WATERLOOWORKS_PASSWORD")
        return

    print(f"   Using credentials from configuration: {username}")
    print()

    auth = WaterlooWorksAuth(username, password)
    auth.login()

    cover_config = analyzer.config.get("cover_letter", {})
    resume_path = analyzer.config.get("resume_path", "input/resume.pdf")
    cached_jobs_path = cover_config.get("cached_jobs_path", "data/jobs_sample.json")
    prompt_template = cover_config.get("prompt_template", "Write a professional cover letter.")

    resume_text = _load_resume_text(resume_path)
    if not resume_text:
        auth.driver.quit()
        return

    generator = CoverLetterGenerator(
        auth.driver,
        resume_text,
        prompt_template,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    stats = generator.generate_all_cover_letters(cached_jobs_path)

    auth.driver.quit()

    print("\n" + "=" * 70)
    print("📊 COVER LETTER GENERATION SUMMARY")
    print("=" * 70)
    print(f"Total Jobs: {stats['total_jobs']}")
    print(f"✅ Generated: {stats['generated']}")
    print(f"⏭  Skipped (already exists): {stats['skipped_existing']}")
    print(f"❌ Failed: {stats['failed']}")
    print("=" * 70)


def _run_upload_covers_mode(analyzer: "JobAnalyzer") -> None:
    from modules.auth import WaterlooWorksAuth
    from modules.cover_letter_generator import CoverLetterUploader

    print("=" * 70)
    print("📤 COVER LETTER UPLOADER")
    print("=" * 70)
    print()

    print("🔐 Logging into WaterlooWorks...")
    username, password = resolve_waterlooworks_credentials()

    if not username or not password:
        print("❌ Error: Credentials not found in .env file")
        print("   Please set WATERLOOWORKS_USERNAME and WATERLOOWORKS_PASSWORD")
        return

    print(f"   Using credentials from configuration: {username}")
    print()

    auth = WaterlooWorksAuth(username, password)
    auth.login()

    uploader = CoverLetterUploader(auth.driver)
    stats = uploader.upload_all_cover_letters()

    auth.driver.quit()

    print("\n" + "=" * 70)
    print("📊 UPLOAD SUMMARY")
    print("=" * 70)
    print(f"Total Files: {stats['total_files']}")
    print(f"✅ Uploaded: {stats['uploaded']}")
    print(f"❌ Failed: {stats['failed']}")
    print("=" * 70)


def _load_resume_text(resume_path: str) -> str:
    if os.path.exists(resume_path):
        from pypdf import PdfReader

        reader = PdfReader(resume_path)
        resume_text = "".join(page.extract_text() for page in reader.pages)
        print(f"✓ Loaded resume from PDF: {resume_path}")
        return resume_text

    parsed_path = "data/resume_parsed.txt"
    if os.path.exists(parsed_path):
        with open(parsed_path, "r", encoding="utf-8") as handle:
            resume_text = handle.read()
        print("✓ Loaded resume from text: data/resume_parsed.txt")
        return resume_text

    print("❌ Error: Resume not found!")
    print(f"   Expected: {resume_path} OR data/resume_parsed.txt")
    print("   Please add your resume to one of these locations.")
    return ""


def _run_db_stats_mode() -> None:
    """Show database statistics"""
    from modules.database import get_db
    
    print("=" * 70)
    print("📊 DATABASE STATISTICS")
    print("=" * 70)
    print()
    
    db = get_db()
    stats = db.get_stats()
    
    print("Table Statistics:")
    for table, count in stats.items():
        print(f"  {table:25} {count:>6} records")
    
    # Show top matches
    print("\n🎯 Top Matches:")
    top_matches = db.get_top_matches(limit=10)
    for i, match in enumerate(top_matches, 1):
        print(f"  {i}. {match['title']} @ {match['company']}")
        print(f"     Score: {match['match_score']:.1f} | Decision: {match['decision']}")
    
    print("\n" + "=" * 70)


def _run_db_export_mode() -> None:
    """Export database matches to markdown report"""
    from modules.database import get_db
    from datetime import datetime
    
    print("=" * 70)
    print("📄 EXPORTING DATABASE TO MARKDOWN")
    print("=" * 70)
    print()
    
    db = get_db()
    
    # Get all matches with job data
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                j.job_id, j.title, j.company, j.location, j.deadline,
                j.openings, j.applications, j.chances,
                m.match_score, m.decision, m.ai_reasoning
            FROM jobs j
            INNER JOIN job_matches m ON j.job_id = m.job_id
            WHERE m.decision = 'apply'
            ORDER BY m.match_score DESC
        """)
        results = cursor.fetchall()
    
    if not results:
        print("   ℹ️  No matches found in database")
        return
    
    # Generate markdown
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    md_path = f"data/database_export_{timestamp}.md"
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Job Matches Export\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Total Matches: {len(results)}\n\n")
        f.write("---\n\n")
        
        for i, row in enumerate(results, 1):
            f.write(f"## {i}. {row['title']}\n\n")
            f.write(f"**Company:** {row['company']}  \n")
            f.write(f"**Location:** {row['location']}  \n")
            f.write(f"**Match Score:** {row['match_score']:.1f}/100  \n")
            f.write(f"**Decision:** {row['decision']}  \n")
            f.write(f"**Openings:** {row['openings']} | **Applications:** {row['applications']} | **Chances:** {row['chances']:.2f}  \n")
            f.write(f"**Deadline:** {row['deadline']}  \n")
            f.write(f"**Job ID:** {row['job_id']}  \n\n")
            
            if row['ai_reasoning']:
                f.write(f"**AI Analysis:**\n")
                f.write(f"{row['ai_reasoning']}\n\n")
            
            f.write("---\n\n")
    
    print(f"✅ Exported {len(results)} matches to: {md_path}")
    print("\n" + "=" * 70)
