import { NextResponse } from 'next/server'
import { getSupabase } from '@/lib/supabase'

// Get all unique folder names from saved_folders table
export async function GET() {
  try {
    const supabase = getSupabase()
    
    // Get distinct folder names with job counts
    const { data: folders, error } = await supabase
      .from('saved_folders')
      .select('folder_name')
    
    if (error) {
      console.error('Error fetching folders:', error)
      return NextResponse.json({ error: 'Failed to fetch folders' }, { status: 500 })
    }
    
    // Count jobs per folder
    const folderCounts = folders.reduce((acc: Record<string, number>, curr) => {
      acc[curr.folder_name] = (acc[curr.folder_name] || 0) + 1
      return acc
    }, {})
    
    const folderList = Object.entries(folderCounts).map(([name, count]) => ({
      name,
      jobCount: count
    }))
    
    return NextResponse.json({ folders: folderList })
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
