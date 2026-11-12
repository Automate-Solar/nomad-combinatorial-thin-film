from nomad.datamodel.metainfo.plot import PlotlyFigure

from nomad_combinatorial_thin_film.constants import (
    CHANNEL_AXIS,
    COLOR_IMAGE_DIMENSIONS,
    GRAYSCALE_CHANNELS,
    MIN_IMAGE_DIMENSIONS,
    RGB_CHANNELS,
)

PCA_COMPONENT_COUNT = 3


def _read_wavelengths(hdr_path, band_count, np):
    """Read wavelength metadata or fall back to zero-based band numbers."""
    if isinstance(hdr_path, (list, tuple, np.ndarray)):
        wavelengths = np.asarray(hdr_path, dtype=float)
        return (
            wavelengths
            if wavelengths.size == band_count
            else np.arange(band_count, dtype=float)
        )

    from nomad_combinatorial_thin_film.parser.utils import read_envi_hdr

    hdr = read_envi_hdr(str(hdr_path))
    raw_wavelengths = hdr.get('wavelength')
    if isinstance(raw_wavelengths, (list, tuple)):
        wavelengths = np.asarray(raw_wavelengths, dtype=float)
    elif isinstance(raw_wavelengths, str):
        wavelengths = np.asarray(
            [float(value) for value in raw_wavelengths.strip('{} \n').split(',')],
            dtype=float,
        )
    else:
        wavelengths = np.arange(band_count, dtype=float)

    wavelength_unit = str(hdr.get('wavelength units', '')).strip().lower()
    if wavelength_unit in {
        'um',
        'µm',
        'μm',
        'micron',
        'microns',
        'micrometer',
        'micrometers',
    }:
        wavelengths = wavelengths * 1000

    if wavelengths.size != band_count:
        wavelengths = np.arange(band_count, dtype=float)
    return wavelengths


def _load_hyperspectral_cube(source, np):
    """Accept an in-memory cube, open file, or NPY path."""
    if isinstance(source, np.ndarray):
        return source
    if hasattr(source, 'read'):
        return np.load(source)
    return np.load(str(source), mmap_mode='r')


def _sampled_cube(cube, max_side=150):
    """Downsample only the spatial axes to keep interactive plots responsive."""
    import numpy as np

    stride = max(
        1,
        int(np.ceil(cube.shape[0] / max_side)),
        int(np.ceil(cube.shape[1] / max_side)),
    )
    return np.asarray(cube[::stride, ::stride, :], dtype=float), stride


def _finite_percentile_limits(values, np, lower=1, upper=99):
    finite = np.asarray(values)[np.isfinite(values)]
    if finite.size == 0:
        return 0.0, 1.0
    low, high = np.percentile(finite, [lower, upper])
    if high <= low:
        high = low + 1.0
    return float(low), float(high)


def create_mean_spectrum_plot(
    cube_path,
    hdr_path,
    logger=None,
):

    try:
        import numpy as np
        import plotly.graph_objects as go

        cube = _load_hyperspectral_cube(cube_path, np)
        sample, _ = _sampled_cube(cube, max_side=180)
        wavelengths = _read_wavelengths(hdr_path, cube.shape[2], np)
        pixels = sample.reshape(-1, sample.shape[2])
        mean_spectrum = np.nanmean(pixels, axis=0)
        low_spectrum, high_spectrum = np.nanpercentile(pixels, [10, 90], axis=0)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=high_spectrum,
                mode='lines',
                line=dict(width=0),
                hoverinfo='skip',
                showlegend=False,
                name='90th percentile',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=low_spectrum,
                mode='lines',
                line=dict(width=0),
                fill='tonexty',
                fillcolor='rgba(31, 119, 180, 0.18)',
                hoverinfo='skip',
                showlegend=True,
                name='10th–90th percentile',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=mean_spectrum,
                mode='lines',
                line=dict(color='#1769aa', width=2.5),
                name='Spatial mean',
            )
        )
        fig.update_layout(
            title='Mean spectrum and spatial variability',
            template='plotly_white',
            xaxis_title='Wavelength (nm)',
            yaxis_title='Signal intensity',
            hovermode='x unified',
            height=520,
            margin=dict(l=70, r=30, t=70, b=60),
        )
        fig.update_xaxes(showgrid=True, zeroline=False)
        fig.update_yaxes(showgrid=True, zeroline=False)

        return PlotlyFigure(label='Mean spectrum', figure=fig.to_plotly_json())

    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create mean spectrum: %s',
                exc,
            )

        return None


