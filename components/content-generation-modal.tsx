"use client";

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Progress } from './ui/progress';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { useToast } from '../hooks/use-toast';
import { supabase } from '../lib/supabase';

interface ContentGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  serpApiEnabled?: boolean;  // Add SerpAPI status
  serpApiContents?: any;     // Add SerpAPI research results
}

interface AIModel {
  openai: string[];
  gemini: string[];
}

interface GenerationStatus {
  project_id: string;
  blogs_generated: number;
  num_blogs_requested: number;  // Changed from total_blogs_requested
  progress_percentage: number;
  status_breakdown: Record<string, number>;
  project_status: string;
}

export function ContentGenerationModal({
  isOpen,
  onClose,
  projectId,
  projectName,
  serpApiEnabled,
  serpApiContents
}: ContentGenerationModalProps) {
  const [prompt, setPrompt] = useState('');
  const [numBlogs, setNumBlogs] = useState(5);
  const [aiModel, setAiModel] = useState('openai');
  const [aiModelVersion, setAiModelVersion] = useState('');
  const [batchSize, setBatchSize] = useState(5);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus | null>(null);
  const [availableModels, setAvailableModels] = useState<AIModel>({ openai: [], gemini: [] });
  const [statusInterval, setStatusInterval] = useState<NodeJS.Timeout | null>(null);
  
  const { toast } = useToast();

  // Fetch available AI models
  useEffect(() => {
    if (isOpen) {
      fetchAvailableModels();
    }
  }, [isOpen]);

  // Update model version when AI model changes
  useEffect(() => {
    if (availableModels[aiModel as keyof AIModel]?.length > 0) {
      setAiModelVersion(availableModels[aiModel as keyof AIModel][0]);
    }
  }, [aiModel, availableModels]);

  // Start status polling when generation starts
  useEffect(() => {
    if (isGenerating && generationStatus) {
      const interval = setInterval(() => {
        fetchGenerationStatus();
      }, 5000); // Poll every 5 seconds
      
      setStatusInterval(interval);
      
      return () => {
        if (interval) clearInterval(interval);
      };
    }
  }, [isGenerating, generationStatus]);

  const fetchAvailableModels = async () => {
    try {
      const response = await fetch('/api/content-generation/available-models');
      if (response.ok) {
        const data = await response.json();
        setAvailableModels(data.models);
        
        // Set default model version based on available models
        if (data.models.openai.length > 0) {
          setAiModelVersion(data.models.openai[0]);
        } else if (data.models.gemini.length > 0) {
          setAiModelVersion(data.models.gemini[0]);
        }
      }
    } catch (error) {
      console.error('Error fetching available models:', error);
    }
  };

  const fetchGenerationStatus = async () => {
    try {
      const response = await fetch(`/api/content-generation/generation-status/${projectId}`);
      if (response.ok) {
        const status = await response.json();
        setGenerationStatus(status);
        
        // Check if generation is complete
        if (['completed', 'completed_with_errors', 'failed'].includes(status.project_status)) {
          setIsGenerating(false);
          if (statusInterval) {
            clearInterval(statusInterval);
            setStatusInterval(null);
          }
          
          toast({
            title: "Generation Complete",
            description: `Generated ${status.blogs_generated}/${status.num_blogs_requested} blogs`,
          });
        }
      }
    } catch (error) {
      console.error('Error fetching generation status:', error);
    }
  };

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      toast({
        title: "Error",
        description: "Please enter a prompt for blog generation",
        variant: "destructive"
      });
      return;
    }

    setIsGenerating(true);
    
    try {
      // Prepare the request payload
      const requestPayload = {
        project_id: projectId,
        prompt: prompt.trim(),
        num_blogs: numBlogs,
        ai_model: aiModel,
        ai_model_version: aiModelVersion,
        batch_size: batchSize,
      };

      console.log('Sending request payload:', requestPayload);

      // Use the direct generation endpoint for immediate results
      const response = await fetch('http://localhost:8000/api/content-generation/generate-direct', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestPayload),
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', response.headers);

      if (response.ok) {
        const data = await response.json();
        console.log('Success response:', data);
        
        toast({
          title: "Success",
          description: `Successfully generated ${data.blogs_requested} blogs!`,
        });
        
        // Close modal after successful generation
        setTimeout(() => {
          onClose();
          // Trigger page refresh to show new blogs
          window.location.reload();
        }, 2000);
        
      } else {
        const errorData = await response.json();
        console.error('Error response:', errorData);
        
        let errorMessage = 'Failed to generate blogs';
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((err: any) => 
              `${err.loc?.join('.')}: ${err.msg}`
            ).join(', ');
          } else {
            errorMessage = errorData.detail;
          }
        }
        
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('Error generating blogs:', error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : 'Failed to generate blogs. Please check your API keys.',
        variant: "destructive"
      });
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClose = () => {
    if (statusInterval) {
      clearInterval(statusInterval);
      setStatusInterval(null);
    }
    setIsGenerating(false);
    setGenerationStatus(null);
    onClose();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'completed_with_errors': return 'bg-yellow-100 text-yellow-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'generating': return 'bg-blue-100 text-blue-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Generate Blogs for "{projectName}"</DialogTitle>
          
          {/* SerpAPI Status Display */}
          {serpApiEnabled && (
            <div className="mt-2">
              <div className="flex items-center gap-2 text-sm">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <span className="text-blue-700 font-medium">SerpAPI Research Enabled</span>
                {serpApiContents && (
                  <Badge variant="secondary" className="ml-2">
                    {serpApiContents.total_results || 0} sources researched
                  </Badge>
                )}
              </div>
              
              {/* Show research summary if available */}
              {serpApiContents && serpApiContents.research_summary && (
                <div className="mt-2 p-3 bg-blue-50 rounded-md">
                  <p className="text-xs text-blue-800">
                    <strong>Research Summary:</strong> {serpApiContents.research_summary.substring(0, 150)}...
                  </p>
                </div>
              )}
            </div>
          )}
        </DialogHeader>

        <div className="space-y-6">
          {/* Generation Form */}
          {!isGenerating && (
            <div className="space-y-4">
              <div>
                <Label htmlFor="prompt">Blog Topic/Prompt</Label>
                <Textarea
                  id="prompt"
                  placeholder="Enter the topic or prompt for blog generation..."
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={3}
                  className="mt-1"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="numBlogs">Number of Blogs</Label>
                  <Input
                    id="numBlogs"
                    type="number"
                    min="1"
                    max="100"
                    value={numBlogs}
                    onChange={(e) => setNumBlogs(parseInt(e.target.value) || 1)}
                    className="mt-1"
                  />
                </div>

                <div>
                  <Label htmlFor="batchSize">Batch Size</Label>
                  <Input
                    id="batchSize"
                    type="number"
                    min="1"
                    max="20"
                    value={batchSize}
                    onChange={(e) => setBatchSize(parseInt(e.target.value) || 5)}
                    className="mt-1"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="aiModel">AI Model</Label>
                  <Select value={aiModel} onValueChange={setAiModel}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {availableModels.openai.length > 0 && (
                        <SelectItem value="openai">OpenAI</SelectItem>
                      )}
                      {availableModels.gemini.length > 0 && (
                        <SelectItem value="gemini">Gemini</SelectItem>
                      )}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label htmlFor="aiModelVersion">Model Version</Label>
                  <Select value={aiModelVersion} onValueChange={setAiModelVersion}>
                    <SelectTrigger className="mt-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {aiModel === 'openai' && availableModels.openai.map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                      {aiModel === 'gemini' && availableModels.gemini.map((model) => (
                        <SelectItem key={model} value={model}>
                          {model}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button 
                onClick={handleGenerate} 
                className="w-full"
                disabled={!prompt.trim() || availableModels[aiModel as keyof AIModel]?.length === 0}
              >
                Start Generation
              </Button>
            </div>
          )}

          {/* Generation Progress */}
          {isGenerating && generationStatus && (
            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    Generation Progress
                    <Badge className={getStatusColor(generationStatus.project_status)}>
                      {generationStatus.project_status}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between text-sm mb-2">
                        <span>Progress</span>
                        <span>{generationStatus.progress_percentage}%</span>
                      </div>
                      <Progress value={generationStatus.progress_percentage} className="w-full" />
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Blogs Generated:</span>
                        <span className="ml-2">{generationStatus.blogs_generated}/{generationStatus.num_blogs_requested}</span>
                      </div>
                      <div>
                        <span className="font-medium">Status:</span>
                        <span className="ml-2 capitalize">{generationStatus.project_status}</span>
                      </div>
                    </div>

                    <div>
                      <span className="font-medium text-sm">Status Breakdown:</span>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {Object.entries(generationStatus.status_breakdown).map(([status, count]) => (
                          <Badge key={status} variant="outline">
                            {status}: {count}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="text-center text-sm text-gray-600">
                Generation is in progress. This may take several minutes depending on the number of blogs.
              </div>
            </div>
          )}

          {/* Available Models Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Available AI Models</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {Object.entries(availableModels).map(([provider, models]) => (
                  <div key={provider}>
                    <span className="font-medium capitalize">{provider}:</span>
                    {models.length > 0 ? (
                      <div className="flex flex-wrap gap-2 mt-1">
                        {models.map((model) => (
                          <Badge key={model} variant="secondary" className="text-xs">
                            {model}
                          </Badge>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-500 ml-2">No API key configured</span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default ContentGenerationModal;
