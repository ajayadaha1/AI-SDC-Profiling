import { useState } from 'react';
import { Accordion, AccordionSummary, AccordionDetails, Typography } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

interface ReasoningSectionProps {
  reasoning: string;
}

export default function ReasoningSection({ reasoning }: ReasoningSectionProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Accordion
      expanded={expanded}
      onChange={() => setExpanded(!expanded)}
      disableGutters
      elevation={0}
      sx={{ bgcolor: 'transparent', '&:before': { display: 'none' } }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 32, px: 0 }}>
        <Typography variant="caption" sx={{ fontWeight: 600 }}>
          Reasoning
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 0 }}>
        <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
          {reasoning}
        </Typography>
      </AccordionDetails>
    </Accordion>
  );
}
