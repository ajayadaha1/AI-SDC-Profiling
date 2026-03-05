import { useEffect } from 'react';
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  Typography,
  IconButton,
  Divider,
  Button,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { formatDistanceToNow } from 'date-fns';
import { useChatStore } from '../../stores/chatStore';
import { useConversations, useCreateConversation, useDeleteConversation } from '../../hooks/useConversations';

interface SidebarProps {
  width: number;
}

export default function Sidebar({ width }: SidebarProps) {
  const { activeConversationId, setActiveConversation, setConversations, setMessages, resetStreamingState } =
    useChatStore();
  const { data: conversations, isLoading } = useConversations();
  const createMutation = useCreateConversation();
  const deleteMutation = useDeleteConversation();

  useEffect(() => {
    if (conversations) {
      setConversations(conversations);
    }
  }, [conversations, setConversations]);

  const handleNew = async () => {
    const conv = await createMutation.mutateAsync('New Analysis');
    setActiveConversation(conv.id);
    setMessages([]);
    resetStreamingState();
  };

  const handleSelect = (id: string) => {
    setActiveConversation(id);
    setMessages([]);
    resetStreamingState();
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    await deleteMutation.mutateAsync(id);
  };

  return (
    <Box
      sx={{
        width,
        height: '100vh',
        bgcolor: 'background.default',
        borderRight: 1,
        borderColor: 'divider',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, fontSize: '1rem' }}>
          AI SDC Profiling
        </Typography>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={handleNew}
          disabled={createMutation.isPending}
          sx={{ textTransform: 'none' }}
        >
          New Analysis
        </Button>
      </Box>
      <Divider />
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {isLoading ? (
          <Typography sx={{ p: 2, color: 'text.secondary', fontSize: '0.85rem' }}>Loading...</Typography>
        ) : (
          <List dense disablePadding>
            {(conversations || []).map((conv) => (
              <ListItemButton
                key={conv.id}
                selected={conv.id === activeConversationId}
                onClick={() => handleSelect(conv.id)}
                sx={{ px: 2, py: 1 }}
              >
                <ListItemText
                  primary={conv.title || 'Untitled'}
                  secondary={formatDistanceToNow(new Date(conv.created_at), { addSuffix: true })}
                  primaryTypographyProps={{ noWrap: true, fontSize: '0.85rem' }}
                  secondaryTypographyProps={{ fontSize: '0.75rem' }}
                />
                <IconButton
                  size="small"
                  onClick={(e) => handleDelete(e, conv.id)}
                  sx={{ opacity: 0.5, '&:hover': { opacity: 1 } }}
                >
                  <DeleteOutlineIcon fontSize="small" />
                </IconButton>
              </ListItemButton>
            ))}
          </List>
        )}
      </Box>
    </Box>
  );
}
