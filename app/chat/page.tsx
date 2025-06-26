"use client"

import AiChatbot from "@/components/ai-chatbot"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowLeft } from "lucide-react"

export default function ChatPage() {
  // On a separate page, the chatbot won't automatically know the
  // predictedDisease from the main page unless we pass it via
  // query params or use global state.
  // For simplicity, we'll let AiChatbot use its default prompt.
  // The AiChatbot component is already designed to handle an undefined predictedDisease.

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-4 md:p-8">
      <div className="container mx-auto max-w-3xl">
        <div className="mb-6">
          <Button
            asChild
            variant="outline"
            className="border-slate-600 text-slate-300 hover:bg-slate-700/50 hover:text-slate-200"
          >
            <Link href="/">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Classifier
            </Link>
          </Button>
        </div>

        <header className="text-center mb-8">
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-sky-400 via-purple-400 to-pink-500">
            AI Medical Assistant
          </h1>
          <p className="text-slate-400 mt-2 text-lg">
            Ask questions about ECG signals, heart conditions, symptoms, and treatments.
          </p>
        </header>

        <main>
          <AiChatbot />
          {/*
            If you want to pass context like predictedDisease here, you could use:
            1. URL Query Parameters: e.g., /chat?disease=Arrhythmia
               - Modify AiChatbot to read from useSearchParams()
            2. Global State (Context API, Zustand, etc.)
               - Update state on main page, read state here.
            For now, AiChatbot will use its general prompt.
          */}
        </main>

        <footer className="text-center mt-12 text-slate-500">
          <p>&copy; {new Date().getFullYear()} ECG Analysis Platform. All rights reserved.</p>
        </footer>
      </div>
    </div>
  )
}
