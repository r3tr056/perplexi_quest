"use client"

import * as React from "react"
import { Save, User, Bell, Shield, Database, Key } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Separator } from "@/components/ui/separator"

export function SettingsPage() {
  const [settings, setSettings] = React.useState({
    // Profile
    displayName: "John Doe",
    email: "john.doe@example.com",
    bio: "",

    // Notifications
    emailNotifications: true,
    pushNotifications: false,
    researchUpdates: true,
    weeklyDigest: true,

    // Research Preferences
    defaultResearchType: "comprehensive",
    autoSaveDrafts: true,
    citationStyle: "apa",
    language: "en",

    // Privacy
    profileVisibility: "private",
    dataRetention: "1year",
    analyticsOptIn: false,

    // API
    apiKey: "pk_live_••••••••••••••••",
    rateLimitTier: "pro",
  })

  const handleSave = () => {
    // Save settings logic
    console.log("Settings saved:", settings)
  }

  const updateSetting = (key: string, value: any) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
  }

  return (
    <div className="flex-1 p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-semibold text-white mb-2">Settings</h1>
        <p className="text-slate-400">Manage your account preferences and research settings</p>
      </div>

      <div className="space-y-8">
        {/* Profile Settings */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="displayName" className="text-slate-300">
                  Display Name
                </Label>
                <Input
                  id="displayName"
                  value={settings.displayName}
                  onChange={(e) => updateSetting("displayName", e.target.value)}
                  className="bg-slate-800/50 border-slate-700/50 text-white"
                />
              </div>
              <div>
                <Label htmlFor="email" className="text-slate-300">
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={settings.email}
                  onChange={(e) => updateSetting("email", e.target.value)}
                  className="bg-slate-800/50 border-slate-700/50 text-white"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="bio" className="text-slate-300">
                Bio
              </Label>
              <Textarea
                id="bio"
                placeholder="Tell us about yourself..."
                value={settings.bio}
                onChange={(e) => updateSetting("bio", e.target.value)}
                className="bg-slate-800/50 border-slate-700/50 text-white placeholder:text-slate-500"
              />
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-300">Email Notifications</Label>
                <p className="text-sm text-slate-500">Receive notifications via email</p>
              </div>
              <Switch
                checked={settings.emailNotifications}
                onCheckedChange={(checked) => updateSetting("emailNotifications", checked)}
              />
            </div>
            <Separator className="bg-slate-700/50" />
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-300">Push Notifications</Label>
                <p className="text-sm text-slate-500">Receive browser push notifications</p>
              </div>
              <Switch
                checked={settings.pushNotifications}
                onCheckedChange={(checked) => updateSetting("pushNotifications", checked)}
              />
            </div>
            <Separator className="bg-slate-700/50" />
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-300">Research Updates</Label>
                <p className="text-sm text-slate-500">Get notified when research completes</p>
              </div>
              <Switch
                checked={settings.researchUpdates}
                onCheckedChange={(checked) => updateSetting("researchUpdates", checked)}
              />
            </div>
            <Separator className="bg-slate-700/50" />
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-300">Weekly Digest</Label>
                <p className="text-sm text-slate-500">Weekly summary of your research activity</p>
              </div>
              <Switch
                checked={settings.weeklyDigest}
                onCheckedChange={(checked) => updateSetting("weeklyDigest", checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Research Preferences */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <Database className="h-5 w-5" />
              Research Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Default Research Type</Label>
                <Select
                  value={settings.defaultResearchType}
                  onValueChange={(value) => updateSetting("defaultResearchType", value)}
                >
                  <SelectTrigger className="bg-slate-800/50 border-slate-700/50 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="comprehensive">Comprehensive Analysis</SelectItem>
                    <SelectItem value="quick">Quick Overview</SelectItem>
                    <SelectItem value="comparative">Comparative Study</SelectItem>
                    <SelectItem value="trend">Trend Analysis</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">Citation Style</Label>
                <Select value={settings.citationStyle} onValueChange={(value) => updateSetting("citationStyle", value)}>
                  <SelectTrigger className="bg-slate-800/50 border-slate-700/50 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="apa">APA</SelectItem>
                    <SelectItem value="mla">MLA</SelectItem>
                    <SelectItem value="chicago">Chicago</SelectItem>
                    <SelectItem value="harvard">Harvard</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-300">Auto-save Drafts</Label>
                <p className="text-sm text-slate-500">Automatically save research progress</p>
              </div>
              <Switch
                checked={settings.autoSaveDrafts}
                onCheckedChange={(checked) => updateSetting("autoSaveDrafts", checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Privacy & Security
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Profile Visibility</Label>
                <Select
                  value={settings.profileVisibility}
                  onValueChange={(value) => updateSetting("profileVisibility", value)}
                >
                  <SelectTrigger className="bg-slate-800/50 border-slate-700/50 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="public">Public</SelectItem>
                    <SelectItem value="private">Private</SelectItem>
                    <SelectItem value="team">Team Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">Data Retention</Label>
                <Select value={settings.dataRetention} onValueChange={(value) => updateSetting("dataRetention", value)}>
                  <SelectTrigger className="bg-slate-800/50 border-slate-700/50 text-white">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-700">
                    <SelectItem value="3months">3 Months</SelectItem>
                    <SelectItem value="6months">6 Months</SelectItem>
                    <SelectItem value="1year">1 Year</SelectItem>
                    <SelectItem value="indefinite">Indefinite</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <Label className="text-slate-300">Analytics Opt-in</Label>
                <p className="text-sm text-slate-500">Help improve our service with usage analytics</p>
              </div>
              <Switch
                checked={settings.analyticsOptIn}
                onCheckedChange={(checked) => updateSetting("analyticsOptIn", checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* API Settings */}
        <Card className="bg-slate-800/30 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-lg font-medium text-white flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Access
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label className="text-slate-300">API Key</Label>
              <div className="flex gap-2">
                <Input
                  value={settings.apiKey}
                  readOnly
                  className="bg-slate-800/50 border-slate-700/50 text-white font-mono"
                />
                <Button variant="outline" className="border-slate-700/50 text-slate-300 hover:text-white">
                  Regenerate
                </Button>
              </div>
            </div>
            <div>
              <Label className="text-slate-300">Rate Limit Tier</Label>
              <p className="text-sm text-slate-500 mb-2">Current tier: {settings.rateLimitTier.toUpperCase()}</p>
              <Button variant="outline" className="border-slate-700/50 text-slate-300 hover:text-white">
                Upgrade Plan
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end">
          <Button onClick={handleSave} className="bg-cyan-600 hover:bg-cyan-700 text-white">
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>
    </div>
  )
}
