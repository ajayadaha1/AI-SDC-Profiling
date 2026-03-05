import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import { useUIStore } from '../../stores/uiStore';

const SIDEBAR_WIDTH = 280;

export default function AppLayout() {
  const sidebarOpen = useUIStore((s) => s.sidebarOpen);

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Box
        sx={{
          width: sidebarOpen ? SIDEBAR_WIDTH : 0,
          flexShrink: 0,
          transition: 'width 0.2s ease',
          overflow: 'hidden',
        }}
      >
        <Sidebar width={SIDEBAR_WIDTH} />
      </Box>
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <Outlet />
      </Box>
    </Box>
  );
}
