'use client';

import { useState, useEffect } from 'react';
import { EnrichedJob, Job, JobMatch } from '@/lib/types';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { DataTable } from './data-table';
import { columns } from './columns';

export default function Home() {
  const [jobs, setJobs] = useState<EnrichedJob[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [matchesRes, jobsRes] = await Promise.all([
          fetch('/data/job_matches_cache.json'),
          fetch('/data/jobs_scraped.json'),
        ]);

        const matches: Record<string, JobMatch> = await matchesRes.json();
        const jobsList: Job[] = await jobsRes.json();

        const enriched: EnrichedJob[] = jobsList
          .map((job) => ({
            ...job,
            match: matches[job.id],
          }))
          .filter((job) => job.match);

        setJobs(enriched);
      } catch (error) {
        console.error('Error loading data:', error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-2xl">Loading jobs...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Browse and filter through {jobs.length} matched job opportunities
        </p>
      </div>

      <DataTable columns={columns} data={jobs} />
    </div>
  );
}
