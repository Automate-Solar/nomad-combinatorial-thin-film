"""NOMAD schema for spatially resolved XRD measurements."""

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    SectionProperties,
)
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection
from plotly.colors import hex_to_rgb, qualitative
from plotly.subplots import make_subplots

from nomad_combinatorial_thin_film.categories import Uppsala

m_package = Package(
    name='Uppsala XRD Analysis',
    description=(
        'Spatially resolved XRD measurements, '
        'experimental peak detection and visualization.'
    ),
    categories=[Uppsala],
)

# ============================================================
# 1. Individual detected XRD peak
# ============================================================


class XRDPeak(ArchiveSection):
    """An experimentally detected XRD reflection."""

    m_def = Section()

    two_theta_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Peak position in 2-theta.',
    )

    intensity = Quantity(
        type=np.float64,
        description='Measured intensity at the detected peak.',
    )

    smoothed_intensity = Quantity(
        type=np.float64,
        description='Smoothed intensity at the detected peak.',
    )

    prominence = Quantity(
        type=np.float64,
        description='Absolute peak prominence.',
    )

    relative_prominence = Quantity(
        type=np.float64,
        description='Peak prominence divided by the intensity range.',
    )

    width_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Peak width at half prominence.',
    )

    width_samples = Quantity(
        type=np.float64,
        description='Peak width expressed in sampling points.',
    )

    left_width_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Left position of the peak width.',
    )

    right_width_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Right position of the peak width.',
    )


# ============================================================
# 2. Individual spatial XRD pattern
# ============================================================


