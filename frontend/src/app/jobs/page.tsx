import { AppLayout } from '@/components/app-layout'
import { fetchJobs } from '@/lib/supabase'
import { JobsTable } from '@/components/jobs-table'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Briefcase, TrendingUp, CheckCircle, Clock } from 'lucide-react'

export const dynamic = 'force-dynamic'

export default async function JobsPage() {
  const jobs = await fetchJobs()

  // Calculate stats
  const totalJobs = jobs.length
  const appliedJobs = jobs.filter(j => j.is_applied).length
  const avgMatchScore = jobs.length > 0 
    ? Math.round(jobs.reduce((sum, j) => sum + (j.match_score || 0), 0) / jobs.length)
    : 0
  const highMatchJobs = jobs.filter(j => (j.match_score || 0) >= 70).length

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Job Opportunities</h1>
          <p className="text-muted-foreground mt-2">
            Browse and filter co-op positions from WaterlooWorks
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalJobs}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Available positions
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Applied</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{appliedJobs}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {totalJobs > 0 ? Math.round((appliedJobs / totalJobs) * 100) : 0}% of total
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">High Matches</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{highMatchJobs}</div>
              <p className="text-xs text-muted-foreground mt-1">
                70%+ match score
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Match</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{avgMatchScore}%</div>
              <p className="text-xs text-muted-foreground mt-1">
                Average compatibility
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Jobs Table */}
        <JobsTable jobs={jobs} />
      </div>
    </AppLayout>
  )
}
