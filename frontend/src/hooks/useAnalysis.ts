import { useState, useCallback } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { RootState } from '../store'
import { startAnalysis, updateProgress, setResults, setError } from '../store/slices/analysisSlice'

export const useAnalysis = () => {
  const dispatch = useDispatch()
  const { results, isAnalyzing, progress, error } = useSelector((state: RootState) => state.analysis)
  
  const analyze = useCallback(async (code: string, file: File | null) => {
    dispatch(startAnalysis())
    
    try {
      // Create FormData
      const formData = new FormData()
      if (file) {
        formData.append('file', file)
      } else {
        formData.append('code', code)
      }
      
      // Start analysis
      const response = await fetch('/api/v1/analysis/analyze', {
        method: 'POST',
        body: formData,
      })
      
      const data = await response.json()
      const analysisId = data.analysis_id
      
      // Poll for results
      const pollInterval = setInterval(async () => {
        const statusResponse = await fetch(`/api/v1/analysis/status/${analysisId}`)
        const status = await statusResponse.json()
        
        if (status.progress) {
          dispatch(updateProgress(status.progress))
        }
        
        if (status.status === 'completed') {
          clearInterval(pollInterval)
          
          // Get results
          const resultResponse = await fetch(`/api/v1/analysis/result/${analysisId}`)
          const results = await resultResponse.json()
          dispatch(setResults(results))
        } else if (status.status === 'error') {
          clearInterval(pollInterval)
          dispatch(setError(status.error || 'Analysis failed'))
        }
      }, 1000)
      
    } catch (err) {
      dispatch(setError(err instanceof Error ? err.message : 'Analysis failed'))
    }
  }, [dispatch])
  
  return { analyze, results, isAnalyzing, progress, error }
}