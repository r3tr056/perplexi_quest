"use client"

import * as React from "react"
import { Search, Sparkles, TrendingUp, Clock, BookOpen, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const recentResearch = [
  {
    id: 1,
    title: "Climate Change Impact Analysis",
    description: "Comprehensive analysis of global climate patterns and their socioeconomic implications",
    status: "completed",
    date: "2 hours ago",
    tags: ["Climate", "Environment", "Analysis"],
  },
  {
    id: 2,
    title: "AI Ethics in Healthcare",
    description: "Exploring ethical considerations in AI-driven medical diagnosis and treatment",
    status: "in-progress",
    date: "1 day ago",
    tags: ["AI", "Healthcare", "Ethics"],
  },
  {
    id: 3,
    title: "Quantum Computing Applications",
    description: "Survey of current and potential applications of quantum computing in various industries",
    status: "completed",
    date: "3 days ago",
    tags: ["Quantum", "Computing", "Technology"],
  },
]

const trendingTopics = [
  "Artificial General Intelligence",
  "Sustainable Energy Solutions",
  "Gene Therapy Advances",
  "Space Exploration Technologies",
  "Blockchain Applications",
]

export function HomePage() {
  const [searchQuery, setSearchQuery] = React.useState("")

  const handleStartResearch = () => {
    if (searchQuery.trim()) {
      window.location.href = `/new-research?q=${encodeURIComponent(searchQuery)}`
    } else {
      window.location.href = "/new-research"
    }
  }

  return (
    <div className="flex-1 p-8 max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-semibold text-white mb-4">Welcome to PerplexiQuest</h1>
        <p className="text-xl text-slate-400 mb-8 max-w-2xl mx-auto">
          Advanced AI-powered research platform that helps you discover, analyze, and synthesize information from across
          the web
        </p>

        {/* Search Bar */}
        <div className="max-w-2xl mx-auto mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-slate-500" />
            <Input
              placeholder="What would you like to research today?"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleStartResearch()}
              className="pl-12 pr-32 py-4 text-lg bg-slate-800/30 border-slate-700/50 text-white placeholder:text-slate-500 rounded-xl"
            />
            <Button
              onClick={handleStartResearch}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-cyan-600 hover:bg-cyan-700 text-white px-6"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Research
            </Button>
          </div>
          <div className="flex items-center justify-center gap-2 mt-3 text-sm text-slate-500">
            <span>Press</span>
            <kbd className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded text-xs">Ctrl</kbd>
            <span>+</span>
            <kbd className="px-2 py-1 bg-slate-800/50 border border-slate-700/50 rounded text-xs">K</kbd>
            <span>for quick search</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Research */}
        <div className="lg:col-span-2">
          <div className="flex items-center gap-2 mb-6">
            <Clock className="h-5 w-5 text-slate-400" />
            <h2 className="text-xl font-medium text-white">Recent Research</h2>
          </div>

          <div className="space-y-4">
            {recentResearch.map((research) => (
              <Card
                key={research.id}
                className="bg-slate-800/30 border-slate-700/50 hover:bg-slate-800/50 transition-colors cursor-pointer"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <CardTitle className="text-lg font-medium text-white">{research.title}</CardTitle>
                    <Badge
                      variant={research.status === "completed" ? "default" : "secondary"}
                      className={
                        research.status === "completed"
                          ? "bg-green-600/20 text-green-400 border-green-600/30"
                          : "bg-yellow-600/20 text-yellow-400 border-yellow-600/30"
                      }
                    >
                      {research.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  <p className="text-slate-400 mb-3 line-clamp-2">{research.description}</p>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-2">
                      {research.tags.map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs border-slate-600/50 text-slate-400">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                    <span className="text-sm text-slate-500">{research.date}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Trending Topics */}
        <div>
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="h-5 w-5 text-slate-400" />
            <h2 className="text-xl font-medium text-white">Trending Topics</h2>
          </div>

          <Card className="bg-slate-800/30 border-slate-700/50 mb-6">
            <CardContent className="p-6">
              <div className="space-y-3">
                {trendingTopics.map((topic, index) => (
                  <button
                    key={topic}
                    onClick={() => setSearchQuery(topic)}
                    className="flex items-center gap-3 w-full text-left p-3 rounded-lg hover:bg-slate-700/30 transition-colors group"
                  >
                    <span className="text-sm font-medium text-slate-500 w-6">#{index + 1}</span>
                    <span className="text-slate-300 group-hover:text-white transition-colors">{topic}</span>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-slate-800/30 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
                <Zap className="h-5 w-5" />
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="ghost"
                className="w-full justify-start text-slate-300 hover:text-white hover:bg-slate-700/30"
              >
                <BookOpen className="h-4 w-4 mr-3" />
                Browse Templates
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start text-slate-300 hover:text-white hover:bg-slate-700/30"
              >
                <Search className="h-4 w-4 mr-3" />
                Advanced Search
              </Button>
              <Button
                variant="ghost"
                className="w-full justify-start text-slate-300 hover:text-white hover:bg-slate-700/30"
              >
                <TrendingUp className="h-4 w-4 mr-3" />
                Analytics Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
