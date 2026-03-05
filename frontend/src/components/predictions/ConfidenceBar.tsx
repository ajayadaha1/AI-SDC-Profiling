import { Box, LinearProgress, Typography } from '@mui/material';

interface ConfidenceBarProps {
  confidence: number;
}

export default function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? 'success' : pct >= 50 ? 'warning' : 'error';

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 120 }}>
      <LinearProgress
        variant="determinate"
        value={pct}
        color={color}
        sx={{ flex: 1, height: 6, borderRadius: 3 }}
      />
      <Typography variant="body2" sx={{ fontSize: '0.75rem', fontWeight: 600, minWidth: 35 }}>
        {pct}%
      </Typography>
    </Box>
  );
}
