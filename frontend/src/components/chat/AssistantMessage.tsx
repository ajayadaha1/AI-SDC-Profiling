import { Box, Paper, Avatar, Alert, Typography } from '@mui/material';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import type { Message, PredictionData, ParsedProfile, SearchCompleteData, ThinkingStep } from '../../types/chat';
import CommandTable from '../predictions/CommandTable';
import CaveatsBox from '../predictions/CaveatsBox';
import AnalysisSummary from '../predictions/AnalysisSummary';
import ThinkingProcess from './ThinkingProcess';

interface AssistantMessageProps {
  message: Message;
}

/**
 * Reconstruct thinking steps + data from a persisted prediction message.
 * The backend embeds _thinking_parsed_profile and _thinking_search_result
 * inside content_structured so thinking survives page reloads.
 */
function extractThinkingFromPrediction(prediction: PredictionData & {
  _thinking_parsed_profile?: ParsedProfile;
  _thinking_search_result?: SearchCompleteData;
}): {
  steps: ThinkingStep[];
  parsedProfile: ParsedProfile | null;
  searchResult: SearchCompleteData | null;
} {
  const parsedProfile = prediction._thinking_parsed_profile ?? null;
  const searchResult = prediction._thinking_search_result ?? null;

  // If no thinking data was saved, try to reconstruct minimal steps from the prediction itself
  const steps: ThinkingStep[] = [];

  if (parsedProfile || prediction.analysis?.parsed_profile) {
    const profile = parsedProfile ?? prediction.analysis.parsed_profile;
    steps.push({
      id: 'parse',
      stage: 'parsing_complete',
      label: 'Failure symptoms parsed',
      detail: `Identified: ${profile.failure_type}${profile.mce_bank !== null && profile.mce_bank !== undefined ? ` (Bank ${profile.mce_bank})` : ''} — confidence ${Math.round((profile.confidence ?? 0) * 100)}%`,
      status: 'done',
      timestamp: 0,
      data: profile as unknown as Record<string, unknown>,
    });
  }

  if (searchResult) {
    const srcList = searchResult.sources?.join(', ') ?? '';
    steps.push({
      id: 'search',
      stage: 'search_complete',
      label: `Found ${searchResult.count?.toLocaleString()} records from ${searchResult.sources?.length ?? 0} source(s)`,
      detail: srcList ? `Sources: ${srcList}` : undefined,
      status: 'done',
      timestamp: 0,
      data: searchResult as unknown as Record<string, unknown>,
    });
  }

  if (prediction.commands?.length > 0) {
    const topTools = prediction.commands.slice(0, 3).map((c) => c.command).join(', ');
    steps.push({
      id: 'rank',
      stage: 'prediction',
      label: 'Commands ranked',
      detail: topTools ? `Top picks: ${topTools}` : undefined,
      status: 'done',
      timestamp: 0,
    });
  }

  return {
    steps,
    parsedProfile: parsedProfile ?? prediction.analysis?.parsed_profile ?? null,
    searchResult,
  };
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

      const thinking = extractThinkingFromPrediction(prediction);

      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {thinking.steps.length > 0 && (
            <ThinkingProcess
              steps={thinking.steps}
              isStreaming={false}
              parsedProfile={thinking.parsedProfile}
              searchResult={thinking.searchResult}
            />
          )}
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
