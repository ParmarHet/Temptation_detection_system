const API_BASE = '/api/v1';

export async function analyzeDocument(file, deep = false) {
  const endpoint = deep ? '/analyze/deep' : '/analyze';
  const formData = new FormData();
  formData.append('file', file);

  const submitResponse = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    body: formData,
  });

  if (!submitResponse.ok) {
    const error = await submitResponse.json().catch(() => ({ detail: 'Failed to submit job' }));
    throw new Error(error.detail || `HTTP ${submitResponse.status}`);
  }

  const { job_id } = await submitResponse.json();
  const rawResult = await pollJob(job_id);
  return transformResult(rawResult, file.name);
}

function transformResult(data, filename) {
  // Map verdict
  const verdictMap = {
    clean: 'CLEAN',
    suspicious: 'SUSPICIOUS',
    likely_tampered: 'TAMPERED',
  };
  const verdict = verdictMap[data.verdict] || data.verdict?.toUpperCase() || 'UNKNOWN';

  // Convert techniques dict to array
  const techniques = [];
  if (data.techniques) {
    for (const [key, info] of Object.entries(data.techniques)) {
      if (info.skipped && (info.score === 0 || info.score == null)) continue;
      techniques.push({
        name: formatTechniqueName(key),
        score: info.score || 0,
        details: info.details || {},
        heatmapUrl: info.heatmap_url,
      });
    }
  }

  // Build heatmap URLs
  const heatmap_urls = {};
  if (data.fused_heatmap_url) heatmap_urls.fused = data.fused_heatmap_url;
  for (const [key, info] of Object.entries(data.techniques || {})) {
    if (info.heatmap_url) heatmap_urls[key] = info.heatmap_url;
  }

  // Build findings from actual technique data
  const findings = buildFindings(data.techniques || {}, data.fusion, data.format);

  return {
    analysis_id: data.id,
    overall_score: data.overall_score,
    verdict,
    techniques,
    findings,
    image_url: data.original_image_url,
    heatmap_urls,
    format: data.format,
    filename: data.filename || filename,
  };
}

function formatTechniqueName(key) {
  const names = {
    ela: 'Error Level Analysis',
    noise: 'Noise/Residual Analysis',
    copymove: 'Copy-Move Detection',
    metadata: 'Metadata Consistency',
    jpeg_ghost: 'JPEG Ghost Detection',
    ocr: 'OCR Consistency',
  };
  return names[key] || key;
}

function extractFlagMessage(flag) {
  if (typeof flag === 'string') return flag;
  if (flag && typeof flag === 'object') {
    return flag.detail || flag.message || flag.description || JSON.stringify(flag);
  }
  return String(flag);
}

function extractFlagSeverity(flag, fallback) {
  if (flag && typeof flag === 'object' && flag.severity) {
    return flag.severity;
  }
  return fallback;
}

