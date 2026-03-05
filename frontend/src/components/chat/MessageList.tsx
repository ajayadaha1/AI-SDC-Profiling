import { useEffect, useRef } from 'react';
import { Box } from '@mui/material';
import type { Message } from '../../types/chat';
import UserMessage from './UserMessage';
import AssistantMessage from './AssistantMessage';

interface MessageListProps {
  messages: Message[];
}

export default function MessageList({ messages }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length]);

  return (
    <Box
      sx={{
        flex: 1,
        overflow: 'auto',
        px: { xs: 2, md: 4 },
        py: 2,
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {messages.map((msg, idx) =>
        msg.role === 'user' ? (
          <UserMessage key={idx} message={msg} />
        ) : (
          <AssistantMessage key={idx} message={msg} />
        ),
      )}
      <div ref={endRef} />
    </Box>
  );
}
