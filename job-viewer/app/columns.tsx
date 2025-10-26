"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { EnrichedJob } from "@/lib/types"

const getFitScoreColor = (score: number) => {
  if (score >= 70) return "bg-green-500 hover:bg-green-600"
  if (score >= 50) return "bg-yellow-500 hover:bg-yellow-600"
  return "bg-red-500 hover:bg-red-600"
}

const getCompensationDisplay = (job: EnrichedJob) => {
  if (!job.compensation.value) return "N/A"
  return `$${job.compensation.value}/${job.compensation.time_period || "hr"}`
}

export const columns: ColumnDef<EnrichedJob>[] = [
  {
    id: "select",
    header: ({ table }) => (
      <Checkbox
        checked={
          table.getIsAllPageRowsSelected() ||
          (table.getIsSomePageRowsSelected() && "indeterminate")
        }
        onCheckedChange={(value: boolean) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value: boolean) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: "match.fit_score",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Fit Score
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const score = row.original.match.fit_score
      return (
        <Badge className={getFitScoreColor(score)}>
          {score.toFixed(1)}%
        </Badge>
      )
    },
    sortingFn: (rowA, rowB) => {
      return rowA.original.match.fit_score - rowB.original.match.fit_score
    },
  },
  {
    accessorKey: "title",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Job Title
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      return <div className="font-medium">{row.getValue("title")}</div>
    },
  },
  {
    accessorKey: "company",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Company
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      return <div>{row.getValue("company")}</div>
    },
  },
  {
    accessorKey: "compensation.value",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Pay
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      return (
        <div className="font-semibold">
          {getCompensationDisplay(row.original)}
        </div>
      )
    },
    sortingFn: (rowA, rowB) => {
      const aVal = rowA.original.compensation.value || 0
      const bVal = rowB.original.compensation.value || 0
      return aVal - bVal
    },
  },
  {
    accessorKey: "location",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Location
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      return <Badge variant="outline">{row.getValue("location")}</Badge>
    },
  },
  {
    accessorKey: "match.missing_technologies",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Missing Skills
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const missingTechs = row.original.match.missing_technologies
      const missingMustHaves = row.original.match.missing_must_haves

      return (
        <div className="flex flex-col gap-1">
          {missingMustHaves > 0 && (
            <Badge variant="destructive" className="w-fit">
              {missingMustHaves} must-have
            </Badge>
          )}
          {missingTechs.length > 0 ? (
            <div className="text-sm text-muted-foreground">
              {missingTechs.slice(0, 3).join(", ")}
              {missingTechs.length > 3 && ` +${missingTechs.length - 3} more`}
            </div>
          ) : (
            <Badge variant="secondary" className="w-fit">All skills matched</Badge>
          )}
        </div>
      )
    },
    sortingFn: (rowA, rowB) => {
      return (
        rowA.original.match.missing_technologies.length -
        rowB.original.match.missing_technologies.length
      )
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const job = row.original

      return (
        <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm">
              Details
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="text-2xl">{job.title}</DialogTitle>
              <DialogDescription>
                {job.company} - {job.location}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">
                    Fit Score
                  </div>
                  <Badge className={getFitScoreColor(job.match.fit_score)}>
                    {job.match.fit_score.toFixed(1)}%
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    Compensation
                  </div>
                  <div className="font-semibold">
                    {getCompensationDisplay(job)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    Applications
                  </div>
                  <div className="font-semibold">{job.applications}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Openings</div>
                  <div className="font-semibold">{job.openings}</div>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">
                    Skill Match
                  </div>
                  <div className="font-semibold">
                    {job.match.skill_match.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Coverage</div>
                  <div className="font-semibold">
                    {job.match.coverage.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    Keyword Match
                  </div>
                  <div className="font-semibold">
                    {job.match.keyword_match.toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">
                    Must-Have Skills
                  </div>
                  <div className="font-semibold">
                    {job.match.must_have_skills - job.match.missing_must_haves}/
                    {job.match.must_have_skills}
                  </div>
                </div>
              </div>

              {job.match.matched_technologies.length > 0 && (
                <div>
                  <div className="text-sm font-semibold mb-2">
                    Matched Technologies ({job.match.matched_technologies.length}
                    )
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {job.match.matched_technologies.map((tech) => (
                      <Badge key={tech} variant="secondary">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {job.match.missing_technologies.length > 0 && (
                <div>
                  <div className="text-sm font-semibold mb-2">
                    Missing Technologies ({job.match.missing_technologies.length}
                    )
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {job.match.missing_technologies.map((tech) => (
                      <Badge key={tech} variant="destructive">
                        {tech}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {job.match.matched_bullets.length > 0 && (
                <div>
                  <div className="text-sm font-semibold mb-2">
                    Top Matched Resume Points
                  </div>
                  <ul className="space-y-2">
                    {job.match.matched_bullets.slice(0, 5).map((bullet, i) => (
                      <li key={i} className="text-sm">
                        <span className="text-muted-foreground">
                          {(bullet.similarity * 100).toFixed(0)}%
                        </span>{" "}
                        - {bullet.text}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div>
                <div className="text-sm font-semibold mb-2">Job Summary</div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {job.summary}
                </p>
              </div>

              <div>
                <div className="text-sm font-semibold mb-2">
                  Required Skills
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {job.skills}
                </p>
              </div>

              <div>
                <div className="text-sm font-semibold mb-2">
                  Responsibilities
                </div>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                  {job.responsibilities}
                </p>
              </div>

              <div className="pt-4 border-t">
                <div className="text-sm text-muted-foreground">
                  Deadline: {job.deadline}
                </div>
                <div className="text-sm text-muted-foreground">
                  Work Term: {job.work_term_duration}
                </div>
                <div className="text-sm text-muted-foreground">
                  Arrangement: {job.employment_location_arrangement}
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )
    },
  },
]
