'use client'

import { useState, useMemo } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Job } from '@/lib/supabase'
import { ArrowUpDown, Search, Filter } from 'lucide-react'

interface JobsTableProps {
  jobs: Job[]
}

type SortKey = keyof Job
type SortOrder = 'asc' | 'desc'

export function JobsTable({ jobs }: JobsTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('scraped_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  
  // Filter states
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [selectedWorkTerm, setSelectedWorkTerm] = useState<string>('all')
  const [minPay, setMinPay] = useState('')
  const [maxPay, setMaxPay] = useState('')
  const [selectedDegree, setSelectedDegree] = useState<string>('all')

  // Extract unique values for filters
  const uniqueLocations = useMemo(() => {
    const locations = new Set(jobs.map(job => job.location).filter(Boolean))
    return Array.from(locations).sort()
  }, [jobs])

  const uniqueWorkTerms = useMemo(() => {
    const terms = new Set(jobs.map(job => job.work_term_duration).filter(Boolean))
    return Array.from(terms).sort()
  }, [jobs])

  const uniqueDegrees = useMemo(() => {
    const degrees = new Set<string>()
    jobs.forEach(job => {
      if (job.targeted_degrees_disciplines) {
        job.targeted_degrees_disciplines.forEach(degree => degrees.add(degree))
      }
    })
    return Array.from(degrees).sort()
  }, [jobs])

  // Filter and sort jobs
  const filteredAndSortedJobs = useMemo(() => {
    let filtered = jobs.filter(job => {
      // Search filter
      const searchLower = searchQuery.toLowerCase()
      const matchesSearch = 
        job.company?.toLowerCase().includes(searchLower) ||
        job.title?.toLowerCase().includes(searchLower) ||
        job.summary?.toLowerCase().includes(searchLower)
      
      if (!matchesSearch) return false

      // Location filter
      if (selectedLocation !== 'all' && job.location !== selectedLocation) {
        return false
      }

      // Work term filter
      if (selectedWorkTerm !== 'all' && job.work_term_duration !== selectedWorkTerm) {
        return false
      }

      // Pay range filter
      if (job.compensation_value && (minPay || maxPay)) {
        const jobPay = job.compensation_value
        if (minPay && jobPay < parseInt(minPay)) return false
        if (maxPay && jobPay > parseInt(maxPay)) return false
      }

      // Degree filter
      if (selectedDegree !== 'all') {
        if (!job.targeted_degrees_disciplines || !job.targeted_degrees_disciplines.includes(selectedDegree)) {
          return false
        }
      }

      return true
    })

    // Sort
    return filtered.sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]
      
      if (aVal == null) return 1
      if (bVal == null) return -1
      
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortOrder === 'asc' 
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal)
      }
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal
      }
      
      return 0
    })
  }, [jobs, searchQuery, sortKey, sortOrder, selectedLocation, selectedWorkTerm, minPay, maxPay, selectedDegree])

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortOrder('asc')
    }
  }

  const clearFilters = () => {
    setSearchQuery('')
    setSelectedLocation('all')
    setSelectedWorkTerm('all')
    setMinPay('')
    setMaxPay('')
    setSelectedDegree('all')
  }

  return (
    <div className="space-y-4">
      {/* Filters Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search */}
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by company, position, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1"
            />
          </div>

          {/* Filter Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Location Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Location</label>
              <Select value={selectedLocation} onValueChange={setSelectedLocation}>
                <SelectTrigger>
                  <SelectValue placeholder="All locations" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All locations</SelectItem>
                  {uniqueLocations.map(location => (
                    <SelectItem key={location} value={location}>
                      {location}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Work Term Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Work Term</label>
              <Select value={selectedWorkTerm} onValueChange={setSelectedWorkTerm}>
                <SelectTrigger>
                  <SelectValue placeholder="All terms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All terms</SelectItem>
                  {uniqueWorkTerms.map(term => (
                    <SelectItem key={term} value={term}>
                      {term}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Degree Filter */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Targeted Degree</label>
              <Select value={selectedDegree} onValueChange={setSelectedDegree}>
                <SelectTrigger>
                  <SelectValue placeholder="All degrees" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All degrees</SelectItem>
                  {uniqueDegrees.map(degree => (
                    <SelectItem key={degree} value={degree}>
                      {degree}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Pay Range */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Min Pay ($)</label>
              <Input
                type="number"
                placeholder="e.g. 20"
                value={minPay}
                onChange={(e) => setMinPay(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Max Pay ($)</label>
              <Input
                type="number"
                placeholder="e.g. 50"
                value={maxPay}
                onChange={(e) => setMaxPay(e.target.value)}
              />
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <Button variant="outline" onClick={clearFilters} className="w-full">
                Clear Filters
              </Button>
            </div>
          </div>

          {/* Results Count */}
          <div className="text-sm text-muted-foreground">
            Showing {filteredAndSortedJobs.length} of {jobs.length} jobs
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('company')}
                      className="h-8 w-full justify-start"
                    >
                      Company
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('title')}
                      className="h-8 w-full justify-start"
                    >
                      Position
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('location')}
                      className="h-8 w-full justify-start"
                    >
                      Location
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('work_term_duration')}
                      className="h-8 w-full justify-start"
                    >
                      Work Term
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('compensation_value')}
                      className="h-8 w-full justify-start"
                    >
                      Pay
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('openings')}
                      className="h-8 w-full justify-start"
                    >
                      Openings
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('chances')}
                      className="h-8 w-full justify-start"
                    >
                      Chances
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredAndSortedJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      No jobs found matching your criteria.
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredAndSortedJobs.map((job) => (
                    <TableRow key={job.job_id} className="cursor-pointer hover:bg-muted/50">
                      <TableCell className="font-medium">{job.company}</TableCell>
                      <TableCell>{job.title}</TableCell>
                      <TableCell>{job.location || 'N/A'}</TableCell>
                      <TableCell>{job.work_term_duration || 'N/A'}</TableCell>
                      <TableCell>{job.compensation_raw || 'N/A'}</TableCell>
                      <TableCell>
                        <Badge variant="secondary">
                          {job.openings} / {job.applications}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {job.chances ? (
                          <Badge 
                            variant={job.chances >= 0.3 ? 'default' : 'secondary'}
                          >
                            {(job.chances * 100).toFixed(0)}%
                          </Badge>
                        ) : (
                          'N/A'
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">Active</Badge>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
