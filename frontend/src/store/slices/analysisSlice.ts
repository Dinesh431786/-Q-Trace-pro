import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface AnalysisState {
  results: any | null
  isAnalyzing: boolean
  progress: number
  error: string | null
}

const initialState: AnalysisState = {
  results: null,
  isAnalyzing: false,
  progress: 0,
  error: null,
}

const analysisSlice = createSlice({
  name: 'analysis',
  initialState,
  reducers: {
    startAnalysis: (state) => {
      state.isAnalyzing = true
      state.progress = 0
      state.error = null
    },
    updateProgress: (state, action: PayloadAction<number>) => {
      state.progress = action.payload
    },
    setResults: (state, action: PayloadAction<any>) => {
      state.results = action.payload
      state.isAnalyzing = false
      state.progress = 100
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload
      state.isAnalyzing = false
    },
  },
})

export const { startAnalysis, updateProgress, setResults, setError } = analysisSlice.actions
export default analysisSlice.reducer