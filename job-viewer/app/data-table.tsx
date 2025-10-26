"use client"

import * as React from "react"
import {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
  VisibilityState,
  RowSelectionState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { 
  FileText, 
  Upload, 
  Send, 
  Loader2,
  CheckCircle2 
} from "lucide-react"
import { BulkActionsDialog, ActionType } from "@/components/bulk-actions-dialog"
import { EnrichedJob } from "@/lib/types"

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
}

export function DataTable<TData, TValue>({
  columns,
  data,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>([
    { id: "match.fit_score", desc: true }, // Default sort by fit score descending
  ])
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>(
    []
  )
  const [columnVisibility, setColumnVisibility] =
    React.useState<VisibilityState>({})
  const [rowSelection, setRowSelection] = React.useState<RowSelectionState>({})
  const [globalFilter, setGlobalFilter] = React.useState("")
  const [locationFilter, setLocationFilter] = React.useState("all")
  const [levelFilter, setLevelFilter] = React.useState("all")
  const [scoreFilter, setScoreFilter] = React.useState("all")
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [currentAction, setCurrentAction] = React.useState<ActionType>("generate")

  const table = useReactTable({
    data,
    columns,
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onColumnVisibilityChange: setColumnVisibility,
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: setRowSelection,
    enableRowSelection: true,
    globalFilterFn: (row, columnId, filterValue) => {
      const searchValue = filterValue.toLowerCase()
      const job = row.original as any

      // Apply search filter
      const matchesSearch = 
        job.title?.toLowerCase().includes(searchValue) ||
        job.company?.toLowerCase().includes(searchValue) ||
        job.location?.toLowerCase().includes(searchValue)

      // Apply level filter
      const matchesLevel = 
        levelFilter === "all" || job.level?.toLowerCase() === levelFilter.toLowerCase()

      // Apply score filter
      let matchesScore = true
      if (scoreFilter === "high" && job.match?.fit_score < 70) matchesScore = false
      if (scoreFilter === "medium" && (job.match?.fit_score < 50 || job.match?.fit_score >= 70)) matchesScore = false
      if (scoreFilter === "low" && job.match?.fit_score >= 50) matchesScore = false

      return matchesSearch && matchesLevel && matchesScore
    },
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      globalFilter,
      rowSelection,
    },
  })

  // Get unique locations and levels for filters
  const locations = React.useMemo(() => {
    const locs = new Set(
      data.map((item: any) => item.location).filter(Boolean)
    )
    return ["all", ...Array.from(locs).sort()]
  }, [data])

  const levels = React.useMemo(() => {
    const lvls = new Set(
      data.map((item: any) => item.level).filter(Boolean)
    )
    return ["all", ...Array.from(lvls).sort()]
  }, [data])

  // Apply location filter
  React.useEffect(() => {
    if (locationFilter === "all") {
      table.getColumn("location")?.setFilterValue(undefined)
    } else {
      table.getColumn("location")?.setFilterValue(locationFilter)
    }
  }, [locationFilter, table])

  // Get selected rows count
  const selectedRows = table.getFilteredSelectedRowModel().rows
  const selectedCount = selectedRows.length
  const selectedJobs = selectedRows.map(row => row.original as EnrichedJob)

  const handleGenerateCoverLetters = () => {
    setCurrentAction("generate")
    setDialogOpen(true)
  }

  const handleUploadCoverLetters = () => {
    setCurrentAction("upload")
    setDialogOpen(true)
  }

  const handleApplyAll = () => {
    setCurrentAction("apply")
    setDialogOpen(true)
  }

  return (
    <div className="space-y-4">
      {/* Filter Controls */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row gap-4">
          <Input
            placeholder="Search by title, company, or location..."
            value={globalFilter ?? ""}
            onChange={(event) => setGlobalFilter(event.target.value)}
            className="md:flex-1"
          />
          <Select value={locationFilter} onValueChange={setLocationFilter}>
            <SelectTrigger className="md:w-48">
              <SelectValue placeholder="Filter by location" />
            </SelectTrigger>
            <SelectContent>
              {locations.map((loc) => (
                <SelectItem key={loc} value={loc}>
                  {loc === "all" ? "All Locations" : loc}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="md:w-48">
              <SelectValue placeholder="Filter by level" />
            </SelectTrigger>
            <SelectContent>
              {levels.map((lvl) => (
                <SelectItem key={lvl} value={lvl}>
                  {lvl === "all" ? "All Levels" : lvl}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={scoreFilter} onValueChange={setScoreFilter}>
            <SelectTrigger className="md:w-48">
              <SelectValue placeholder="Filter by score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Scores</SelectItem>
              <SelectItem value="high">High (≥70%)</SelectItem>
              <SelectItem value="medium">Medium (50-69%)</SelectItem>
              <SelectItem value="low">Low (&lt;50%)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Bulk Actions Toolbar */}
        {selectedCount > 0 && (
          <Card className="p-4 bg-primary/5 border-primary">
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-base px-3 py-1">
                  {selectedCount} selected
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => table.toggleAllPageRowsSelected(false)}
                >
                  Clear selection
                </Button>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleGenerateCoverLetters}
                  className="gap-2"
                >
                  <FileText className="h-4 w-4" />
                  Generate Cover Letters
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleUploadCoverLetters}
                  className="gap-2"
                >
                  <Upload className="h-4 w-4" />
                  Upload to WaterlooWorks
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleApplyAll}
                  className="gap-2"
                >
                  <Send className="h-4 w-4" />
                  Apply to All
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  return (
                    <TableHead key={header.id}>
                      {header.isPlaceholder
                        ? null
                        : flexRender(
                            header.column.columnDef.header,
                            header.getContext()
                          )}
                    </TableHead>
                  )
                })}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && "selected"}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="h-24 text-center"
                >
                  No results.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-between px-2">
        <div className="flex-1 text-sm text-muted-foreground">
          Showing {table.getFilteredRowModel().rows.length} of {data.length}{" "}
          job(s)
        </div>
        <div className="flex items-center space-x-6 lg:space-x-8">
          <div className="flex items-center space-x-2">
            <p className="text-sm font-medium">Rows per page</p>
            <Select
              value={`${table.getState().pagination.pageSize}`}
              onValueChange={(value) => {
                table.setPageSize(Number(value))
              }}
            >
              <SelectTrigger className="h-8 w-[70px]">
                <SelectValue
                  placeholder={table.getState().pagination.pageSize}
                />
              </SelectTrigger>
              <SelectContent side="top">
                {[10, 20, 30, 40, 50].map((pageSize) => (
                  <SelectItem key={pageSize} value={`${pageSize}`}>
                    {pageSize}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="flex w-[100px] items-center justify-center text-sm font-medium">
            Page {table.getState().pagination.pageIndex + 1} of{" "}
            {table.getPageCount()}
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => table.setPageIndex(0)}
              disabled={!table.getCanPreviousPage()}
            >
              <span className="sr-only">Go to first page</span>
              {"<<"}
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <span className="sr-only">Go to previous page</span>
              {"<"}
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              <span className="sr-only">Go to next page</span>
              {">"}
            </Button>
            <Button
              variant="outline"
              className="h-8 w-8 p-0"
              onClick={() => table.setPageIndex(table.getPageCount() - 1)}
              disabled={!table.getCanNextPage()}
            >
              <span className="sr-only">Go to last page</span>
              {">>"}
            </Button>
          </div>
        </div>
      </div>

      {/* Bulk Actions Dialog */}
      <BulkActionsDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        actionType={currentAction}
        selectedJobs={selectedJobs}
      />
    </div>
  )
}
