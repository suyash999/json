"""
Video Processor
===============
Handles video file reading and frame extraction using OpenCV.
Optimized for sequential processing with configurable skip intervals.
"""

import cv2
import numpy as np
from typing import Optional, Tuple


class VideoProcessor:
    """Reads video frames sequentially with metadata tracking."""
    
    def __init__(self, video_path: str):
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_frame_idx = 0
    
    def read_frame(self) -> Optional[np.ndarray]:
        """Read next frame. Returns None when video ends."""
        ret, frame = self.cap.read()
        if not ret:
            return None
        self.current_frame_idx += 1
        return frame
    
    def skip_to(self, frame_idx: int) -> Optional[np.ndarray]:
        """Jump to a specific frame index."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        self.current_frame_idx = frame_idx
        return self.read_frame()
    
    def get_timestamp(self) -> float:
        """Get current position in seconds."""
        return self.current_frame_idx / self.fps
    
    def get_frame_at_time(self, seconds: float) -> Optional[np.ndarray]:
        """Get frame at specific timestamp."""
        frame_idx = int(seconds * self.fps)
        return self.skip_to(frame_idx)
    
    @property
    def duration(self) -> float:
        """Total video duration in seconds."""
        return self.total_frames / self.fps
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Video resolution as (width, height)."""
        return (self.width, self.height)
    
    def release(self):
        """Release the video capture resource."""
        if self.cap:
            self.cap.release()
    
    def __del__(self):
        self.release()
    
    def __repr__(self):
        return (
            f"VideoProcessor({self.video_path}, "
            f"{self.width}x{self.height} @ {self.fps:.1f}fps, "
            f"{self.duration:.1f}s)"
        )
