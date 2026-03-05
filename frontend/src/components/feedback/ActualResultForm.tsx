import { Box, RadioGroup, FormControlLabel, Radio, Typography, TextField } from '@mui/material';

interface ActualResultFormProps {
  commandName: string;
  value: string;
  onChange: (value: string) => void;
  notes: string;
  onNotesChange: (notes: string) => void;
}

export default function ActualResultForm({
  commandName,
  value,
  onChange,
  notes,
  onNotesChange,
}: ActualResultFormProps) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
        {commandName}
      </Typography>
      <RadioGroup row value={value} onChange={(e) => onChange(e.target.value)}>
        <FormControlLabel value="FAIL" control={<Radio size="small" />} label="FAIL" />
        <FormControlLabel value="PASS" control={<Radio size="small" />} label="PASS" />
        <FormControlLabel value="NOT_RUN" control={<Radio size="small" />} label="Not run" />
      </RadioGroup>
      {value && (
        <TextField
          size="small"
          placeholder="Notes..."
          value={notes}
          onChange={(e) => onNotesChange(e.target.value)}
          variant="standard"
          sx={{ ml: 2 }}
        />
      )}
    </Box>
  );
}