def create_integrated_intensity_plot(
    cube_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go

        cube = _load_hyperspectral_cube(cube_path, np)
        integrated = cube.sum(axis=2)
        max_display_size = 1000
        scale = max(
            1,
            int(np.ceil(integrated.shape[0] / max_display_size)),
            int(np.ceil(integrated.shape[1] / max_display_size)),
        )
        integrated = integrated[
            ::scale,
            ::scale,
        ]
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                z=integrated,
                colorbar=dict(title='Intensity'),
            )
        )
        fig.update_layout(
            title='Integrated Intensity Map',
            template='plotly_white',
            width=850,
            height=750,
            xaxis_title='Pixel X',
            yaxis_title='Pixel Y',
        )
        return PlotlyFigure(
            label='Integrated Intensity',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create intensity map: %s',
                exc,
            )
        return None


def create_spatial_maps_plot(cube_path, hdr_path, logger=None):
    """Show intensity, peak wavelength, and spectral variability together."""
    try:
        import numpy as np
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        cube = _load_hyperspectral_cube(cube_path, np)
        sample, stride = _sampled_cube(cube, max_side=180)
        wavelengths = _read_wavelengths(hdr_path, sample.shape[2], np)

        intensity = np.nanmean(sample, axis=2)
        finite_sample = np.where(np.isfinite(sample), sample, -np.inf)
        peak_index = np.argmax(finite_sample, axis=2)
        peak_wavelength = wavelengths[peak_index]
        all_invalid = ~np.isfinite(sample).any(axis=2)
        peak_wavelength[all_invalid] = np.nan
        spectral_std = np.nanstd(sample, axis=2)

        map_specs = [
            (
                intensity,
                'Mean signal',
                'Viridis',
                'Signal',
            ),
            (
                peak_wavelength,
                'Peak wavelength',
                'Turbo',
                'Wavelength (nm)',
            ),
            (
                spectral_std,
                'Spectral variability',
                'Magma',
                'Standard deviation',
            ),
        ]
        fig = make_subplots(
            rows=1,
            cols=3,
            subplot_titles=[item[1] for item in map_specs],
            horizontal_spacing=0.12,
        )
        colorbar_x = [0.285, 0.64, 0.995]
        for column, (values, title, colorscale, colorbar_title) in enumerate(
            map_specs,
            start=1,
        ):
            low, high = _finite_percentile_limits(values, np)
            fig.add_trace(
                go.Heatmap(
                    z=values,
                    x=np.arange(values.shape[1]) * stride,
                    y=np.arange(values.shape[0]) * stride,
                    colorscale=colorscale,
                    zmin=low,
                    zmax=high,
                    colorbar=dict(
                        title=colorbar_title,
                        x=colorbar_x[column - 1],
                        len=0.78,
                        thickness=12,
                        outlinewidth=0,
                    ),
                    hovertemplate=(
                        'Pixel X: %{x}<br>'
                        'Pixel Y: %{y}<br>'
                        f'{title}: %{{z:.4g}}<extra></extra>'
                    ),
                ),
                row=1,
                col=column,
            )
            fig.update_xaxes(
                title_text='Pixel X',
                row=1,
                col=column,
                showgrid=False,
            )
            fig.update_yaxes(
                title_text='Pixel Y' if column == 1 else None,
                autorange='reversed',
                scaleanchor='x' if column == 1 else f'x{column}',
                scaleratio=1,
                row=1,
                col=column,
                showgrid=False,
            )

        fig.update_layout(
            title='Spatial signal and spectral feature maps',
            template='plotly_white',
            height=520,
            margin=dict(l=60, r=90, t=90, b=55),
        )
        return PlotlyFigure(
            label='Spatial spectral maps',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning('Could not create spatial spectral maps: %s', exc)
        return None


def create_peak_wavelength_map(
    cube_path,
    hdr_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go

        from nomad_combinatorial_thin_film.parser.utils import (
            read_envi_hdr,
        )

        cube = _load_hyperspectral_cube(cube_path, np)
        hdr = read_envi_hdr(str(hdr_path))
        raw_wl = hdr.get('wavelength', None)
        if isinstance(raw_wl, (list, tuple)):
            wavelengths = np.array(
                raw_wl,
                dtype=float,
            )
        elif isinstance(raw_wl, str):
            wavelengths = np.array([float(v) for v in raw_wl.strip('{} \n').split(',')])
        else:
            wavelengths = np.arange(
                int(hdr.get('bands', cube.shape[2])),
                dtype=float,
            )
        # -----------------------------------
        # Peak wavelength calculation
        # -----------------------------------
        peak_idx = np.argmax(
            cube,
            axis=2,
        )
        peak_wavelength = wavelengths[peak_idx]
        # -----------------------------------
        # Downsample for display
        # -----------------------------------
        max_display_size = 1000
        scale = max(
            1,
            int(np.ceil(peak_wavelength.shape[0] / max_display_size)),
            int(np.ceil(peak_wavelength.shape[1] / max_display_size)),
        )
        peak_wavelength = peak_wavelength[
            ::scale,
            ::scale,
        ]
        # -----------------------------------
        # Plot
        # -----------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                z=peak_wavelength,
                colorscale='Turbo',
                colorbar=dict(title='Peak λ (nm)'),
            )
        )
        fig.update_layout(
            title='Peak Wavelength Map',
            template='plotly_white',
            width=850,
            height=750,
            xaxis_title='Pixel X',
            yaxis_title='Pixel Y',
        )
        return PlotlyFigure(
            label='Peak Wavelength Map',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create peak wavelength map: %s',
                exc,
            )
        return None


