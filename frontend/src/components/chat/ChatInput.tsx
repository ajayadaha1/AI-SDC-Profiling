import { useState, useRef, useCallback } from 'react';
import { Box, TextField, IconButton, Chip, Backdrop, Typography } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import CloseIcon from '@mui/icons-material/Close';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useChat } from '../../hooks/useChat';
import { useImageUpload } from '../../hooks/useImageUpload';
import { useChatStore } from '../../stores/chatStore';

export default function ChatInput() {
  const [text, setText] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { send } = useChat();
  const isStreaming = useChatStore((s) => s.isStreaming);
  const { pendingImages, handleDrop, handlePaste, handleFileSelect, removePendingImage } =
    useImageUpload();

  const handleSend = useCallback(() => {
    if (!text.trim() && pendingImages.length === 0) return;
    if (isStreaming) return;
    send(text.trim());
    setText('');
  }, [text, pendingImages.length, isStreaming, send]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const onDragLeave = () => setDragOver(false);

  const onDrop = (e: React.DragEvent) => {
    setDragOver(false);
    handleDrop(e);
  };

  return (
    <Box
      sx={{ px: { xs: 2, md: 4 }, pb: 2, pt: 1, position: 'relative' }}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {/* Drag overlay */}
      <Backdrop
        open={dragOver}
        sx={{
          position: 'absolute',
          zIndex: 1,
          bgcolor: 'rgba(124, 138, 255, 0.1)',
          borderRadius: 2,
          border: '2px dashed',
          borderColor: 'primary.main',
          top: 0,
          left: 16,
          right: 16,
          bottom: 8,
        }}
      >
        <Box sx={{ textAlign: 'center' }}>
          <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main' }} />
          <Typography color="primary">Drop images here</Typography>
        </Box>
      </Backdrop>

      {/* Pending image previews */}
      {pendingImages.length > 0 && (
        <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap' }}>
          {pendingImages.map((file, idx) => (
            <Chip
              key={idx}
              label={file.name}
              size="small"
              onDelete={() => removePendingImage(idx)}
              deleteIcon={<CloseIcon />}
              sx={{ maxWidth: 200 }}
            />
          ))}
        </Box>
      )}

      {/* Input area */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          multiple
          style={{ display: 'none' }}
          onChange={handleFileSelect}
        />
        <IconButton
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming}
          size="small"
          sx={{ mb: 0.5 }}
        >
          <AttachFileIcon />
        </IconButton>
        <TextField
          fullWidth
          multiline
          maxRows={4}
          placeholder="Describe CPU failure symptoms... (Shift+Enter for new line)"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          disabled={isStreaming}
          variant="outlined"
          size="small"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2,
              bgcolor: 'background.paper',
            },
          }}
        />
        <IconButton
          onClick={handleSend}
          disabled={isStreaming || (!text.trim() && pendingImages.length === 0)}
          color="primary"
          sx={{ mb: 0.5 }}
        >
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}
