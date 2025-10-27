import { AppLayout } from '@/components/app-layout'
import { fetchJobs } from '@/lib/supabase'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Briefcase, TrendingUp, Target, Zap } from 'lucide-react'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

export default async function Home() {
  const jobs = await fetchJobs()
  
  // Calculate quick stats
  const totalJobs = jobs.length
  const highMatchJobs = jobs.filter(j => (j.match_score || 0) >= 70).length
  const recentJobs = jobs.slice(0, 5)

  return (
    <AppLayout>
      <div className="space-y-8">
        {/* Hero Section */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold tracking-tight">
            WaterlooWorks Automator
          </h1>
          <p className="text-lg text-muted-foreground">
            Streamline your co-op job search with automated matching and intelligent filtering
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Opportunities</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalJobs}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Active job postings
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">High Matches</CardTitle>
              <Target className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{highMatchJobs}</div>
              <p className="text-xs text-muted-foreground mt-1">
                70%+ compatibility
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Match Rate</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {totalJobs > 0 ? Math.round((highMatchJobs / totalJobs) * 100) : 0}%
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Of all positions
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Jobs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Opportunities</CardTitle>
                <CardDescription>Latest jobs added to the system</CardDescription>
              </div>
              <Button asChild>
                <Link href="/jobs">View All</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentJobs.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No jobs available yet. Run the scraper to fetch jobs from WaterlooWorks.
                </p>
              ) : (
                recentJobs.map((job) => (
                  <div
                    key={job.id}
                    className="flex items-start justify-between p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold">{job.position_title}</h3>
                        {job.match_score && job.match_score >= 70 && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700">
                            <Zap className="h-3 w-3" />
                            {job.match_score}%
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {job.company_name} • {job.location} • {job.work_term}
                      </p>
                      {job.compensation && (
                        <p className="text-sm font-medium text-green-600">
                          {job.compensation}
                        </p>
                      )}
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <Link href="/jobs">View Details</Link>
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Get started with common tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button variant="outline" className="h-auto py-4" asChild>
                <Link href="/jobs">
                  <div className="flex flex-col items-center gap-2">
                    <Briefcase className="h-6 w-6" />
                    <span className="font-semibold">Browse Jobs</span>
                    <span className="text-xs text-muted-foreground">
                      View and filter all opportunities
                    </span>
                  </div>
                </Link>
              </Button>
              <Button variant="outline" className="h-auto py-4" asChild>
                <Link href="/applications">
                  <div className="flex flex-col items-center gap-2">
                    <Target className="h-6 w-6" />
                    <span className="font-semibold">My Applications</span>
                    <span className="text-xs text-muted-foreground">
                      Track your application status
                    </span>
                  </div>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
