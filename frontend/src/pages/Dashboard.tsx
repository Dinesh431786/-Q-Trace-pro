import React, { useState, useCallback } from 'react'
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  LinearProgress,
  Chip,
  IconButton,
  Alert,
  Skeleton,
} from '@mui/material'
import {
  Security,
  BugReport,
  Speed,
  CloudUpload,
  PlayArrow,
  Code,
  Assessment,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

import CodeEditor from '../components/CodeEditor'
import AnalysisResults from '../components/AnalysisResults'
import RealTimeMonitor from '../components/RealTimeMonitor'
import { useAnalysis } from '../hooks/useAnalysis'

const Dashboard: React.FC = () => {
  const [code, setCode] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const { analyze, isAnalyzing, results, progress } = useAnalysis()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (file && file.name.endsWith('.py')) {
      setFile(file)
      const reader = new FileReader()
      reader.onload = (e) => {
        const content = e.target?.result as string
        setCode(content)
        toast.success(`File ${file.name} loaded`)
      }
      reader.readAsText(file)
    } else {
      toast.error('Please upload a Python file')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/python': ['.py'],
    },
    maxFiles: 1,
  })

  const handleAnalyze = async () => {
    if (!code && !file) {
      toast.error('Please provide code to analyze')
      return
    }

    try {
      await analyze(code, file)
      toast.success('Analysis complete!')
    } catch (error) {
      toast.error('Analysis failed')
    }
  }

  const handleQuickScan = async () => {
    if (!code) {
      toast.error('Please provide code to scan')
      return
    }

    try {
      const response = await fetch('/api/v1/analysis/quick-scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await response.json()
      toast.success(`Quick scan found ${data.critical_issues} critical issues`)
    } catch (error) {
      toast.error('Quick scan failed')
    }
  }

  return (
    <Box>
      {/* Header Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }}>
            <Card sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" variant="h4">
                      {results?.summary?.risk_score || 0}
                    </Typography>
                    <Typography color="rgba(255,255,255,0.8)" variant="body2">
                      Risk Score
                    </Typography>
                  </Box>
                  <Security sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }}>
            <Card sx={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" variant="h4">
                      {results?.summary?.total_issues || 0}
                    </Typography>
                    <Typography color="rgba(255,255,255,0.8)" variant="body2">
                      Issues Found
                    </Typography>
                  </Box>
                  <BugReport sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }}>
            <Card sx={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" variant="h4">
                      {results?.ml_analysis?.threat_score ? 
                        (results.ml_analysis.threat_score * 100).toFixed(0) + '%' : '0%'}
                    </Typography>
                    <Typography color="rgba(255,255,255,0.8)" variant="body2">
                      ML Threat Score
                    </Typography>
                  </Box>
                  <Speed sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <motion.div whileHover={{ scale: 1.05 }}>
            <Card sx={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="white" variant="h4">
                      {results?.summary?.risk_level || 'LOW'}
                    </Typography>
                    <Typography color="rgba(255,255,255,0.8)" variant="body2">
                      Risk Level
                    </Typography>
                  </Box>
                  <Assessment sx={{ fontSize: 40, color: 'rgba(255,255,255,0.8)' }} />
                </Box>
              </CardContent>
            </Card>
          </motion.div>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Code Input Section */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
              <Code sx={{ mr: 1 }} /> Code Analysis
            </Typography>

            {/* File Upload */}
            <Box
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'divider',
                borderRadius: 2,
                p: 3,
                mb: 2,
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.3s',
                '&:hover': { borderColor: 'primary.main' },
              }}
            >
              <input {...getInputProps()} />
              <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              <Typography>
                {isDragActive
                  ? 'Drop the Python file here...'
                  : 'Drag & drop a Python file here, or click to select'}
              </Typography>
              {file && (
                <Chip
                  label={file.name}
                  color="primary"
                  sx={{ mt: 2 }}
                  onDelete={() => setFile(null)}
                />
              )}
            </Box>

            {/* Code Editor */}
            <CodeEditor code={code} onChange={setCode} />

            {/* Action Buttons */}
            <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<PlayArrow />}
                onClick={handleAnalyze}
                disabled={isAnalyzing || (!code && !file)}
                fullWidth
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #5a67d8 0%, #6b4299 100%)',
                  },
                }}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Code'}
              </Button>
              <Button
                variant="outlined"
                size="large"
                onClick={handleQuickScan}
                disabled={isAnalyzing || !code}
                sx={{ minWidth: 150 }}
              >
                Quick Scan
              </Button>
            </Box>

            {/* Progress Bar */}
            {isAnalyzing && (
              <Box sx={{ mt: 2 }}>
                <LinearProgress variant="determinate" value={progress} />
                <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                  {progress}% Complete
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Real-time Monitor */}
        <Grid item xs={12} lg={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <RealTimeMonitor />
          </Paper>
        </Grid>

        {/* Analysis Results */}
        {results && (
          <Grid item xs={12}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <AnalysisResults results={results} />
            </motion.div>
          </Grid>
        )}
      </Grid>
    </Box>
  )
}

export default Dashboard