class XRDPattern(ArchiveSection):
    """One experimental XRD pattern at a spatial position."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'source_filename',
                    'position_label',
                    'phi_deg',
                    'x_mm',
                    'y_mm',
                    'two_theta_deg',
                    'intensity',
                    'uncertainty',
                    'peaks',
                ]
            )
        )
    )

    source_filename = Quantity(
        type=str,
        description='Original ASC or XRDML filename.',
    )

    position_label = Quantity(
        type=str,
        description='Position label extracted from the filename.',
    )

    phi_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Sample rotation angle phi.',
    )

    x_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='X measurement coordinate.',
    )

    y_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='Y measurement coordinate.',
    )

    two_theta_deg = Quantity(
        type=np.float64,
        shape=['*'],
        unit='degree',
        description='Experimental 2-theta values.',
    )

    intensity = Quantity(
        type=np.float64,
        shape=['*'],
        description='Original measured XRD intensity.',
    )

    uncertainty = Quantity(
        type=np.float64,
        shape=['*'],
        description='Intensity uncertainty, when provided by the input file.',
    )

    peaks = SubSection(
        section_def=XRDPeak,
        repeats=True,
    )


# ============================================================
# 3. Complete XRD experiment
# ============================================================


class XRDRun(EntryData, PlotSection):
    """Spatially resolved XRD experiment."""

    m_def = Section(
        categories=[Uppsala],
        label='Spatially Resolved XRD Experiment',
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    'source_filename',
                    'condition_label',
                    'input_format',
                    'number_of_patterns',
                    'number_of_detected_peaks',
                    'peak_detection_enabled',
                    'smoothing_enabled',
                    'smoothing_window',
                    'smoothing_polyorder',
                    'prominence_fraction',
                    'minimum_prominence',
                    'minimum_distance_deg',
                    'minimum_width_deg',
                    'patterns',
                    'film_diameter_mm',
                    'notch_width_mm',
                    'notch_depth_mm',
                    'measurement_width_mm',
                    'measurement_height_mm',
                ]
            )
        ),
    )

    source_filename = Quantity(
        type=str,
        description='Uploaded XRD file or ZIP archive.',
    )

    condition_label = Quantity(
        type=str,
        description='Experimental condition derived from the uploaded filename.',
        a_eln=ELNAnnotation(component='StringEditQuantity'),
    )

    input_format = Quantity(
        type=str,
        description='Original XRD input format.',
    )

    number_of_patterns = Quantity(
        type=int,
        description='Number of spatial XRD patterns.',
    )

    number_of_detected_peaks = Quantity(
        type=int,
        description='Total number of detected experimental peaks.',
    )

    peak_detection_enabled = Quantity(
        type=bool,
        description='Whether experimental peak detection was performed.',
    )

    smoothing_enabled = Quantity(
        type=bool,
        description='Whether Savitzky-Golay smoothing was enabled.',
    )

    smoothing_window = Quantity(
        type=int,
        description='Savitzky-Golay smoothing window length.',
    )

    smoothing_polyorder = Quantity(
        type=int,
        description='Savitzky-Golay polynomial order.',
    )

    prominence_fraction = Quantity(
        type=np.float64,
        description='Fraction of the intensity range used for peak prominence.',
    )

    minimum_prominence = Quantity(
        type=np.float64,
        description='Minimum absolute peak prominence.',
    )

    minimum_distance_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Minimum separation between detected peaks.',
    )

    minimum_width_deg = Quantity(
        type=np.float64,
        unit='degree',
        description='Minimum accepted peak width.',
    )

    patterns = SubSection(
        section_def=XRDPattern,
        repeats=True,
    )

    # Optional physical dimensions for the sample-position schematic.
    # If left empty, the diagram is generated with estimated dimensions
    # and explicitly labelled "not to scale".
    film_diameter_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='Physical film diameter. Leave empty for an automatically sized schematic.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    notch_width_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='Width of the north notch. Leave empty for a schematic default.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    notch_depth_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='Depth of the north notch. Leave empty for a schematic default.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    measurement_width_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='Width of each XRD measurement footprint. Leave empty for a schematic default.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    measurement_height_mm = Quantity(
        type=np.float64,
        unit='mm',
        description='Height of each XRD measurement footprint. Leave empty for a schematic default.',
        a_eln=ELNAnnotation(component='NumberEditQuantity'),
    )

    # ========================================================
    # Plotting
    # ========================================================

    def plot(self):  # noqa: PLR0915
        """Plot all spatial XRD patterns together with their sample position map."""

        def as_float_array(value):
            if hasattr(value, 'magnitude'):
                value = value.magnitude
            return np.asarray(value, dtype=float)

        def optional_float(value):
            if value is None:
                return None
            if hasattr(value, 'magnitude'):
                value = value.magnitude
            try:
                result = float(value)
                return result if np.isfinite(result) else None
            except (TypeError, ValueError):
                return None

        patterns = list(self.patterns)
        if not patterns:
            self.figures = []
            return

        patterns.sort(
            key=lambda pattern: (
                optional_float(pattern.phi_deg) or 0.0,
                optional_float(pattern.y_mm) or 0.0,
                optional_float(pattern.x_mm) or 0.0,
            )
        )

        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=(
                'Raw Intensity (Vertically Offset)',
                'Normalized Intensity (Vertically Offset)',
                'Circular Film and Measurement Positions',
            ),
            row_heights=[0.39, 0.31, 0.30],
            vertical_spacing=0.09,
        )

        palette = qualitative.Plotly
        colors = {
            id(pattern): palette[index % len(palette)]
            for index, pattern in enumerate(patterns)
        }

        all_x = np.concatenate(
            [as_float_array(pattern.two_theta_deg) for pattern in patterns]
        )
        all_x = all_x[np.isfinite(all_x)]
        x_min = float(np.min(all_x)) if all_x.size else 0.0
        x_max = float(np.max(all_x)) if all_x.size else 1.0
        if x_min == x_max:
            x_max = x_min + 1.0

        raw_ranges = []
        normalized_patterns = []
        for pattern in patterns:
            y = as_float_array(pattern.intensity)
            finite_y = y[np.isfinite(y)]
            raw_ranges.append(float(np.ptp(finite_y)) if finite_y.size else 0.0)
            scale = float(np.max(np.abs(finite_y))) if finite_y.size else 0.0
            normalized_patterns.append(y / scale if scale > 0 else y.copy())

        raw_offset = max(max(raw_ranges, default=0.0) * 1.15, 1.0)
        normalized_ranges = [
            float(np.ptp(values[np.isfinite(values)]))
            for values in normalized_patterns
            if np.isfinite(values).any()
        ]
        normalized_offset = max(max(normalized_ranges, default=0.0) * 1.15, 1.0)

        for index, (pattern, normalized_y) in enumerate(
            zip(patterns, normalized_patterns)
        ):
            x = as_float_array(pattern.two_theta_deg)
            y = as_float_array(pattern.intensity)
            color = colors[id(pattern)]
            raw_y_offset = y + index * raw_offset
            normalized_y_offset = normalized_y + index * normalized_offset

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=raw_y_offset,
                    mode='lines',
                    name=pattern.position_label,
                    legendgroup=pattern.position_label,
                    line=dict(color=color, width=1.5),
                    connectgaps=False,
                    hovertemplate=(
                        f'{pattern.position_label}<br>'
                        '2-theta: %{x:.3f} degrees<br>'
                        'Intensity: %{customdata:.4g}<extra></extra>'
                    ),
                    customdata=y,
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=normalized_y_offset,
                    mode='lines',
                    name=f'{pattern.position_label} normalized',
                    legendgroup=pattern.position_label,
                    showlegend=False,
                    line=dict(color=color, width=1.5),
                    connectgaps=False,
                    hovertemplate=(
                        f'{pattern.position_label}<br>'
                        '2-theta: %{x:.3f} degrees<br>'
                        'Normalized intensity: %{customdata:.4g}<extra></extra>'
                    ),
                    customdata=normalized_y,
                ),
                row=2,
                col=1,
            )

            if pattern.peaks:
                peak_positions = [
                    optional_float(peak.two_theta_deg) for peak in pattern.peaks
                ]
                peak_intensities = [
                    optional_float(peak.intensity) for peak in pattern.peaks
                ]
                valid_peaks = [
                    (position, intensity)
                    for position, intensity in zip(peak_positions, peak_intensities)
                    if position is not None and intensity is not None
                ]
                if valid_peaks:
                    fig.add_trace(
                        go.Scatter(
                            x=[position for position, _ in valid_peaks],
                            y=[
                                intensity + index * raw_offset
                                for _, intensity in valid_peaks
                            ],
                            mode='markers',
                            name=f'{pattern.position_label} peaks',
                            legendgroup=pattern.position_label,
                            showlegend=False,
                            marker=dict(color=color, size=6, symbol='x'),
                            hovertemplate=(
                                f'{pattern.position_label} detected peak<br>'
                                '2-theta: %{x:.3f} degrees<br>'
                                'Intensity: %{y:.4g}<extra></extra>'
                            ),
                        ),
                        row=1,
                        col=1,
                    )

                    scale = (
                        max(abs(float(np.nanmax(y))), abs(float(np.nanmin(y))))
                        if y.size
                        else 0.0
                    )
                    normalized_peak_values = [
                        intensity / scale if scale > 0 else intensity
                        for _, intensity in valid_peaks
                    ]
                    fig.add_trace(
                        go.Scatter(
                            x=[position for position, _ in valid_peaks],
                            y=[
                                intensity + index * normalized_offset
                                for intensity in normalized_peak_values
                            ],
                            mode='markers',
                            name=f'{pattern.position_label} normalized peaks',
                            legendgroup=pattern.position_label,
                            showlegend=False,
                            marker=dict(color=color, size=6, symbol='x'),
                            hovertemplate=(
                                f'{pattern.position_label} detected peak<br>'
                                '2-theta: %{x:.3f} degrees<br>'
                                'Normalized intensity: %{customdata:.4g}<extra></extra>'
                            ),
                            customdata=normalized_peak_values,
                        ),
                        row=2,
                        col=1,
                    )

        for row in (1, 2):
            fig.update_xaxes(
                title_text='2-theta (degrees)',
                range=[x_min, x_max],
                showgrid=True,
                gridcolor='rgba(180,180,180,0.3)',
                row=row,
                col=1,
            )
            fig.update_yaxes(
                title_text=(
                    f'Intensity + {raw_offset:g} counts per pattern'
                    if row == 1
                    else f'Normalized intensity + {normalized_offset:g} per pattern'
                ),
                showgrid=True,
                gridcolor='rgba(180,180,180,0.3)',
                row=row,
                col=1,
            )

        # Filename coordinates are the centres of the measurement footprints.
        points = []
        for pattern in patterns:
            x = optional_float(pattern.x_mm)
            y = optional_float(pattern.y_mm)
            phi = optional_float(pattern.phi_deg) or 0.0
            if x is not None and y is not None:
                points.append((pattern, x, y, phi))

        max_coord = max([max(abs(x), abs(y)) for _, x, y, _ in points] or [10.0])
        diameter = optional_float(self.film_diameter_mm)
        notch_width = optional_float(self.notch_width_mm)
        notch_depth = optional_float(self.notch_depth_mm)
        rect_width = optional_float(self.measurement_width_mm)
        rect_height = optional_float(self.measurement_height_mm)

        dimensions_supplied = all(
            value is not None and value > 0
            for value in (diameter, notch_width, notch_depth, rect_width, rect_height)
        )

        radius = (
            diameter / 2 if diameter and diameter > 0 else max(max_coord + 3.0, 5.0)
        )
        notch_width = (
            notch_width if notch_width and notch_width > 0 else max(0.12 * radius, 0.8)
        )
        notch_depth = (
            notch_depth if notch_depth and notch_depth > 0 else max(0.07 * radius, 0.5)
        )
        rect_width = (
            rect_width if rect_width and rect_width > 0 else max(0.075 * radius, 0.8)
        )
        rect_height = (
            rect_height
            if rect_height and rect_height > 0
            else max(0.035 * radius, 0.45)
        )

        half_notch = min(notch_width / 2, radius * 0.45)
        notch_y = np.sqrt(max(radius**2 - half_notch**2, 0.0))
        notch_angle = np.arcsin(half_notch / radius)
        theta = np.linspace(np.pi / 2 + notch_angle, 5 * np.pi / 2 - notch_angle, 240)
        film_x = list(radius * np.cos(theta)) + [
            half_notch,
            half_notch,
            -half_notch,
            -half_notch,
        ]
        film_y = list(radius * np.sin(theta)) + [
            notch_y,
            radius - notch_depth,
            radius - notch_depth,
            notch_y,
        ]

        fig.add_trace(
            go.Scatter(
                x=film_x,
                y=film_y,
                mode='lines',
                fill='toself',
                fillcolor='rgba(180,190,205,0.22)',
                line=dict(color='#263238', width=2.5),
                name='Film boundary',
                showlegend=False,
                hoverinfo='skip',
            ),
            row=3,
            col=1,
        )

        for pattern, center_x, center_y, phi in points:
            color = colors[id(pattern)]
            angle = np.deg2rad(phi)
            corners = np.array(
                [
                    [-rect_width / 2, -rect_height / 2],
                    [rect_width / 2, -rect_height / 2],
                    [rect_width / 2, rect_height / 2],
                    [-rect_width / 2, rect_height / 2],
                ]
            )
            rotation = np.array(
                [[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]]
            )
            corners = corners @ rotation.T
            rectangle_x = list(corners[:, 0] + center_x)
            rectangle_y = list(corners[:, 1] + center_y)
            rectangle_x.append(rectangle_x[0])
            rectangle_y.append(rectangle_y[0])

            red, green, blue = hex_to_rgb(color)
            fig.add_trace(
                go.Scatter(
                    x=rectangle_x,
                    y=rectangle_y,
                    mode='lines',
                    fill='toself',
                    fillcolor=f'rgba({red},{green},{blue},0.30)',
                    line=dict(color=color, width=2),
                    name=pattern.position_label,
                    showlegend=False,
                    hovertemplate=(
                        f'{pattern.position_label}<br>X={center_x:g} mm<br>'
                        f'Y={center_y:g} mm<br>phi={phi:g} degrees<extra></extra>'
                    ),
                ),
                row=3,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=[center_x],
                    y=[center_y],
                    mode='markers',
                    marker=dict(
                        color=color,
                        size=6,
                        line=dict(color='white', width=1),
                    ),
                    showlegend=False,
                    hoverinfo='skip',
                ),
                row=3,
                col=1,
            )

        map_limit = max(radius * 1.18, max_coord + rect_width + 1.0)
        fig.update_xaxes(
            title_text='X (mm)',
            range=[-map_limit, map_limit],
            showgrid=True,
            zeroline=True,
            row=3,
            col=1,
        )
        fig.update_yaxes(
            title_text='Y (mm)',
            range=[-map_limit, map_limit],
            showgrid=True,
            zeroline=True,
            scaleanchor='x3',
            scaleratio=1,
            row=3,
            col=1,
        )
        fig.add_annotation(
            x=0.97,
            y=0.95,
            xref='x3 domain',
            yref='y3 domain',
            text='N',
            showarrow=False,
            font=dict(size=15, color='#263238'),
        )
        note = (
            'Dimensions supplied'
            if dimensions_supplied
            else 'SCHEMATIC - NOT TO SCALE. Set film diameter, notch and footprint dimensions in the ELN fields.'
        )
        fig.add_annotation(
            x=0.5,
            y=0.02,
            xref='x3 domain',
            yref='y3 domain',
            text=note,
            showarrow=False,
            font=dict(size=11, color='#555'),
        )

        fig.update_layout(
            title='Spatially Resolved XRD Patterns',
            template='plotly_white',
            width=1600,
            height=1500,
            margin=dict(l=65, r=35, t=150, b=55),
            hovermode='closest',
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='left',
                x=0,
                groupclick='togglegroup',
            ),
            font=dict(size=11),
        )

        self.figures = [
            PlotlyFigure(
                label='Offset XRD Patterns and Sample Map',
                figure=fig.to_plotly_json(),
            )
        ]


m_package.__init_metainfo__()
