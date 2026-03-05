import { Box, Paper, Typography, Avatar } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import type { Message } from '../../types/chat';

interface UserMessageProps {
  message: Message;
}

export default function UserMessage({ message }: UserMessageProps) {
  return (
    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start', justifyContent: 'flex-end' }}>
      <Paper
        elevation={0}
        sx={{
          px: 2,
          py: 1.5,
          maxWidth: '70%',
          bgcolor: 'primary.main',
          color: 'primary.contrastText',
          borderRadius: 2,
          borderTopRightRadius: 0.5,
        }}
      >
        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
          {message.content_text}
        </Typography>
      </Paper>
      <Avatar sx={{ bgcolor: 'primary.dark', width: 32, height: 32 }}>
        <PersonIcon fontSize="small" />
      </Avatar>
    </Box>
  );
}
