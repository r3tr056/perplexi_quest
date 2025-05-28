"use client"
import { Edit, Calendar, MapPin, LinkIcon, Mail, Trophy, TrendingUp, FileText, Clock } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const profileData = {
  name: "John Doe",
  email: "john.doe@example.com",
  bio: "AI researcher and data scientist passionate about leveraging technology to solve complex problems. Specializing in machine learning, natural language processing, and research automation.",
  location: "San Francisco, CA",
  website: "https://johndoe.dev",
  joinDate: "January 2024",
  avatar: "/placeholder.svg?height=120&width=120",
}

const stats = [
  { label: "Research Projects", value: "47", icon: FileText },
  { label: "Total Research Time", value: "156h", icon: Clock },
  { label: "Citations Generated", value: "1,247", icon: Trophy },
  { label: "Success Rate", value: "94%", icon: TrendingUp },
]

const recentActivity = [
  {
    id: 1,
    type: "research",
    title: "Completed Climate Change Impact Analysis",
    date: "2 hours ago",
    status: "completed",
  },
  {
    id: 2,
    type: "research",
    title: "Started AI Ethics in Healthcare research",
    date: "1 day ago",
    status: "in-progress",
  },
  {
    id: 3,
    type: "achievement",
    title: "Reached 1,000 citations milestone",
    date: "3 days ago",
    status: "achievement",
  },
  {
    id: 4,
    type: "research",
    title: "Published Quantum Computing Applications report",
    date: "1 week ago",
    status: "published",
  },
]

const achievements = [
  {
    id: 1,
    title: "Research Pioneer",
    description: "Completed your first research project",
    icon: "🎯",
    earned: true,
    date: "January 2024",
  },
  {
    id: 2,
    title: "Citation Master",
    description: "Generated over 1,000 citations",
    icon: "📚",
    earned: true,
    date: "March 2024",
  },
  {
    id: 3,
    title: "Speed Researcher",
    description: "Completed 10 research projects in a month",
    icon: "⚡",
    earned: true,
    date: "February 2024",
  },
  {
    id: 4,
    title: "Quality Expert",
    description: "Maintain 95%+ research accuracy",
    icon: "💎",
    earned: false,
    date: null,
  },
]

export function ProfilePage() {
  return (
    <div className="flex-1 p-8 max-w-6xl mx-auto">
      {/* Profile Header */}
      <Card className="bg-slate-800/30 border-slate-700/50 mb-8">
        <CardContent className="p-8">
          <div className="flex flex-col md:flex-row gap-6">
            <div className="flex-shrink-0">
              <Avatar className="h-32 w-32">
                <AvatarImage src={profileData.avatar || "/placeholder.svg"} alt={profileData.name} />
                <AvatarFallback className="bg-cyan-600 text-white text-2xl">
                  {profileData.name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")}
                </AvatarFallback>
              </Avatar>
            </div>

            <div className="flex-1">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-semibold text-white mb-2">{profileData.name}</h1>
                  <div className="flex flex-col gap-2 text-slate-400">
                    <div className="flex items-center gap-2">
                      <Mail className="h-4 w-4" />
                      <span>{profileData.email}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      <span>{profileData.location}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <LinkIcon className="h-4 w-4" />
                      <a href={profileData.website} className="text-cyan-400 hover:text-cyan-300 transition-colors">
                        {profileData.website}
                      </a>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <span>Joined {profileData.joinDate}</span>
                    </div>
                  </div>
                </div>

                <Button variant="outline" className="border-slate-700/50 text-slate-300 hover:text-white">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Profile
                </Button>
              </div>

              <p className="text-slate-300 leading-relaxed">{profileData.bio}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <Card key={stat.label} className="bg-slate-800/30 border-slate-700/50">
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-cyan-600/20 rounded-lg">
                  <stat.icon className="h-5 w-5 text-cyan-400" />
                </div>
                <div>
                  <p className="text-2xl font-semibold text-white">{stat.value}</p>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <Tabs defaultValue="activity" className="space-y-6">
        <TabsList className="bg-slate-800/50 border border-slate-700/50">
          <TabsTrigger value="activity" className="data-[state=active]:bg-slate-700/50 data-[state=active]:text-white">
            Recent Activity
          </TabsTrigger>
          <TabsTrigger
            value="achievements"
            className="data-[state=active]:bg-slate-700/50 data-[state=active]:text-white"
          >
            Achievements
          </TabsTrigger>
        </TabsList>

        <TabsContent value="activity">
          <Card className="bg-slate-800/30 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-white">Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center gap-4 p-4 bg-slate-800/50 rounded-lg">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        activity.status === "completed"
                          ? "bg-green-500"
                          : activity.status === "in-progress"
                            ? "bg-yellow-500"
                            : activity.status === "achievement"
                              ? "bg-purple-500"
                              : "bg-blue-500"
                      }`}
                    />
                    <div className="flex-1">
                      <p className="text-white font-medium">{activity.title}</p>
                      <p className="text-sm text-slate-400">{activity.date}</p>
                    </div>
                    <Badge
                      variant="outline"
                      className={`${
                        activity.status === "completed"
                          ? "border-green-600/50 text-green-400"
                          : activity.status === "in-progress"
                            ? "border-yellow-600/50 text-yellow-400"
                            : activity.status === "achievement"
                              ? "border-purple-600/50 text-purple-400"
                              : "border-blue-600/50 text-blue-400"
                      }`}
                    >
                      {activity.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="achievements">
          <Card className="bg-slate-800/30 border-slate-700/50">
            <CardHeader>
              <CardTitle className="text-lg font-medium text-white">Achievements</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {achievements.map((achievement) => (
                  <div
                    key={achievement.id}
                    className={`p-4 rounded-lg border transition-colors ${
                      achievement.earned
                        ? "bg-slate-800/50 border-slate-700/50"
                        : "bg-slate-800/20 border-slate-700/30 opacity-60"
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className="text-2xl">{achievement.icon}</div>
                      <div className="flex-1">
                        <h3 className={`font-medium mb-1 ${achievement.earned ? "text-white" : "text-slate-400"}`}>
                          {achievement.title}
                        </h3>
                        <p className="text-sm text-slate-400 mb-2">{achievement.description}</p>
                        {achievement.earned && achievement.date && (
                          <p className="text-xs text-slate-500">Earned {achievement.date}</p>
                        )}
                        {!achievement.earned && (
                          <Badge variant="outline" className="text-xs border-slate-600/50 text-slate-500">
                            Not Earned
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