def create_quadrant_spectra_plot(
    cube_path,
    hdr_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go

        from nomad_combinatorial_thin_film.parser.utils import (
            read_envi_hdr,
        )

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        hdr = read_envi_hdr(str(hdr_path))
        raw_wl = hdr.get(
            'wavelength',
            None,
        )
        if isinstance(
            raw_wl,
            (list, tuple),
        ):
            wavelengths = np.array(
                raw_wl,
                dtype=float,
            )
        elif isinstance(
            raw_wl,
            str,
        ):
            wavelengths = np.array([float(v) for v in raw_wl.strip('{} \n').split(',')])
        else:
            wavelengths = np.arange(
                cube.shape[2],
                dtype=float,
            )
        # -----------------------------------
        # Split cube into quadrants
        # -----------------------------------
        ny, nx, _ = cube.shape
        ymid = ny // 2
        xmid = nx // 2
        q1 = cube[:ymid, :xmid, :]
        q2 = cube[:ymid, xmid:, :]
        q3 = cube[ymid:, :xmid, :]
        q4 = cube[ymid:, xmid:, :]
        # -----------------------------------
        # Mean spectra
        # -----------------------------------
        q1_spec = q1.mean(axis=(0, 1))
        q2_spec = q2.mean(axis=(0, 1))
        q3_spec = q3.mean(axis=(0, 1))
        q4_spec = q4.mean(axis=(0, 1))
        # -----------------------------------
        # Plot
        # -----------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=q1_spec,
                mode='lines',
                name='Q1',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=q2_spec,
                mode='lines',
                name='Q2',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=q3_spec,
                mode='lines',
                name='Q3',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=q4_spec,
                mode='lines',
                name='Q4',
            )
        )
        fig.update_layout(
            title='Regional Mean Spectra',
            template='plotly_white',
            width=900,
            height=650,
            xaxis_title='Wavelength (nm)',
            yaxis_title='Intensity',
            legend_title='Region',
        )
        return PlotlyFigure(
            label='2×2 Regional Spectra',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create quadrant spectra: %s',
                exc,
            )
        return None


