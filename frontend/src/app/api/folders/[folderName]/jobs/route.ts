import { NextRequest, NextResponse } from 'next/server'
import { getSupabase } from '@/lib/supabase'

// Get all jobs in a specific folder
export async function GET(
  request: NextRequest,
  { params }: { params: { folderName: string } }
) {
  try {
    const folderName = params.folderName
    const supabase = getSupabase()
    
    // Get job IDs from saved_folders
    const { data: savedJobs, error: folderError } = await supabase
      .from('saved_folders')
      .select('job_id')
      .eq('folder_name', folderName)
    
    if (folderError) {
      console.error('Error fetching folder jobs:', folderError)
      return NextResponse.json({ error: 'Failed to fetch folder jobs' }, { status: 500 })
    }
    
    if (!savedJobs || savedJobs.length === 0) {
      return NextResponse.json({ jobs: [] })
    }
    
    const jobIds = savedJobs.map(s => s.job_id)
    
    // Get full job details
    const { data: jobs, error: jobsError } = await supabase
      .from('jobs')
      .select('*')
      .in('job_id', jobIds)
    
    if (jobsError) {
      console.error('Error fetching jobs:', jobsError)
      return NextResponse.json({ error: 'Failed to fetch jobs' }, { status: 500 })
    }
    
    return NextResponse.json({ jobs })
  } catch (error) {
    console.error('Error:', error)
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 })
  }
}
