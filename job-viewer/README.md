# Job Matches Viewer

A simple and functional frontend built with Next.js, TanStack Table, and shadcn/ui to visualize job matches from WaterlooWorks.

## Features

- **Powerful Data Table** using TanStack Table with shadcn/ui components
- **Sortable columns**: Click any column header to sort (Fit Score, Job Title, Company, Pay, Location, Missing Skills)
- **Advanced filtering**: 
  - Global search across title, company, and location
  - Location-specific filter dropdown
- **Pagination controls**: Navigate through pages with customizable page size
- **Detailed job view** in a modal dialog showing:
  - Match metrics (Fit Score, Skill Match, Coverage, Keyword Match)
  - Matched vs Missing technologies
  - Top matched resume points with similarity scores
  - Full job description, responsibilities, and required skills
  - Compensation, deadline, and application details

## Column Details

The table displays these key columns:

1. **Fit Score** - Overall match score (0-100) with color coding:
   - 🟢 Green: 70+ (Great match)
   - 🟡 Yellow: 50-70 (Good match)
   - 🔴 Red: <50 (Weak match)
2. **Job Title** - Position name
3. **Company** - Employer name
4. **Pay** - Compensation (hourly/salary)
5. **Location** - City/work location
6. **Missing Skills** - Technologies you don't have yet:
   - Shows must-have skills in red badge
   - Lists up to 3 missing techs with count
7. **Actions** - "Details" button to open full job information

## Getting Started

### Prerequisites

- Node.js 20+ installed
- The job data files should be in `public/data/`:
  - `job_matches_cache.json`
  - `jobs_scraped.json`

### Installation

The project is already set up. To run it:

```bash
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

### Updating Job Data

To refresh the job data:

1. Run your Python scraper and matcher in the parent directory
2. Copy the updated JSON files to `public/data/`:

```powershell
Copy-Item "..\data\job_matches_cache.json" "public\data\job_matches_cache.json"
Copy-Item "..\data\jobs_scraped.json" "public\data\jobs_scraped.json"
```

3. Refresh the browser to see the updated data

## Key Metrics Explained

- **Fit Score**: Overall match score (0-100)
  - 🟢 Green: 70+ (Great match)
  - 🟡 Yellow: 50-70 (Good match)
  - 🔴 Red: <50 (Weak match)
- **Missing Skills**: Number of must-have skills you're missing
- **Skill Match**: How well your skills align with requirements
- **Coverage**: What percentage of requirements are addressed
- **Keyword Match**: How many required keywords match your resume

## Use Cases

This viewer is designed to help you:

1. **Identify top opportunities**: Sort by fit score to find your best matches
2. **Target high-paying jobs**: Sort by compensation to prioritize high-value positions
3. **Find jobs in specific cities**: Filter by location (San Francisco, New York, etc.)
4. **Identify skill gaps**: See which skills you need to add to your resume
5. **Make informed decisions**: View all details to decide where to put extra effort

## Technology Stack

- **Next.js 15** - React framework with App Router
- **TypeScript** - Type safety
- **TanStack Table (React Table v8)** - Powerful table and data grid library
- **Tailwind CSS** - Styling
- **shadcn/ui** - Beautiful UI components
- **Radix UI** - Accessible component primitives

## How It Works

The app follows shadcn's recommended data table pattern:

1. **Column Definitions** (`app/columns.tsx`) - Defines table structure, sorting, and cell rendering
2. **DataTable Component** (`app/data-table.tsx`) - Reusable table with filtering, sorting, and pagination
3. **Page Component** (`app/page.tsx`) - Loads data and renders the DataTable

This architecture provides:
- Type-safe column definitions
- Built-in sorting with custom sort functions
- Column filtering capabilities
- Pagination with customizable page sizes
- Responsive design that works on all screen sizes

## Project Structure

```
job-viewer/
├── app/
│   ├── page.tsx          # Main dashboard page
│   └── globals.css       # Global styles
├── components/
│   └── ui/               # shadcn/ui components
├── lib/
│   ├── types.ts          # TypeScript type definitions
│   └── utils.ts          # Utility functions
└── public/
    └── data/             # Job data JSON files
```

## Future Improvements

Potential enhancements you could add:

- Export filtered jobs to CSV
- Bookmark/favorite jobs
- Notes/comments on specific jobs
- Application tracking
- Side-by-side job comparison
- Dark/light theme toggle
- Mobile-responsive improvements
