"use client"

import * as React from "react"
import {
  Search,
  History,
  Settings,
  Bell,
  Brain,
  Zap,
  BookOpen,
  ExternalLink,
  Copy,
  Share2,
  Loader2,
  CheckCircle2,
  Circle,
  User,
  Home,
  Sparkles,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Separator } from "@/components/ui/separator"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarTrigger,
} from "@/components/ui/sidebar"

// Import page components
import { HomePage } from "@/components/pages/home-page"
import { NewResearchPage } from "@/components/pages/new-research-page"
import { HistoryPage } from "@/components/pages/history-page"
import { SettingsPage } from "@/components/pages/settings-page"
import { ProfilePage } from "@/components/pages/profile-page"

// Mock data
const recentProjects = [
  { id: 1, title: "Climate Change Impact Analysis", status: "completed", lastAccessed: "2 hours ago" },
  { id: 2, title: "AI Ethics in Healthcare", status: "in-progress", lastAccessed: "1 day ago" },
  { id: 3, title: "Quantum Computing Applications", status: "completed", lastAccessed: "3 days ago" },
]

const researchOutline = [
  { id: 1, title: "Executive Summary", completed: true, active: false },
  { id: 2, title: "Introduction", completed: true, active: false },
  { id: 3, title: "Current State Analysis", completed: true, active: true },
  { id: 4, title: "Key Findings", completed: false, active: false },
  { id: 5, title: "Recommendations", completed: false, active: false },
  { id: 6, title: "Conclusion", completed: false, active: false },
]

const citations = [
  {
    id: 1,
    title: "Nature Climate Change Journal",
    url: "https://nature.com/climate",
    snippet: "Recent studies show significant acceleration in global temperature rise...",
    type: "journal",
  },
  {
    id: 2,
    title: "IPCC Report 2023",
    url: "https://ipcc.ch/report",
    snippet: "The latest assessment reveals unprecedented changes in climate patterns...",
    type: "report",
  },
  {
    id: 3,
    title: "NASA Climate Data",
    url: "https://nasa.gov/climate",
    snippet: "Satellite observations confirm accelerating ice sheet loss...",
    type: "data",
  },
]

