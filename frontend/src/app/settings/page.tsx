import { AppLayout } from '@/components/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

export default function SettingsPage() {
  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Configure your preferences and integration settings
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Supabase Configuration</CardTitle>
            <CardDescription>
              Connect to your Supabase database
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="supabase-url">Supabase URL</Label>
              <Input 
                id="supabase-url"
                placeholder="https://your-project.supabase.co"
                defaultValue={process.env.NEXT_PUBLIC_SUPABASE_URL}
                disabled
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="supabase-key">Supabase Anon Key</Label>
              <Input 
                id="supabase-key"
                type="password"
                placeholder="your-anon-key"
                defaultValue={process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY}
                disabled
              />
            </div>
            <p className="text-sm text-muted-foreground">
              Update these values in your <code className="bg-muted px-1 py-0.5 rounded">.env.local</code> file
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Coming Soon</CardTitle>
            <CardDescription>
              Additional settings will be available in future updates
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">
              More configuration options coming soon.
            </p>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
