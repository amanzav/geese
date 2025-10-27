import { AppLayout } from '@/components/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function AnalyticsPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground mt-2">
            View insights and statistics about your job search
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Coming Soon</CardTitle>
            <CardDescription>
              This page will display analytics and insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Analytics features will be available in a future update.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