def create_pca_rgb_plot(
    cube_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go
        from sklearn.decomposition import PCA

        cube = _load_hyperspectral_cube(cube_path, np)
        # ----------------------------------
        # Downsample
        # ----------------------------------
        cube_small, _ = _sampled_cube(cube, max_side=180)
        ny, nx, nbands = cube_small.shape
        if nbands < PCA_COMPONENT_COUNT or ny * nx < PCA_COMPONENT_COUNT:
            return None
        # ----------------------------------
        # Reshape for PCA
        # ----------------------------------
        pixels = cube_small.reshape(
            -1,
            nbands,
        )
        pixels = np.nan_to_num(pixels, nan=0.0, posinf=0.0, neginf=0.0)
        # ----------------------------------
        # PCA
        # ----------------------------------
        pca = PCA(
            n_components=PCA_COMPONENT_COUNT,
            random_state=0,
        )
        scores = pca.fit_transform(pixels)
        # ----------------------------------
        # Normalize
        # ----------------------------------
        rgb = np.zeros(
            (
                scores.shape[0],
                3,
            ),
            dtype=float,
        )
        for i in range(3):
            component = scores[:, i]
            low, high = _finite_percentile_limits(component, np, 2, 98)
            component = np.clip((component - low) / (high - low), 0, 1)
            rgb[:, i] = component
        rgb = rgb.reshape(
            ny,
            nx,
            3,
        )
        rgb = np.nan_to_num(
            rgb * 255,
            nan=0,
            posinf=255,
            neginf=0,
        ).astype(np.uint8)
        # ----------------------------------
        # Plot
        # ----------------------------------
        fig = go.Figure()
        fig.add_trace(go.Image(z=rgb))
        explained = pca.explained_variance_ratio_ * 100
        fig.update_layout(
            title=(
                'PCA RGB Map '
                f'(PC1={explained[0]:.1f}% '
                f'PC2={explained[1]:.1f}% '
                f'PC3={explained[2]:.1f}%)'
            ),
            template='plotly_white',
            height=650,
            xaxis_title='Pixel X (downsampled)',
            yaxis_title='Pixel Y (downsampled)',
            margin=dict(l=45, r=30, t=75, b=45),
        )
        return PlotlyFigure(
            label='PCA RGB Map',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create PCA RGB map: %s',
                exc,
            )
    return None


def create_regional_spectra_plot(cube_path, hdr_path, logger=None):
    """Compare average spectra from the four spatial quadrants."""
    try:
        import numpy as np
        import plotly.graph_objects as go

        cube = _load_hyperspectral_cube(cube_path, np)
        sample, _ = _sampled_cube(cube, max_side=180)
        wavelengths = _read_wavelengths(hdr_path, sample.shape[2], np)
        ymid, xmid = sample.shape[0] // 2, sample.shape[1] // 2
        regions = [
            ('Top left', sample[:ymid, :xmid, :], '#0077b6'),
            ('Top right', sample[:ymid, xmid:, :], '#f77f00'),
            ('Bottom left', sample[ymid:, :xmid, :], '#2a9d8f'),
            ('Bottom right', sample[ymid:, xmid:, :], '#9b5de5'),
        ]
        fig = go.Figure()
        for name, region, color in regions:
            if region.size == 0:
                continue
            mean_spectrum = np.nanmean(region.reshape(-1, region.shape[2]), axis=0)
            fig.add_trace(
                go.Scatter(
                    x=wavelengths,
                    y=mean_spectrum,
                    mode='lines',
                    name=name,
                    line=dict(color=color, width=2),
                )
            )

        fig.update_layout(
            title='Mean spectra by image region',
            template='plotly_white',
            height=520,
            xaxis_title='Wavelength (nm)',
            yaxis_title='Signal intensity',
            hovermode='x unified',
            legend_title_text='Region',
            margin=dict(l=70, r=30, t=70, b=60),
        )
        fig.update_xaxes(showgrid=True, zeroline=False)
        fig.update_yaxes(showgrid=True, zeroline=False)
        return PlotlyFigure(label='Regional spectra', figure=fig.to_plotly_json())
    except Exception as exc:
        if logger:
            logger.warning('Could not create regional spectra: %s', exc)
        return None


def create_pca_component_maps(
    cube_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go
        from sklearn.decomposition import PCA

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        cube_small = cube[::4, ::4, :]
        ny, nx, nbands = cube_small.shape
        pixels = cube_small.reshape(
            -1,
            nbands,
        )
        pca = PCA(
            n_components=3,
            random_state=0,
        )
        scores = pca.fit_transform(pixels)
        explained = pca.explained_variance_ratio_ * 100
        figures = []
        for pc in range(3):
            image = scores[:, pc].reshape(
                ny,
                nx,
            )
            fig = go.Figure()
            fig.add_trace(
                go.Heatmap(
                    z=image,
                    colorscale='RdBu',
                    colorbar=dict(title=f'PC{pc + 1}'),
                )
            )
            fig.update_layout(
                title=(f'Principal Component {pc + 1} ({explained[pc]:.1f}% variance)'),
                template='plotly_white',
                width=850,
                height=750,
                xaxis_title='Pixel X',
                yaxis_title='Pixel Y',
            )
            figures.append(
                PlotlyFigure(
                    label=f'PC{pc + 1} Map',
                    figure=fig.to_plotly_json(),
                )
            )
        return figures
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create PCA maps: %s',
                exc,
            )
        return []


def create_pca_loading_plot(
    cube_path,
    hdr_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go
        from sklearn.decomposition import PCA

        from nomad_combinatorial_thin_film.parser.utils import (
            read_envi_hdr,
        )

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        hdr = read_envi_hdr(str(hdr_path))
        raw_wl = hdr.get(
            'wavelength',
            None,
        )
        if isinstance(
            raw_wl,
            (list, tuple),
        ):
            wavelengths = np.array(
                raw_wl,
                dtype=float,
            )
        elif isinstance(
            raw_wl,
            str,
        ):
            wavelengths = np.array([float(v) for v in raw_wl.strip('{} \n').split(',')])
        else:
            wavelengths = np.arange(
                cube.shape[2],
                dtype=float,
            )
        # ----------------------------------
        # Downsample spatially
        # ----------------------------------
        cube_small = cube[::4, ::4, :]
        ny, nx, nbands = cube_small.shape
        pixels = cube_small.reshape(
            -1,
            nbands,
        )
        pca = PCA(
            n_components=3,
            random_state=0,
        )
        pca.fit(pixels)
        explained = pca.explained_variance_ratio_ * 100
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=pca.components_[0],
                mode='lines',
                name=f'PC1 ({explained[0]:.1f}%)',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=pca.components_[1],
                mode='lines',
                name=f'PC2 ({explained[1]:.1f}%)',
            )
        )
        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=pca.components_[2],
                mode='lines',
                name=f'PC3 ({explained[2]:.1f}%)',
            )
        )
        fig.update_layout(
            title='PCA Loading Spectra',
            template='plotly_white',
            width=900,
            height=650,
            xaxis_title='Wavelength (nm)',
            yaxis_title='Loading Weight',
            legend_title='Component',
        )
        return PlotlyFigure(
            label='PCA Loading Spectra',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create PCA loading spectra: %s',
                exc,
            )
        return None


