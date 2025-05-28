"use client"

import * as React from "react"
import { Sparkles, FileText, Globe, Database, Brain, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const researchTemplates = [
  {
    id: 1,
    title: "Market Analysis",
    description: "Comprehensive market research and competitive analysis",
    icon: Globe,
    tags: ["Business", "Market", "Analysis"],
  },
  {
    id: 2,
    title: "Literature Review",
    description: "Academic literature review and synthesis",
    icon: FileText,
    tags: ["Academic", "Research", "Literature"],
  },
  {
    id: 3,
    title: "Technology Assessment",
    description: "Evaluate emerging technologies and their implications",
    icon: Brain,
    tags: ["Technology", "Innovation", "Assessment"],
  },
  {
    id: 4,
    title: "Data Analysis",
    description: "Statistical analysis and data interpretation",
    icon: Database,
    tags: ["Data", "Statistics", "Analysis"],
  },
]

export function NewResearchPage() {
  const [researchQuery, setResearchQuery] = React.useState("")
  const [researchType, setResearchType] = React.useState("")
  const [customInstructions, setCustomInstructions] = React.useState("")
  const [selectedSources, setSelectedSources] = React.useState<string[]>([])
  const [isStarting, setIsStarting] = React.useState(false)

  const sources = [
    "Academic Papers",
    "News Articles",
    "Government Reports",
    "Industry Reports",
    "Patents",
    "Books",
    "Websites",
    "Social Media",
  ]

  const handleSourceToggle = (source: string) => {
    setSelectedSources((prev) => (prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]))
  }

  const handleStartResearch = async () => {
    if (!researchQuery.trim()) return

    setIsStarting(true)
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Redirect to research workspace
    window.location.href = "/"
  }

  return (
    <div className="flex-1 p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-white mb-2">Start New Research</h1>
        <p className="text-slate-400">
          Configure your research parameters and let our AI agents gather comprehensive insights
        </p>
      </div>

      <div className="space-y-8">
        {/* Research Query */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white">Research Question</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="query" className="text-slate-300 mb-2 block">
                What would you like to research?
              </Label>
              <Textarea
                id="query"
                placeholder="Enter your research question or topic. Be as specific as possible for better results..."
                value={researchQuery}
                onChange={(e) => setResearchQuery(e.target.value)}
                className="min-h-[100px] bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500"
              />
            </div>

            <div>
              <Label htmlFor="type" className="text-slate-300 mb-2 block">
                Research Type
              </Label>
              <Select value={researchType} onValueChange={setResearchType}>
                <SelectTrigger className="bg-slate-800/50 border-slate-700/50 text-white">
                  <SelectValue placeholder="Select research type" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="comprehensive">Comprehensive Analysis</SelectItem>
                  <SelectItem value="quick">Quick Overview</SelectItem>
                  <SelectItem value="comparative">Comparative Study</SelectItem>
                  <SelectItem value="trend">Trend Analysis</SelectItem>
                  <SelectItem value="technical">Technical Deep Dive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Research Templates */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white">Research Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {researchTemplates.map((template) => (
                <button
                  key={template.id}
                  onClick={() => {
                    setResearchQuery(template.description)
                    setResearchType("comprehensive")
                  }}
                  className="p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg hover:bg-slate-700/50 transition-colors text-left group"
                >
                  <div className="flex items-start gap-3">
                    <template.icon className="h-6 w-6 text-cyan-400 mt-1" />
                    <div className="flex-1">
                      <h3 className="font-medium text-white group-hover:text-cyan-400 transition-colors">
                        {template.title}
                      </h3>
                      <p className="text-sm text-slate-400 mt-1">{template.description}</p>
                      <div className="flex gap-2 mt-2">
                        {template.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs border-slate-600/50 text-slate-400">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Source Selection */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white">Source Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {sources.map((source) => (
                <button
                  key={source}
                  onClick={() => handleSourceToggle(source)}
                  className={`p-3 rounded-lg border transition-colors text-sm ${
                    selectedSources.includes(source)
                      ? "bg-cyan-600/20 border-cyan-600/50 text-cyan-400"
                      : "bg-slate-800/50 border-slate-700/50 text-slate-300 hover:bg-slate-700/50"
                  }`}
                >
                  {source}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Custom Instructions */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white">Custom Instructions (Optional)</CardTitle>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="Add any specific instructions for the research agents..."
              value={customInstructions}
              onChange={(e) => setCustomInstructions(e.target.value)}
              className="bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500"
            />
          </CardContent>
        </Card>

        {/* Start Research Button */}
        <div className="flex justify-center">
          <Button
            onClick={handleStartResearch}
            disabled={!researchQuery.trim() || isStarting}
            className="bg-cyan-600 hover:bg-cyan-700 text-white px-8 py-3 text-lg"
          >
            {isStarting ? (
              <>
                <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                Starting Research...
              </>
            ) : (
              <>
                <Sparkles className="h-5 w-5 mr-2" />
                Start Research
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
