"use client"

import { useState } from "react"
import FileUploadForm from "@/components/file-upload-form"
import ResultsDisplay from "@/components/results-display"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Terminal } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

// Define the structure of the prediction result based on your Flask backend
interface PredictionResult {
  predicted_diagnosis: string
  overall_confidence: number
  total_heartbeats: number
  continuous_samples: number
  segment_distribution: {
    [key: string]: {
      segment_count: number
      percentage: number
      avg_confidence: number
    }
  }
  preprocessing_success: boolean
  majority_vote_count: number
  filename?: string
  error?: string
}

export default function HomePage() {
  const [predictionResult, setPredictionResult] = useState<PredictionResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-4 md:p-8">
      <div className="container mx-auto max-w-4xl">
        <header className="text-center mb-10">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-green-400 via-cyan-400 to-purple-500">
            ECG Signal Disease Classifier
          </h1>
          <p className="text-slate-400 mt-2 text-lg">
            Upload your ECG data (CSV format) for R-peak based analysis and disease classification.
          </p>
        </header>

        <main className="space-y-8">
          <FileUploadForm
            setPredictionResult={setPredictionResult}
            setIsLoading={setIsLoading}
            setError={setError}
            isLoading={isLoading}
          />

          {error && (
            <Alert variant="destructive">
              <Terminal className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {predictionResult && predictionResult.preprocessing_success && <ResultsDisplay result={predictionResult} />}
          {predictionResult && !predictionResult.preprocessing_success && predictionResult.error && (
            <Alert variant="destructive">
              <Terminal className="h-4 w-4" />
              <AlertTitle>Processing Error for {predictionResult.filename || "file"}</AlertTitle>
              <AlertDescription>{predictionResult.error}</AlertDescription>
            </Alert>
          )}

          <Separator className="my-8 bg-slate-700" />

          <div className="text-center mt-8 mb-4">
            <Button
              asChild
              variant="outline"
              className="border-purple-500 text-purple-400 hover:bg-purple-500/10 hover:text-purple-300"
            >
              <Link href="/chat">Have questions? Ask our AI Assistant</Link>
            </Button>
          </div>
        </main>

        <footer className="text-center mt-12 text-slate-500">
          <p>&copy; {new Date().getFullYear()} ECG Analysis Platform. All rights reserved.</p>
        </footer>
      </div>
    </div>
  )
}
