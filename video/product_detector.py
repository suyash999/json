"""
Product Detector
================
Detects when a new product/card is being shown in the stream.

Uses scene-change detection (structural similarity + histogram comparison)
instead of heavy object detection models. This is CPU-friendly and works
well for the typical auction stream pattern where the seller holds up
items one at a time against a relatively stable background.

Detection strategy:
1. Compare current frame to last captured product frame
2. If difference exceeds threshold → new product detected
3. Wait for frame stability (product held still) before capturing
4. Apply basic quality filters (blur, brightness)
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List


class ProductDetector:
    """
    Detects new products being shown in a video stream and captures snapshots.
    """
    
    def __init__(
        self,
        threshold: float = 0.4,
        stability_frames: int = 3,
        min_area_ratio: float = 0.05,
    ):
        """
        Args:
            threshold: Scene change threshold (0-1). Lower = more sensitive.
            stability_frames: Frames product must be stable before capture.
            min_area_ratio: Minimum ratio of frame area for a valid product region.
        """
        self.threshold = threshold
        self.stability_frames = stability_frames
        self.min_area_ratio = min_area_ratio
        
        self._last_captured_hist = None
        self._last_frame_hist = None
        self._stability_count = 0
        self._candidate_frame = None
        self._captured_products: List[np.ndarray] = []
    
    def _compute_histogram(self, frame: np.ndarray) -> np.ndarray:
        """Compute normalized color histogram for comparison."""
        if len(frame.shape) == 3:
            # Use HSV for better color comparison
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist(
                [hsv], [0, 1], None, [50, 60],
                [0, 180, 0, 256]
            )
        else:
            hist = cv2.calcHist([frame], [0], None, [256], [0, 256])
        
        cv2.normalize(hist, hist)
        return hist.flatten()
    
    def _compute_structural_diff(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Compute structural difference between two frames.
        Returns value 0-1 where 0 = identical, 1 = completely different.
        """
        # Resize both to same small size for fast comparison
        size = (160, 120)
        f1 = cv2.resize(frame1, size)
        f2 = cv2.resize(frame2, size)
        
        # Convert to grayscale
        if len(f1.shape) == 3:
            f1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
        if len(f2.shape) == 3:
            f2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
        
        # Compute absolute difference
        diff = cv2.absdiff(f1, f2)
        
        # Normalize to 0-1
        score = np.mean(diff) / 255.0
        return score
    
    def _histogram_similarity(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """
        Compare two histograms using correlation.
        Returns 0-1 where 1 = identical.
        """
        if hist1 is None or hist2 is None:
            return 0.0
        similarity = cv2.compareHist(
            hist1.reshape(-1, 1).astype(np.float32),
            hist2.reshape(-1, 1).astype(np.float32),
            cv2.HISTCMP_CORREL,
        )
        return max(0.0, similarity)
    
    def _check_image_quality(self, frame: np.ndarray) -> bool:
        """
        Basic quality check to avoid capturing blurry or dark frames.
        """
        if frame is None or frame.size == 0:
            return False
        
        gray = frame if len(frame.shape) == 2 else cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Check brightness
        mean_brightness = np.mean(gray)
        if mean_brightness < 30 or mean_brightness > 240:
            return False
        
        # Check blur using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 50:
            return False
        
        return True
    
    def _is_scene_change(self, frame: np.ndarray) -> bool:
        """Determine if current frame represents a new product."""
        current_hist = self._compute_histogram(frame)
        
        if self._last_captured_hist is None:
            # First frame — always capture
            self._last_captured_hist = current_hist
            return True
        
        # Compare with last captured product
        hist_sim = self._histogram_similarity(current_hist, self._last_captured_hist)
        
        # If histograms are very different, it's a scene change
        if hist_sim < (1.0 - self.threshold):
            return True
        
        return False
    
    def detect_new_product(
        self, frame: np.ndarray, timestamp: float
    ) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Check if a new product is being shown and capture it.
        
        Args:
            frame: Current video frame (product region crop)
            timestamp: Current video timestamp
            
        Returns:
            (is_new_product, captured_image_or_None)
        """
        if frame is None or frame.size == 0:
            return False, None
        
        is_change = self._is_scene_change(frame)
        
        if is_change:
            # Check if frame is stable (not mid-transition)
            if self._candidate_frame is not None:
                structural_diff = self._compute_structural_diff(frame, self._candidate_frame)
                if structural_diff < 0.08:  # Frame is stable
                    self._stability_count += 1
                else:
                    self._stability_count = 0
                    self._candidate_frame = frame.copy()
            else:
                self._candidate_frame = frame.copy()
                self._stability_count = 0
            
            # Capture when stable enough and good quality
            if self._stability_count >= self.stability_frames:
                if self._check_image_quality(frame):
                    captured = frame.copy()
                    self._last_captured_hist = self._compute_histogram(frame)
                    self._stability_count = 0
                    self._candidate_frame = None
                    self._captured_products.append(captured)
                    return True, captured
        else:
            self._stability_count = 0
            self._candidate_frame = None
        
        return False, None
    
    def get_product_count(self) -> int:
        """Number of products captured so far."""
        return len(self._captured_products)
    
    def get_all_products(self) -> List[np.ndarray]:
        """Get all captured product images."""
        return self._captured_products.copy()
    
    def reset(self):
        """Reset detector state."""
        self._last_captured_hist = None
        self._last_frame_hist = None
        self._stability_count = 0
        self._candidate_frame = None
        self._captured_products.clear()
