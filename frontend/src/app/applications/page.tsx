import { AppLayout } from '@/components/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function ApplicationsPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">My Applications</h1>
          <p className="text-muted-foreground mt-2">
            Track and manage your job applications
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Coming Soon</CardTitle>
            <CardDescription>
              This page will display your application history and status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              Application tracking functionality will be available in a future update.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
