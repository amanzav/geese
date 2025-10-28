'use client';

import { useState, useEffect } from 'react';
import { AppLayout } from '@/components/app-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { JobsTable } from '@/components/jobs-table';
import { Folder, RefreshCw, FolderOpen, Briefcase, TrendingUp } from 'lucide-react';
import { Job } from '@/lib/supabase';

interface FolderData {
  [folderName: string]: string[]; // folder name -> job IDs
}

interface FoldersResponse {
  folders: FolderData;
  total_folders: number;
  total_jobs: number;
}

export default function FoldersPage() {
  const [folders, setFolders] = useState<FolderData | null>(null);
  const [totalFolders, setTotalFolders] = useState(0);
  const [totalJobs, setTotalJobs] = useState(0);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [folderJobs, setFolderJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Fetch folders on mount
  useEffect(() => {
    fetchFolders();
  }, []);

  const fetchFolders = async () => {
    setLoading(true);
    try {
      // Try to fetch from Python backend first
      const response = await fetch('http://localhost:8000/api/folders');
      
      if (!response.ok) {
        throw new Error('Backend not available');
      }
      
      const data: FoldersResponse = await response.json();
      setFolders(data.folders);
      setTotalFolders(data.total_folders);
      setTotalJobs(data.total_jobs);
    } catch (error) {
      console.error('Error fetching folders:', error);
      alert('Could not fetch folders. Make sure the backend server is running (python -m modules.api)');
      // Set empty state
      setFolders({});
      setTotalFolders(0);
      setTotalJobs(0);
    } finally {
      setLoading(false);
    }
  };

  const handleFolderClick = async (folderName: string) => {
    setSelectedFolder(folderName);
    setLoadingJobs(true);
    
    try {
      const jobIds = folders?.[folderName] || [];
      
      if (jobIds.length === 0) {
        setFolderJobs([]);
        alert(`No jobs found in "${folderName}"`);
        return;
      }

      // Fetch job details from backend
      const response = await fetch(`http://localhost:8000/api/jobs?job_ids=${jobIds.join(',')}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch jobs');
      }
      
      const jobs: Job[] = await response.json();
      setFolderJobs(jobs);
    } catch (error) {
      console.error('Error fetching folder jobs:', error);
      alert('Could not fetch jobs for this folder');
      setFolderJobs([]);
    } finally {
      setLoadingJobs(false);
    }
  };

  const handleSyncFolders = async () => {
    setSyncing(true);
    
    try {
      alert('Sync started. This will take a few minutes. Check the Python console for progress.');

      const response = await fetch('http://localhost:8000/api/folders/sync', {
        method: 'POST',
      });
      
      const data = await response.json();
      
      if (data.status === 'error') {
        alert(data.message || 'Sync must be run from the Python application with an active browser session.');
      } else if (data.status === 'success') {
        alert('Folders have been synced successfully!');
        // Refresh folders
        await fetchFolders();
      } else {
        alert(data.message || 'Sync is already running.');
      }
    } catch (error) {
      console.error('Error syncing folders:', error);
      alert('Could not trigger sync. Run "python examples/sync_folders.py" manually.');
    } finally {
      setSyncing(false);
    }
  };

  const handleBackToFolders = () => {
    setSelectedFolder(null);
    setFolderJobs([]);
  };

  if (loading) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <Skeleton className="h-12 w-64" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
            <Skeleton className="h-32" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </div>
        </div>
      </AppLayout>
    );
  }

  // Show folder jobs view
  if (selectedFolder) {
    return (
      <AppLayout>
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Button
                variant="ghost"
                onClick={handleBackToFolders}
                className="mb-2"
              >
                ← Back to Folders
              </Button>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                <FolderOpen className="h-8 w-8" />
                {selectedFolder}
              </h1>
              <p className="text-muted-foreground mt-2">
                {folderJobs.length} job{folderJobs.length !== 1 ? 's' : ''} in this folder
              </p>
            </div>
          </div>

          {loadingJobs ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Loading jobs...</p>
              </div>
            </div>
          ) : folderJobs.length > 0 ? (
            <JobsTable jobs={folderJobs} />
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Briefcase className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No jobs found in this folder</p>
              </CardContent>
            </Card>
          )}
        </div>
      </AppLayout>
    );
  }

  // Show folders grid view
  return (
    <AppLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">My Folders</h1>
            <p className="text-muted-foreground mt-2">
              Organize and manage your WaterlooWorks job applications
            </p>
          </div>
          <Button
            onClick={handleSyncFolders}
            disabled={syncing}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            {syncing ? 'Syncing...' : 'Sync Folders'}
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Folders</CardTitle>
              <Folder className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalFolders}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Your collections
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
              <Briefcase className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalJobs}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Across all folders
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg per Folder</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {totalFolders > 0 ? Math.round(totalJobs / totalFolders) : 0}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Jobs per folder
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Folders Grid */}
        {folders && Object.keys(folders).length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(folders).map(([folderName, jobIds]) => (
              <Card
                key={folderName}
                className="cursor-pointer hover:shadow-lg transition-shadow"
                onClick={() => handleFolderClick(folderName)}
              >
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Folder className="h-5 w-5 text-primary" />
                      <CardTitle className="text-lg">{folderName}</CardTitle>
                    </div>
                    <Badge variant="secondary">{jobIds.length}</Badge>
                  </div>
                  <CardDescription>
                    {jobIds.length} job{jobIds.length !== 1 ? 's' : ''} in this folder
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" className="w-full">
                    View Jobs →
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Folder className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Folders Found</h3>
              <p className="text-muted-foreground text-center mb-4">
                Click "Sync Folders" to fetch your WaterlooWorks folders
              </p>
              <p className="text-xs text-muted-foreground text-center">
                Or run: <code className="bg-muted px-2 py-1 rounded">python examples/sync_folders.py</code>
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
