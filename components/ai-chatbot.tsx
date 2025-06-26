"use client"

import type React from "react"
import { useChat } from "ai/react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Bot, User, Send, Loader2, Heart, Activity, AlertCircle, RefreshCw } from "lucide-react"
import { useEffect, useState } from "react"

interface AiChatbotProps {
  predictedDisease?: string
}

const GENERAL_PROMPTS = [
  "What is an ECG and how does it work?",
  "What are common signs of heart problems?",
  "How can I maintain good heart health?",
  "What does irregular heartbeat mean?",
  "When should I see a cardiologist?",
  "What are the different types of arrhythmias?"
]

const DISEASE_SPECIFIC_PROMPTS: Record<string, string[]> = {
  "Atrial Fibrillation": [
    "What is atrial fibrillation?",
    "What are the symptoms of AFib?",
    "How is atrial fibrillation treated?",
    "What lifestyle changes help with AFib?"
  ],
  "Ventricular Tachycardia": [
    "What is ventricular tachycardia?",
    "How serious is VT?",
    "What causes ventricular tachycardia?",
    "What are the treatment options for VT?"
  ],
  "Bradycardia": [
    "What is bradycardia?",
    "What causes slow heart rate?",
    "When is bradycardia dangerous?",
    "How is bradycardia treated?"
  ],
  "Normal": [
    "What does a normal ECG look like?",
    "How can I maintain heart health?",
    "What heart health screenings should I get?",
    "Are there any lifestyle tips for heart health?"
  ]
}

