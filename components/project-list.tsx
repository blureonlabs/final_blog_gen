"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Clock, FileText, CheckCircle, AlertCircle, PlayCircle } from "lucide-react"

interface Project {
  id: string
  name: string
  description: string
  num_blogs: number
  completed_blogs: number
  status: "in_progress" | "completed" | "failed" | "pending" | "ready"
  created_at: string
  updated_at: string
}

interface ProjectListProps {
  projects: Project[]
  loading: boolean
  onProjectSelect: (projectId: string) => void
  onResume: (project: Project) => void
}

export function ProjectList({ projects, loading, onProjectSelect, onResume }: ProjectListProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "in_progress":
        return <PlayCircle className="h-4 w-4 text-blue-600" />
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-600" />
      case "ready":
        return <PlayCircle className="h-4 w-4 text-green-600" />
      default:
        return <Clock className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800"
      case "in_progress":
        return "bg-blue-100 text-blue-800"
      case "failed":
        return "bg-red-100 text-red-800"
      case "pending":
        return "bg-yellow-100 text-yellow-800"
      case "ready":
        return "bg-green-100 text-green-800"
      default:
        return "bg-gray-100 text-gray-800"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "in_progress":
        return "In Progress"
      case "completed":
        return "Completed"
      case "failed":
        return "Failed"
      case "pending":
        return "Ready to Start"
      case "ready":
        return "Ready to Start"
      default:
        return "Unknown"
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <Card key={i} className="bg-white shadow-sm animate-pulse">
            <CardHeader>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2"></div>
            </CardHeader>
            <CardContent>
              <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-2/3"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!projects || projects.length === 0) {
    return (
      <Card className="bg-white shadow-sm">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-600 text-center">Create your first Blu Blog Gen project to get started.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {projects.map((project) => {
        const progressPercentage = (project.completed_blogs / project.num_blogs) * 100

        return (
          <Card
            key={project.id}
            className="bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer"
            onClick={() => onProjectSelect(project.id)}
          >
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg font-medium text-gray-900 truncate">{project.name}</CardTitle>
                <div className="flex items-center space-x-2">
                                     {(project.status === "in_progress" || project.status === "pending" || project.status === "ready") && (
                     <button
                       onClick={(e) => {
                         e.stopPropagation()
                         onResume(project)
                       }}
                       className={`p-2 rounded-full transition-colors ${
                         project.status === "ready" || project.status === "pending"
                           ? "bg-green-100 hover:bg-green-200" 
                           : "bg-blue-100 hover:bg-blue-200"
                       }`}
                       title={project.status === "ready" || project.status === "pending" ? "Start Content Generation" : "Resume Content Generation"}
                     >
                       <PlayCircle className={`h-4 w-4 ${
                         project.status === "ready" || project.status === "pending" ? "text-green-600" : "text-blue-600"
                       }`} />
                     </button>
                   )}
                  {getStatusIcon(project.status)}
                </div>
              </div>
              <CardDescription className="text-gray-600 line-clamp-2">{project.description}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Progress</span>
                  <span className="font-medium">
                    {project.completed_blogs}/{project.num_blogs} blogs
                  </span>
                </div>
                <Progress value={progressPercentage} className="h-2" />
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <FileText className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-600">{Math.round(progressPercentage)}% complete</span>
                </div>
                <Badge className={getStatusColor(project.status)}>{getStatusLabel(project.status)}</Badge>
              </div>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
