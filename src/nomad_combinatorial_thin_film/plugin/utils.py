from nomad.datamodel.metainfo.plot import PlotlyFigure

from nomad_combinatorial_thin_film.constants import (
    CHANNEL_AXIS,
    COLOR_IMAGE_DIMENSIONS,
    GRAYSCALE_CHANNELS,
    MIN_IMAGE_DIMENSIONS,
    RGB_CHANNELS,
)


def create_mean_spectrum_plot(
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

        # Be tolerant to different header formats: some readers
        # provide a list, others a string like "{400.0,401.0,...}".
        raw_wl = hdr.get('wavelength', None)
        if isinstance(raw_wl, (list, tuple)):
            wavelengths = np.array(raw_wl, dtype=float)
        elif isinstance(raw_wl, str):
            wavelengths = np.array([float(v) for v in raw_wl.strip('{} \n').split(',')])
        else:
            # fallback: use band indices if no wavelength info
            wavelengths = np.arange(int(hdr.get('bands', 0)), dtype=float)

        mean_spectrum = cube.mean(axis=(0, 1))

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=wavelengths,
                y=mean_spectrum,
                mode='lines',
                name='Mean Spectrum',
            )
        )

        fig.update_layout(
            title='Mean Spectrum',
            template='plotly_white',
            xaxis_title='Wavelength (nm)',
            yaxis_title='Intensity',
            width=850,
            height=650,
        )

        return PlotlyFigure(
            label='Mean Spectrum',
            figure=fig.to_plotly_json(),
        )

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

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
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

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
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

        cube = np.load(
            str(cube_path),
            mmap_mode='r',
        )
        # ----------------------------------
        # Downsample
        # ----------------------------------
        cube_small = cube[::4, ::4, :]
        ny, nx, nbands = cube_small.shape
        # ----------------------------------
        # Reshape for PCA
        # ----------------------------------
        pixels = cube_small.reshape(
            -1,
            nbands,
        )
        # ----------------------------------
        # PCA
        # ----------------------------------
        pca = PCA(
            n_components=3,
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
            component = (component - component.min()) / (
                component.max() - component.min() + 1e-12
            )
            rgb[:, i] = component
        rgb = rgb.reshape(
            ny,
            nx,
            3,
        )
        rgb = (rgb * 255).astype(np.uint8)
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
            width=900,
            height=750,
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
        create_integrated_intensity_plot(cube_path, logger),
        create_quadrant_spectra_plot(cube_path, hdr_path, logger),
        create_3d_integrated_surface(cube_path, logger),
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
