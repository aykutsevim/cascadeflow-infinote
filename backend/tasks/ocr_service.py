"""
OCR Service for extracting tasks from handwritten notes.

Supports multiple OCR backends:
1. dots.ocr - Advanced vision-language model (requires GPU)
2. EasyOCR - Lightweight neural OCR (CPU/GPU)
3. Tesseract - Traditional OCR (CPU only)
"""
import logging
import re
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from PIL import Image
import io

logger = logging.getLogger(__name__)


class OCRService:
    """
    Service for OCR processing of handwritten task notes.

    Automatically selects the best available OCR backend.
    """

    def __init__(self, confidence_threshold=0.6, backend=None):
        """
        Initialize OCR service.

        Args:
            confidence_threshold: Minimum confidence score for accepting results
            backend: Force specific backend ('dots', 'easyocr', 'tesseract', or None for auto)
        """
        self.confidence_threshold = confidence_threshold
        self.backend = backend or os.getenv('OCR_BACKEND', 'auto')
        self.ocr_engine = None

        # Initialize the appropriate OCR backend
        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the OCR backend."""
        if self.backend == 'auto':
            # Try to initialize in order of preference
            if self._try_init_dots_ocr():
                self.backend = 'dots'
            elif self._try_init_easyocr():
                self.backend = 'easyocr'
            elif self._try_init_tesseract():
                self.backend = 'tesseract'
            else:
                logger.warning("No OCR backend available, using mock")
                self.backend = 'mock'
        elif self.backend == 'dots':
            if not self._try_init_dots_ocr():
                raise RuntimeError("dots.ocr backend requested but not available")
        elif self.backend == 'easyocr':
            if not self._try_init_easyocr():
                raise RuntimeError("EasyOCR backend requested but not available")
        elif self.backend == 'tesseract':
            if not self._try_init_tesseract():
                raise RuntimeError("Tesseract backend requested but not available")

        logger.info(f"Initialized OCR service with backend: {self.backend}")

    def _try_init_dots_ocr(self) -> bool:
        """Try to initialize dots.ocr backend."""
        try:
            from transformers import AutoModelForCausalLM, AutoProcessor
            import torch

            model_path = os.getenv('DOTS_OCR_MODEL_PATH', './weights/DotsOCR')

            if not os.path.exists(model_path):
                logger.info(f"dots.ocr model not found at {model_path}")
                return False

            logger.info("Loading dots.ocr model...")

            # Check if GPU is available
            gpu_available = torch.cuda.is_available()

            if gpu_available:
                # GPU: Load with bfloat16 (matches model's default dtype)
                logger.info("Loading dots.ocr on GPU with bfloat16...")

                # Use bfloat16 which is the model's native dtype
                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.bfloat16,
                    device_map="auto",
                    trust_remote_code=True,
                )

                self.ocr_engine = {
                    'type': 'dots',
                    'model': model,
                    'processor': AutoProcessor.from_pretrained(
                        model_path,
                        trust_remote_code=True
                    )
                }
                logger.info("dots.ocr initialized successfully on GPU with bfloat16")

            if not gpu_available:
                # CPU: Load with float32 to avoid dtype mismatches
                logger.info("Loading dots.ocr on CPU with float32...")
                model = AutoModelForCausalLM.from_pretrained(
                    model_path,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    trust_remote_code=True,
                )

                self.ocr_engine = {
                    'type': 'dots',
                    'model': model,
                    'processor': AutoProcessor.from_pretrained(
                        model_path,
                        trust_remote_code=True
                    )
                }
                logger.info("dots.ocr initialized successfully on CPU with float32")

            return True
        except ImportError:
            logger.debug("dots.ocr dependencies not available")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize dots.ocr: {e}")
            return False

    def _try_init_easyocr(self) -> bool:
        """Try to initialize EasyOCR backend."""
        try:
            import easyocr
            import torch

            # Check if CUDA is available
            gpu_available = torch.cuda.is_available()
            logger.info(f"Initializing EasyOCR with GPU: {gpu_available}...")

            self.ocr_engine = {
                'type': 'easyocr',
                'reader': easyocr.Reader(['en'], gpu=gpu_available)
            }
            logger.info(f"EasyOCR initialized successfully (GPU: {gpu_available})")
            return True
        except ImportError:
            logger.debug("EasyOCR not available")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize EasyOCR: {e}")
            return False

    def _try_init_tesseract(self) -> bool:
        """Try to initialize Tesseract backend."""
        try:
            import pytesseract
            # Test if tesseract is available
            pytesseract.get_tesseract_version()
            self.ocr_engine = {'type': 'tesseract'}
            logger.info("Tesseract initialized successfully")
            return True
        except ImportError:
            logger.debug("pytesseract not available")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize Tesseract: {e}")
            return False

    def extract_tasks(self, image: Image.Image) -> Dict[str, Any]:
        """
        Extract tasks from handwritten notes image.

        Args:
            image: PIL Image object

        Returns:
            Dictionary containing extracted tasks and metadata
        """
        logger.info(f"Processing image with {self.backend} backend")

        if self.backend == 'dots':
            return self._extract_with_dots_ocr(image)
        elif self.backend == 'easyocr':
            return self._extract_with_easyocr(image)
        elif self.backend == 'tesseract':
            return self._extract_with_tesseract(image)
        else:
            # Fallback to mock
            return self._mock_extract_tasks(image)

    def _extract_with_dots_ocr(self, image: Image.Image) -> Dict[str, Any]:
        """Extract tasks using dots.ocr."""
        import torch
        from qwen_vl_utils import process_vision_info

        # Resize image if too large to reduce memory usage
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"Resized image to {new_size} to reduce memory usage")

        # Prepare prompt for task extraction
        prompt = """Extract all tasks from this handwritten note. For each task, identify:
