import React from 'react'
import { Box, Paper, Typography, Tabs, Tab } from '@mui/material'

interface AnalysisResultsProps {
  results: any
}

const AnalysisResults: React.FC<AnalysisResultsProps> = ({ results }) => {
  const [tab, setTab] = React.useState(0)
  
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>Analysis Results</Typography>
      <Tabs value={tab} onChange={(_, v) => setTab(v)}>
        <Tab label="Summary" />
        <Tab label="Vulnerabilities" />
        <Tab label="ML Insights" />
        <Tab label="Quantum Analysis" />
      </Tabs>
      <Box sx={{ mt: 2 }}>
        {tab === 0 && (
          <Box>
            <Typography>Risk Score: {results?.summary?.risk_score || 0}</Typography>
            <Typography>Total Issues: {results?.summary?.total_issues || 0}</Typography>
          </Box>
        )}
      </Box>
    </Paper>
  )
}

export default AnalysisResults