function buildFindings(techniques, fusion, format) {
  const findings = [];

  // ELA findings
  const ela = techniques.ela;
  if (ela && !ela.skipped) {
    const d = ela.details || {};
    if (d.regions_flagged > 0) {
      findings.push({
        message: `ELA flagged ${d.regions_flagged} region${d.regions_flagged > 1 ? 's' : ''} with inconsistent compression`,
        severity: ela.score > 60 ? 'high' : ela.score > 30 ? 'medium' : 'low',
        technique: 'Error Level Analysis',
      });
    }
    if (d.mean_error_level > 5) {
      findings.push({
        message: `Mean error level is elevated at ${d.mean_error_level.toFixed(1)}%`,
        severity: d.mean_error_level > 15 ? 'high' : 'medium',
        technique: 'Error Level Analysis',
      });
    }
    if (d.anomaly_pixel_ratio > 0.05) {
      findings.push({
        message: `${(d.anomaly_pixel_ratio * 100).toFixed(1)}% of pixels show anomalous error levels`,
        severity: d.anomaly_pixel_ratio > 0.15 ? 'high' : 'medium',
        technique: 'Error Level Analysis',
      });
    }
  }

  // Noise findings
  const noise = techniques.noise;
  if (noise && !noise.skipped) {
    const d = noise.details || {};
    if (d.flagged_ratio > 0.01) {
      findings.push({
        message: `${d.blocks_flagged} blocks flagged with anomalous noise patterns (${(d.flagged_ratio * 100).toFixed(1)}% of image)`,
        severity: noise.score > 60 ? 'high' : noise.score > 30 ? 'medium' : 'low',
        technique: 'Noise/Residual Analysis',
      });
    }
    if (d.uniformity_flag) {
      findings.push({
        message: 'Noise distribution is non-uniform — possible spliced regions',
        severity: 'high',
        technique: 'Noise/Residual Analysis',
      });
    }
  }

  // Copy-move findings
  const copymove = techniques.copymove;
  if (copymove && !copymove.skipped) {
    const d = copymove.details || {};
    if (d.matches_found > 0) {
      findings.push({
        message: `Copy-move detected: ${(d.coverage_ratio * 100).toFixed(2)}% image coverage`,
        severity: copymove.score > 50 ? 'high' : 'medium',
        technique: 'Copy-Move Detection',
      });
    }
  }

  // Metadata findings
  const metadata = techniques.metadata;
  if (metadata && !metadata.skipped) {
    const d = metadata.details || {};
    if (d.flags && d.flags.length > 0) {
      for (const flag of d.flags) {
        findings.push({
          message: extractFlagMessage(flag),
          severity: extractFlagSeverity(flag, metadata.score > 60 ? 'high' : metadata.score > 30 ? 'medium' : 'low'),
          technique: 'Metadata Consistency',
        });
      }
    }
  }

  // JPEG ghost findings
  const jpegGhost = techniques.jpeg_ghost;
  if (jpegGhost && !jpegGhost.skipped) {
    const d = jpegGhost.details || {};
    if (d.flags && d.flags.length > 0) {
      for (const flag of d.flags) {
        findings.push({
          message: extractFlagMessage(flag),
          severity: extractFlagSeverity(flag, jpegGhost.score > 60 ? 'high' : jpegGhost.score > 30 ? 'medium' : 'low'),
          technique: 'JPEG Ghost Detection',
        });
      }
    }
    if (d.double_compression_detected) {
      findings.push({
        message: 'Double JPEG compression detected — image may have been re-saved after editing',
        severity: 'high',
        technique: 'JPEG Ghost Detection',
      });
    }
  }

  // OCR findings
  const ocr = techniques.ocr;
  if (ocr && !ocr.skipped) {
    const d = ocr.details || {};
    if (d.flags && d.flags.length > 0) {
      for (const flag of d.flags) {
        findings.push({
          message: extractFlagMessage(flag),
          severity: extractFlagSeverity(flag, ocr.score > 60 ? 'high' : ocr.score > 30 ? 'medium' : 'low'),
          technique: 'OCR Consistency',
        });
      }
    }
    if (d.inconsistencies_found > 0) {
      findings.push({
        message: `${d.inconsistencies_found} text inconsistency detected by OCR`,
        severity: 'medium',
        technique: 'OCR Consistency',
      });
    }
  }

  // Fusion contributions
  if (fusion && fusion.contributing_techniques) {
    for (const [tech, contrib] of Object.entries(fusion.contributing_techniques)) {
      if (contrib.contribution > 10) {
        findings.push({
          message: `${formatTechniqueName(tech)} is a major contributor (weighted score: ${contrib.contribution.toFixed(1)})`,
          severity: contrib.contribution > 30 ? 'high' : 'medium',
          technique: formatTechniqueName(tech),
        });
      }
    }
  }

  // Format-specific notes
  if (format && format.toLowerCase() !== 'jpg' && format.toLowerCase() !== 'jpeg') {
    findings.push({
      message: 'Image is not JPEG — ELA and JPEG ghost results may be less reliable',
      severity: 'info',
      technique: 'General',
    });
  }

  return findings;
}

async function pollJob(jobId, maxAttempts = 600, intervalMs = 500) {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch job status');
    }

    const data = await response.json();

    if (data.status === 'completed') {
      return data.result;
    }

    if (data.status === 'failed') {
      throw new Error(data.error || 'Analysis failed');
    }

    attempts++;
    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error('Analysis timed out');
}

export function getHeatmapUrl(analysisId, technique) {
  return `${API_BASE}/heatmap/${analysisId}/${technique}`;
}

export async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}
