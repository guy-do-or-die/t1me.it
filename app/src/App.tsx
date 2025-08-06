import { useState } from 'react';
import { Link as LinkIcon, Copy, CheckCircle, AlertCircle, Loader2, ChevronUp, ChevronDown, Info } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';

import { Button } from './components/ui/button';
import { Input } from './components/ui/input';


interface VideoMetadata {
  title: string;
  description: string;
  site_name: string;
  original_url: string;
}

interface SmartLinkResponse {
  short_url: string;
  screenshot_url: string;
  metadata: VideoMetadata;
  short_id: string;
}

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [timecode, setTimecode] = useState('00:01:51');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SmartLinkResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedUrl, setCopiedUrl] = useState(false);
  const [showVideoInfo, setShowVideoInfo] = useState(false);

  // Extract timecode from URL if present
  const extractTimecodeFromUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      
      // Check for ?t= parameter
      const tParam = urlObj.searchParams.get('t');
      if (tParam) {
        // Handle formats like "62" (seconds) or "1m2s"
        if (tParam.includes('m') || tParam.includes('s')) {
          // Parse "1m2s" format
          const minutes = tParam.match(/(\d+)m/)?.[1] || '0';
          const seconds = tParam.match(/(\d+)s/)?.[1] || '0';
          const totalSeconds = parseInt(minutes) * 60 + parseInt(seconds);
          const hours = Math.floor(totalSeconds / 3600);
          const mins = Math.floor((totalSeconds % 3600) / 60);
          const secs = totalSeconds % 60;
          return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
          // Handle pure seconds format
          const totalSeconds = parseInt(tParam);
          if (!isNaN(totalSeconds)) {
            const hours = Math.floor(totalSeconds / 3600);
            const mins = Math.floor((totalSeconds % 3600) / 60);
            const secs = totalSeconds % 60;
            return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
          }
        }
      }
      
      // Check for #t= in hash
      if (urlObj.hash.includes('t=')) {
        const hashTParam = urlObj.hash.match(/t=([^&]+)/)?.[1];
        if (hashTParam) {
          const totalSeconds = parseInt(hashTParam);
          if (!isNaN(totalSeconds)) {
            const hours = Math.floor(totalSeconds / 3600);
            const mins = Math.floor((totalSeconds % 3600) / 60);
            const secs = totalSeconds % 60;
            return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
          }
        }
      }
    } catch (e) {
      // Invalid URL, ignore
    }
    return '00:01:51'; // Default timecode
  };

  const handleUrlChange = (url: string) => {
    setVideoUrl(url);
    if (url) {
      const extractedTimecode = extractTimecodeFromUrl(url);
      setTimecode(extractedTimecode);
    }
  };

  const convertTimecodeToSeconds = (timecode: string): number => {
    const parts = timecode.split(':').map(p => parseInt(p) || 0);
    if (parts.length === 3) {
      return parts[0] * 3600 + parts[1] * 60 + parts[2]; // hh:mm:ss
    } else if (parts.length === 2) {
      return parts[0] * 60 + parts[1]; // mm:ss
    } else {
      return parts[0] || 0; // ss
    }
  };

  const adjustTimecode = (direction: number) => {
    const currentSeconds = convertTimecodeToSeconds(timecode);
    const newSeconds = Math.max(0, currentSeconds + direction);
    
    const hours = Math.floor(newSeconds / 3600);
    const mins = Math.floor((newSeconds % 3600) / 60);
    const secs = newSeconds % 60;
    
    const newTimecode = `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    setTimecode(newTimecode);
  };

  const generateSmartLink = async () => {
    if (!videoUrl.trim()) {
      setError('Please enter a video URL');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const timestampSeconds = convertTimecodeToSeconds(timecode);
      
      // Build query parameters for the backend API
      const queryParams = new URLSearchParams({
        url: videoUrl,
        t: timestampSeconds.toString(),
        w: '1280',
        h: '720'
      });
      
      const response = await fetch(`/shorten?${queryParams}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to generate smart link');
      }

      const data: SmartLinkResponse = await response.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedUrl(true);
      setTimeout(() => setCopiedUrl(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-2 bg-primary/10 rounded-lg">
              <img src="/logo.svg" alt="t1me.it logo" className="w-16 h-16" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 bg-clip-text text-transparent">
              t1me.it
            </h1>
          </div>
          <p className="text-lg text-muted-foreground max-w-md mx-auto">
            Create a smart video link with precise timestamp thumbnail for perfect social media preview
          </p>
        </div>

        {/* Main Form */}
        <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
          <CardHeader></CardHeader>
          <CardContent className="space-y-6">
            {/* Input Row */}
            <div className="relative">
              <div className="flex gap-3">
                <Input
                  type="url"
                  value={videoUrl}
                  onChange={(e) => handleUrlChange(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      generateSmartLink();
                    }
                  }}
                  placeholder="Enter video URL (YouTube, Vimeo, etc.)"
                  className="h-12 flex-1 border-0 shadow-md focus:shadow-lg transition-shadow"
                />
                <div className="relative w-28">
                  <Input
                    type="text"
                    value={timecode}
                    onChange={(e) => setTimecode(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        generateSmartLink();
                      }
                    }}
                    placeholder="00:01:51"
                    className="h-12 w-full font-mono border-0 shadow-md focus:shadow-lg transition-shadow pr-8"
                  />
                  <div className="absolute right-1 top-1/2 -translate-y-1/2 flex flex-col">
                    <button
                      type="button"
                      onClick={() => adjustTimecode(1)}
                      className="p-0.5 hover:bg-muted rounded transition-colors"
                    >
                      <ChevronUp className="w-3 h-3 text-muted-foreground" />
                    </button>
                    <button
                      type="button"
                      onClick={() => adjustTimecode(-1)}
                      className="p-0.5 hover:bg-muted rounded transition-colors"
                    >
                      <ChevronDown className="w-3 h-3 text-muted-foreground" />
                    </button>
                  </div>
                </div>
              </div>
              
              {/* Error Display */}
              {error && (
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-red-50 text-red-700 px-3 py-1 rounded-md shadow-sm border-0 text-xs font-medium animate-in fade-in-0 slide-in-from-bottom-2 duration-200 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {error}
                </div>
              )}
            </div>

            {/* Generate Button */}
            <Button
              onClick={generateSmartLink}
              disabled={isLoading}
              className="w-full h-12 text-base bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg hover:shadow-xl transition-all duration-200 border-0"
              size="lg"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Generating
                </>
              ) : (
                <>
                  <LinkIcon className="w-5 h-5 mr-2" />
                  Generate
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        {result && (
          <Card className="shadow-xl border-0 bg-white/90 backdrop-blur-sm">
            <CardHeader></CardHeader>
            <CardContent className="space-y-6">
              {/* Smart Link */}
              <div className="relative">
                <div className="flex gap-2">
                  <Input
                    value={result.short_url}
                    readOnly
                    className="font-mono text-sm bg-muted/50 border-0 shadow-md"
                  />
                  <Button
                    onClick={() => copyToClipboard(result.short_url)}
                    variant="outline"
                    size="icon"
                    className="shrink-0 border-0 shadow-md hover:shadow-lg transition-shadow"
                  >
                    {copiedUrl ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                {copiedUrl && (
                  <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-green-50 text-green-700 px-3 py-1 rounded-md shadow-sm border-0 text-xs font-medium animate-in fade-in-0 slide-in-from-bottom-2 duration-200">
                    ✓ Copied to clipboard!
                  </div>
                )}
              </div>
              {/* Screenshot Preview */}
              <div className="relative">
                <img
                  src={result.screenshot_url.replace(/^https?:\/\/[^/]+/, '')}
                  alt="Video screenshot at specified timestamp"
                  className="w-full rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300"
                  onError={(e) => {
                    console.error('Image failed to load:', result.screenshot_url);
                    e.currentTarget.style.display = 'none';
                  }}
                  onLoad={() => console.log('Image loaded successfully:', result.screenshot_url)}
                />
              </div>

              {/* Video Information - Collapsible */}
              <Card className="bg-muted/20 shadow-sm border-0">
                <CardHeader className="cursor-pointer py-3" onClick={() => setShowVideoInfo(!showVideoInfo)}>
                  <CardTitle className="text-sm flex items-center justify-between">
                    <Info className="h-4 w-4" />
                    {showVideoInfo ? (
                      <ChevronUp className="w-4 h-4 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    )}
                  </CardTitle>
                </CardHeader>
                {showVideoInfo && (
                  <CardContent className="pt-0 pb-3 space-y-1">
                    <div className="grid gap-1 text-xs">
                      <div>
                        <span className="font-medium text-muted-foreground">Title:</span>
                        <p className="text-foreground mt-0.5">{result.metadata.title}</p>
                      </div>
                      {result.metadata.description && (
                        <div>
                          <span className="font-medium text-muted-foreground">Description:</span>
                          <p className="text-foreground mt-0.5 line-clamp-2 whitespace-pre-line">{result.metadata.description}</p>
                        </div>
                      )}
                      <div>
                        <span className="font-medium text-muted-foreground">Source:</span>
                        <p className="text-foreground mt-0.5">{result.metadata.site_name}</p>
                      </div>
                    </div>
                  </CardContent>
                )}
              </Card>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default App;
