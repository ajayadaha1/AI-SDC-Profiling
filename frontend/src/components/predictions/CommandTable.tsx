import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import type { RankedCommand } from '../../types/chat';
import PredictionCard from './PredictionCard';

interface CommandTableProps {
  commands: RankedCommand[];
}

export default function CommandTable({ commands }: CommandTableProps) {
  return (
    <Box>
      <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
        Recommended Debug Commands
      </Typography>
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell sx={{ fontWeight: 600, width: 50 }}>Rank</TableCell>
              <TableCell sx={{ fontWeight: 600 }}>Command</TableCell>
              <TableCell sx={{ fontWeight: 600, width: 140 }}>Confidence</TableCell>
              <TableCell sx={{ fontWeight: 600, width: 130 }}>Fail Rate</TableCell>
              <TableCell sx={{ fontWeight: 600, width: 100 }}>Est. Time</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {commands.map((cmd) => (
              <PredictionCard key={cmd.rank} command={cmd} />
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