def create_wavelength_slider_plot(
    cube_path,
    hdr_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go
        from nomad.datamodel.metainfo.plot import PlotlyFigure

        from nomad_combinatorial_thin_film.parser.utils import (
            read_envi_hdr,
        )

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        hdr = read_envi_hdr(str(hdr_path))
        raw_wl = hdr.get('wavelength', None)
        if isinstance(raw_wl, (list, tuple)):
            wavelengths = np.array(raw_wl, dtype=float)
        elif isinstance(raw_wl, str):
            wavelengths = np.array([float(v) for v in raw_wl.strip('{} \n').split(',')])
        else:
            wavelengths = np.arange(int(hdr.get('bands', 0)), dtype=float)
        # ----------------------------------
        # Spatial downsampling
        # ----------------------------------
        cube = cube[::4, ::4, :]
        # ----------------------------------
        # Spectral downsampling
        # ----------------------------------
        wavelength_step = max(
            1,
            len(wavelengths) // 100,
        )
        cube = cube[
            :,
            :,
            ::wavelength_step,
        ]
        wavelengths = wavelengths[::wavelength_step]
        # ----------------------------------
        # Normalize first image
        # ----------------------------------
        image0 = cube[:, :, 0]
        image0 = (image0 - image0.min()) / (image0.max() - image0.min() + 1e-12)
        fig = go.Figure(
            data=[
                go.Heatmap(
                    z=image0,
                    colorscale='Viridis',
                    showscale=True,
                )
            ]
        )
        # ----------------------------------
        # Frames
        # ----------------------------------
        frames = []
        for i in range(len(wavelengths)):
            image = cube[:, :, i]
            image = (image - image.min()) / (image.max() - image.min() + 1e-12)
            frames.append(
                go.Frame(
                    data=[
                        go.Heatmap(
                            z=image,
                            colorscale='Viridis',
                            showscale=True,
                        )
                    ],
                    name=f'{wavelengths[i]:.1f}',
                )
            )
        fig.frames = frames
        # ----------------------------------
        # Slider
        # ----------------------------------
        slider_steps = []
        for i, wl in enumerate(wavelengths):
            slider_steps.append(
                {
                    'args': [
                        [f'{wl:.1f}'],
                        {
                            'frame': {
                                'duration': 0,
                                'redraw': True,
                            },
                            'mode': 'immediate',
                        },
                    ],
                    'label': f'{wl:.0f}',
                    'method': 'animate',
                }
            )
        fig.update_layout(
            title='Hyperspectral Wavelength Explorer',
            width=850,
            height=750,
            template='plotly_white',
            xaxis_title='Pixel X',
            yaxis_title='Pixel Y',
            sliders=[
                {
                    'active': 0,
                    'currentvalue': {'prefix': 'Wavelength (nm): '},
                    'steps': slider_steps,
                }
            ],
        )
        return PlotlyFigure(
            label='Wavelength Explorer',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create wavelength slider: %s',
                exc,
            )
        return None


def create_spectral_variance_map(
    cube_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        # ----------------------------------
        # Spectral variance
        # ----------------------------------
        variance_map = np.std(
            cube,
            axis=2,
        )
        # ----------------------------------
        # Downsample
        # ----------------------------------
        max_display_size = 1000
        scale = max(
            1,
            int(np.ceil(variance_map.shape[0] / max_display_size)),
            int(np.ceil(variance_map.shape[1] / max_display_size)),
        )
        variance_map = variance_map[
            ::scale,
            ::scale,
        ]
        # ----------------------------------
        # Plot
        # ----------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Heatmap(
                z=variance_map,
                colorscale='Inferno',
                colorbar=dict(title='σ'),
            )
        )
        fig.update_layout(
            title='Spectral Variance Map',
            template='plotly_white',
            width=850,
            height=750,
            xaxis_title='Pixel X',
            yaxis_title='Pixel Y',
        )
        return PlotlyFigure(
            label='Spectral Variance Map',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create variance map: %s',
                exc,
            )
        return None


