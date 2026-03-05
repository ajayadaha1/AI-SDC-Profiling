import { Box, Paper, Avatar, Alert, Typography } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import type { Message, PredictionData } from '../../types/chat';
import CommandTable from '../predictions/CommandTable';
import CaveatsBox from '../predictions/CaveatsBox';
import AnalysisSummary from '../predictions/AnalysisSummary';

interface AssistantMessageProps {
  message: Message;
}

export default function AssistantMessage({ message }: AssistantMessageProps) {
  const renderContent = () => {
    if (message.message_type === 'error') {
      return (
        <Alert severity="error" sx={{ borderRadius: 2 }}>
          {message.content_text}
        </Alert>
      );
    }

    if (message.message_type === 'prediction' && message.content_structured) {
      let prediction: PredictionData;
      try {
        prediction = JSON.parse(message.content_structured);
      } catch {
        return <Typography color="error">Failed to parse prediction data.</Typography>;
      }

      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <AnalysisSummary analysis={prediction.analysis} />
          <CommandTable commands={prediction.commands} />
          {prediction.caveats.length > 0 && <CaveatsBox caveats={prediction.caveats} />}
        </Box>
      );
    }

    // Default: plain text
    return (
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
        {message.content_text}
      </Typography>
    );
  };

  return (
    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start' }}>
      <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
        <SmartToyIcon fontSize="small" />
      </Avatar>
      <Paper
        elevation={0}
        sx={{
          px: 2,
          py: 1.5,
          maxWidth: '85%',
          bgcolor: 'background.paper',
          borderRadius: 2,
          borderTopLeftRadius: 0.5,
        }}
      >
        {renderContent()}
      </Paper>
    </Box>
  );
}
