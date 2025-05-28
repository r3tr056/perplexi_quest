"use client"

import * as React from "react"
import { Search, Calendar, Download, Share2, Trash2, Eye, MoreHorizontal } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const researchHistory = [
  {
    id: 1,
    title: "Climate Change Impact Analysis",
    description:
      "Comprehensive analysis of global climate patterns and their socioeconomic implications across different regions",
    status: "completed",
    date: "2024-01-15",
    duration: "2h 34m",
    sources: 47,
    citations: 23,
    tags: ["Climate", "Environment", "Analysis"],
    size: "2.4 MB",
  },
  {
    id: 2,
    title: "AI Ethics in Healthcare",
    description: "Exploring ethical considerations in AI-driven medical diagnosis and treatment protocols",
    status: "completed",
    date: "2024-01-12",
    duration: "1h 52m",
    sources: 32,
    citations: 18,
    tags: ["AI", "Healthcare", "Ethics"],
    size: "1.8 MB",
  },
  {
    id: 3,
    title: "Quantum Computing Applications",
    description: "Survey of current and potential applications of quantum computing in various industries",
    status: "completed",
    date: "2024-01-10",
    duration: "3h 15m",
    sources: 56,
    citations: 31,
    tags: ["Quantum", "Computing", "Technology"],
    size: "3.1 MB",
  },
  {
    id: 4,
    title: "Sustainable Energy Solutions",
    description: "Analysis of renewable energy technologies and their implementation challenges",
    status: "archived",
    date: "2024-01-08",
    duration: "2h 18m",
    sources: 41,
    citations: 19,
    tags: ["Energy", "Sustainability", "Technology"],
    size: "2.2 MB",
  },
  {
    id: 5,
    title: "Blockchain in Supply Chain",
    description: "Investigating blockchain applications for supply chain transparency and efficiency",
    status: "completed",
    date: "2024-01-05",
    duration: "1h 45m",
    sources: 28,
    citations: 15,
    tags: ["Blockchain", "Supply Chain", "Technology"],
    size: "1.6 MB",
  },
]

export function HistoryPage() {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [statusFilter, setStatusFilter] = React.useState("all")
  const [sortBy, setSortBy] = React.useState("date")

  const filteredHistory = researchHistory
    .filter((item) => {
      const matchesSearch =
        item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      const matchesStatus = statusFilter === "all" || item.status === statusFilter
      return matchesSearch && matchesStatus
    })
    .sort((a, b) => {
      switch (sortBy) {
        case "date":
          return new Date(b.date).getTime() - new Date(a.date).getTime()
        case "title":
          return a.title.localeCompare(b.title)
        case "duration":
          return b.duration.localeCompare(a.duration)
        default:
          return 0
      }
    })

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    })
  }

  return (
    <div className="flex-1 p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-white mb-2">Research History</h1>
        <p className="text-slate-400">View and manage your past research projects</p>
      </div>

      {/* Filters and Search */}
      <Card className="bg-slate-800/30 border-slate-700/50 mb-6">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-500" />
                <Input
                  placeholder="Search research history..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500"
                />
              </div>
            </div>

            <div className="flex gap-3">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40 bg-slate-800/50 border-slate-700/50 text-white">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Completed</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="w-40 bg-slate-800/50 border-slate-700/50 text-white">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-700">
                  <SelectItem value="date">Date</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                  <SelectItem value="duration">Duration</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Research Items */}
      <div className="space-y-4">
        {filteredHistory.map((research) => (
          <Card
            key={research.id}
            className="bg-slate-800/30 border-slate-700/50 hover:bg-slate-800/50 transition-colors"
          >
            <CardContent className="p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-medium text-white">{research.title}</h3>
                    <Badge
                      variant={research.status === "completed" ? "default" : "secondary"}
                      className={
                        research.status === "completed"
                          ? "bg-green-600/20 text-green-400 border-green-600/30"
                          : "bg-slate-600/20 text-slate-400 border-slate-600/30"
                      }
                    >
                      {research.status}
                    </Badge>
                  </div>
                  <p className="text-slate-400 mb-3 line-clamp-2">{research.description}</p>

                  <div className="flex flex-wrap gap-2 mb-4">
                    {research.tags.map((tag) => (
                      <Badge key={tag} variant="outline" className="text-xs border-slate-600/50 text-slate-400">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="bg-slate-800 border-slate-700">
                    <DropdownMenuItem className="text-slate-300 hover:bg-slate-700">
                      <Eye className="h-4 w-4 mr-2" />
                      View
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-slate-300 hover:bg-slate-700">
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-slate-300 hover:bg-slate-700">
                      <Share2 className="h-4 w-4 mr-2" />
                      Share
                    </DropdownMenuItem>
                    <DropdownMenuItem className="text-red-400 hover:bg-slate-700">
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              <div className="flex items-center justify-between text-sm text-slate-500">
                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDate(research.date)}</span>
                  </div>
                  <span>Duration: {research.duration}</span>
                  <span>{research.sources} sources</span>
                  <span>{research.citations} citations</span>
                  <span>{research.size}</span>
                </div>

                <div className="flex gap-2">
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </Button>
                  <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredHistory.length === 0 && (
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardContent className="p-12 text-center">
            <div className="text-slate-400 mb-4">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-lg">No research found</p>
              <p className="text-sm">Try adjusting your search criteria or filters</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