def create_3d_integrated_surface(
    cube_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        # ----------------------------------
        # Integrated intensity
        # ----------------------------------
        integrated = np.sum(
            cube,
            axis=2,
        )
        # ----------------------------------
        # Aggressive downsampling
        # ----------------------------------
        max_size = 150
        scale = max(
            1,
            int(np.ceil(integrated.shape[0] / max_size)),
            int(np.ceil(integrated.shape[1] / max_size)),
        )
        integrated = integrated[
            ::scale,
            ::scale,
        ]
        ny, nx = integrated.shape
        x = np.arange(nx)
        y = np.arange(ny)
        # ----------------------------------
        # Robust normalization
        # ----------------------------------
        p1 = np.percentile(
            integrated,
            1,
        )
        p99 = np.percentile(
            integrated,
            99,
        )
        z = np.clip(
            integrated,
            p1,
            p99,
        )
        z = (z - z.min()) / (z.max() - z.min() + 1e-12)
        # ----------------------------------
        # Surface
        # ----------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Surface(
                z=z,
                x=x,
                y=y,
                colorscale='Viridis',
                showscale=True,
            )
        )
        fig.update_layout(
            title='3D Integrated Intensity Surface',
            template='plotly_white',
            width=1000,
            height=850,
            scene=dict(
                xaxis_title='Pixel X',
                yaxis_title='Pixel Y',
                zaxis_title='Normalized Intensity',
                camera=dict(
                    eye=dict(
                        x=1.8,
                        y=1.8,
                        z=1.2,
                    )
                ),
            ),
        )
        return PlotlyFigure(
            label='3D Integrated Surface',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create 3D integrated surface: %s',
                exc,
            )
        return None


