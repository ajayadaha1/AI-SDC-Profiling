import api from './api';
import type { FeedbackSubmission } from '../types/api';

export async function submitFeedback(feedback: FeedbackSubmission) {
  const response = await api.post('/api/feedback', feedback);
  return response.data;
}
