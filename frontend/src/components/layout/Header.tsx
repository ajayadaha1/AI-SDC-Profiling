import { Box, IconButton, Typography } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useUIStore } from '../../stores/uiStore';

export default function Header() {
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        px: 2,
        py: 1,
        borderBottom: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <IconButton onClick={toggleSidebar} size="small" sx={{ mr: 1 }}>
        <MenuIcon />
      </IconButton>
      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
        SDC Debug Predictor
      </Typography>
    </Box>
  );
}