def create_3d_peak_wavelength_surface(
    cube_path,
    hdr_path,
    logger=None,
):
    try:
        import numpy as np
        import plotly.graph_objects as go

        from nomad_combinatorial_thin_film.parser.utils import (
            read_envi_hdr,
        )

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        hdr = read_envi_hdr(str(hdr_path))
        raw_wl = hdr.get(
            'wavelength',
            None,
        )
        if isinstance(
            raw_wl,
            (list, tuple),
        ):
            wavelengths = np.array(
                raw_wl,
                dtype=float,
            )
        elif isinstance(
            raw_wl,
            str,
        ):
            wavelengths = np.array([float(v) for v in raw_wl.strip('{} \n').split(',')])
        else:
            wavelengths = np.arange(
                cube.shape[2],
                dtype=float,
            )
        # ----------------------------------
        # Peak wavelength map
        # ----------------------------------
        peak_idx = np.argmax(
            cube,
            axis=2,
        )
        peak_wavelength = wavelengths[peak_idx]
        # ----------------------------------
        # Downsample
        # ----------------------------------
        max_size = 150
        scale = max(
            1,
            int(np.ceil(peak_wavelength.shape[0] / max_size)),
            int(np.ceil(peak_wavelength.shape[1] / max_size)),
        )
        peak_wavelength = peak_wavelength[
            ::scale,
            ::scale,
        ]
        ny, nx = peak_wavelength.shape
        x = np.arange(nx)
        y = np.arange(ny)
        # ----------------------------------
        # Surface
        # ----------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Surface(
                z=peak_wavelength,
                x=x,
                y=y,
                colorscale='Turbo',
                showscale=True,
                colorbar=dict(title='λ (nm)'),
            )
        )
        fig.update_layout(
            title='3D Peak Wavelength Surface',
            template='plotly_white',
            width=1000,
            height=850,
            scene=dict(
                xaxis_title='Pixel X',
                yaxis_title='Pixel Y',
                zaxis_title='Peak Wavelength (nm)',
                camera=dict(
                    eye=dict(
                        x=1.8,
                        y=1.8,
                        z=1.2,
                    )
                ),
            ),
        )
        return PlotlyFigure(
            label='3D Peak Wavelength Surface',
            figure=fig.to_plotly_json(),
        )
    except Exception as exc:
        if logger:
            logger.warning(
                'Could not create 3D peak wavelength surface: %s',
                exc,
            )
        return None


# ============================================================
# Image plotting utilities
# ============================================================


def normalize_plot_array(array):
    import numpy as np

    array = np.asarray(array, dtype=np.float32)
    arr_min = np.nanmin(array)
    arr_max = np.nanmax(array)
    if arr_max == arr_min:
        return np.full(array.shape, 128, dtype=np.uint8)
    return ((array - arr_min) / (arr_max - arr_min) * 255).astype(np.uint8)


