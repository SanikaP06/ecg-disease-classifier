// app/api/chat/route.ts
import { google } from "@ai-sdk/google"
import { streamText } from "ai"
import { NextRequest, NextResponse } from "next/server"

export const runtime = "edge"

export async function GET() {
  return NextResponse.json({ 
    message: "Chat API is working!",
    timestamp: new Date().toISOString(),
    hasApiKey: !!process.env.GOOGLE_GENERATIVE_AI_API_KEY
  })
}

export async function POST(request: NextRequest) {
  try {
    console.log("Chat API POST request received")
    
    const body = await request.json()
    console.log("Request body:", JSON.stringify(body, null, 2))
    
    const { messages, systemMessage } = body

    // Validate required data
    if (!messages || !Array.isArray(messages)) {
      console.error("Invalid messages:", messages)
      return NextResponse.json(
        { error: "Messages are required and must be an array" },
        { status: 400 }
      )
    }

    // Check if Google API key is configured
    if (!process.env.GOOGLE_GENERATIVE_AI_API_KEY) {
      console.error("Google API key not configured")
      return NextResponse.json(
        { error: "Google API key not configured. Please add GOOGLE_GENERATIVE_AI_API_KEY to your .env.local file" },
        { status: 500 }
      )
    }

    console.log("Calling Google AI with", messages.length, "messages")

    const result = await streamText({
      model: google("gemini-1.5-flash"),
      system: systemMessage || `You are a helpful AI medical assistant specializing in cardiology and ECG analysis. 
      Provide clear, educational information about heart conditions and ECG readings. 
      Always remind users that this information is for educational purposes only and they should consult healthcare professionals for personalized medical advice.`,
      messages,
      temperature: 0.7,
      maxTokens: 1000,
    })

    console.log("Successfully created stream response")
    return result.toDataStreamResponse()
    
  } catch (error: any) {
    console.error("API Error Details:", {
      message: error.message,
      stack: error.stack,
      name: error.name
    })
    
    // Handle specific error types
    if (error.message?.includes('API key') || error.message?.includes('authentication')) {
      return NextResponse.json(
        { error: "API key configuration error. Please check your Google AI API key." },
        { status: 401 }
      )
    }
    
    if (error.message?.includes('quota') || error.message?.includes('limit')) {
      return NextResponse.json(
        { error: "API quota exceeded. Please try again later." },
        { status: 429 }
      )
    }
    
    return NextResponse.json(
      { 
        error: "Internal server error", 
        details: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
      },
      { status: 500 }
    )
  }
}