function AppSidebar({ currentPage }: { currentPage: string }) {
  return (
    <Sidebar className="border-r border-slate-700/50" style={{ backgroundColor: "hsl(180 20% 6%)" }}>
      <SidebarHeader className="border-b border-slate-700/50 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-600">
            <Brain className="h-4 w-4 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-semibold text-white">PerplexiQuest</span>
            <span className="text-xs text-slate-400">by perplexity</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        {currentPage === "home" && (
          <>
            <SidebarGroup>
              <SidebarGroupLabel className="text-slate-400">Research Outline</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {researchOutline.map((section) => (
                    <SidebarMenuItem key={section.id}>
                      <SidebarMenuButton asChild isActive={section.active} className="flex items-center gap-2">
                        <button className="flex items-center gap-2 w-full">
                          {section.completed ? (
                            <CheckCircle2 className="h-4 w-4 text-green-500" />
                          ) : (
                            <Circle className="h-4 w-4 text-slate-500" />
                          )}
                          <span className="truncate">{section.title}</span>
                        </button>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarGroup>
              <SidebarGroupLabel className="text-slate-400">Recent Projects</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {recentProjects.map((project) => (
                    <SidebarMenuItem key={project.id}>
                      <SidebarMenuButton asChild>
                        <button className="flex flex-col items-start gap-1 w-full">
                          <span className="truncate text-sm">{project.title}</span>
                          <div className="flex items-center gap-2">
                            <Badge
                              variant={project.status === "completed" ? "default" : "secondary"}
                              className="text-xs"
                            >
                              {project.status}
                            </Badge>
                            <span className="text-xs text-slate-500">{project.lastAccessed}</span>
                          </div>
                        </button>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}

        {currentPage !== "home" && (
          <SidebarGroup>
            <SidebarGroupLabel className="text-slate-400">Navigation</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <a href="/" className="flex items-center gap-2">
                      <Home className="h-4 w-4" />
                      <span>Home</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <a href="/new-research" className="flex items-center gap-2">
                      <Sparkles className="h-4 w-4" />
                      <span>New Research</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
                <SidebarMenuItem>
                  <SidebarMenuButton asChild>
                    <a href="/history" className="flex items-center gap-2">
                      <History className="h-4 w-4" />
                      <span>History</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter className="border-t border-slate-700/50 p-4">
        <div className="flex items-center gap-2">
          <div className="flex h-2 w-2 rounded-full bg-green-500"></div>
          <span className="text-xs text-slate-400">Agent Active</span>
        </div>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}

function MainHeader({ currentPage }: { currentPage: string }) {
  return (
    <header
      className="flex h-16 shrink-0 items-center gap-4 border-b border-slate-700/50 px-6"
      style={{ backgroundColor: "hsl(180 20% 8%)" }}
    >
      <SidebarTrigger className="-ml-1 text-slate-300 hover:text-white" />
      <Separator orientation="vertical" className="h-6 bg-slate-600" />

      {/* Search Bar */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-500" />
          <Input
            placeholder="Search docs"
            className="pl-10 pr-16 bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500 rounded-lg"
          />
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 bg-slate-700/50 border border-slate-600/50 rounded text-xs text-slate-400">
              Ctrl
            </kbd>
            <kbd className="px-1.5 py-0.5 bg-slate-700/50 border border-slate-600/50 rounded text-xs text-slate-400">
              K
            </kbd>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="hidden md:flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          className={`text-slate-300 hover:text-white ${currentPage === "home" ? "text-white bg-slate-700/50" : ""}`}
          asChild
        >
          <a href="/">Home</a>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={`text-slate-300 hover:text-white ${currentPage === "new-research" ? "text-white bg-slate-700/50" : ""}`}
          asChild
        >
          <a href="/new-research">New Research</a>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={`text-slate-300 hover:text-white ${currentPage === "history" ? "text-white bg-slate-700/50" : ""}`}
          asChild
        >
          <a href="/history">History</a>
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className={`text-slate-300 hover:text-white ${currentPage === "settings" ? "text-white bg-slate-700/50" : ""}`}
          asChild
        >
          <a href="/settings">Settings</a>
        </Button>
      </nav>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-3">
        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white">
          <Sparkles className="h-4 w-4 mr-2" />
          Ask AI
        </Button>

        <Button variant="outline" size="sm" className="border-slate-700/50 text-slate-300 hover:text-white">
          Playground
        </Button>

        <Button variant="ghost" size="sm" className="text-slate-300 hover:text-white">
          <Bell className="h-4 w-4" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="flex items-center gap-2">
              <Avatar className="h-6 w-6">
                <AvatarImage src="/placeholder.svg?height=24&width=24" />
                <AvatarFallback className="bg-cyan-600 text-white text-xs">JD</AvatarFallback>
              </Avatar>
              <span className="text-sm text-slate-300 hidden md:block">John Doe</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
            <DropdownMenuItem className="text-slate-300 hover:bg-slate-700" asChild>
              <a href="/profile">
                <User className="h-4 w-4 mr-2" />
                Profile
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem className="text-slate-300 hover:bg-slate-700" asChild>
              <a href="/settings">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </a>
            </DropdownMenuItem>
            <DropdownMenuItem className="text-slate-300 hover:bg-slate-700">Sign out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}

function StreamingContent() {
  const [isStreaming, setIsStreaming] = React.useState(false)
  const [content, setContent] = React.useState("")

  const simulateStreaming = () => {
    setIsStreaming(true)
    setContent("")

    const fullContent = `# Current State Analysis

## Overview
Climate change represents one of the most pressing challenges of our time. Recent data indicates that global temperatures have risen by approximately 1.1°C since pre-industrial times, with significant implications for ecosystems, human societies, and economic systems worldwide.

## Key Indicators
- **Temperature Rise**: Global average temperatures have increased consistently over the past decade
- **Sea Level Rise**: Ocean levels have risen by 21-24 cm since 1880
- **Ice Sheet Loss**: Arctic sea ice is declining at a rate of 13% per decade

## Regional Impacts
Different regions are experiencing varying degrees of climate impact, with polar regions showing the most dramatic changes...`

    let index = 0
    const interval = setInterval(() => {
      if (index < fullContent.length) {
        setContent(fullContent.slice(0, index + 1))
        index++
      } else {
        setIsStreaming(false)
        clearInterval(interval)
      }
    }, 20)
  }

  return (
    <div className="flex-1 p-6">
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-semibold text-white">Climate Change Impact Analysis</h1>
          <div className="flex items-center gap-2">
            {isStreaming && <Loader2 className="h-4 w-4 animate-spin text-cyan-500" />}
            <Badge
              variant={isStreaming ? "default" : "secondary"}
              className="bg-cyan-600/20 text-cyan-400 border-cyan-600/30"
            >
              {isStreaming ? "Researching..." : "Complete"}
            </Badge>
          </div>
        </div>

        <div className="flex items-center gap-4 mb-6">
          <Input
            placeholder="Ask a follow-up question or request specific analysis..."
            className="flex-1 bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500"
          />
          <Button onClick={simulateStreaming} disabled={isStreaming} className="bg-cyan-600 hover:bg-cyan-700">
            <Search className="h-4 w-4 mr-2" />
            Research
          </Button>
        </div>
      </div>

      <Card className="bg-slate-800/30 border-slate-700/50">
        <CardContent className="p-6">
          <div className="prose prose-invert max-w-none">
            <div className="whitespace-pre-wrap text-slate-200 leading-relaxed">
              {content}
              {isStreaming && <span className="animate-pulse">|</span>}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function CitationsPanel() {
  return (
    <div className="w-80 border-l border-slate-700/50 p-4" style={{ backgroundColor: "hsl(180 20% 8%)" }}>
      <div className="mb-4">
        <h3 className="text-lg font-medium text-white mb-2">Citations & Sources</h3>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Zap className="h-4 w-4" />
          <span>Agent Status: Active</span>
        </div>
      </div>

      <div className="space-y-3">
        {citations.map((citation) => (
          <Card key={citation.id} className="bg-slate-800/30 border-slate-700/50">
            <CardHeader className="pb-2">
              <div className="flex items-start justify-between">
                <CardTitle className="text-sm text-white">{citation.title}</CardTitle>
                <Badge variant="outline" className="text-xs border-slate-600/50 text-slate-400">
                  {citation.type}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-slate-400 mb-3 line-clamp-2">{citation.snippet}</p>
              <div className="flex items-center gap-2">
                <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-slate-400 hover:text-white">
                  <ExternalLink className="h-3 w-3 mr-1" />
                  View
                </Button>
                <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-slate-400 hover:text-white">
                  <Copy className="h-3 w-3 mr-1" />
                  Copy
                </Button>
                <Button variant="ghost" size="sm" className="h-6 px-2 text-xs text-slate-400 hover:text-white">
                  <Share2 className="h-3 w-3" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="mt-6 p-3 bg-slate-800/30 rounded-lg border border-slate-700/50">
        <div className="flex items-center gap-2 mb-2">
          <BookOpen className="h-4 w-4 text-cyan-500" />
          <span className="text-sm font-medium text-white">Research Progress</span>
        </div>
        <div className="space-y-2 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-3 w-3 text-green-500" />
            <span>Gathered 15 sources</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-3 w-3 text-green-500" />
            <span>Analyzed key findings</span>
          </div>
          <div className="flex items-center gap-2">
            <Loader2 className="h-3 w-3 animate-spin text-cyan-500" />
            <span>Synthesizing conclusions</span>
          </div>
        </div>
      </div>
    </div>
  )
}

interface PerplexiQuestAppProps {
  currentPage: string
}

export function PerplexiQuestApp({ currentPage }: PerplexiQuestAppProps) {
  const renderPageContent = () => {
    switch (currentPage) {
      case "home":
        return (
          <div className="flex flex-1">
            <StreamingContent />
            <CitationsPanel />
          </div>
        )
      case "new-research":
        return <NewResearchPage />
      case "history":
        return <HistoryPage />
      case "settings":
        return <SettingsPage />
      case "profile":
        return <ProfilePage />
      default:
        return <HomePage />
    }
  }

  return (
    <SidebarProvider>
      <div className="flex min-h-screen" style={{ backgroundColor: "hsl(180 20% 6%)" }}>
        <AppSidebar currentPage={currentPage} />
        <SidebarInset className="flex-1">
          <MainHeader currentPage={currentPage} />
          {currentPage === "home" ? renderPageContent() : <div className="flex flex-1">{renderPageContent()}</div>}
        </SidebarInset>
      </div>
    </SidebarProvider>
  )
}
