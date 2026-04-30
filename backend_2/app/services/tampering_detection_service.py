"""
Tampering Detection Service
Detects image tampering using Error Level Analysis, copy-move detection, and other forensic techniques
"""

import io
import logging
from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2
from PIL import Image
from skimage import feature, filters, segmentation
from skimage.measure import label, regionprops

logger = logging.getLogger(__name__)


class TamperingDetectionService:
    """Service for detecting image tampering and manipulation"""

    def detect_tampering(self, image_content: bytes) -> Dict[str, Any]:
        """
        Perform comprehensive tampering detection analysis
        
        Args:
            image_content: Raw image bytes
        
        Returns:
            Dictionary containing tampering detection results
        """
        results = {
            "tampering_detected": False,
            "confidence": 0.0,
            "techniques": {},
            "anomalies": [],
            "regions_of_interest": []
        }
        
        try:
            # Convert to numpy array
            image = Image.open(io.BytesIO(image_content))
            image_rgb = np.array(image.convert('RGB'))
            image_gray = np.array(image.convert('L'))
            
            # Perform various detection techniques
            ela_results = self._error_level_analysis(image_rgb)
            copy_move_results = self._copy_move_detection(image_gray)
            noise_results = self._noise_pattern_analysis(image_gray)
            edge_results = self._edge_inconsistency_detection(image_gray)
            compression_results = self._compression_artifact_analysis(image_gray)
            
            # Store individual technique results
            results["techniques"] = {
                "error_level_analysis": ela_results,
                "copy_move_detection": copy_move_results,
                "noise_pattern_analysis": noise_results,
                "edge_inconsistency": edge_results,
                "compression_artifacts": compression_results
            }
            
            # Aggregate results
            tampering_indicators = []
            confidence_scores = []
            
            if ela_results.get("anomalies_detected", False):
                tampering_indicators.append("Error Level Analysis detected anomalies")
                confidence_scores.append(ela_results.get("confidence", 0.5))
            
            if copy_move_results.get("clones_detected", False):
                tampering_indicators.append("Copy-move regions detected")
                confidence_scores.append(copy_move_results.get("confidence", 0.6))
            
            if noise_results.get("inconsistent_noise", False):
                tampering_indicators.append("Inconsistent noise patterns")
                confidence_scores.append(noise_results.get("confidence", 0.5))
            
            if edge_results.get("inconsistencies_detected", False):
                tampering_indicators.append("Edge inconsistencies detected")
                confidence_scores.append(edge_results.get("confidence", 0.5))
            
            if compression_results.get("inconsistencies_detected", False):
                tampering_indicators.append("Compression inconsistencies detected")
                confidence_scores.append(compression_results.get("confidence", 0.4))
            
            # Calculate overall confidence
            if confidence_scores:
                results["confidence"] = float(np.mean(confidence_scores))
                results["tampering_detected"] = results["confidence"] > 0.4
            else:
                results["confidence"] = 0.1  # Low confidence if no indicators
            
            results["anomalies"] = tampering_indicators
            
            # Combine regions of interest from all techniques
            all_regions = []
            if ela_results.get("regions"):
                all_regions.extend(ela_results["regions"])
            if copy_move_results.get("regions"):
                all_regions.extend(copy_move_results["regions"])
            results["regions_of_interest"] = all_regions[:10]  # Limit to top 10
            
        except Exception as e:
            logger.error(f"Error in tampering detection: {e}")
            results["error"] = str(e)
        
        return results

    def _error_level_analysis(self, image_rgb: np.ndarray, quality: int = 90) -> Dict[str, Any]:
        """
        Error Level Analysis (ELA) - detects compression inconsistencies
        
        Args:
            image_rgb: RGB image as numpy array
            quality: JPEG quality for recompression (default 90)
        
        Returns:
            Dictionary with ELA analysis results
        """
        results = {
            "anomalies_detected": False,
            "confidence": 0.0,
            "mean_ela_value": 0.0,
            "std_ela_value": 0.0,
            "regions": []
        }
        
        try:
            # Convert to PIL, save as JPEG, reload to get ELA
            pil_image = Image.fromarray(image_rgb)
            
            # Save with specific quality
            buffer = io.BytesIO()
            pil_image.save(buffer, format='JPEG', quality=quality)
            buffer.seek(0)
            recompressed = Image.open(buffer)
            recompressed_array = np.array(recompressed.convert('RGB'))
            
            # Calculate difference (ELA)
            ela = np.abs(image_rgb.astype(np.float32) - recompressed_array.astype(np.float32))
            ela_gray = np.mean(ela, axis=2).astype(np.uint8)
            
            # Analyze ELA image
            mean_ela = np.mean(ela_gray)
            std_ela = np.std(ela_gray)
            
            results["mean_ela_value"] = float(mean_ela)
            results["std_ela_value"] = float(std_ela)
            
            # Threshold for anomaly detection (regions with high ELA values)
            threshold = mean_ela + (2 * std_ela)
            anomaly_mask = ela_gray > threshold
            
            if np.any(anomaly_mask):
                results["anomalies_detected"] = True
                anomaly_ratio = np.sum(anomaly_mask) / anomaly_mask.size
                
                # Calculate confidence based on anomaly ratio
                if anomaly_ratio > 0.05:  # More than 5% of image
                    results["confidence"] = min(0.9, 0.5 + anomaly_ratio)
                else:
                    results["confidence"] = 0.3 + (anomaly_ratio * 2)
                
                # Find regions of interest
                labeled = label(anomaly_mask)
                regions = regionprops(labeled)
                
                for region in regions[:5]:  # Top 5 largest regions
                    if region.area > 100:  # Minimum area threshold
                        results["regions"].append({
                            "type": "ela_anomaly",
                            "area": int(region.area),
                            "centroid": [int(c) for c in region.centroid],
                            "bbox": [int(b) for b in region.bbox]
                        })
        
        except Exception as e:
            logger.warning(f"Error in ELA analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _copy_move_detection(self, image_gray: np.ndarray, block_size: int = 32) -> Dict[str, Any]:
        """
        Copy-move detection using block-based method
        
        Args:
            image_gray: Grayscale image as numpy array
            block_size: Size of blocks to compare
        
        Returns:
            Dictionary with copy-move detection results
        """
        results = {
            "clones_detected": False,
            "confidence": 0.0,
            "num_matches": 0,
            "regions": []
        }
        
        try:
            h, w = image_gray.shape
            
            # Divide image into blocks
            blocks = []
            positions = []
            
            for y in range(0, h - block_size, block_size // 2):
                for x in range(0, w - block_size, block_size // 2):
                    block = image_gray[y:y+block_size, x:x+block_size]
                    if block.shape == (block_size, block_size):
                        # Use DCT coefficients as feature vector
                        dct = cv2.dct(np.float32(block))
                        # Take only low frequency components
                        feature_vector = dct[:8, :8].flatten()
                        blocks.append(feature_vector)
                        positions.append((x, y))
            
            if len(blocks) < 2:
                return results
            
            blocks_array = np.array(blocks)
            
            # Find similar blocks using correlation
            # Normalize blocks
            blocks_norm = blocks_array / (np.linalg.norm(blocks_array, axis=1, keepdims=True) + 1e-8)
            similarity_matrix = np.dot(blocks_norm, blocks_norm.T)
            
            # Find pairs with high similarity (above threshold, but not identical)
            threshold = 0.95
            matches = []
            for i in range(len(similarity_matrix)):
                for j in range(i + 1, len(similarity_matrix)):
                    if 0.85 < similarity_matrix[i, j] < 0.99:  # High similarity but not identical
                        # Check distance between positions (should be far apart for copy-move)
                        pos1 = positions[i]
                        pos2 = positions[j]
                        distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
                        
                        if distance > block_size * 2:  # Blocks are far apart
                            matches.append((i, j, similarity_matrix[i, j], distance))
            
            if matches:
                results["clones_detected"] = True
                results["num_matches"] = len(matches)
                results["confidence"] = min(0.8, 0.3 + (len(matches) / 100))
                
                # Get unique regions
                matched_positions = set()
                for match in matches[:10]:  # Limit to top 10 matches
                    idx1, idx2 = match[0], match[1]
                    pos1, pos2 = positions[idx1], positions[idx2]
                    
                    if pos1 not in matched_positions:
                        matched_positions.add(pos1)
                        results["regions"].append({
                            "type": "copy_move_source",
                            "bbox": [pos1[0], pos1[1], pos1[0] + block_size, pos1[1] + block_size],
                            "similarity": float(match[2])
                        })
                    
                    if pos2 not in matched_positions:
                        matched_positions.add(pos2)
                        results["regions"].append({
                            "type": "copy_move_destination",
                            "bbox": [pos2[0], pos2[1], pos2[0] + block_size, pos2[1] + block_size],
                            "similarity": float(match[2])
                        })
        
        except Exception as e:
            logger.warning(f"Error in copy-move detection: {e}")
            results["error"] = str(e)
        
        return results

    def _noise_pattern_analysis(self, image_gray: np.ndarray) -> Dict[str, Any]:
        """
        Analyze noise patterns for inconsistencies
        
        Args:
            image_gray: Grayscale image as numpy array
        
        Returns:
            Dictionary with noise analysis results
        """
        results = {
            "inconsistent_noise": False,
            "confidence": 0.0,
            "noise_variance": 0.0,
            "noise_std": 0.0
        }
        
        try:
            # Apply high-pass filter to extract noise
            blurred = cv2.GaussianBlur(image_gray, (5, 5), 0)
            noise = image_gray.astype(np.float32) - blurred.astype(np.float32)
            
            # Calculate noise statistics in different regions
            h, w = image_gray.shape
            regions = [
                noise[:h//3, :w//3],      # Top-left
                noise[:h//3, 2*w//3:],    # Top-right
                noise[2*h//3:, :w//3],    # Bottom-left
                noise[2*h//3:, 2*w//3:]   # Bottom-right
            ]
            
            region_stds = [np.std(r) for r in regions]
            
            # Check for high variance in noise statistics (inconsistency)
            std_of_stds = np.std(region_stds)
            mean_of_stds = np.mean(region_stds)
            
            results["noise_variance"] = float(std_of_stds)
            results["noise_std"] = float(mean_of_stds)
            
            # If noise varies significantly between regions, may indicate tampering
            if std_of_stds > mean_of_stds * 0.5:  # High variance
                results["inconsistent_noise"] = True
                results["confidence"] = min(0.7, 0.3 + (std_of_stds / mean_of_stds))
        
        except Exception as e:
            logger.warning(f"Error in noise pattern analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _edge_inconsistency_detection(self, image_gray: np.ndarray) -> Dict[str, Any]:
        """
        Detect edge inconsistencies that may indicate splicing
        
        Args:
            image_gray: Grayscale image as numpy array
        
        Returns:
            Dictionary with edge analysis results
        """
        results = {
            "inconsistencies_detected": False,
            "confidence": 0.0,
            "edge_density": 0.0
        }
        
        try:
            # Detect edges using Canny
            edges = feature.canny(image_gray, sigma=1.0)
            
            # Calculate edge density
            edge_density = np.sum(edges) / edges.size
            results["edge_density"] = float(edge_density)
            
            # Divide image into regions and check edge consistency
            h, w = image_gray.shape
            regions = [
                edges[:h//2, :w//2],      # Top-left
                edges[:h//2, w//2:],       # Top-right
                edges[h//2:, :w//2],       # Bottom-left
                edges[h//2:, w//2:]        # Bottom-right
            ]
            
            region_densities = [np.sum(r) / r.size for r in regions]
            std_density = np.std(region_densities)
            mean_density = np.mean(region_densities)
            
            # High variance in edge density may indicate splicing
            if mean_density > 0 and std_density > mean_density * 0.4:
                results["inconsistencies_detected"] = True
                results["confidence"] = min(0.6, 0.2 + (std_density / mean_density))
        
        except Exception as e:
            logger.warning(f"Error in edge inconsistency detection: {e}")
            results["error"] = str(e)
        
        return results

    def _compression_artifact_analysis(self, image_gray: np.ndarray) -> Dict[str, Any]:
        """
        Analyze compression artifacts for inconsistencies
        
        Args:
            image_gray: Grayscale image as numpy array
        
        Returns:
            Dictionary with compression analysis results
        """
        results = {
            "inconsistencies_detected": False,
            "confidence": 0.0,
            "block_artifacts": []
        }
        
        try:
            # DCT-based block analysis (JPEG compression works in 8x8 blocks)
            h, w = image_gray.shape
            
            # Divide into 8x8 blocks and analyze DCT coefficients
            block_variance = []
            for y in range(0, h - 8, 8):
                for x in range(0, w - 8, 8):
                    block = image_gray[y:y+8, x:x+8].astype(np.float32)
                    dct = cv2.dct(block)
                    
                    # High frequency components variance (compression artifacts)
                    hf_variance = np.var(dct[4:, 4:])
                    block_variance.append(hf_variance)
            
            if block_variance:
                mean_var = np.mean(block_variance)
                std_var = np.std(block_variance)
                
                # High variance in block compression may indicate tampering
                if std_var > mean_var * 0.6:
                    results["inconsistencies_detected"] = True
                    results["confidence"] = min(0.5, 0.2 + (std_var / mean_var) * 0.3)
        
        except Exception as e:
            logger.warning(f"Error in compression artifact analysis: {e}")
            results["error"] = str(e)
        
        return results


# Singleton instance
_tampering_detection_service: Optional[TamperingDetectionService] = None


def get_tampering_detection_service() -> TamperingDetectionService:
    """Get or create the tampering detection service singleton"""
    global _tampering_detection_service
    if _tampering_detection_service is None:
        _tampering_detection_service = TamperingDetectionService()
    return _tampering_detection_service

