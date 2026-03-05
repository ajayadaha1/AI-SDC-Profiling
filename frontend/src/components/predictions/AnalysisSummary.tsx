import { Box, Chip, Typography } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import type { PredictionData } from '../../types/chat';

interface AnalysisSummaryProps {
  analysis: PredictionData['analysis'];
}

export default function AnalysisSummary({ analysis }: AnalysisSummaryProps) {
  const profile = analysis.parsed_profile;

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <SearchIcon fontSize="small" color="secondary" />
        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
          Analysis Summary
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 1 }}>
        <Chip label={profile.failure_type} size="small" color="error" variant="outlined" />
        {profile.mce_bank !== null && (
          <Chip label={`Bank ${profile.mce_bank}`} size="small" color="warning" variant="outlined" />
        )}
        {profile.mce_code && (
          <Chip label={profile.mce_code} size="small" variant="outlined" />
        )}
        {profile.thermal_state && (
          <Chip label={`Thermal: ${profile.thermal_state}`} size="small" color="info" variant="outlined" />
        )}
        {profile.boot_stage && (
          <Chip label={`Stage: ${profile.boot_stage}`} size="small" variant="outlined" />
        )}
        {profile.error_severity && (
          <Chip label={profile.error_severity} size="small" color="error" variant="outlined" />
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
        Tier {analysis.match_tier} match &mdash; {analysis.similar_parts_count} similar parts found
        {analysis.dominant_failure_pattern && ` &mdash; ${analysis.dominant_failure_pattern}`}
      </Typography>
    </Box>
  );
}
