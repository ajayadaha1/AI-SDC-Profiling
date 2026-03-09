import { useCallback } from 'react';
import { sendChatMessage } from '../services/chatApi';
import { useChatStore } from '../stores/chatStore';
import type { PredictionData, ParsedProfile, SSEEvent, SearchCompleteData } from '../types/chat';

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
    addThinkingStep,
    updateThinkingStep,
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
      resetStreamingState();
      setStreaming(true);
      setPipelineStage('idle');

      const handleEvent = (event: SSEEvent) => {
        setPipelineStage(event.type as ReturnType<typeof useChatStore.getState>['pipelineStage']);

        switch (event.type) {
          case 'parsing_started':
            addThinkingStep({
              id: 'parse',
              stage: 'parsing_started',
              label: 'Analyzing failure symptoms',
              detail: 'Sending description to LLM for structured parsing...',
              status: 'running',
              timestamp: Date.now(),
            });
            break;

          case 'parsing_complete': {
            const profile = event.data as unknown as ParsedProfile;
            setParsedProfile(profile);
            updateThinkingStep('parse', {
              status: 'done',
              label: 'Failure symptoms parsed',
              detail: `Identified: ${profile.failure_type}${profile.mce_bank !== null ? ` (Bank ${profile.mce_bank})` : ''} — confidence ${Math.round((profile.confidence ?? 0) * 100)}%`,
              data: event.data,
            });
            break;
          }

          case 'search_started':
            addThinkingStep({
              id: 'search',
              stage: 'search_started',
              label: 'Querying Snowflake databases',
              detail: 'Searching MSFT_MCEFAIL, LEVEL3DEBUG_LOGFILES, AURA_PMDATA, PRISM_PMDATA...',
              status: 'running',
              timestamp: Date.now(),
            });
            break;

          case 'search_complete': {
            const searchData = event.data as unknown as SearchCompleteData;
            setSearchResult(searchData);
            const srcList = searchData.sources?.join(', ') ?? '';
            updateThinkingStep('search', {
              status: 'done',
              label: `Found ${searchData.count?.toLocaleString()} records from ${searchData.sources?.length ?? 0} source(s)`,
              detail: srcList ? `Sources: ${srcList}` : undefined,
              data: event.data,
            });
            break;
          }

          case 'ranking_started':
            addThinkingStep({
              id: 'rank',
              stage: 'ranking_started',
              label: 'AI ranking debug commands',
              detail: 'LLM analyzing tool distributions to recommend top AFHC/ANC commands...',
              status: 'running',
              timestamp: Date.now(),
            });
            break;

          case 'prediction': {
            const prediction = event.data as unknown as PredictionData;
            setCurrentPrediction(prediction);
            const topTools = prediction.commands?.slice(0, 3).map((c) => c.command).join(', ') ?? '';
            updateThinkingStep('rank', {
              status: 'done',
              label: 'Commands ranked',
              detail: topTools ? `Top picks: ${topTools}` : undefined,
            });
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

          case 'conversational':
            addThinkingStep({
              id: 'conv',
              stage: 'conversational',
              label: 'Generating response',
              detail: 'Processing conversational input...',
              status: 'running',
              timestamp: Date.now(),
            });
            break;

          case 'chat_response':
            updateThinkingStep('conv', { status: 'done', label: 'Response ready' });
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
        // Don't reset immediately — let the thinking panel linger for the user
        // resetStreamingState() clears thinkingSteps; we delay it
        useChatStore.getState().setStreaming(false);
        useChatStore.getState().setPipelineStage('done');
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
      addThinkingStep,
      updateThinkingStep,
    ],
  );

  return { send };
}
