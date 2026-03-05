import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import type { ConversationSummary } from '../types/chat';

export function useConversations() {
  return useQuery<ConversationSummary[]>({
    queryKey: ['conversations'],
    queryFn: async () => {
      const response = await api.get('/api/conversations');
      return response.data;
    },
  });
}

export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (title?: string) => {
      const response = await api.post('/api/conversations', { title });
      return response.data as ConversationSummary;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/api/conversations/${id}`);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['conversations'] });
    },
  });
}

export function useConversationMessages(conversationId: string | null) {
  return useQuery({
    queryKey: ['conversation', conversationId],
    queryFn: async () => {
      if (!conversationId) return null;
      const response = await api.get(`/api/conversations/${conversationId}`);
      return response.data;
    },
    enabled: !!conversationId,
  });
}
