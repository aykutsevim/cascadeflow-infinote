import { useState, useRef, useCallback, useEffect } from 'react';
import { createShapeId } from 'tldraw';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Box,
  Typography,
  CircularProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  Chip,
  Paper,
  Fab,
  Tooltip,
  LinearProgress,
  Snackbar,
} from '@mui/material';
import {
  CameraAlt as CameraIcon,
  Close as CloseIcon,
  PhotoCamera as PhotoCameraIcon,
  Upload as UploadIcon,
  CheckCircle as CheckCircleIcon,
  AddToPhotos as AddToCanvasIcon,
} from '@mui/icons-material';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const priorityColors = {
  urgent: 'error',
  high: 'warning',
  medium: 'info',
  low: 'success',
};

const priorityColorHex = {
  urgent: '#ef4444',
  high: '#f97316',
  medium: '#3b82f6',
  low: '#22c55e',
};

// Polling configuration
const POLL_CONFIG = {
  initialInterval: 1000,    // Start with 1 second
  maxInterval: 5000,        // Max 5 seconds between polls
  backoffMultiplier: 1.5,   // Increase interval by 50% each time
  maxAttempts: 120,         // Max 120 attempts (about 5 minutes with backoff)
  timeout: 300000,          // 5 minute absolute timeout
};

