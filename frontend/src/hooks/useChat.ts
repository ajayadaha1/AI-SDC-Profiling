import { useCallback } from 'react';
import { sendChatMessage } from '../services/chatApi';
import { useChatStore } from '../stores/chatStore';
import type { PredictionData, ParsedProfile, SSEEvent } from '../types/chat';

export function useChat() {
  const {
    activeConversationId,
    isStreaming,
    pendingImages,
    addMessage,
    setStreaming,
    setPipelineStage,
    setParsedProfile,
    setSearchResult,
    setCurrentPrediction,
    clearPendingImages,
    resetStreamingState,
  } = useChatStore();

  const send = useCallback(
    async (text: string) => {
      if (!activeConversationId || isStreaming || !text.trim()) return;

      // Add user message to UI
      addMessage({
        conversation_id: activeConversationId,
        role: 'user',
        content_text: text,
        content_structured: null,
        message_type: 'text',
        created_at: new Date().toISOString(),
        images: [],
      });

      const imagesToSend = [...pendingImages];
      clearPendingImages();
      setStreaming(true);
      setPipelineStage('idle');

      const handleEvent = (event: SSEEvent) => {
        setPipelineStage(event.type as ReturnType<typeof useChatStore.getState>['pipelineStage']);

        switch (event.type) {
          case 'parsing_complete':
            setParsedProfile(event.data as unknown as ParsedProfile);
            break;
          case 'search_complete':
            setSearchResult(event.data as unknown as { tier: number; count: number });
            break;
          case 'prediction': {
            const prediction = event.data as unknown as PredictionData;
            setCurrentPrediction(prediction);
            addMessage({
              conversation_id: activeConversationId,
              role: 'assistant',
              content_text: null,
              content_structured: JSON.stringify(prediction),
              message_type: 'prediction',
              created_at: new Date().toISOString(),
              images: [],
            });
            break;
          }
          case 'chat_response':
            addMessage({
              conversation_id: activeConversationId,
              role: 'assistant',
              content_text: (event.data as Record<string, string>).message || '',
              content_structured: null,
              message_type: 'text',
              created_at: new Date().toISOString(),
              images: [],
            });
            break;
          case 'error':
            addMessage({
              conversation_id: activeConversationId,
              role: 'assistant',
              content_text: (event.data as Record<string, string>).message || 'An error occurred',
              content_structured: null,
              message_type: 'error',
              created_at: new Date().toISOString(),
              images: [],
            });
            break;
        }
      };

      const handleDone = () => {
        resetStreamingState();
      };

      const handleError = (error: Error) => {
        addMessage({
          conversation_id: activeConversationId,
          role: 'assistant',
          content_text: `Connection error: ${error.message}`,
          content_structured: null,
          message_type: 'error',
          created_at: new Date().toISOString(),
          images: [],
        });
        resetStreamingState();
      };

      await sendChatMessage(
        activeConversationId,
        text,
        imagesToSend,
        handleEvent,
        handleDone,
        handleError,
      );
    },
    [
      activeConversationId,
      isStreaming,
      pendingImages,
      addMessage,
      setStreaming,
      setPipelineStage,
      setParsedProfile,
      setSearchResult,
      setCurrentPrediction,
      clearPendingImages,
      resetStreamingState,
    ],
  );

  return { send };
}
