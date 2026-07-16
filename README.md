# Combinatorial Thin Film Characterization Plugin for NOMAD

## Overview

This repository implements a multimodal characterization framework for combinatorial thin-film research within NOMAD Oasis.

The project currently supports:

- Image data parsing and visualization
- Hyperspectral image parsing and visualization
- Synthesis metadata integration
- Plotly-based interactive visualizations inside NOMAD
- Extensible architecture for future Raman and XRD modules

---

## Architecture

```text
Combinatorial Thin Film Dataset
│
├── Synthesis Information
│
├── Image Characterization
│   ├── Metadata
│   ├── ROI
│   ├── Dimensions
│   ├── Preview
│   └── Plotly Visualization
│
└── Hyperspectral Characterization
    ├── ENVI Header Parsing
    ├── Cube Loading
    ├── Cube Metadata
    ├── NPY Storage
    ├── RGB Preview
    └── Plotly Visualization
```

## Image Module

- Image metadata parsing
- ROI handling
- Bounding box support
- Plotly visualization inside NOMAD

## Hyperspectral Module

### Core Features

- ENVI header reader
- BIL file reader
- Wavelength handling
- Spectrum extraction
- Band extraction
- RGB rendering
- Mean spectrum calculation

### Data Model

- AcquisitionMetadata
- CubeMetadata
- RawData
- Visualization

## Parser Workflow

```text
Find folder
 ↓
Find HDR
 ↓
Find BIL
 ↓
Read metadata
 ↓
Load cube
 ↓
Create cube.npy
 ↓
Create RGB preview
 ↓
Build NOMAD archive
 ↓
Generate visualizations
```

## Current Visualization Strategy

Implemented:
- RGB Preview
- Mean Spectrum
- Integrated Intensity Map
- Wavelength Explorer (in development)

Planned:
- Peak Wavelength Map
- 2×2 Mean Spectra Viewer
- PCA Component Maps
- PCA RGB Composite
- 3D Surface Visualizations

## Long-Term Vision

```text
Combinatorial Thin Film Characterization Platform
│
├── Image
├── Hyperspectral
├── Raman
└── XRD
```

Future goals:

- FAIR data management
- Automated characterization workflows
- Machine learning pipelines
- Self-driving laboratory infrastructure
- Autonomous materials discovery

## Development Status

Infrastructure: ~70% complete

Visualization: ~30% complete

## Roadmap

### Phase 1
- Mean Spectrum
- Integrated Intensity Map
- Peak Wavelength Map
- 2×2 Spectral Regions

### Phase 2
- PCA Visualization
- PCA RGB Maps
- Spectral Clustering

### Phase 3
- Raman Integration
- XRD Integration
- Cross-modal Analysis

### Phase 4
- Machine Learning Workflows
- Self-Driving Laboratory Integration
- Autonomous Experiment Planning
