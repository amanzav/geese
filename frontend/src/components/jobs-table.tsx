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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Job } from '@/lib/supabase'
import { ArrowUpDown, Search, Filter, Eye, Calendar, MapPin, Briefcase, DollarSign, Users, Target, FileText } from 'lucide-react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

interface JobsTableProps {
  jobs: Job[]
}

type SortKey = keyof Job
type SortOrder = 'asc' | 'desc'

const ITEMS_PER_PAGE = 50

export function JobsTable({ jobs }: JobsTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('scraped_at')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  
  // Filter states
  const [selectedLocation, setSelectedLocation] = useState<string>('all')
  const [selectedWorkTerm, setSelectedWorkTerm] = useState<string>('all')
  const [minPay, setMinPay] = useState('')
  const [maxPay, setMaxPay] = useState('')
  const [selectedDegree, setSelectedDegree] = useState<string>('all')

  // Extract unique values for filters
  const uniqueLocations = useMemo(() => {
    const locations = new Set(jobs.map(job => job.location).filter((loc): loc is string => Boolean(loc)))
    return Array.from(locations).sort()
  }, [jobs])

  const uniqueWorkTerms = useMemo(() => {
    const terms = new Set(jobs.map(job => job.work_term_duration).filter((term): term is string => Boolean(term)))
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

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedJobs.length / ITEMS_PER_PAGE)
  const paginatedJobs = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    return filteredAndSortedJobs.slice(startIndex, startIndex + ITEMS_PER_PAGE)
  }, [filteredAndSortedJobs, currentPage])

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

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    try {
      return new Date(dateString).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric' 
      })
    } catch {
      return 'N/A'
    }
  }

  // Component continues in next edit due to size
  return (
    <div className="space-y-6">
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
            Showing {paginatedJobs.length} of {filteredAndSortedJobs.length} jobs (Page {currentPage} of {totalPages})
          </div>
        </CardContent>
      </Card>

      {/* TABLE SECTION CONTINUES BELOW - Split for readability */}
      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <div className="rounded-md border overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('job_id')}
                      className="h-8 w-full justify-start font-semibold"
                    >
                      ID
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('title')}
                      className="h-8 w-full justify-start font-semibold"
                    >
                      Position
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('company')}
                      className="h-8 w-full justify-start font-semibold"
                    >
                      Company
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('location')}
                      className="h-8 w-full justify-start font-semibold"
                    >
                      Location
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('work_term_duration')}
                      className="h-8 w-full justify-start font-semibold"
                    >
                      Work Term
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead className="text-center">
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('applications')}
                      className="h-8 w-full justify-center font-semibold"
                    >
                      Applications
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead className="text-center">
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('chances')}
                      className="h-8 w-full justify-center font-semibold"
                    >
                      Chances
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      onClick={() => handleSort('deadline')}
                      className="h-8 w-full justify-start font-semibold"
                    >
                      Deadline
                      <ArrowUpDown className="ml-2 h-4 w-4" />
                    </Button>
                  </TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedJobs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center py-8 text-muted-foreground">
                      No jobs found matching your criteria.
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedJobs.map((job) => (
                    <TableRow key={job.job_id} className="hover:bg-muted/50">
                      <TableCell className="font-mono text-xs">{job.job_id}</TableCell>
                      <TableCell className="font-medium max-w-[200px] truncate">{job.title}</TableCell>
                      <TableCell>{job.company}</TableCell>
                      <TableCell>{job.location || 'N/A'}</TableCell>
                      <TableCell>{job.work_term_duration || 'N/A'}</TableCell>
                      <TableCell className="text-center">
                        <Badge variant="secondary">
                          {job.openings} / {job.applications}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        {job.chances ? (
                          <Badge 
                            variant={job.chances >= 0.3 ? 'default' : 'secondary'}
                          >
                            {(job.chances * 100).toFixed(0)}%
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground text-sm">N/A</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1 text-sm">
                          <Calendar className="h-3 w-3 text-muted-foreground" />
                          {formatDate(job.deadline)}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => setSelectedJob(job)}
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-3xl max-h-[90vh]">
                            <DialogHeader>
                              <DialogTitle className="text-2xl">{job.title}</DialogTitle>
                              <DialogDescription className="text-lg">{job.company}</DialogDescription>
                            </DialogHeader>
                            <ScrollArea className="max-h-[70vh] pr-4">
                              <div className="space-y-6">
                                {/* Quick Info Grid */}
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                      <MapPin className="h-4 w-4" />
                                      Location
                                    </div>
                                    <div className="font-medium">{job.location || 'N/A'}</div>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                      <Briefcase className="h-4 w-4" />
                                      Work Term
                                    </div>
                                    <div className="font-medium">{job.work_term_duration || 'N/A'}</div>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                      <DollarSign className="h-4 w-4" />
                                      Compensation
                                    </div>
                                    <div className="font-medium">{job.compensation_raw || 'N/A'}</div>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                      <Users className="h-4 w-4" />
                                      Openings
                                    </div>
                                    <div className="font-medium">{job.openings} openings</div>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                      <Target className="h-4 w-4" />
                                      Applications
                                    </div>
                                    <div className="font-medium">{job.applications} applied</div>
                                  </div>
                                  <div className="space-y-1">
                                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                      <Calendar className="h-4 w-4" />
                                      Deadline
                                    </div>
                                    <div className="font-medium">{formatDate(job.deadline)}</div>
                                  </div>
                                </div>

                                {/* Job ID */}
                                {job.job_id && (
                                  <div>
                                    <h3 className="font-semibold text-sm text-muted-foreground mb-2">Job ID</h3>
                                    <code className="text-sm bg-muted px-2 py-1 rounded">{job.job_id}</code>
                                  </div>
                                )}

                                {/* Division */}
                                {job.division && (
                                  <div>
                                    <h3 className="font-semibold text-sm text-muted-foreground mb-2">Division</h3>
                                    <p className="text-sm">{job.division}</p>
                                  </div>
                                )}

                                {/* Level */}
                                {job.level && (
                                  <div>
                                    <h3 className="font-semibold text-sm text-muted-foreground mb-2">Level</h3>
                                    <Badge>{job.level}</Badge>
                                  </div>
                                )}

                                {/* Summary */}
                                {job.summary && (
                                  <div>
                                    <h3 className="font-semibold mb-2 flex items-center gap-2">
                                      <FileText className="h-4 w-4" />
                                      Job Summary
                                    </h3>
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{job.summary}</p>
                                  </div>
                                )}

                                <Separator />

                                {/* Responsibilities */}
                                {job.responsibilities && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Responsibilities</h3>
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{job.responsibilities}</p>
                                  </div>
                                )}

                                {/* Skills */}
                                {job.skills && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Required Skills</h3>
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{job.skills}</p>
                                  </div>
                                )}

                                {/* Additional Info */}
                                {job.additional_info && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Additional Information</h3>
                                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{job.additional_info}</p>
                                  </div>
                                )}

                                <Separator />

                                {/* Employment Location Arrangement */}
                                {job.employment_location_arrangement && (
                                  <div>
                                    <h3 className="font-semibold text-sm text-muted-foreground mb-2">Work Arrangement</h3>
                                    <Badge variant="outline">{job.employment_location_arrangement}</Badge>
                                  </div>
                                )}

                                {/* Application Documents */}
                                {job.application_documents_required && job.application_documents_required.length > 0 && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Required Documents</h3>
                                    <div className="flex flex-wrap gap-2">
                                      {job.application_documents_required.map((doc, idx) => (
                                        <Badge key={idx} variant="secondary">{doc}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Targeted Degrees */}
                                {job.targeted_degrees_disciplines && job.targeted_degrees_disciplines.length > 0 && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Targeted Degrees/Disciplines</h3>
                                    <div className="flex flex-wrap gap-2">
                                      {job.targeted_degrees_disciplines.map((degree, idx) => (
                                        <Badge key={idx} variant="outline">{degree}</Badge>
                                      ))}
                                    </div>
                                  </div>
                                )}

                                {/* Compensation Details */}
                                {(job.compensation_value || job.compensation_currency || job.compensation_period) && (
                                  <div>
                                    <h3 className="font-semibold mb-2">Compensation Details</h3>
                                    <div className="space-y-1 text-sm">
                                      {job.compensation_value && (
                                        <div>
                                          <span className="text-muted-foreground">Value: </span>
                                          <span className="font-medium">${job.compensation_value}</span>
                                        </div>
                                      )}
                                      {job.compensation_currency && (
                                        <div>
                                          <span className="text-muted-foreground">Currency: </span>
                                          <span className="font-medium">{job.compensation_currency}</span>
                                        </div>
                                      )}
                                      {job.compensation_period && (
                                        <div>
                                          <span className="text-muted-foreground">Period: </span>
                                          <span className="font-medium">{job.compensation_period}</span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Metadata */}
                                <Separator />
                                <div className="text-xs text-muted-foreground space-y-1">
                                  <div>Scraped: {formatDate(job.scraped_at)}</div>
                                  {job.updated_at && <div>Updated: {formatDate(job.updated_at)}</div>}
                                  <div>Status: {job.is_active ? 'Active' : 'Inactive'}</div>
                                </div>
                              </div>
                            </ScrollArea>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious 
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  className={currentPage === 1 ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
              
              {[...Array(Math.min(5, totalPages))].map((_, idx) => {
                let pageNum
                if (totalPages <= 5) {
                  pageNum = idx + 1
                } else if (currentPage <= 3) {
                  pageNum = idx + 1
                } else if (currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + idx
                } else {
                  pageNum = currentPage - 2 + idx
                }

                return (
                  <PaginationItem key={pageNum}>
                    <PaginationLink
                      onClick={() => setCurrentPage(pageNum)}
                      isActive={currentPage === pageNum}
                      className="cursor-pointer"
                    >
                      {pageNum}
                    </PaginationLink>
                  </PaginationItem>
                )
              })}

              {totalPages > 5 && currentPage < totalPages - 2 && (
                <PaginationItem>
                  <PaginationEllipsis />
                </PaginationItem>
              )}

              <PaginationItem>
                <PaginationNext 
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  className={currentPage === totalPages ? 'pointer-events-none opacity-50' : 'cursor-pointer'}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        </div>
      )}
    </div>
  )
}
