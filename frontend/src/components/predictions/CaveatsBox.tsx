import { Box, Typography } from '@mui/material';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

interface CaveatsBoxProps {
  caveats: string[];
}

export default function CaveatsBox({ caveats }: CaveatsBoxProps) {
  if (caveats.length === 0) return null;

  return (
    <Box
      sx={{
        display: 'flex',
        gap: 1,
        p: 1.5,
        borderRadius: 1,
        bgcolor: 'rgba(255, 152, 0, 0.08)',
        border: '1px solid',
        borderColor: 'rgba(255, 152, 0, 0.3)',
      }}
    >
      <WarningAmberIcon fontSize="small" sx={{ color: 'warning.main', mt: 0.2 }} />
      <Box>
        <Typography variant="caption" sx={{ fontWeight: 600, color: 'warning.main' }}>
          Caveats
        </Typography>
        {caveats.map((caveat, idx) => (
          <Typography key={idx} variant="body2" sx={{ fontSize: '0.8rem', mt: 0.25 }}>
            &bull; {caveat}
          </Typography>
        ))}
      </Box>
    </Box>
  );
}
