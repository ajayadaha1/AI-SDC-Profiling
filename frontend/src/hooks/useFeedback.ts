import { useMutation } from '@tanstack/react-query';
import { submitFeedback } from '../services/feedbackApi';
import type { FeedbackSubmission } from '../types/api';

export function useFeedback() {
  return useMutation({
    mutationFn: (feedback: FeedbackSubmission) => submitFeedback(feedback),
  });
}
