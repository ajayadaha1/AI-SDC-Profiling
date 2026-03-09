import { useEffect, useRef } from 'react';
import { Box, Typography } from '@mui/material';
import Header from '../layout/Header';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import ThinkingProcess from './ThinkingProcess';
import { useChatStore } from '../../stores/chatStore';
import { useConversationMessages } from '../../hooks/useConversations';

export default function ChatPage() {
  const {
    activeConversationId,
    messages,
    setMessages,
    isStreaming,
    thinkingSteps,
    parsedProfile,
    searchResult,
  } = useChatStore();
  const { data: convDetail } = useConversationMessages(activeConversationId);

  // Track which conversation we last loaded from server.
  // Only overwrite local messages when the user switches conversations,
  // NOT when streaming state or TanStack cache changes (which would wipe
  // locally-added messages from the current exchange).
  const loadedConvRef = useRef<string | null>(null);

  // Reset tracker when switching conversations
  useEffect(() => {
    loadedConvRef.current = null;
  }, [activeConversationId]);

  // Load server messages only once per conversation switch
  useEffect(() => {
    if (
      convDetail?.messages &&
      activeConversationId &&
      activeConversationId !== loadedConvRef.current &&
      !isStreaming
    ) {
      setMessages(convDetail.messages);
      loadedConvRef.current = activeConversationId;
    }
  }, [convDetail, activeConversationId, setMessages, isStreaming]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <Header />
      <Box sx={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
        {!activeConversationId ? (
          <Box
            sx={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: 2,
            }}
          >
            <Typography variant="h5" sx={{ fontWeight: 700, color: 'text.secondary' }}>
              AI SDC Profiling
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 500, textAlign: 'center' }}>
              Describe CPU failure symptoms or upload MCE screenshots to get ranked AFHC/ANC debug command predictions.
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Create a new analysis from the sidebar to get started.
            </Typography>
          </Box>
        ) : (
          <>
            <MessageList messages={messages} />
            {thinkingSteps.length > 0 && (
              <ThinkingProcess
                steps={thinkingSteps}
                isStreaming={isStreaming}
                parsedProfile={parsedProfile}
                searchResult={searchResult}
              />
            )}
          </>
        )}
      </Box>
      {activeConversationId && <ChatInput />}
    </Box>
  );
}
