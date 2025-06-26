"use client"

import { useState, type ChangeEvent, type FormEvent } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { UploadCloud, FileText, Loader2 } from "lucide-react"
import { classifyECG } from "@/lib/actions"

interface FileUploadFormProps {
  setPredictionResult: (result: any) => void
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  isLoading: boolean
}

export default function FileUploadForm({
  setPredictionResult,
  setIsLoading,
  setError,
  isLoading,
}: FileUploadFormProps) {
  const [file, setFile] = useState<File | null>(null)
  const [fileName, setFileName] = useState<string>("")

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const selectedFile = event.target.files[0]
      if (selectedFile.type === "text/csv" || selectedFile.name.endsWith(".csv")) {
        setFile(selectedFile)
        setFileName(selectedFile.name)
        setError(null) // Clear previous errors
      } else {
        setError("Invalid file type. Please upload a CSV file.")
        setFile(null)
        setFileName("")
      }
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!file) {
      setError("Please select a file to upload.")
      return
    }

    setIsLoading(true)
    setError(null)
    setPredictionResult(null)

    const formData = new FormData()
    formData.append("file", file)

    try {
      const result = await classifyECG(formData)
      if (result.error) {
        setError(result.error)
        if (result.preprocessing_success === false) {
          // Backend might return specific error structure
          setPredictionResult(result) // Show partial error info if available
        }
      } else {
        setPredictionResult(result)
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during file upload.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="bg-slate-800 border-slate-700 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center text-2xl text-sky-400">
          <UploadCloud className="mr-2 h-6 w-6" /> Upload ECG Data
        </CardTitle>
        <CardDescription className="text-slate-400">
          Select a CSV file containing ECG signals (e.g., MLII lead data).
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="ecg-file" className="text-slate-300">
              ECG File (CSV)
            </Label>
            <div className="flex items-center space-x-2">
              <Input
                id="ecg-file"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="text-slate-300 border-slate-600 bg-slate-700 file:text-sky-400 file:font-semibold hover:file:bg-sky-500/20"
                disabled={isLoading}
              />
            </div>
            {fileName && (
              <p className="text-sm text-slate-400 flex items-center">
                <FileText className="h-4 w-4 mr-1 text-green-400" /> Selected: {fileName}
              </p>
            )}
          </div>
          <Button type="submit" className="w-full bg-sky-500 hover:bg-sky-600 text-white" disabled={isLoading || !file}>
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Processing...
              </>
            ) : (
              "Analyze ECG"
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
