'use client'

import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/app-layout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  FileText, 
  Send, 
  Upload, 
  Folder, 
  Loader2,
  CheckCircle2,
  AlertCircle,
  Copy,
  Plus
} from 'lucide-react'
import { Job } from '@/lib/supabase'
import { toast } from 'sonner'

interface FolderInfo {
  name: string
  jobCount: number
}

interface AutomationResponse {
  action: string
  folderName: string
  message: string
  command: string
}

// Common WaterlooWorks folder names
const COMMON_FOLDERS = [
  'Applied',
  'Interested',
  'Maybe',
  'Top Choices',
  'Backup Options',
  'First Round',
  'Second Round',
  'High Priority',
]

export default function ApplicationsPage() {
  const [folders, setFolders] = useState<FolderInfo[]>([])
  const [selectedFolder, setSelectedFolder] = useState<string>('')
  const [customFolder, setCustomFolder] = useState<string>('')
  const [showCustomInput, setShowCustomInput] = useState(false)
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // Fetch folders on mount
  useEffect(() => {
    fetchFolders()
  }, [])

  // Fetch jobs when folder changes
  useEffect(() => {
    if (selectedFolder && selectedFolder !== 'custom') {
      fetchJobsInFolder(selectedFolder)
    }
  }, [selectedFolder])

  const fetchFolders = async () => {
    try {
      const response = await fetch('/api/folders')
      const data = await response.json()
      
      // Combine common folders with any found in database
      const dbFolders = data.folders || []
      const allFolders = [...new Set([...COMMON_FOLDERS, ...dbFolders.map((f: FolderInfo) => f.name)])]
      
      setFolders(allFolders.map(name => ({ name, jobCount: 0 })))
    } catch (error) {
      console.error('Error fetching folders:', error)
      // Use common folders as fallback
      setFolders(COMMON_FOLDERS.map(name => ({ name, jobCount: 0 })))
    }
  }

  const fetchJobsInFolder = async (folderName: string) => {
    setLoading(true)
    try {
      const response = await fetch(`/api/folders/${encodeURIComponent(folderName)}/jobs`)
      const data = await response.json()
      setJobs(data.jobs || [])
    } catch (error) {
      console.error('Error fetching jobs:', error)
      toast.error('Failed to fetch jobs in folder')
    } finally {
      setLoading(false)
    }
  }

  const handleAutomation = async (action: string) => {
    const folderToUse = selectedFolder === 'custom' ? customFolder : selectedFolder
    
    if (!folderToUse) {
      toast.error('Please select or enter a folder name first')
      return
    }

    setActionLoading(action)
    try {
      const response = await fetch('/api/automation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, folderName: folderToUse })
      })
      
      const data: AutomationResponse = await response.json()
      
      // Show command to user
      toast.success('Automation Command', {
        description: (
          <div className="space-y-2">
            <p className="text-sm">{data.message}</p>
            <div className="flex items-center gap-2 mt-2">
              <code className="text-xs bg-muted p-2 rounded flex-1 overflow-x-auto">
                {data.command}
              </code>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  navigator.clipboard.writeText(data.command)
                  toast.success('Copied to clipboard!')
                }}
              >
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )
      })
    } catch (error) {
      console.error('Error:', error)
      toast.error('Failed to execute automation')
    } finally {
      setActionLoading(null)
    }
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Applications Management</h1>
          <p className="text-muted-foreground mt-2">
            Manage job applications, generate cover letters, and automate submissions
          </p>
        </div>

        {/* Folder Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Folder className="h-5 w-5" />
              Select Folder
            </CardTitle>
            <CardDescription>
              Choose a WaterlooWorks folder name for automation (folder doesn't need to exist yet)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Select value={selectedFolder} onValueChange={(value) => {
                  setSelectedFolder(value)
                  if (value === 'custom') {
                    setShowCustomInput(true)
                  } else {
                    setShowCustomInput(false)
                  }
                }}>
                  <SelectTrigger className="w-full md:w-[300px]">
                    <SelectValue placeholder="Select a folder..." />
                  </SelectTrigger>
                  <SelectContent>
                    {folders.map((folder) => (
                      <SelectItem key={folder.name} value={folder.name}>
                        {folder.name}
                      </SelectItem>
                    ))}
                    <SelectItem value="custom">
                      <div className="flex items-center gap-2">
                        <Plus className="h-4 w-4" />
                        Custom folder name...
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
                {selectedFolder && selectedFolder !== 'custom' && (
                  <Badge variant="secondary">
                    Selected: {selectedFolder}
                  </Badge>
                )}
              </div>
              
              {showCustomInput && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Custom Folder Name</label>
                  <Input
                    placeholder="Enter folder name (e.g., 'Top Picks', 'Applied')"
                    value={customFolder}
                    onChange={(e) => setCustomFolder(e.target.value)}
                    className="max-w-md"
                  />
                  <p className="text-xs text-muted-foreground">
                    This will be the folder name in WaterlooWorks where automation will work
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        {(selectedFolder && selectedFolder !== 'custom') || (selectedFolder === 'custom' && customFolder) ? (
          <Card>
            <CardHeader>
              <CardTitle>Automation Actions</CardTitle>
              <CardDescription>
                Perform bulk actions on all jobs in folder: <strong>{selectedFolder === 'custom' ? customFolder : selectedFolder}</strong>
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Generate Cover Letters */}
                <Button
                  onClick={() => handleAutomation('generate_cover_letters')}
                  disabled={actionLoading !== null}
                  className="h-auto flex-col gap-2 py-6"
                  variant="outline"
                >
                  {actionLoading === 'generate_cover_letters' ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <FileText className="h-6 w-6" />
                  )}
                  <span className="font-semibold">Generate Cover Letters</span>
                  <span className="text-xs text-muted-foreground">
                    Create personalized cover letters for all jobs
                  </span>
                </Button>

                {/* Apply to All */}
                <Button
                  onClick={() => handleAutomation('apply_all')}
                  disabled={actionLoading !== null}
                  className="h-auto flex-col gap-2 py-6"
                  variant="outline"
                >
                  {actionLoading === 'apply_all' ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <Send className="h-6 w-6" />
                  )}
                  <span className="font-semibold">Apply to All Jobs</span>
                  <span className="text-xs text-muted-foreground">
                    Automatically submit applications
                  </span>
                </Button>

                {/* Upload Cover Letters */}
                <Button
                  onClick={() => handleAutomation('upload_cover_letters')}
                  disabled={actionLoading !== null}
                  className="h-auto flex-col gap-2 py-6"
                  variant="outline"
                >
                  {actionLoading === 'upload_cover_letters' ? (
                    <Loader2 className="h-6 w-6 animate-spin" />
                  ) : (
                    <Upload className="h-6 w-6" />
                  )}
                  <span className="font-semibold">Upload Cover Letters</span>
                  <span className="text-xs text-muted-foreground">
                    Upload generated cover letters to applications
                  </span>
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        {/* Jobs Table - Remove this section since Supabase doesn't track folders */}

        {/* Instructions */}
        {!selectedFolder && (
          <Card className="border-dashed">
            <CardContent className="pt-6">
              <div className="text-center text-muted-foreground space-y-2">
                <Folder className="h-12 w-12 mx-auto opacity-50" />
                <h3 className="font-semibold text-lg">Get Started</h3>
                <p className="text-sm">
                  Select or enter a folder name above to generate automation commands
                </p>
                <p className="text-xs mt-2">
                  The folder will be used by Python scripts when saving, applying, or generating cover letters
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info Card */}
        <Card className="border-blue-200 bg-blue-50/50">
          <CardContent className="pt-6">
            <div className="space-y-2">
              <h3 className="font-semibold flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-blue-600" />
                How It Works
              </h3>
              <ul className="text-sm text-muted-foreground space-y-1 ml-7">
                <li>• Select a folder name (or create a custom one)</li>
                <li>• Click an automation action to get the Python command</li>
                <li>• Copy and run the command in your terminal</li>
                <li>• The Python script will work with jobs in that WaterlooWorks folder</li>
                <li>• Make sure you've saved jobs to the folder in WaterlooWorks first!</li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  )
}