export default function AiChatbot({ predictedDisease }: AiChatbotProps) {
  const [showPrompts, setShowPrompts] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  const systemMessage = predictedDisease
    ? `You are a helpful medical assistant specializing in cardiology and ECG analysis. A user has received a potential ECG diagnosis of "${predictedDisease}". Answer their questions clearly and concisely. Provide information about symptoms, causes, treatments, and lifestyle advice related to heart conditions. Always remind users that this information is for educational purposes only and they should consult with healthcare professionals for personalized medical advice. If asked about something outside your expertise, politely state that you are specialized in heart-related queries.`
    : `You are a helpful medical assistant specializing in cardiology and ECG analysis. Answer user questions clearly and concisely about ECG signals, heart conditions, symptoms, causes, and treatments. Always remind users that this information is for educational purposes only and they should consult with healthcare professionals for personalized medical advice. If asked about something outside your expertise, politely state that you are specialized in heart-related queries.`

  const initialMessages = predictedDisease
    ? [
        {
          id: "initial-bot-message",
          role: "assistant" as const,
          content: `I see a diagnosis of "${predictedDisease}" has been detected from your ECG. I'm here to help you understand this condition and answer any questions you might have. 

Please remember that this information is for educational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for personalized medical guidance.

How can I help you today?`,
        },
      ]
    : [
        {
          id: "initial-bot-message-general",
          role: "assistant" as const,
          content: "Hello! I'm your AI Medical Assistant specializing in cardiology and ECG analysis. I can help you understand heart conditions, ECG readings, symptoms, and general heart health information.\n\nPlease remember that this information is for educational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for personalized medical guidance.\n\nHow can I help you today?",
        },
      ]

  const { messages, input, handleInputChange, handleSubmit, isLoading, setMessages, setInput, reload } = useChat({
    api: "/api/chat",
    initialMessages: initialMessages,
    body: {
      systemMessage: systemMessage,
    },
    onError: (error) => {
      console.error('Chat error:', error)
      setError(error.message || 'An error occurred while processing your request')
    },
    onResponse: (response) => {
      if (!response.ok) {
        console.error('Chat response error:', response.status, response.statusText)
      }
    },
    onFinish: () => {
      setError(null) // Clear error on successful completion
    }
  })

  useEffect(() => {
    if (predictedDisease) {
      setMessages([
        {
          id: "initial-bot-message-" + predictedDisease,
          role: "assistant",
          content: `I see a diagnosis of "${predictedDisease}" has been detected from your ECG. I'm here to help you understand this condition and answer any questions you might have. 

Please remember that this information is for educational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for personalized medical guidance.

How can I help you today?`,
        },
      ])
    } else {
      setMessages([
        {
          id: "initial-bot-message-general",
          role: "assistant",
          content: "Hello! I'm your AI Medical Assistant specializing in cardiology and ECG analysis. I can help you understand heart conditions, ECG readings, symptoms, and general heart health information.\n\nPlease remember that this information is for educational purposes only and should not replace professional medical advice. Always consult with your healthcare provider for personalized medical guidance.\n\nHow can I help you today?",
        },
      ])
    }
    setShowPrompts(true)
    setError(null)
  }, [predictedDisease, setMessages])

  const handlePromptClick = (prompt: string) => {
    setInput(prompt)
    setShowPrompts(false)
  }

  const getRelevantPrompts = () => {
    if (predictedDisease && DISEASE_SPECIFIC_PROMPTS[predictedDisease]) {
      return DISEASE_SPECIFIC_PROMPTS[predictedDisease]
    }
    return GENERAL_PROMPTS
  }

  const hasUserMessages = messages.some(m => m.role === "user")

  const handleRetry = () => {
    setError(null)
    reload()
  }

  return (
    <Card className="bg-slate-800 border-slate-700 shadow-xl">
      <CardHeader>
        <CardTitle className="flex items-center text-2xl text-purple-400">
          <Bot className="mr-2 h-6 w-6" /> AI Medical Assistant
        </CardTitle>
        <CardDescription className="text-slate-400">
          {predictedDisease 
            ? `Get information about ${predictedDisease} and related heart conditions`
            : "Ask questions about ECG, heart conditions, and cardiovascular health"
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col h-[500px]">
          <ScrollArea className="flex-grow p-4 border border-slate-700 rounded-md bg-slate-850 mb-4">
            {messages.map((m) => (
              <div key={m.id} className={`flex mb-4 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                {m.role === "assistant" && <Bot className="h-8 w-8 text-purple-400 mr-2 flex-shrink-0" />}
                <div
                  className={`p-3 rounded-lg max-w-[80%] ${
                    m.role === "user" ? "bg-sky-600 text-white" : "bg-slate-700 text-slate-200"
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{m.content}</p>
                </div>
                {m.role === "user" && <User className="h-8 w-8 text-sky-400 ml-2 flex-shrink-0" />}
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start mb-4">
                <Bot className="h-8 w-8 text-purple-400 mr-2 flex-shrink-0" />
                <div className="p-3 rounded-lg bg-slate-700 text-slate-200">
                  <Loader2 className="h-5 w-5 animate-spin text-slate-400" />
                </div>
              </div>
            )}
            
            {/* Error display */}
            {error && (
              <div className="mb-4 p-3 bg-red-900/20 border border-red-700/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center text-red-400 text-sm">
                    <AlertCircle className="h-4 w-4 mr-2 flex-shrink-0" />
                    <span>{error}</span>
                  </div>
                  <Button
                    onClick={handleRetry}
                    size="sm"
                    variant="outline"
                    className="ml-2 text-red-400 border-red-700 hover:bg-red-900/20"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    Retry
                  </Button>
                </div>
              </div>
            )}
            
            {/* Suggested Prompts */}
            {showPrompts && !hasUserMessages && (
              <div className="mt-4 p-4 bg-slate-750 rounded-lg border border-slate-600">
                <div className="flex items-center mb-3">
                  <Heart className="h-5 w-5 text-red-400 mr-2" />
                  <h3 className="text-slate-300 font-medium">Suggested Questions:</h3>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {getRelevantPrompts().map((prompt, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      className="text-left justify-start h-auto p-3 bg-slate-700 border-slate-600 hover:bg-slate-600 text-slate-300 hover:text-white"
                      onClick={() => handlePromptClick(prompt)}
                    >
                      <Activity className="h-4 w-4 mr-2 flex-shrink-0" />
                      <span className="text-sm">{prompt}</span>
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </ScrollArea>
          
          {/* Medical Disclaimer */}
          <div className="mb-3 p-2 bg-amber-900/20 border border-amber-700/50 rounded-md">
            <div className="flex items-center text-amber-400 text-xs">
              <AlertCircle className="h-3 w-3 mr-1 flex-shrink-0" />
              <span>For educational purposes only. Consult healthcare professionals for medical advice.</span>
            </div>
          </div>
          
          <form onSubmit={handleSubmit} className="flex items-center space-x-2">
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder="Ask about your ECG results or heart health..."
              className="flex-grow text-slate-300 border-slate-600 bg-slate-700 focus:ring-purple-500 focus:border-purple-500"
              disabled={isLoading}
            />
            <Button
              type="submit"
              className="bg-purple-500 hover:bg-purple-600 text-white"
              disabled={isLoading || !input.trim()}
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  )
}