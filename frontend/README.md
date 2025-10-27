# WaterlooWorks Automator - Frontend

A modern Next.js 15 frontend for the WaterlooWorks job automation system. Built with TypeScript, shadcn/ui, and Supabase.

## Features

- 🎯 **Job Dashboard**: Browse and filter co-op opportunities
- 📊 **Advanced Filtering**: Filter by location, work term, pay range, targeted degrees, and more
- 🔍 **Smart Search**: Search across company names, positions, and descriptions
- 📈 **Sorting**: Sort by any column including pay, match score, openings, etc.
- 🎨 **Modern UI**: Built with shadcn/ui components and Tailwind CSS
- 🗄️ **Supabase Integration**: Real-time data synchronization
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

## Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/) with App Router
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **UI Components**: [shadcn/ui](https://ui.shadcn.com/)
- **Database**: [Supabase](https://supabase.com/)
- **Icons**: [Lucide React](https://lucide.dev/)

## Getting Started

### Prerequisites

- Node.js 18+ installed
- A Supabase account and project
- The backend scraper running and populating data

### Installation

1. **Install dependencies**:
```bash
npm install
```

2. **Configure environment variables**:

Create a `.env.local` file:

```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Get these from your [Supabase Dashboard](https://app.supabase.com/) → Settings → API

3. **Run the development server**:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── page.tsx           # Home/Dashboard
│   │   ├── jobs/page.tsx      # Jobs listing with filters
│   │   ├── applications/      # Application tracking
│   │   ├── analytics/         # Analytics page
│   │   └── settings/          # Settings page
│   ├── components/
│   │   ├── ui/                # shadcn/ui components
│   │   ├── app-layout.tsx     # Main layout with sidebar
│   │   └── jobs-table.tsx     # Jobs data table with filters
│   └── lib/
│       ├── supabase.ts        # Supabase client & queries
│       └── utils.ts           # Utility functions
└── .env.local                 # Environment variables (create this)
```

## Features

### Jobs Table
- Advanced filtering (location, work term, pay range, degrees)
- Real-time search
- Sortable columns
- Match score indicators
- Application status badges

### Sidebar Navigation
- Dashboard
- Jobs
- Applications (coming soon)
- Analytics (coming soon)
- Settings

## Build & Deploy

```bash
# Production build
npm run build

# Start production server
npm start
```

Deploy to [Vercel](https://vercel.com/new):
```bash
vercel
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anonymous key | Yes |

## Troubleshooting

### "No jobs found"
- Ensure the backend scraper has populated the Supabase database
- Check `.env.local` has correct credentials
- Verify Supabase table is named `jobs`

### Build errors
- Clear `.next`: `rm -rf .next`
- Reinstall: `rm -rf node_modules && npm install`

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
