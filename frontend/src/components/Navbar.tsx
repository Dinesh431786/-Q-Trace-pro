import React from 'react'
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { Shield } from '@mui/icons-material'

const Navbar: React.FC = () => {
  const navigate = useNavigate()
  
  return (
    <AppBar position="static" sx={{ background: 'rgba(26, 26, 46, 0.9)', backdropFilter: 'blur(10px)' }}>
      <Toolbar>
        <Shield sx={{ mr: 2 }} />
        <Typography variant="h6" sx={{ flexGrow: 1, fontWeight: 600 }}>
          Q-Trace Pro 2.0
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" onClick={() => navigate('/')}>Dashboard</Button>
          <Button color="inherit" onClick={() => navigate('/analysis')}>Analysis</Button>
          <Button color="inherit" onClick={() => navigate('/reports')}>Reports</Button>
          <Button color="inherit" onClick={() => navigate('/settings')}>Settings</Button>
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Navbar