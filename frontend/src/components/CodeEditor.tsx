import React from 'react'
import { Box, TextField } from '@mui/material'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface CodeEditorProps {
  code: string
  onChange: (code: string) => void
  readOnly?: boolean
}

const CodeEditor: React.FC<CodeEditorProps> = ({ code, onChange, readOnly = false }) => {
  return (
    <Box sx={{ position: 'relative' }}>
      {readOnly ? (
        <SyntaxHighlighter
          language="python"
          style={atomDark}
          customStyle={{
            borderRadius: 8,
            fontSize: 14,
            maxHeight: 400,
            overflow: 'auto',
          }}
        >
          {code}
        </SyntaxHighlighter>
      ) : (
        <TextField
          multiline
          fullWidth
          value={code}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Paste your Python code here..."
          variant="outlined"
          minRows={15}
          maxRows={25}
          sx={{
            '& .MuiInputBase-input': {
              fontFamily: 'monospace',
              fontSize: 14,
            },
          }}
        />
      )}
    </Box>
  )
}

export default CodeEditor