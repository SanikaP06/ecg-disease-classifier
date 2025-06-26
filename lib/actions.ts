"use server"

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
  filename?: string // Added for context
  error?: string // To carry over error messages
}

export async function classifyECG(formData: FormData): Promise<PredictionResult> {
  const file = formData.get("file") as File
  if (!file) {
    return {
      error: "No file provided to server action.",
      // Fill with default/error values for other fields if necessary
      predicted_diagnosis: "",
      overall_confidence: 0,
      total_heartbeats: 0,
      continuous_samples: 0,
      segment_distribution: {},
      preprocessing_success: false,
      majority_vote_count: 0,
      filename: "",
    }
  }

  const flaskBackendUrl = process.env.FLASK_BACKEND_URL || "http://localhost:5000"

  try {
    const response = await fetch(`${flaskBackendUrl}/predict`, {
      method: "POST",
      body: formData, // FormData is sent directly
    })

    if (!response.ok) {
      // Try to parse the JSON error body from Flask
      let errorMessage = `Request failed with status: ${response.status}`
      try {
        const errorData = await response.json()
        // Use the specific error from Flask if it exists
        if (errorData && errorData.error) {
          errorMessage = errorData.error
        }
      } catch (e) {
        // Could not parse JSON, stick with the status code error.
        console.error("Could not parse error JSON from backend", e)
      }

      return {
        error: errorMessage,
        filename: file.name,
        // Fill with default/error values
        predicted_diagnosis: "",
        overall_confidence: 0,
        total_heartbeats: 0,
        continuous_samples: 0,
        segment_distribution: {},
        preprocessing_success: false,
        majority_vote_count: 0,
      }
    }

    const data: PredictionResult = await response.json()
    return { ...data, filename: file.name } // Add filename for context
  } catch (error: any) {
    console.error("Error in classifyECG server action:", error)
    return {
      error: error.message || "An unexpected error occurred while communicating with the backend.",
      filename: file.name,
      // Fill with default/error values
      predicted_diagnosis: "",
      overall_confidence: 0,
      total_heartbeats: 0,
      continuous_samples: 0,
      segment_distribution: {},
      preprocessing_success: false,
      majority_vote_count: 0,
    }
  }
}