- Task name (main action item)
- Description (additional details if any)
- Assignee (person responsible, if mentioned)
- Due date (deadline, if mentioned)
- Priority (high/medium/low based on visual cues like underlining, stars, exclamation marks)

Format the output as a structured list with bounding boxes."""

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt}
            ]
        }]

        # Process with dots.ocr
        processor = self.ocr_engine['processor']
        model = self.ocr_engine['model']

        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        image_inputs, video_inputs = process_vision_info(messages)
        inputs = processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt"
        )
        inputs = inputs.to(model.device)

        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                use_cache=True
            )

        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output_text = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        # Log raw output for debugging
        logger.info(f"dots.ocr raw output: {output_text}")

        # Parse the structured output
        tasks = self._parse_dots_ocr_output(output_text, image.size)

        return {
            'tasks': tasks,
            'image_size': {'width': image.size[0], 'height': image.size[1]},
            'processing_method': 'dots.ocr',
            'raw_output': output_text
        }

    def _extract_with_easyocr(self, image: Image.Image) -> Dict[str, Any]:
        """Extract tasks using EasyOCR."""
        import numpy as np

        # Convert PIL Image to numpy array
        img_array = np.array(image)

        # Perform OCR
        reader = self.ocr_engine['reader']
        results = reader.readtext(img_array)

        # Log raw OCR results for debugging
        logger.info(f"EasyOCR detected {len(results)} text regions")
        for i, (bbox, text, conf) in enumerate(results):
            logger.info(f"OCR result {i}: text='{text}', confidence={conf:.2f}")

        # Parse results into tasks
        tasks = self._parse_ocr_results(results, image.size)

        return {
            'tasks': tasks,
            'image_size': {'width': image.size[0], 'height': image.size[1]},
            'processing_method': 'easyocr',
        }

    def _extract_with_tesseract(self, image: Image.Image) -> Dict[str, Any]:
        """Extract tasks using Tesseract OCR."""
        import pytesseract

        # Get detailed OCR data
        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        # Parse results into tasks
        tasks = self._parse_tesseract_results(data, image.size)

        return {
            'tasks': tasks,
            'image_size': {'width': image.size[0], 'height': image.size[1]},
            'processing_method': 'tesseract',
        }

    def _parse_dots_ocr_output(self, output_text: str, image_size: tuple) -> List[Dict[str, Any]]:
        """Parse dots.ocr JSON output into tasks."""
        import json
        from datetime import datetime

        tasks = []
        position_index = 0

        try:
            # Parse JSON output from the model
            ocr_items = json.loads(output_text)

            # Ensure it's a list
            if not isinstance(ocr_items, list):
                logger.warning(f"Expected JSON array from model, got: {type(ocr_items)}")
                return []

            # Process each task from the structured output
            for item in ocr_items:
                # Handle both new structured format and old format for backward compatibility
                if 'task_name' in item:
                    # New structured format with LLM-extracted fields
                    task_name = item.get('task_name', '').strip()
                    assignee = item.get('assignee', '').strip() or None
                    description = item.get('description', '').strip()
                    priority = item.get('priority', 'medium').lower()

                    # Parse due_date if provided
                    due_date = None
                    due_date_str = item.get('due_date', '').strip()
                    if due_date_str and due_date_str != "null":
                        try:
                            # Try to parse the date
                            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            # Try alternative formats
                            for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d']:
                                try:
                                    due_date = datetime.strptime(due_date_str, fmt).date()
                                    break
                                except ValueError:
                                    continue

                    # Extract bbox
                    bbox_data = item.get('bbox', [0, 0, 0, 0])
                    bbox = {
                        'x': int(bbox_data[0]) if len(bbox_data) > 0 else 0,
                        'y': int(bbox_data[1]) if len(bbox_data) > 1 else 0,
                        'width': int(bbox_data[2] - bbox_data[0]) if len(bbox_data) > 2 else 0,
                        'height': int(bbox_data[3] - bbox_data[1]) if len(bbox_data) > 3 else 0
                    }

                elif item.get('category') == 'List-item':
                    # Old format (backward compatibility) - parse with smart extraction
                    text = item.get('text', '')

                    # Remove bullet markers
                    clean_text = re.sub(r'^[\-\*\•\d]+[\.\)]?\s*', '', text)

                    # Extract assignee first
                    assignee = self._extract_assignee(clean_text)

                    # Remove assignee from text to get clean task name
                    task_name = self._remove_assignee_from_text(clean_text, assignee)

                    # Extract due date and remove it from task name
                    due_date = self._extract_date(clean_text)
                    if due_date:
                        # Remove date patterns from task name
                        task_name = re.sub(r'\s+\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', '', task_name)

                    description = ''
                    priority = self._extract_priority(clean_text)

                    bbox_data = item.get('bbox', [0, 0, 0, 0])
                    bbox = {
                        'x': int(bbox_data[0]) if len(bbox_data) > 0 else 0,
                        'y': int(bbox_data[1]) if len(bbox_data) > 1 else 0,
                        'width': int(bbox_data[2] - bbox_data[0]) if len(bbox_data) > 2 else 0,
                        'height': int(bbox_data[3] - bbox_data[1]) if len(bbox_data) > 3 else 0
                    }
                else:
                    # Skip non-task items
                    continue

                # Only add tasks with a name
                if task_name:
                    tasks.append({
                        'name': task_name[:100],
                        'description': description,
                        'assignee': assignee,
                        'due_date': due_date,
                        'priority': priority,
                        'position_index': position_index,
                        'confidence': 0.90,  # dots.ocr is generally high quality
                        'bbox': bbox
                    })
                    position_index += 1

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse dots.ocr JSON output: {e}")
            logger.warning(f"Raw output was: {output_text}")
            # Fallback to empty list
            tasks = []

        return tasks

    def _parse_ocr_results(self, results: List, image_size: tuple) -> List[Dict[str, Any]]:
        """Parse EasyOCR results into structured tasks."""
        # Group text by vertical position
        lines = []
        for bbox, text, conf in results:
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            lines.append({
                'text': text,
                'y': y_center,
                'bbox': bbox,
                'confidence': conf
            })

        # Sort by Y position
        lines.sort(key=lambda x: x['y'])

        # Group into tasks
        tasks = []
        current_task = None
        position_index = 0

        for line in lines:
            text = line['text'].strip()

            # Check if this starts a new task
            # Match bullets/numbers optionally followed by . or ), then whitespace
            if re.match(r'^[\-\*\•\d]+[\.\)]?\s+', text) or any(marker in text.lower() for marker in ['todo', 'task', '☐', '□']):
                if current_task:
                    tasks.append(current_task)

                task_name = re.sub(r'^[\-\*\•\d]+[\.\)]?\s*', '', text)
                current_task = {
                    'name': task_name,
                    'description': '',
                    'assignee': self._extract_assignee(text),
                    'due_date': self._extract_date(text),
                    'priority': self._extract_priority(text),
                    'position_index': position_index,
                    'confidence': line['confidence'],
                    'bbox': {
                        'x': int(line['bbox'][0][0]),
                        'y': int(line['bbox'][0][1]),
                        'width': int(line['bbox'][2][0] - line['bbox'][0][0]),
                        'height': int(line['bbox'][2][1] - line['bbox'][0][1])
                    }
                }
                position_index += 1
            elif current_task:
                if current_task['description']:
                    current_task['description'] += ' '
                current_task['description'] += text

        if current_task:
            tasks.append(current_task)

        return tasks

    def _parse_tesseract_results(self, data: Dict, image_size: tuple) -> List[Dict[str, Any]]:
        """Parse Tesseract OCR data into structured tasks."""
        # Combine words into lines
        lines = []
        current_line = {'text': '', 'y': 0, 'x': 0, 'conf': 0, 'count': 0}

        for i, text in enumerate(data['text']):
            if int(data['conf'][i]) < 0:  # Skip low confidence
                continue

            y = data['top'][i]
            x = data['left'][i]

            # New line if Y position changes significantly
            if current_line['count'] > 0 and abs(y - current_line['y']) > 20:
                lines.append(current_line)
                current_line = {'text': '', 'y': y, 'x': x, 'conf': 0, 'count': 0}

            if current_line['text']:
                current_line['text'] += ' '
            current_line['text'] += text.strip()
            current_line['y'] = y
            current_line['conf'] += int(data['conf'][i])
            current_line['count'] += 1

        if current_line['count'] > 0:
            lines.append(current_line)

        # Parse lines into tasks
        tasks = []
        position_index = 0

        for line in lines:
            text = line['text'].strip()
            if not text:
                continue

            # Check for task markers
            if re.match(r'^[\-\*\•\d]+[\.\)]\s+', text):
                task_name = re.sub(r'^[\-\*\•\d]+[\.\)]\s*', '', text)
                avg_conf = line['conf'] / line['count'] / 100 if line['count'] > 0 else 0.5

                tasks.append({
                    'name': task_name[:100],
                    'description': '',
                    'assignee': self._extract_assignee(text),
                    'due_date': self._extract_date(text),
                    'priority': self._extract_priority(text),
                    'position_index': position_index,
                    'confidence': avg_conf,
                    'bbox': self._estimate_bbox(position_index, image_size)
                })
                position_index += 1

        return tasks

    def _extract_priority(self, text: str) -> str:
        """Extract priority from text patterns."""
        text_lower = text.lower()

        if any(marker in text_lower for marker in ['urgent', '!!!', 'asap', 'critical', 'high priority']):
            return 'urgent'
        elif any(marker in text_lower for marker in ['high', '!!', 'important']):
            return 'high'
        elif any(marker in text_lower for marker in ['low', 'minor', 'whenever']):
            return 'low'
        else:
            return 'medium'

    def _extract_date(self, text: str) -> Optional[datetime.date]:
        """Extract due date from text using pattern matching."""
        # Common date patterns
        date_patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{2,4})', lambda m: self._parse_date_parts(m.group(1), m.group(2), m.group(3))),
            (r'(\d{4})-(\d{2})-(\d{2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3))).date()),
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* (\d{1,2})', lambda m: self._parse_month_day(m.group(1), m.group(2))),
        ]

        for pattern, parser in date_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return parser(match)
                except:
                    pass

        return None

    def _parse_date_parts(self, part1: str, part2: str, part3: str) -> datetime.date:
        """Parse date from parts (handles MM/DD/YYYY or DD/MM/YYYY)."""
        year = int(part3)
        if year < 100:
            year += 2000

        # Try MM/DD/YYYY first
        try:
            return datetime(year, int(part1), int(part2)).date()
        except ValueError:
            # Try DD/MM/YYYY
            return datetime(year, int(part2), int(part1)).date()

    def _parse_month_day(self, month_str: str, day: str) -> datetime.date:
        """Parse month name and day."""
        months = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        month = months.get(month_str[:3].lower())
        if month:
            year = datetime.now().year
            return datetime(year, month, int(day)).date()
        return None

    def _extract_assignee(self, text: str) -> Optional[str]:
        """Extract assignee from text patterns."""
        patterns = [
            r'[→>]\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # → Name or -> Name (arrow pattern, handles names like "Aykut" or "Hasan Smith")
            r'@(\w+)',  # @username
            r'assigned to:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # assigned to: Name
            r'owner:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)',  # owner: Name
            r'\[([A-Z][a-z]+)\]',  # [Name]
            r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\)',  # (Name) in parentheses
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                assignee = match.group(1).strip()
                # Remove any trailing dates or numbers
                assignee = re.sub(r'\s+\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}.*$', '', assignee)
                # Remove any trailing non-letter characters
                assignee = re.sub(r'[^\w\s]+$', '', assignee).strip()
                if assignee:
                    return assignee

        return None

    def _remove_assignee_from_text(self, text: str, assignee: Optional[str]) -> str:
        """Remove assignee pattern from text to get clean task name."""
        if not assignee:
            return text

        # Remove arrow patterns with assignee
        text = re.sub(rf'\s*[→>]\s*{re.escape(assignee)}(?:\s+\d{{1,2}}[/\-\.]\d{{1,2}}[/\-\.]\d{{2,4}})?', '', text)
        # Remove other assignee patterns
        text = re.sub(rf'@{re.escape(assignee)}', '', text)
        text = re.sub(rf'assigned to:?\s*{re.escape(assignee)}', '', text, flags=re.IGNORECASE)
        text = re.sub(rf'owner:?\s*{re.escape(assignee)}', '', text, flags=re.IGNORECASE)
        text = re.sub(rf'\[{re.escape(assignee)}\]', '', text)
        text = re.sub(rf'\({re.escape(assignee)}\)', '', text)

        return text.strip()

    def _estimate_bbox(self, position_index: int, image_size: tuple) -> Dict[str, int]:
        """Estimate bounding box for task based on position."""
        width, height = image_size
        row_height = 80
        y = 100 + (position_index * row_height)

        return {
            'x': 50,
            'y': y,
            'width': int(width * 0.8),
            'height': row_height - 20
        }

    def _mock_extract_tasks(self, image: Image.Image) -> Dict[str, Any]:
        """
        Mock implementation for testing when no OCR backend is available.
        """
        logger.warning("Using mock OCR implementation")
        width, height = image.size

        mock_tasks = [
            {
                'name': 'Review project proposal',
                'description': 'Review and provide feedback on Q1 project proposal document',
                'assignee': 'John Doe',
                'due_date': (datetime.now() + timedelta(days=3)).date(),
                'priority': 'high',
                'confidence': 0.89,
                'bbox': {'x': 50, 'y': 100, 'width': 400, 'height': 60}
            },
            {
                'name': 'Update documentation',
                'description': 'Update API documentation with new endpoints',
                'assignee': 'Jane Smith',
                'due_date': (datetime.now() + timedelta(days=7)).date(),
                'priority': 'medium',
                'confidence': 0.92,
                'bbox': {'x': 50, 'y': 180, 'width': 450, 'height': 60}
            },
            {
                'name': 'Schedule team meeting',
                'description': 'Schedule weekly sync meeting with the team',
                'assignee': '',
                'due_date': (datetime.now() + timedelta(days=1)).date(),
                'priority': 'low',
                'confidence': 0.85,
                'bbox': {'x': 50, 'y': 260, 'width': 380, 'height': 60}
            },
        ]

        return {
            'tasks': mock_tasks,
            'image_size': {'width': width, 'height': height},
            'processing_method': 'mock',
        }


# Global singleton instance for reusing the loaded model
_ocr_service_instance = None


def get_ocr_service(confidence_threshold=0.6, backend=None):
    """
    Get or create a singleton OCR service instance.

    This ensures the model is loaded only once and reused across all requests,
    preventing memory leaks and improving performance.

    Args:
        confidence_threshold: Minimum confidence score for accepting results
        backend: Force specific backend ('dots', 'easyocr', 'tesseract', or None for auto)

    Returns:
        OCRService: Singleton instance of the OCR service
    """
    global _ocr_service_instance

    if _ocr_service_instance is None:
        logger.info("Initializing singleton OCR service instance...")
        _ocr_service_instance = OCRService(
            confidence_threshold=confidence_threshold,
            backend=backend
        )
        logger.info("Singleton OCR service instance created successfully")

    return _ocr_service_instance
