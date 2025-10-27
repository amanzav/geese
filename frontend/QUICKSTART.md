# Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Configure Supabase
Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

### Step 2: Start the Backend
```bash
# From project root
python main.py
```

### Step 3: View the Frontend
The dev server is already running at:
**http://localhost:3000**

## 📊 Features

- **Dashboard** (`/`) - Overview with stats
- **Jobs** (`/jobs`) - Browse with filters & sorting
- **Filters**: Location, Work Term, Pay Range, Degrees
- **Sort**: Any column (click column headers)
- **Search**: Company, position, description

## 🎨 Built With

- Next.js 15 + TypeScript
- shadcn/ui components
- Tailwind CSS
- Supabase

## 📝 Notes

- All placeholder pages are ready for future features
- Jobs table is fully functional with mock data support
- Responsive design works on all devices
- Build tested and passing ✅

---

**Need help?** Check `frontend/README.md` for detailed documentation.