export default function PhotoCapture({ editor }) {
  const [open, setOpen] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [extractedTasks, setExtractedTasks] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [pollProgress, setPollProgress] = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [tasksAddedToCanvas, setTasksAddedToCanvas] = useState(false);

  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const pollAbortRef = useRef(null);
  const pollStartTimeRef = useRef(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollAbortRef.current) {
        pollAbortRef.current.abort = true;
      }
    };
  }, []);

  const handleOpen = () => {
    setOpen(true);
    setError(null);
  };

  const handleClose = () => {
    setOpen(false);
    stopCamera();
    stopPolling();
    resetState();
  };

  const resetState = () => {
    setPreviewUrl(null);
    setSelectedFile(null);
    setExtractedTasks(null);
    setJobStatus(null);
    setPollProgress(0);
    setTasksAddedToCanvas(false);
    setError(null);
  };

  const stopPolling = () => {
    if (pollAbortRef.current) {
      pollAbortRef.current.abort = true;
    }
  };

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      setCameraOpen(true);
    } catch (err) {
      setError('Unable to access camera. Please check permissions or use file upload.');
      console.error('Camera error:', err);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setCameraOpen(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
      if (blob) {
        const file = new File([blob], 'captured-photo.jpg', { type: 'image/jpeg' });
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(blob));
        stopCamera();
      }
    }, 'image/jpeg', 0.9);
  };

  const handleFileSelect = (event) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!['image/jpeg', 'image/jpg', 'image/png'].includes(file.type)) {
        setError('Please select a JPG or PNG image.');
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError('Image size must be less than 10MB.');
        return;
      }
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
    }
  };

  const pollJobStatus = useCallback(async (transactionId) => {
    const abortController = { abort: false };
    pollAbortRef.current = abortController;
    pollStartTimeRef.current = Date.now();

    let attempts = 0;
    let currentInterval = POLL_CONFIG.initialInterval;

    const poll = async () => {
      if (abortController.abort) return;

      const elapsed = Date.now() - pollStartTimeRef.current;
      if (elapsed > POLL_CONFIG.timeout) {
        setError('Processing timeout. The server might be busy. Please try again later.');
        setProcessing(false);
        return;
      }

      try {
        const response = await fetch(`${API_URL}/api/status/${transactionId}/`);
        if (!response.ok) throw new Error('Failed to check status');

        const data = await response.json();
        setJobStatus(data.status);

        // Update progress based on status
        if (data.status === 'pending') {
          setPollProgress(10);
        } else if (data.status === 'processing') {
          setPollProgress(Math.min(90, 30 + (attempts * 2)));
        }

        if (data.status === 'completed') {
          setPollProgress(100);
          setExtractedTasks(data.extracted_tasks || []);
          setProcessing(false);
          return;
        }

        if (data.status === 'failed') {
          setError(data.error_message || 'Processing failed. Please try again with a different image.');
          setProcessing(false);
          return;
        }

        attempts++;
        if (attempts < POLL_CONFIG.maxAttempts) {
          // Exponential backoff
          currentInterval = Math.min(
            currentInterval * POLL_CONFIG.backoffMultiplier,
            POLL_CONFIG.maxInterval
          );
          setTimeout(poll, currentInterval);
        } else {
          setError('Processing timeout after maximum attempts. Please try again.');
          setProcessing(false);
        }
      } catch (err) {
        console.error('Polling error:', err);
        // Retry on network errors with backoff
        attempts++;
        if (attempts < POLL_CONFIG.maxAttempts) {
          currentInterval = Math.min(
            currentInterval * POLL_CONFIG.backoffMultiplier,
            POLL_CONFIG.maxInterval
          );
          setTimeout(poll, currentInterval);
        } else {
          setError('Failed to check processing status. Please check your connection.');
          setProcessing(false);
        }
      }
    };

    poll();
  }, []);

  const uploadImage = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setPollProgress(0);

    try {
      const formData = new FormData();
      formData.append('image', selectedFile);

      const response = await fetch(`${API_URL}/api/upload/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Upload failed');
      }

      const data = await response.json();
      setUploading(false);
      setProcessing(true);
      setJobStatus('pending');
      setPollProgress(5);

      pollJobStatus(data.transaction_id);
    } catch (err) {
      setError(err.message || 'Failed to upload image');
      setUploading(false);
    }
  };

  // Create task boxes on the tldraw canvas
  const createTasksOnCanvas = useCallback(() => {
    if (!editor || !extractedTasks || extractedTasks.length === 0) {
      setSnackbar({
        open: true,
        message: 'No tasks to add or canvas not ready',
        severity: 'warning',
      });
      return;
    }

    try {
      // Get the current viewport bounds
      const viewportPageBounds = editor.getViewportPageBounds();

      // Calculate starting position (top-left of visible area with padding)
      const startX = viewportPageBounds.x + 50;
      const startY = viewportPageBounds.y + 50;

      // Card dimensions
      const cardWidth = 280;
      const cardHeight = 160;
      const cardGap = 20;
      const cardsPerRow = 3;

      const shapes = extractedTasks.map((task, index) => {
        const row = Math.floor(index / cardsPerRow);
        const col = index % cardsPerRow;

        const x = startX + (col * (cardWidth + cardGap));
        const y = startY + (row * (cardHeight + cardGap));

        // Create a task-card shape for each task
        return {
          id: createShapeId(),
          type: 'task-card',
          x,
          y,
          props: {
            w: cardWidth,
            h: cardHeight,
            taskName: task.task_name || 'Untitled Task',
            description: task.description || '',
            assignee: task.assignee || '',
            dueDate: task.due_date || '',
            priority: task.priority || 'medium',
          },
        };
      });

      // Create all shapes at once
      editor.createShapes(shapes);

      // Select the new shapes
      editor.select(...shapes.map(s => s.id));

      // Zoom to fit the new shapes
      editor.zoomToSelection();

      setTasksAddedToCanvas(true);
      setSnackbar({
        open: true,
        message: `${extractedTasks.length} task${extractedTasks.length !== 1 ? 's' : ''} added to canvas!`,
        severity: 'success',
      });

      // Close the dialog after adding to canvas
      setTimeout(() => {
        handleClose();
      }, 1500);

    } catch (err) {
      console.error('Error creating shapes:', err);
      setSnackbar({
        open: true,
        message: 'Failed to add tasks to canvas. Please try again.',
        severity: 'error',
      });
    }
  }, [editor, extractedTasks]);

  const handleSnackbarClose = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <>
      <Tooltip title="Capture handwritten tasks" placement="left">
        <Fab
          color="primary"
          onClick={handleOpen}
          sx={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 1000,
          }}
        >
          <CameraIcon />
        </Fab>
      </Tooltip>

      <Dialog
        open={open}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { maxHeight: '90vh' } }}
      >
        <DialogTitle sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span>Capture Task List</span>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>

        <DialogContent dividers>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {!previewUrl && !cameraOpen && !extractedTasks && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, alignItems: 'center', py: 3 }}>
              <Typography variant="body1" color="text.secondary" textAlign="center">
                Take a photo or upload an image of your handwritten task list
              </Typography>

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<PhotoCameraIcon />}
                  onClick={startCamera}
                >
                  Take Photo
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<UploadIcon />}
                  onClick={() => fileInputRef.current?.click()}
                >
                  Upload Image
                </Button>
              </Box>

              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/jpg,image/png"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
            </Box>
          )}

          {cameraOpen && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <video
                ref={videoRef}
                autoPlay
                playsInline
                style={{ width: '100%', maxHeight: '400px', borderRadius: 8 }}
              />
              <canvas ref={canvasRef} style={{ display: 'none' }} />

              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant="contained" onClick={capturePhoto}>
                  Capture
                </Button>
                <Button variant="outlined" onClick={stopCamera}>
                  Cancel
                </Button>
              </Box>
            </Box>
          )}

          {previewUrl && !extractedTasks && (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <img
                src={previewUrl}
                alt="Preview"
                style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: 8 }}
              />

              {!uploading && !processing && (
                <Box sx={{ display: 'flex', gap: 2 }}>
                  <Button variant="contained" onClick={uploadImage}>
                    Extract Tasks
                  </Button>
                  <Button variant="outlined" onClick={resetState}>
                    Retake
                  </Button>
                </Box>
              )}

              {(uploading || processing) && (
                <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2, width: '100%' }}>
                  <Box sx={{ width: '100%', px: 2 }}>
                    <LinearProgress
                      variant="determinate"
                      value={pollProgress}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={20} />
                    <Typography variant="body2" color="text.secondary">
                      {uploading ? 'Uploading image...' : getStatusMessage(jobStatus)}
                    </Typography>
                  </Box>
                  <Typography variant="caption" color="text.secondary">
                    {pollProgress}% complete
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {extractedTasks && (
            <Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <CheckCircleIcon color="success" />
                <Typography variant="h6">
                  {extractedTasks.length} Task{extractedTasks.length !== 1 ? 's' : ''} Extracted
                </Typography>
              </Box>

              {extractedTasks.length === 0 ? (
                <Alert severity="info">
                  No tasks were detected in the image. Try with a clearer image or different handwriting.
                </Alert>
              ) : (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<AddToCanvasIcon />}
                      onClick={createTasksOnCanvas}
                      disabled={tasksAddedToCanvas || !editor}
                      fullWidth
                      size="large"
                    >
                      {tasksAddedToCanvas ? 'Tasks Added to Canvas!' : 'Add All Tasks to Canvas'}
                    </Button>
                  </Box>

                  <List sx={{ maxHeight: '300px', overflow: 'auto' }}>
                    {extractedTasks.map((task, index) => (
                      <Paper key={task.id || index} elevation={1} sx={{ mb: 1 }}>
                        <ListItem>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="subtitle1" component="span">{task.task_name}</Typography>
                                <Chip
                                  label={task.priority}
                                  size="small"
                                  color={priorityColors[task.priority] || 'default'}
                                />
                              </Box>
                            }
                            secondary={
                              <Box component="span" sx={{ display: 'block', mt: 0.5 }}>
                                {task.description && (
                                  <Typography variant="body2" color="text.secondary" component="span" display="block">
                                    {task.description}
                                  </Typography>
                                )}
                                <Box component="span" sx={{ display: 'flex', gap: 2, mt: 0.5 }}>
                                  {task.assignee && (
                                    <Typography variant="caption" color="text.secondary" component="span">
                                      Assignee: {task.assignee}
                                    </Typography>
                                  )}
                                  {task.due_date && (
                                    <Typography variant="caption" color="text.secondary" component="span">
                                      Due: {task.due_date}
                                    </Typography>
                                  )}
                                </Box>
                              </Box>
                            }
                            secondaryTypographyProps={{ component: 'div' }}
                          />
                        </ListItem>
                      </Paper>
                    ))}
                  </List>
                </>
              )}
            </Box>
          )}
        </DialogContent>

        <DialogActions>
          {extractedTasks && extractedTasks.length > 0 && !tasksAddedToCanvas && (
            <Button onClick={resetState} variant="outlined">
              Capture Another
            </Button>
          )}
          <Button onClick={handleClose}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
}

// Helper function to get user-friendly status messages
function getStatusMessage(status) {
  switch (status) {
    case 'pending':
      return 'Waiting in queue...';
    case 'processing':
      return 'Analyzing handwriting and extracting tasks...';
    case 'completed':
      return 'Processing complete!';
    case 'failed':
      return 'Processing failed';
    default:
      return 'Processing...';
  }
}
