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
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { 
  RefreshCw, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  Search
} from "lucide-react"

interface ScrapeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ScrapeDialog({ open, onOpenChange }: ScrapeDialogProps) {
  const [isProcessing, setIsProcessing] = React.useState(false)
  const [progress, setProgress] = React.useState(0)
  const [status, setStatus] = React.useState<"idle" | "scraping" | "analyzing" | "complete">("idle")
  const [maxPages, setMaxPages] = React.useState("5")
  const [minFitScore, setMinFitScore] = React.useState("50")
  const [jobsFound, setJobsFound] = React.useState(0)
  const [newMatches, setNewMatches] = React.useState(0)

  React.useEffect(() => {
    if (open) {
      // Reset state when dialog opens
      setIsProcessing(false)
      setProgress(0)
      setStatus("idle")
      setJobsFound(0)
      setNewMatches(0)
    }
  }, [open])

  const handleStart = async () => {
    setIsProcessing(true)
    setStatus("scraping")
    setProgress(0)

    // Simulate scraping process
    for (let i = 0; i <= 50; i += 10) {
      await new Promise((resolve) => setTimeout(resolve, 400))
      setProgress(i)
      if (i === 30) setJobsFound(Math.floor(Math.random() * 50) + 20)
    }

    setStatus("analyzing")
    setProgress(50)

    // Simulate analysis
    for (let i = 50; i <= 100; i += 10) {
      await new Promise((resolve) => setTimeout(resolve, 500))
      setProgress(i)
      if (i === 80) setNewMatches(Math.floor(Math.random() * 15) + 5)
    }

    setStatus("complete")
    setIsProcessing(false)
  }

  const handleClose = () => {
    if (!isProcessing) {
      onOpenChange(false)
    }
  }

  const statusMessages = {
    idle: "Configure scraping parameters",
    scraping: "Scraping WaterlooWorks for new postings...",
    analyzing: "Analyzing jobs and calculating match scores...",
    complete: "Scraping complete!",
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RefreshCw className="h-5 w-5" />
            Quick Scrape
          </DialogTitle>
          <DialogDescription>
            Scrape new job postings from WaterlooWorks and analyze matches
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Configuration */}
          {status === "idle" && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="maxPages">Maximum Pages to Scrape</Label>
                <Select value={maxPages} onValueChange={setMaxPages}>
                  <SelectTrigger id="maxPages">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 page (~50 jobs)</SelectItem>
                    <SelectItem value="3">3 pages (~150 jobs)</SelectItem>
                    <SelectItem value="5">5 pages (~250 jobs)</SelectItem>
                    <SelectItem value="10">10 pages (~500 jobs)</SelectItem>
                    <SelectItem value="0">All pages</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="minScore">Minimum Fit Score to Save</Label>
                <Select value={minFitScore} onValueChange={setMinFitScore}>
                  <SelectTrigger id="minScore">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="0">Save all (0%+)</SelectItem>
                    <SelectItem value="30">Low threshold (30%+)</SelectItem>
                    <SelectItem value="50">Medium threshold (50%+)</SelectItem>
                    <SelectItem value="70">High threshold (70%+)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                <AlertCircle className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                <div className="text-sm text-blue-900 dark:text-blue-100">
                  <div className="font-medium mb-1">Note</div>
                  <div>
                    You must be logged into WaterlooWorks. The scraper will automatically
                    match jobs against your resume and save matches to the database.
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Progress */}
          {(status === "scraping" || status === "analyzing") && (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {statusMessages[status]}
                  </span>
                  <span className="font-medium">{Math.round(progress)}%</span>
                </div>
                <Progress value={progress} className="h-2" />
              </div>

              {jobsFound > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <Search className="h-4 w-4 text-muted-foreground" />
                  <span>Found {jobsFound} new job postings</span>
                </div>
              )}

              {status === "analyzing" && (
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                  <span className="text-sm">Calculating match scores with resume embeddings...</span>
                </div>
              )}
            </div>
          )}

          {/* Complete */}
          {status === "complete" && (
            <div className="space-y-4">
              <div className="flex items-start gap-2 p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600 shrink-0 mt-0.5" />
                <div className="text-sm text-green-900 dark:text-green-100">
                  <div className="font-medium mb-1">{statusMessages.complete}</div>
                  <div>
                    Found {jobsFound} jobs, identified {newMatches} strong matches
                    (≥{minFitScore}% fit score).
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-muted rounded-lg">
                  <div className="text-sm text-muted-foreground">Jobs Scraped</div>
                  <div className="text-2xl font-bold">{jobsFound}</div>
                </div>
                <div className="p-4 bg-muted rounded-lg">
                  <div className="text-sm text-muted-foreground">New Matches</div>
                  <div className="text-2xl font-bold text-green-600">
                    {newMatches}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          {status === "idle" && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button onClick={handleStart}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Start Scraping
              </Button>
            </>
          )}
          {isProcessing && (
            <Button disabled>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Processing...
            </Button>
          )}
          {status === "complete" && (
            <Button onClick={handleClose}>
              <CheckCircle2 className="mr-2 h-4 w-4" />
              Done
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
