"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Clock, FileText, CheckCircle, AlertCircle, PlayCircle } from "lucide-react"

interface Project {
  id: string
  name: string
  description: string
  num_blogs: number
  completed_blogs: number
  status: "in_progress" | "partial" | "completed" | "failed" | "pending" | "ready"
  created_at: string
  updated_at: string
  blogs?: Array<{
    id: string
    status: string
    project_id: string
    is_published?: boolean
  }>
}

interface ProjectListProps {
  projects: Project[]
  loading: boolean
  onProjectSelect: (projectId: string) => void
  onResume: (project: Project) => void
}

export function ProjectList({ projects, loading, onProjectSelect, onResume }: ProjectListProps) {
  // Simple function to get project status - just use what's in the database
  const getProjectStatus = (project: Project): string => {
    return project.status
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case "partial":
        return <FileText className="h-4 w-4 text-orange-600" />
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
      case "partial":
        return "bg-orange-100 text-orange-800"
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
      case "partial":
        return "Partial"
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
         const projectStatus = getProjectStatus(project)
         
         // Calculate blog statistics
         const blogs = project.blogs || []
         console.log(`Project ${project.name} blogs:`, blogs) // Debug log
         
         // Handle both array and object formats from Supabase
         let generatedBlogs = 0
         let publishedBlogs = 0
         
         if (Array.isArray(blogs)) {
           // Debug: Log all unique status values
           const uniqueStatuses = [...new Set(blogs.map((blog: any) => blog.status))]
           console.log(`Project ${project.name} unique blog statuses:`, uniqueStatuses)
           
           // Count blogs that are generated (regardless of publishing status)
           generatedBlogs = blogs.filter((blog: any) => 
             blog.status === 'generating' || 
             blog.status === 'generated' || 
             blog.status === 'completed' || 
             blog.status === 'ready' ||
             blog.status === 'pending'
           ).length
           
           // Count blogs that are published (using the new is_published column)
           publishedBlogs = blogs.filter((blog: any) => blog.is_published === true).length
         } else if (blogs && typeof blogs === 'object') {
           // If blogs is an object with blog IDs as keys
           const blogArray = Object.values(blogs)
           const uniqueStatuses = [...new Set(blogArray.map((blog: any) => blog.status))]
           console.log(`Project ${project.name} unique blog statuses:`, uniqueStatuses)
           
           generatedBlogs = blogArray.filter((blog: any) => 
             blog.status === 'generating' || 
             blog.status === 'completed' || 
             blog.status === 'ready' ||
             blog.status === 'pending'
           ).length
           
           publishedBlogs = blogArray.filter((blog: any) => blog.is_published === true).length
         }
         
         // Fallback to completed_blogs if no blogs array or empty blogs
         if (generatedBlogs === 0 && publishedBlogs === 0 && project.completed_blogs > 0) {
           // If we have no blog data but completed_blogs exists, use it as generated
           generatedBlogs = project.completed_blogs
           console.log(`Using fallback: project.completed_blogs = ${project.completed_blogs}`)
         }

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
                   {getStatusIcon(projectStatus)}
                 </div>
               </div>
               <CardDescription className="text-gray-600 line-clamp-2">{project.description}</CardDescription>
             </CardHeader>
             <CardContent className="space-y-4">
               <div className="grid grid-cols-2 gap-4">
                 <div className="text-center p-3 bg-blue-50 rounded-lg">
                   <div className="text-2xl font-bold text-blue-600">{generatedBlogs}</div>
                   <div className="text-xs text-blue-600">Generated</div>
                 </div>
                 <div className="text-center p-3 bg-green-50 rounded-lg">
                   <div className="text-2xl font-bold text-green-600">{publishedBlogs}</div>
                   <div className="text-xs text-green-600">Published</div>
                 </div>
               </div>

               <div className="flex items-center justify-between">
                 <div className="flex items-center space-x-2">
                   <FileText className="h-4 w-4 text-gray-400" />
                   <span className="text-sm text-gray-600">{generatedBlogs}/{project.num_blogs} blogs</span>
                 </div>
                 <Badge className={getStatusColor(projectStatus)}>{getStatusLabel(projectStatus)}</Badge>
               </div>

             </CardContent>
           </Card>
         )
       })}
    </div>
  )
}