def create_image_plot(npy_path, roi=None, logger=None):
    try:
        import numpy as np
        import plotly.graph_objects as go

        image_array = np.load(str(npy_path), mmap_mode='r')
        if image_array.size == 0 or len(image_array.shape) < MIN_IMAGE_DIMENSIONS:
            return []

        max_display_size = 1000
        scale = max(
            1,
            int(np.ceil(image_array.shape[0] / max_display_size)),
            int(np.ceil(image_array.shape[1] / max_display_size)),
        )
        image_display = np.asarray(image_array[::scale, ::scale])

        if (
            len(image_display.shape) == COLOR_IMAGE_DIMENSIONS
            and image_display.shape[CHANNEL_AXIS] >= RGB_CHANNELS
        ):
            display_data = normalize_plot_array(image_display[:, :, :RGB_CHANNELS])
        elif (
            len(image_display.shape) == COLOR_IMAGE_DIMENSIONS
            and image_display.shape[CHANNEL_AXIS] == GRAYSCALE_CHANNELS
        ):
            gray = normalize_plot_array(image_display[:, :, 0])
            display_data = np.stack([gray, gray, gray], axis=2)
        else:
            gray = normalize_plot_array(image_display)
            display_data = np.stack([gray, gray, gray], axis=2)

        fig = go.Figure()
        fig.add_trace(go.Image(z=display_data.astype(np.uint8), name='Image'))

        if roi and roi.bounding_box:
            bbox = roi.bounding_box
            fig.add_shape(
                type='rect',
                x0=bbox.x_min / scale,
                y0=bbox.y_min / scale,
                x1=bbox.x_max / scale,
                y1=bbox.y_max / scale,
                line=dict(color='red', width=3),
            )

        if roi and roi.center_x_px is not None:
            radius = roi.radius_px or 0
            theta = np.linspace(0, 2 * np.pi, 96)
            circle_x = (roi.center_x_px + radius * np.cos(theta)) / scale
            circle_y = (roi.center_y_px + radius * np.sin(theta)) / scale
            fig.add_trace(
                go.Scatter(
                    x=circle_x,
                    y=circle_y,
                    mode='lines',
                    name='ROI',
                    line=dict(color='cyan', width=2),
                )
            )

        fig.update_layout(
            title='Image preview',
            template='plotly_white',
            dragmode='zoom',
            hovermode='closest',
            width=850,
            height=750,
            margin=dict(l=40, r=20, t=50, b=40),
            xaxis=dict(title='Pixel X', constrain='domain'),
            yaxis=dict(
                title='Pixel Y',
                scaleanchor='x',
                scaleratio=1,
                autorange='reversed',
            ),
        )

        return [
            PlotlyFigure(label='Image preview with ROI', figure=fig.to_plotly_json())
        ]

    except Exception as exc:
        if logger:
            logger.warning('Could not create image plot for %s: %s', npy_path, exc)
        return []


# ============================================================
# Hyperspectral plotting orchestration
# ============================================================


def create_hyperspectral_analysis_figures(cube_path, hdr_path, logger=None):
    figures = []

    for figure in (
        create_mean_spectrum_plot(cube_path, hdr_path, logger),
        create_peak_wavelength_map(cube_path, hdr_path, logger),
        create_pca_rgb_plot(cube_path, logger),
        create_pca_loading_plot(cube_path, hdr_path, logger),
        create_spectral_variance_map(cube_path, logger),
        create_3d_peak_wavelength_surface(cube_path, hdr_path, logger),
    ):
        if figure:
            figures.append(figure)

    pc_figs = create_pca_component_maps(cube_path, logger)
    if pc_figs:
        figures.extend(pc_figs)

    return figures


def create_hyperspectral_overview_figures(cube_path, hdr_path, logger=None):
    figures = []

    for figure in (
        create_mean_spectrum_plot(cube_path, hdr_path, logger),
        create_spatial_maps_plot(cube_path, hdr_path, logger),
        create_regional_spectra_plot(cube_path, hdr_path, logger),
        create_pca_rgb_plot(cube_path, logger),
    ):
        if figure:
            figures.append(figure)

    return figures


def collect_image_dataset_figures(measurements):
    figures = []

    for measurement in measurements or []:
        image = getattr(measurement, 'image', None)
        if image is None or not getattr(image, 'figures', None):
            continue

        for figure in image.figures:
            figures.append(
                PlotlyFigure(
                    label=getattr(figure, 'label', None),
                    index=getattr(figure, 'index', None),
                    open=getattr(figure, 'open', None),
                    figure=getattr(figure, 'figure', None),
                )
            )

    return figures
