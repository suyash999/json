"""
OCR Engine
==========
Extracts text from video frames using EasyOCR.
Includes preprocessing pipeline optimized for live-stream chat overlays:
- Contrast enhancement for dark/semi-transparent chat backgrounds
- Noise reduction
- Text region isolation
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class OCREngine:
    """
    OCR engine for extracting text from video frames.
    Uses EasyOCR (CPU-optimized) with preprocessing for stream overlays.
    """
    
    def __init__(self, languages: List[str] = None, use_gpu: bool = False):
        """
        Initialize OCR engine.
        
        Args:
            languages: List of language codes (default: ['en'])
            use_gpu: Whether to use GPU acceleration (default: False for Apple Silicon)
        """
        self.languages = languages or ["en"]
        self.use_gpu = use_gpu
        self._reader = None  # Lazy initialization
        self._fallback_to_tesseract = False
    
    @property
    def reader(self):
        """Lazy-load the EasyOCR reader (it's heavy on import)."""
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(
                    self.languages,
                    gpu=self.use_gpu,
                    verbose=False,
                )
            except ImportError:
                # Fallback to pytesseract if easyocr not available
                self._fallback_to_tesseract = True
                try:
                    import pytesseract
                    self._reader = pytesseract
                except ImportError:
                    raise ImportError(
                        "Neither easyocr nor pytesseract is installed. "
                        "Install one: pip install easyocr  OR  pip install pytesseract"
                    )
        return self._reader
    
    def preprocess_chat_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess a chat region crop for better OCR accuracy.
        
        Handles common live-stream chat overlay styles:
        - Semi-transparent dark backgrounds
        - White/colored text on dark bg
        - Emoji overlaps and visual noise
        """
        if frame is None or frame.size == 0:
            return frame
        
        # Convert to grayscale
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame.copy()
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
        
        # Adaptive thresholding — works well for text on varying backgrounds
        # Use both methods and pick the one with more detected contours (= text)
        thresh_mean = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 8
        )
        thresh_gauss = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
        )
        
        # Pick the threshold that yields more white pixels (likely more text)
        if np.sum(thresh_mean > 128) > np.sum(thresh_gauss > 128):
            processed = thresh_mean
        else:
            processed = thresh_gauss
        
        # Light morphological cleanup — close small gaps in letters
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, kernel)
        
        # Scale up if too small (OCR works better on larger text)
        h, w = processed.shape[:2]
        if h < 200 or w < 300:
            scale = max(200 / h, 300 / w, 1.5)
            processed = cv2.resize(
                processed, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
            )
        
        return processed
    
    def extract_text(self, frame: np.ndarray, preprocess: bool = True) -> List[str]:
        """
        Extract text lines from a frame.
        
        Args:
            frame: Image (numpy array, BGR or grayscale)
            preprocess: Whether to apply chat-optimized preprocessing
            
        Returns:
            List of detected text strings
        """
        if frame is None or frame.size == 0:
            return []
        
        if preprocess:
            processed = self.preprocess_chat_frame(frame)
        else:
            processed = frame
        
        try:
            if self._fallback_to_tesseract:
                # Tesseract fallback
                import pytesseract
                raw = pytesseract.image_to_string(processed)
                lines = [line.strip() for line in raw.split("\n") if line.strip()]
                return lines
            else:
                # EasyOCR
                results = self.reader.readtext(processed, detail=1, paragraph=False)
                
                # Sort by vertical position (top to bottom) to preserve chat order
                results.sort(key=lambda r: r[0][0][1])  # Sort by top-left y coordinate
                
                # Filter by confidence
                texts = []
                for bbox, text, confidence in results:
                    if confidence > 0.3 and len(text.strip()) > 1:
                        texts.append(text.strip())
                
                return texts
                
        except Exception as e:
            return []
    
    def extract_text_with_positions(
        self, frame: np.ndarray, preprocess: bool = True
    ) -> List[Tuple[str, List, float]]:
        """
        Extract text with bounding box positions and confidence.
        
        Returns:
            List of (text, bbox, confidence) tuples
        """
        if frame is None or frame.size == 0:
            return []
        
        if preprocess:
            processed = self.preprocess_chat_frame(frame)
        else:
            processed = frame
        
        try:
            if self._fallback_to_tesseract:
                import pytesseract
                data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
                results = []
                for i in range(len(data["text"])):
                    text = data["text"][i].strip()
                    conf = float(data["conf"][i]) / 100.0
                    if text and conf > 0.3:
                        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
                        bbox = [[x, y], [x+w, y], [x+w, y+h], [x, y+h]]
                        results.append((text, bbox, conf))
                return results
            else:
                results = self.reader.readtext(processed, detail=1, paragraph=False)
                results.sort(key=lambda r: r[0][0][1])
                return [
                    (text, bbox, conf)
                    for bbox, text, conf in results
                    if conf > 0.3 and len(text.strip()) > 1
                ]
        except Exception:
            return []
