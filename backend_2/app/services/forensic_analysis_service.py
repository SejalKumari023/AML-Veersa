"""
Forensic Analysis Service
Deep forensic inspection combining multiple analysis techniques
"""

import io
import logging
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import cv2
from PIL import Image
from skimage import filters, feature, restoration
from skimage.measure import label, regionprops
import pywt

logger = logging.getLogger(__name__)


class ForensicAnalysisService:
    """Service for comprehensive forensic image analysis"""

    def perform_forensic_analysis(self, image_content: bytes) -> Dict[str, Any]:
        """
        Perform comprehensive forensic analysis
        
        Args:
            image_content: Raw image bytes
        
        Returns:
            Dictionary containing forensic analysis results
        """
        results = {
            "forensic_score": 0.0,
            "manipulation_probability": 0.0,
            "techniques": {},
            "indicators": [],
            "detailed_findings": {}
        }
        
        try:
            # Convert to numpy array
            image = Image.open(io.BytesIO(image_content))
            image_rgb = np.array(image.convert('RGB'))
            image_gray = np.array(image.convert('L'))
            
            # Perform various forensic techniques
            frequency_results = self._frequency_domain_analysis(image_gray)
            wavelet_results = self._wavelet_analysis(image_gray)
            statistical_results = self._statistical_analysis(image_rgb, image_gray)
            luminance_results = self._luminance_consistency_analysis(image_gray)
            color_results = self._color_analysis(image_rgb)
            advanced_ela = self._advanced_ela_analysis(image_rgb)
            
            # Store individual technique results
            results["techniques"] = {
                "frequency_domain": frequency_results,
                "wavelet_analysis": wavelet_results,
                "statistical_analysis": statistical_results,
                "luminance_consistency": luminance_results,
                "color_analysis": color_results,
                "advanced_ela": advanced_ela
            }
            
            # Collect indicators from all techniques
            all_indicators = []
            manipulation_scores = []
            
            # Aggregate indicators and scores
            for technique_name, technique_results in results["techniques"].items():
                if technique_results.get("indicators"):
                    all_indicators.extend(technique_results["indicators"])
                
                if "manipulation_score" in technique_results:
                    manipulation_scores.append(technique_results["manipulation_score"])
            
            results["indicators"] = all_indicators
            
            # Calculate overall manipulation probability
            if manipulation_scores:
                results["manipulation_probability"] = float(np.mean(manipulation_scores))
            else:
                results["manipulation_probability"] = 0.0
            
            # Calculate forensic score (inverse of manipulation probability, weighted)
            results["forensic_score"] = max(0.0, min(1.0, 1.0 - results["manipulation_probability"] * 0.8))
            
            # Generate detailed findings
            results["detailed_findings"] = self._generate_detailed_findings(results["techniques"])
            
        except Exception as e:
            logger.error(f"Error in forensic analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _frequency_domain_analysis(self, image_gray: np.ndarray) -> Dict[str, Any]:
        """
        Frequency domain analysis using FFT
        
        Args:
            image_gray: Grayscale image as numpy array
        
        Returns:
            Dictionary with frequency domain analysis results
        """
        results = {
            "manipulation_score": 0.0,
            "indicators": [],
            "frequency_characteristics": {}
        }
        
        try:
            # Compute 2D FFT
            f_transform = np.fft.fft2(image_gray.astype(np.float32))
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = np.abs(f_shift)
            
            # Analyze frequency distribution
            h, w = magnitude_spectrum.shape
            center_y, center_x = h // 2, w // 2
            
            # Divide into regions: low, mid, high frequency
            low_freq_mask = np.zeros_like(magnitude_spectrum)
            mid_freq_mask = np.zeros_like(magnitude_spectrum)
            high_freq_mask = np.zeros_like(magnitude_spectrum)
            
            radius_low = min(h, w) // 8
            radius_mid = min(h, w) // 4
            radius_high = min(h, w) // 2
            
            y, x = np.ogrid[:h, :w]
            
            # Create masks
            dist_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            low_freq_mask[dist_from_center <= radius_low] = 1
            mid_freq_mask[(dist_from_center > radius_low) & (dist_from_center <= radius_mid)] = 1
            high_freq_mask[(dist_from_center > radius_mid) & (dist_from_center <= radius_high)] = 1
            
            # Calculate energy in each frequency band
            low_energy = np.sum(magnitude_spectrum * low_freq_mask)
            mid_energy = np.sum(magnitude_spectrum * mid_freq_mask)
            high_energy = np.sum(magnitude_spectrum * high_freq_mask)
            total_energy = low_energy + mid_energy + high_energy
            
            # Normalize
            low_ratio = low_energy / total_energy if total_energy > 0 else 0
            mid_ratio = mid_energy / total_energy if total_energy > 0 else 0
            high_ratio = high_energy / total_energy if total_energy > 0 else 0
            
            results["frequency_characteristics"] = {
                "low_frequency_ratio": float(low_ratio),
                "mid_frequency_ratio": float(mid_ratio),
                "high_frequency_ratio": float(high_ratio)
            }
            
            # Check for anomalies (unusual frequency distribution)
            # Tampered images often show irregular frequency patterns
            if high_ratio > 0.3 or low_ratio < 0.4:
                results["indicators"].append("Unusual frequency distribution detected")
                results["manipulation_score"] = 0.3
            
            # Check for frequency inconsistencies across regions
            regions = [
                magnitude_spectrum[:h//2, :w//2],      # Top-left
                magnitude_spectrum[:h//2, w//2:],       # Top-right
                magnitude_spectrum[h//2:, :w//2],     # Bottom-left
                magnitude_spectrum[h//2:, w//2:]       # Bottom-right
            ]
            
            region_energies = [np.sum(r) for r in regions]
            energy_std = np.std(region_energies)
            energy_mean = np.mean(region_energies)
            
            if energy_mean > 0 and energy_std / energy_mean > 0.3:
                results["indicators"].append("Inconsistent frequency patterns across regions")
                results["manipulation_score"] = max(results["manipulation_score"], 0.4)
        
        except Exception as e:
            logger.warning(f"Error in frequency domain analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _wavelet_analysis(self, image_gray: np.ndarray, wavelet: str = 'db4', levels: int = 3) -> Dict[str, Any]:
        """
        Wavelet decomposition analysis
        
        Args:
            image_gray: Grayscale image as numpy array
            wavelet: Wavelet type (default: Daubechies 4)
            levels: Decomposition levels
        
        Returns:
            Dictionary with wavelet analysis results
        """
        results = {
            "manipulation_score": 0.0,
            "indicators": [],
            "wavelet_coefficients": {}
        }
        
        try:
            # Perform wavelet decomposition
            coeffs = pywt.wavedec2(image_gray.astype(np.float32), wavelet, level=levels)
            
            # Analyze coefficients at different levels
            cA = coeffs[0]  # Approximation coefficients
            details = coeffs[1:]  # Detail coefficients (horizontal, vertical, diagonal)
            
            # Calculate statistics for approximation
            cA_mean = np.mean(np.abs(cA))
            cA_std = np.std(cA)
            
            # Analyze detail coefficients (should be sparse for natural images)
            detail_stats = []
            for level_details in details:
                h_detail, v_detail, d_detail = level_details
                
                for detail in [h_detail, v_detail, d_detail]:
                    detail_energy = np.sum(np.abs(detail))
                    detail_nonzero = np.count_nonzero(detail)
                    detail_ratio = detail_nonzero / detail.size if detail.size > 0 else 0
                    
                    detail_stats.append({
                        "energy": float(detail_energy),
                        "sparsity": float(1.0 - detail_ratio)
                    })
            
            results["wavelet_coefficients"] = {
                "approximation_mean": float(cA_mean),
                "approximation_std": float(cA_std),
                "detail_stats": detail_stats
            }
            
            # Check for unusual sparsity (manipulated images often show different patterns)
            avg_sparsity = np.mean([s["sparsity"] for s in detail_stats])
            
            if avg_sparsity < 0.7:  # Less sparse than expected
                results["indicators"].append("Unusual wavelet coefficient sparsity")
                results["manipulation_score"] = 0.3
            
            # Check for inconsistencies across decomposition levels
            if len(detail_stats) > 1:
                energies = [s["energy"] for s in detail_stats]
                energy_variance = np.var(energies)
                if energy_variance > np.mean(energies) * 0.5:
                    results["indicators"].append("Inconsistent energy across wavelet levels")
                    results["manipulation_score"] = max(results["manipulation_score"], 0.25)
        
        except Exception as e:
            logger.warning(f"Error in wavelet analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _statistical_analysis(self, image_rgb: np.ndarray, image_gray: np.ndarray) -> Dict[str, Any]:
        """
        Statistical analysis of pixel distributions
        
        Args:
            image_rgb: RGB image as numpy array
            image_gray: Grayscale image as numpy array
        
        Returns:
            Dictionary with statistical analysis results
        """
        results = {
            "manipulation_score": 0.0,
            "indicators": [],
            "statistics": {}
        }
        
        try:
            # Analyze histogram characteristics
            hist, bins = np.histogram(image_gray.flatten(), bins=256, range=(0, 256))
            
            # Calculate histogram statistics
            mean_intensity = np.mean(image_gray)
            std_intensity = np.std(image_gray)
            skewness = self._calculate_skewness(image_gray.flatten())
            kurtosis = self._calculate_kurtosis(image_gray.flatten())
            
            results["statistics"] = {
                "mean_intensity": float(mean_intensity),
                "std_intensity": float(std_intensity),
                "skewness": float(skewness),
                "kurtosis": float(kurtosis),
                "histogram_peaks": int(len(np.where(hist > np.mean(hist) * 2)[0]))
            }
            
            # Check for unusual distributions
            # Natural images typically have bell-shaped histograms
            if abs(skewness) > 1.5:
                results["indicators"].append("Unusual histogram skewness detected")
                results["manipulation_score"] += 0.2
            
            if abs(kurtosis) > 5:
                results["indicators"].append("Unusual histogram kurtosis detected")
                results["manipulation_score"] += 0.2
            
            # Analyze correlation between color channels
            if len(image_rgb.shape) == 3:
                r, g, b = image_rgb[:, :, 0], image_rgb[:, :, 1], image_rgb[:, :, 2]
                
                # Calculate correlations
                rg_corr = np.corrcoef(r.flatten(), g.flatten())[0, 1]
                rb_corr = np.corrcoef(r.flatten(), b.flatten())[0, 1]
                gb_corr = np.corrcoef(g.flatten(), b.flatten())[0, 1]
                
                avg_correlation = (rg_corr + rb_corr + gb_corr) / 3
                
                results["statistics"]["color_correlation"] = {
                    "rg": float(rg_corr),
                    "rb": float(rb_corr),
                    "gb": float(gb_corr),
                    "average": float(avg_correlation)
                }
                
                # Low correlation might indicate manipulation
                if avg_correlation < 0.7:
                    results["indicators"].append("Low color channel correlation")
                    results["manipulation_score"] = max(results["manipulation_score"], 0.25)
        
        except Exception as e:
            logger.warning(f"Error in statistical analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _luminance_consistency_analysis(self, image_gray: np.ndarray) -> Dict[str, Any]:
        """
        Analyze luminance consistency across image
        
        Args:
            image_gray: Grayscale image as numpy array
        
        Returns:
            Dictionary with luminance analysis results
        """
        results = {
            "manipulation_score": 0.0,
            "indicators": [],
            "luminance_stats": {}
        }
        
        try:
            h, w = image_gray.shape
            
            # Divide into grid regions
            grid_size = 8
            regions = []
            
            for y in range(0, h, h // grid_size):
                for x in range(0, w, w // grid_size):
                    region = image_gray[y:min(y+h//grid_size, h), x:min(x+w//grid_size, w)]
                    if region.size > 0:
                        regions.append({
                            "mean": np.mean(region),
                            "std": np.std(region),
                            "pos": (x, y)
                        })
            
            # Analyze consistency
            region_means = [r["mean"] for r in regions]
            region_stds = [r["std"] for r in regions]
            
            mean_of_means = np.mean(region_means)
            std_of_means = np.std(region_means)
            mean_of_stds = np.mean(region_stds)
            std_of_stds = np.std(region_stds)
            
            results["luminance_stats"] = {
                "global_mean": float(mean_of_means),
                "regional_mean_variance": float(std_of_means),
                "regional_std_mean": float(mean_of_stds),
                "regional_std_variance": float(std_of_stds)
            }
            
            # Check for high variance (inconsistent luminance)
            if std_of_means > mean_of_means * 0.3:
                results["indicators"].append("Inconsistent luminance across regions")
                results["manipulation_score"] = 0.3
            
            # Check for unusual standard deviation patterns
            if std_of_stds > mean_of_stds * 0.4:
                results["indicators"].append("Irregular noise patterns detected")
                results["manipulation_score"] = max(results["manipulation_score"], 0.25)
        
        except Exception as e:
            logger.warning(f"Error in luminance consistency analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _color_analysis(self, image_rgb: np.ndarray) -> Dict[str, Any]:
        """
        Analyze color properties and consistency
        
        Args:
            image_rgb: RGB image as numpy array
        
        Returns:
            Dictionary with color analysis results
        """
        results = {
            "manipulation_score": 0.0,
            "indicators": [],
            "color_stats": {}
        }
        
        try:
            # Convert to different color spaces
            hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
            
            # Analyze saturation and value (brightness)
            saturation = hsv[:, :, 1]
            value = hsv[:, :, 2]
            
            sat_mean = np.mean(saturation)
            sat_std = np.std(saturation)
            val_mean = np.mean(value)
            val_std = np.std(value)
            
            results["color_stats"] = {
                "saturation_mean": float(sat_mean),
                "saturation_std": float(sat_std),
                "brightness_mean": float(val_mean),
                "brightness_std": float(val_std)
            }
            
            # Check for unusual color properties
            # Very high or low saturation might indicate manipulation
            if sat_mean > 200 or sat_mean < 20:
                results["indicators"].append("Unusual saturation levels")
                results["manipulation_score"] = 0.2
            
            # Analyze color distribution across regions
            h, w = saturation.shape
            regions = [
                saturation[:h//2, :w//2],
                saturation[:h//2, w//2:],
                saturation[h//2:, :w//2],
                saturation[h//2:, w//2:]
            ]
            
            region_means = [np.mean(r) for r in regions]
            if np.std(region_means) > np.mean(region_means) * 0.3:
                results["indicators"].append("Inconsistent color saturation across regions")
                results["manipulation_score"] = max(results["manipulation_score"], 0.25)
        
        except Exception as e:
            logger.warning(f"Error in color analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _advanced_ela_analysis(self, image_rgb: np.ndarray, quality_levels: List[int] = [90, 75, 50]) -> Dict[str, Any]:
        """
        Advanced ELA analysis with multiple quality levels
        
        Args:
            image_rgb: RGB image as numpy array
            quality_levels: List of JPEG quality levels to test
        
        Returns:
            Dictionary with advanced ELA results
        """
        results = {
            "manipulation_score": 0.0,
            "indicators": [],
            "ela_consistency": {}
        }
        
        try:
            pil_image = Image.fromarray(image_rgb)
            ela_results = []
            
            for quality in quality_levels:
                # Recompress at different quality
                buffer = io.BytesIO()
                pil_image.save(buffer, format='JPEG', quality=quality)
                buffer.seek(0)
                recompressed = Image.open(buffer)
                recompressed_array = np.array(recompressed.convert('RGB'))
                
                # Calculate ELA
                ela = np.abs(image_rgb.astype(np.float32) - recompressed_array.astype(np.float32))
                ela_gray = np.mean(ela, axis=2)
                
                ela_mean = np.mean(ela_gray)
                ela_std = np.std(ela_gray)
                
                ela_results.append({
                    "quality": quality,
                    "mean": float(ela_mean),
                    "std": float(ela_std)
                })
            
            results["ela_consistency"] = {
                "results": ela_results,
                "mean_variance": float(np.std([r["mean"] for r in ela_results]))
            }
            
            # Check for inconsistent ELA across quality levels
            mean_variance = results["ela_consistency"]["mean_variance"]
            if mean_variance > 5.0:  # High variance indicates inconsistency
                results["indicators"].append("Inconsistent ELA patterns across quality levels")
                results["manipulation_score"] = 0.4
        
        except Exception as e:
            logger.warning(f"Error in advanced ELA analysis: {e}")
            results["error"] = str(e)
        
        return results

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of distribution"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        n = len(data)
        skew = (1/n) * np.sum(((data - mean) / std) ** 3)
        return float(skew)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of distribution"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        n = len(data)
        kurt = (1/n) * np.sum(((data - mean) / std) ** 4) - 3.0
        return float(kurt)

    def _generate_detailed_findings(self, techniques: Dict[str, Any]) -> Dict[str, Any]:
        """Generate human-readable detailed findings"""
        findings = {
            "summary": "",
            "technical_details": {},
            "recommendations": []
        }
        
        # Count indicators
        total_indicators = sum(len(t.get("indicators", [])) for t in techniques.values())
        avg_manipulation = np.mean([t.get("manipulation_score", 0) for t in techniques.values()])
        
        if total_indicators == 0 and avg_manipulation < 0.2:
            findings["summary"] = "No significant manipulation indicators detected. Image appears authentic."
        elif avg_manipulation > 0.5:
            findings["summary"] = "Multiple manipulation indicators detected. High probability of image tampering."
        else:
            findings["summary"] = "Some manipulation indicators detected. Further investigation recommended."
        
        # Technical details
        findings["technical_details"] = {
            "techniques_applied": list(techniques.keys()),
            "total_indicators": total_indicators,
            "average_manipulation_score": float(avg_manipulation)
        }
        
        # Recommendations
        if avg_manipulation > 0.5:
            findings["recommendations"].append("Image shows strong signs of manipulation. Verify source.")
        elif avg_manipulation > 0.3:
            findings["recommendations"].append("Minor anomalies detected. Cross-reference with metadata analysis.")
        else:
            findings["recommendations"].append("Image appears authentic. No action required.")
        
        return findings


# Singleton instance
_forensic_analysis_service: Optional[ForensicAnalysisService] = None


def get_forensic_analysis_service() -> ForensicAnalysisService:
    """Get or create the forensic analysis service singleton"""
    global _forensic_analysis_service
    if _forensic_analysis_service is None:
        _forensic_analysis_service = ForensicAnalysisService()
    return _forensic_analysis_service

