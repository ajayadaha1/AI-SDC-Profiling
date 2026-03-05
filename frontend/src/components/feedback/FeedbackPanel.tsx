import { useState } from 'react';
import {
  Box,
  Typography,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Button,
  Chip,
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { useFeedback } from '../../hooks/useFeedback';
import type { RankedCommand } from '../../types/chat';

interface FeedbackPanelProps {
  commands: RankedCommand[];
  predictionCommandIds?: number[];
}

export default function FeedbackPanel({ commands, predictionCommandIds }: FeedbackPanelProps) {
  const [feedbackMap, setFeedbackMap] = useState<Record<number, string>>({});
  const [notes, setNotes] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const feedbackMutation = useFeedback();

  const handleResultChange = (rank: number, value: string) => {
    setFeedbackMap((prev) => ({ ...prev, [rank]: value }));
  };

  const handleSubmit = async () => {
    if (!predictionCommandIds) return;

    for (const cmd of commands) {
      const result = feedbackMap[cmd.rank];
      const cmdId = predictionCommandIds[cmd.rank - 1];
      if (result && cmdId) {
        await feedbackMutation.mutateAsync({
          prediction_command_id: cmdId,
          actual_result: result as 'FAIL' | 'PASS' | 'NOT_RUN',
          notes: notes || undefined,
        });
      }
    }
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
        <CheckCircleIcon color="success" fontSize="small" />
        <Chip label="Feedback submitted" size="small" color="success" variant="outlined" />
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
        How did these predictions perform?
      </Typography>
      {commands.map((cmd) => (
        <Box key={cmd.rank} sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 0.5 }}>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem', minWidth: 200 }}>
            #{cmd.rank} {cmd.command}
          </Typography>
          <RadioGroup
            row
            value={feedbackMap[cmd.rank] || ''}
            onChange={(e) => handleResultChange(cmd.rank, e.target.value)}
          >
            <FormControlLabel value="FAIL" control={<Radio size="small" />} label="FAIL" />
            <FormControlLabel value="PASS" control={<Radio size="small" />} label="PASS" />
            <FormControlLabel value="NOT_RUN" control={<Radio size="small" />} label="Not run" />
          </RadioGroup>
        </Box>
      ))}
      <TextField
        size="small"
        placeholder="Optional notes..."
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        fullWidth
        sx={{ mt: 1, mb: 1 }}
      />
      <Button
        variant="contained"
        size="small"
        onClick={handleSubmit}
        disabled={Object.keys(feedbackMap).length === 0 || feedbackMutation.isPending}
        sx={{ textTransform: 'none' }}
      >
        Submit Feedback
      </Button>
    </Box>
  );
}
