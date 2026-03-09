import { Box, IconButton, Typography } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { useUIStore } from '../../stores/uiStore';
import Logo from '../common/Logo';

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
      <Logo size={30} />
      <Typography variant="subtitle1" sx={{ fontWeight: 600, ml: 1 }}>
        Failure Debug Predictor
      </Typography>
    </Box>
  );
}
