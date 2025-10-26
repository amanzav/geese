"use client"

import * as React from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  AlertCircle,
  FileText,
  Upload,
  Send
} from "lucide-react"
import { EnrichedJob } from "@/lib/types"
import { ScrollArea } from "@/components/ui/scroll-area"

export type ActionType = "generate" | "upload" | "apply"

interface BulkActionsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  actionType: ActionType
  selectedJobs: EnrichedJob[]
}

interface JobStatus {
  jobId: string
  jobTitle: string
  status: "pending" | "processing" | "success" | "error"
  message?: string
}

const actionConfig = {
  generate: {
    title: "Generate Cover Letters",
    description: "Creating personalized cover letters using AI",
    icon: FileText,
    successMessage: "Cover letters generated successfully",
    actionVerb: "Generating",
  },
  upload: {
    title: "Upload to WaterlooWorks",
    description: "Uploading cover letters to your WaterlooWorks account",
    icon: Upload,
    successMessage: "Cover letters uploaded successfully",
    actionVerb: "Uploading",
  },
  apply: {
    title: "Apply to Jobs",
    description: "Submitting applications to selected positions",
    icon: Send,
    successMessage: "Applications submitted successfully",
    actionVerb: "Applying",
  },
}

export function BulkActionsDialog({
  open,
  onOpenChange,
  actionType,
  selectedJobs,
}: BulkActionsDialogProps) {
  const [isProcessing, setIsProcessing] = React.useState(false)
  const [jobStatuses, setJobStatuses] = React.useState<JobStatus[]>([])
  const [currentIndex, setCurrentIndex] = React.useState(0)

  const config = actionConfig[actionType]
  const Icon = config.icon

  React.useEffect(() => {
    if (open && selectedJobs.length > 0) {
      // Initialize job statuses
      setJobStatuses(
        selectedJobs.map((job) => ({
          jobId: job.id,
          jobTitle: job.title,
          status: "pending",
        }))
      )
      setCurrentIndex(0)
      setIsProcessing(false)
    }
  }, [open, selectedJobs])

  const handleStart = async () => {
    setIsProcessing(true)
    
    // Simulate processing each job
    for (let i = 0; i < selectedJobs.length; i++) {
      setCurrentIndex(i)
      
      // Update status to processing
      setJobStatuses((prev) =>
        prev.map((status, idx) =>
          idx === i ? { ...status, status: "processing" } : status
        )
      )

      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1500))

      // Randomly succeed or fail for demo (90% success rate)
      const success = Math.random() > 0.1

      setJobStatuses((prev) =>
        prev.map((status, idx) =>
          idx === i
            ? {
                ...status,
                status: success ? "success" : "error",
                message: success
                  ? undefined
                  : "Failed to process. Please try again.",
              }
            : status
        )
      )
    }

    setIsProcessing(false)
  }

  const handleClose = () => {
    if (!isProcessing) {
      onOpenChange(false)
    }
  }

  const successCount = jobStatuses.filter((s) => s.status === "success").length
  const errorCount = jobStatuses.filter((s) => s.status === "error").length
  const progress = (currentIndex / selectedJobs.length) * 100
  const isComplete = currentIndex === selectedJobs.length && !isProcessing

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Icon className="h-5 w-5" />
            {config.title}
          </DialogTitle>
          <DialogDescription>{config.description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Summary Stats */}
          <div className="flex items-center gap-4 p-4 bg-muted rounded-lg">
            <div className="flex-1">
              <div className="text-sm text-muted-foreground">Total Jobs</div>
              <div className="text-2xl font-bold">{selectedJobs.length}</div>
            </div>
            {isProcessing || isComplete ? (
              <>
                <div className="flex-1">
                  <div className="text-sm text-muted-foreground">Success</div>
                  <div className="text-2xl font-bold text-green-600">
                    {successCount}
                  </div>
                </div>
                {errorCount > 0 && (
                  <div className="flex-1">
                    <div className="text-sm text-muted-foreground">Failed</div>
                    <div className="text-2xl font-bold text-red-600">
                      {errorCount}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>

          {/* Progress Bar */}
          {isProcessing && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  {config.actionVerb}... {currentIndex + 1} of{" "}
                  {selectedJobs.length}
                </span>
                <span className="font-medium">{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {/* Job Status List */}
          {(isProcessing || isComplete) && (
            <ScrollArea className="h-[300px] rounded-md border p-4">
              <div className="space-y-2">
                {jobStatuses.map((status, idx) => (
                  <div
                    key={status.jobId}
                    className="flex items-start gap-3 p-3 rounded-lg bg-muted/50"
                  >
                    <div className="mt-0.5">
                      {status.status === "pending" && (
                        <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
                      )}
                      {status.status === "processing" && (
                        <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
                      )}
                      {status.status === "success" && (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      )}
                      {status.status === "error" && (
                        <XCircle className="h-5 w-5 text-red-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">
                        {status.jobTitle}
                      </div>
                      {status.message && (
                        <div className="text-sm text-muted-foreground">
                          {status.message}
                        </div>
                      )}
                    </div>
                    <Badge
                      variant={
                        status.status === "success"
                          ? "default"
                          : status.status === "error"
                          ? "destructive"
                          : "secondary"
                      }
                      className="shrink-0"
                    >
                      {status.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Pre-start View */}
          {!isProcessing && !isComplete && (
            <div className="space-y-3">
              <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                <AlertCircle className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                <div className="text-sm text-blue-900 dark:text-blue-100">
                  <div className="font-medium mb-1">Ready to proceed?</div>
                  <div>
                    This will {config.actionVerb.toLowerCase()} for{" "}
                    {selectedJobs.length} selected job
                    {selectedJobs.length > 1 ? "s" : ""}. This process may take
                    a few minutes.
                  </div>
                </div>
              </div>

              {/* Preview first few jobs */}
              <div className="text-sm font-medium text-muted-foreground">
                Selected Jobs:
              </div>
              <div className="space-y-1">
                {selectedJobs.slice(0, 5).map((job) => (
                  <div
                    key={job.id}
                    className="flex items-center gap-2 text-sm p-2 rounded bg-muted/50"
                  >
                    <Badge className="bg-green-500">
                      {job.match.fit_score.toFixed(0)}%
                    </Badge>
                    <span className="font-medium">{job.title}</span>
                    <span className="text-muted-foreground">at {job.company}</span>
                  </div>
                ))}
                {selectedJobs.length > 5 && (
                  <div className="text-sm text-muted-foreground pl-2">
                    + {selectedJobs.length - 5} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Completion Message */}
          {isComplete && (
            <div className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
              <div className="text-sm text-green-900 dark:text-green-100">
                <div className="font-medium">{config.successMessage}</div>
                <div>
                  Successfully processed {successCount} of {selectedJobs.length}{" "}
                  jobs
                  {errorCount > 0 && ` (${errorCount} failed)`}.
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          {!isProcessing && !isComplete && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleStart}>
                <Icon className="mr-2 h-4 w-4" />
                Start {config.actionVerb}
              </Button>
            </>
          )}
          {isProcessing && (
            <Button disabled>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </Button>
          )}
          {isComplete && (
            <Button onClick={handleClose}>
              Close
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
