import type { SSEEvent } from '../types/chat';

export async function sendChatMessage(
  conversationId: string,
  text: string,
  images: File[],
  onEvent: (event: SSEEvent) => void,
  onDone: () => void,
  onError: (error: Error) => void,
): Promise<void> {
  const formData = new FormData();
  formData.append('conversation_id', conversationId);
  formData.append('text', text);
  images.forEach((img) => formData.append('images', img));

  try {
    const response = await fetch('/ai-failure-profiling-api/api/chat', {
      method: 'POST',
      body: formData,
      headers: {
        Accept: 'text/event-stream',
      },
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.status}`);
    }

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEventType = '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const dataStr = line.slice(6).trim();
          try {
            const data = JSON.parse(dataStr);
            onEvent({ type: currentEventType, data });
          } catch {
            // Skip malformed JSON
          }
          currentEventType = '';
        }
      }
    }

    onDone();
  } catch (error) {
    onError(error instanceof Error ? error : new Error(String(error)));
  }
}
