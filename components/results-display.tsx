import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CheckCircle, BarChart3 } from "lucide-react"

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
}

interface ResultsDisplayProps {
  result: PredictionResult
}

export default function ResultsDisplay({ result }: ResultsDisplayProps) {
  if (!result || !result.preprocessing_success) {
    return null // Error handled by parent
  }

  const confidenceColor =
    result.overall_confidence > 0.8
      ? "bg-green-500/20 text-green-300 border-green-500/50"
      : result.overall_confidence > 0.6
        ? "bg-yellow-500/20 text-yellow-300 border-yellow-500/50"
        : "bg-red-500/20 text-red-300 border-red-500/50"

  return (
    <Card className="bg-slate-800 border-slate-700 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center text-2xl text-green-400">
          <CheckCircle className="mr-2 h-6 w-6" /> Classification Result
        </CardTitle>
        {result.filename && (
          <CardDescription className="text-slate-400">Analysis for: {result.filename}</CardDescription>
        )}
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-300 mb-1">Predicted Diagnosis:</h3>
          <p className="text-2xl font-bold text-sky-300">{result.predicted_diagnosis}</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-300 mb-1">Overall Confidence:</h3>
          <Badge variant="outline" className={`text-xl px-3 py-1 ${confidenceColor}`}>
            {(result.overall_confidence * 100).toFixed(2)}%
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="bg-slate-700/50 p-3 rounded-md">
            <p className="text-slate-400">Total Heartbeats Analyzed</p>
            <p className="text-lg font-semibold text-slate-200">{result.total_heartbeats}</p>
          </div>
          <div className="bg-slate-700/50 p-3 rounded-md">
            <p className="text-slate-400">Majority Vote Count</p>
            <p className="text-lg font-semibold text-slate-200">{result.majority_vote_count}</p>
          </div>
          <div className="bg-slate-700/50 p-3 rounded-md">
            <p className="text-slate-400">Continuous Samples</p>
            <p className="text-lg font-semibold text-slate-200">{result.continuous_samples}</p>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-slate-300 mb-2 flex items-center">
            <BarChart3 className="mr-2 h-5 w-5 text-purple-400" /> Segment Distribution:
          </h3>
          <div className="overflow-x-auto rounded-md border border-slate-700">
            <Table className="bg-slate-850">
              <TableHeader className="bg-slate-700/50">
                <TableRow className="border-slate-700">
                  <TableHead className="text-slate-300">Diagnosis</TableHead>
                  <TableHead className="text-slate-300 text-right">Segments</TableHead>
                  <TableHead className="text-slate-300 text-right">Percentage</TableHead>
                  <TableHead className="text-slate-300 text-right">Avg. Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(result.segment_distribution).map(([diagnosis, data]) => (
                  <TableRow key={diagnosis} className="border-slate-700 hover:bg-slate-700/30">
                    <TableCell className="font-medium text-slate-300">{diagnosis}</TableCell>
                    <TableCell className="text-right text-slate-400">{data.segment_count}</TableCell>
                    <TableCell className="text-right text-slate-400">{data.percentage.toFixed(2)}%</TableCell>
                    <TableCell className="text-right text-slate-400">
                      {(data.avg_confidence * 100).toFixed(2)}%
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
