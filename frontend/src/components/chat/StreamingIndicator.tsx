import { Box, Typography } from '@mui/material';
import type { PipelineStage } from '../../types/chat';

const STAGE_LABELS: Record<string, string> = {
  idle: '',
  conversational: 'Generating response...',
  chat_response: '',
  parsing_started: 'Analyzing failure symptoms...',
  parsing_complete: 'Symptoms parsed. Searching historical database...',
  search_started: 'Querying Snowflake for similar failure cases...',
  search_complete: 'Similar parts found. Ranking debug commands...',
  ranking_started: 'AI ranking commands by likelihood of failure...',
  prediction: 'Prediction ready.',
  done: '',
  error: 'An error occurred.',
};

interface StreamingIndicatorProps {
  stage: PipelineStage;
}

export default function StreamingIndicator({ stage }: StreamingIndicatorProps) {
  const label = STAGE_LABELS[stage] || '';
  if (!label) return null;

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: 1 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Box
          sx={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            bgcolor: 'secondary.main',
            animation: 'pulse 1.2s ease-in-out infinite',
            '@keyframes pulse': {
              '0%, 100%': { opacity: 1 },
              '50%': { opacity: 0.3 },
            },
          }}
        />
        <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
          {label}
        </Typography>
      </Box>
    </Box>
  );
}
