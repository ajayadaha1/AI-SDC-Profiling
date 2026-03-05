import { create } from 'zustand';
import type { ConversationSummary, Message, PipelineStage, PredictionData, ParsedProfile } from '../types/chat';

interface ChatState {
  // Conversations
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  setConversations: (conversations: ConversationSummary[]) => void;
  setActiveConversation: (id: string | null) => void;
  addConversation: (conv: ConversationSummary) => void;
  removeConversation: (id: string) => void;

  // Messages
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;

  // Streaming state
  isStreaming: boolean;
  pipelineStage: PipelineStage;
  parsedProfile: ParsedProfile | null;
  searchResult: { tier: number; count: number } | null;
  currentPrediction: PredictionData | null;
  setStreaming: (streaming: boolean) => void;
  setPipelineStage: (stage: PipelineStage) => void;
  setParsedProfile: (profile: ParsedProfile | null) => void;
  setSearchResult: (result: { tier: number; count: number } | null) => void;
  setCurrentPrediction: (prediction: PredictionData | null) => void;

  // Pending images
  pendingImages: File[];
  addPendingImage: (file: File) => void;
  removePendingImage: (index: number) => void;
  clearPendingImages: () => void;

  // Reset
  resetStreamingState: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  activeConversationId: null,
  setConversations: (conversations) => set({ conversations }),
  setActiveConversation: (id) => set({ activeConversationId: id }),
  addConversation: (conv) =>
    set((state) => ({ conversations: [conv, ...state.conversations] })),
  removeConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter((c) => c.id !== id),
      activeConversationId: state.activeConversationId === id ? null : state.activeConversationId,
    })),

  messages: [],
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),

  isStreaming: false,
  pipelineStage: 'idle',
  parsedProfile: null,
  searchResult: null,
  currentPrediction: null,
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setPipelineStage: (stage) => set({ pipelineStage: stage }),
  setParsedProfile: (profile) => set({ parsedProfile: profile }),
  setSearchResult: (result) => set({ searchResult: result }),
  setCurrentPrediction: (prediction) => set({ currentPrediction: prediction }),

  pendingImages: [],
  addPendingImage: (file) =>
    set((state) => ({ pendingImages: [...state.pendingImages, file] })),
  removePendingImage: (index) =>
    set((state) => ({
      pendingImages: state.pendingImages.filter((_, i) => i !== index),
    })),
  clearPendingImages: () => set({ pendingImages: [] }),

  resetStreamingState: () =>
    set({
      isStreaming: false,
      pipelineStage: 'idle',
      parsedProfile: null,
      searchResult: null,
      currentPrediction: null,
    }),
}));
