import { useState } from 'react';
import {
  TableRow,
  TableCell,
  Typography,
  Collapse,
  Box,
  IconButton,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import type { RankedCommand } from '../../types/chat';
import ConfidenceBar from './ConfidenceBar';

interface PredictionCardProps {
  command: RankedCommand;
}

export default function PredictionCard({ command }: PredictionCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <TableRow
        hover
        onClick={() => setExpanded(!expanded)}
        sx={{ cursor: 'pointer', '& > *': { borderBottom: expanded ? 'none' : undefined } }}
      >
        <TableCell>
          <Typography variant="body2" sx={{ fontWeight: 700 }}>
            #{command.rank}
          </Typography>
        </TableCell>
        <TableCell>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
              {command.command}
            </Typography>
            <IconButton size="small">
              {expanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
            </IconButton>
          </Box>
        </TableCell>
        <TableCell>
          <ConfidenceBar confidence={command.confidence} />
        </TableCell>
        <TableCell>
          <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
            {command.fail_rate_on_similar || 'N/A'}
          </Typography>
        </TableCell>
        <TableCell>
          <Typography variant="body2" sx={{ fontSize: '0.8rem' }}>
            {command.estimated_time_to_fail || 'N/A'}
          </Typography>
        </TableCell>
      </TableRow>
      <TableRow>
        <TableCell colSpan={5} sx={{ py: 0, px: 0 }}>
          <Collapse in={expanded} timeout="auto" unmountOnExit>
            <Box sx={{ px: 2, py: 1.5, bgcolor: 'action.hover', borderRadius: 1, m: 1 }}>
              <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                Reasoning
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5, fontSize: '0.8rem' }}>
                {command.reasoning || 'No reasoning provided.'}
              </Typography>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
}
