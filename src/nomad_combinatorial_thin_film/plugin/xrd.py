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

m_package = Package(
    name="Uppsala XRD Analysis",
    description=(
        "Spatially resolved XRD measurements, "
        "experimental peak detection and visualization."
    ),
)

LOG_INTENSITY_MODE_INDEX = 2


# ============================================================
# 1. Individual detected XRD peak
# ============================================================


class XRDPeak(ArchiveSection):
    """An experimentally detected XRD reflection."""

    m_def = Section()

    two_theta_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Peak position in 2-theta.",
    )

    intensity = Quantity(
        type=np.float64,
        description="Measured intensity at the detected peak.",
    )

    smoothed_intensity = Quantity(
        type=np.float64,
        description="Smoothed intensity at the detected peak.",
    )

    prominence = Quantity(
        type=np.float64,
        description="Absolute peak prominence.",
    )

    relative_prominence = Quantity(
        type=np.float64,
        description="Peak prominence divided by the intensity range.",
    )

    width_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Peak width at half prominence.",
    )

    width_samples = Quantity(
        type=np.float64,
        description="Peak width expressed in sampling points.",
    )

    left_width_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Left position of the peak width.",
    )

    right_width_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Right position of the peak width.",
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
                    "source_filename",
                    "position_label",
                    "phi_deg",
                    "x_mm",
                    "y_mm",
                    "two_theta_deg",
                    "intensity",
                    "uncertainty",
                    "peaks",
                ]
            )
        )
    )

    source_filename = Quantity(
        type=str,
        description="Original ASC or XRDML filename.",
    )

    position_label = Quantity(
        type=str,
        description="Position label extracted from the filename.",
    )

    phi_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Sample rotation angle phi.",
    )

    x_mm = Quantity(
        type=np.float64,
        unit="mm",
        description="X measurement coordinate.",
    )

    y_mm = Quantity(
        type=np.float64,
        unit="mm",
        description="Y measurement coordinate.",
    )

    two_theta_deg = Quantity(
        type=np.float64,
        shape=["*"],
        unit="degree",
        description="Experimental 2-theta values.",
    )

    intensity = Quantity(
        type=np.float64,
        shape=["*"],
        description="Original measured XRD intensity.",
    )

    uncertainty = Quantity(
        type=np.float64,
        shape=["*"],
        description="Intensity uncertainty, when provided by the input file.",
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
        label="Spatially Resolved XRD Experiment",
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "source_filename",
                    "condition_label",
                    "input_format",
                    "number_of_patterns",
                    "number_of_detected_peaks",
                    "peak_detection_enabled",
                    "smoothing_enabled",
                    "smoothing_window",
                    "smoothing_polyorder",
                    "prominence_fraction",
                    "minimum_prominence",
                    "minimum_distance_deg",
                    "minimum_width_deg",
                    "patterns",
                    "film_diameter_mm",
                    "notch_width_mm",
                    "notch_depth_mm",
                    "measurement_width_mm",
                    "measurement_height_mm",
                ]
            )
        ),
    )

    source_filename = Quantity(
        type=str,
        description="Uploaded XRD file or ZIP archive.",
    )

    condition_label = Quantity(
        type=str,
        description="Experimental condition derived from the uploaded filename.",
        a_eln=ELNAnnotation(component="StringEditQuantity"),
    )

    input_format = Quantity(
        type=str,
        description="Original XRD input format.",
    )

    number_of_patterns = Quantity(
        type=int,
        description="Number of spatial XRD patterns.",
    )

    number_of_detected_peaks = Quantity(
        type=int,
        description="Total number of detected experimental peaks.",
    )

    peak_detection_enabled = Quantity(
        type=bool,
        description="Whether experimental peak detection was performed.",
    )

    smoothing_enabled = Quantity(
        type=bool,
        description="Whether Savitzky-Golay smoothing was enabled.",
    )

    smoothing_window = Quantity(
        type=int,
        description="Savitzky-Golay smoothing window length.",
    )

    smoothing_polyorder = Quantity(
        type=int,
        description="Savitzky-Golay polynomial order.",
    )

    prominence_fraction = Quantity(
        type=np.float64,
        description="Fraction of the intensity range used for peak prominence.",
    )

    minimum_prominence = Quantity(
        type=np.float64,
        description="Minimum absolute peak prominence.",
    )

    minimum_distance_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Minimum separation between detected peaks.",
    )

    minimum_width_deg = Quantity(
        type=np.float64,
        unit="degree",
        description="Minimum accepted peak width.",
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
        unit="mm",
        description="Physical film diameter. Leave empty for an automatically sized schematic.",
        a_eln=ELNAnnotation(component="NumberEditQuantity"),
    )

    notch_width_mm = Quantity(
        type=np.float64,
        unit="mm",
        description="Width of the north notch. Leave empty for a schematic default.",
        a_eln=ELNAnnotation(component="NumberEditQuantity"),
    )

    notch_depth_mm = Quantity(
        type=np.float64,
        unit="mm",
        description="Depth of the north notch. Leave empty for a schematic default.",
        a_eln=ELNAnnotation(component="NumberEditQuantity"),
    )

    measurement_width_mm = Quantity(
        type=np.float64,
        unit="mm",
        description="Width of each XRD measurement footprint. Leave empty for a schematic default.",
        a_eln=ELNAnnotation(component="NumberEditQuantity"),
    )

    measurement_height_mm = Quantity(
        type=np.float64,
        unit="mm",
        description="Height of each XRD measurement footprint. Leave empty for a schematic default.",
        a_eln=ELNAnnotation(component="NumberEditQuantity"),
    )

    # ========================================================
    # Plotting
    # ========================================================

    def plot(self):  # noqa: PLR0912, PLR0915
        """Create one Plotly canvas with raw, normalized, log grids and a film map."""

        def as_float_array(value):
            if hasattr(value, "magnitude"):
                value = value.magnitude
            return np.asarray(value, dtype=float)

        def optional_float(value):
            if value is None:
                return None
            if hasattr(value, "magnitude"):
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
            key=lambda p: (
                optional_float(p.phi_deg) or 0.0,
                optional_float(p.y_mm) or 0.0,
                optional_float(p.x_mm) or 0.0,
            )
        )

        n_patterns = len(patterns)
        ncols = min(5, n_patterns)
        nrows = int(np.ceil(n_patterns / ncols))
        total_rows = 3 * nrows + 1

        specs = [[{} for _ in range(ncols)] for _ in range(3 * nrows)]
        specs.append([{"colspan": ncols}] + [None] * (ncols - 1))

        titles = []
        for mode in ("RAW INTENSITY", "NORMALIZED INTENSITY", "LOG INTENSITY"):
            for row_index in range(nrows):
                for col_index in range(ncols):
                    pattern_index = row_index * ncols + col_index
                    titles.append(
                        f"{mode}<br>{patterns[pattern_index].position_label}"
                        if pattern_index < n_patterns
                        else ""
                    )
        titles.append("CIRCULAR FILM AND MEASUREMENT POSITIONS")

        fig = make_subplots(
            rows=total_rows,
            cols=ncols,
            specs=specs,
            subplot_titles=titles,
            row_heights=[0.14] * (3 * nrows) + [0.20],
            vertical_spacing=0.035,
            horizontal_spacing=0.035,
        )

        palette = qualitative.Plotly
        colors = {id(p): palette[i % len(palette)] for i, p in enumerate(patterns)}

        all_x = [as_float_array(p.two_theta_deg) for p in patterns]
        all_x = np.concatenate(all_x)
        all_x = all_x[np.isfinite(all_x)]
        x_min = float(np.min(all_x)) if all_x.size else 0.0
        x_max = float(np.max(all_x)) if all_x.size else 1.0
        if x_min == x_max:
            x_max = x_min + 1.0

        # Three matching grids: same pattern order and colour in every grid.
        for mode_index in range(3):
            row_offset = mode_index * nrows

            for index, pattern in enumerate(patterns):
                row = row_offset + index // ncols + 1
                col = index % ncols + 1
                x = as_float_array(pattern.two_theta_deg)
                y = as_float_array(pattern.intensity)
                color = colors[id(pattern)]

                if mode_index == 0:
                    plotted_y = y
                    y_title = "Counts"
                elif mode_index == 1:
                    scale = np.nanmax(np.abs(y)) if y.size else 0.0
                    plotted_y = y / scale if np.isfinite(scale) and scale > 0 else y
                    y_title = "I / max(|I|)"
                else:
                    plotted_y = np.where(y > 0, y, np.nan)
                    y_title = "Counts (log)"

                fig.add_trace(
                    go.Scatter(
                        x=x,
                        y=plotted_y,
                        mode="lines",
                        name=pattern.position_label,
                        line=dict(color=color, width=1.25),
                        showlegend=False,
                        connectgaps=False,
                        hovertemplate=(
                            f"{pattern.position_label}<br>"
                            "2θ: %{x:.3f}°<br>I: %{y:.4g}<extra></extra>"
                        ),
                    ),
                    row=row,
                    col=col,
                )

                # Detected peak markers are overlaid on the raw-intensity grid.
                if mode_index == 0 and pattern.peaks:
                    px = [optional_float(p.two_theta_deg) for p in pattern.peaks]
                    py = [optional_float(p.intensity) for p in pattern.peaks]
                    valid = [(a, b) for a, b in zip(px, py) if a is not None and b is not None]
                    if valid:
                        fig.add_trace(
                            go.Scatter(
                                x=[v[0] for v in valid],
                                y=[v[1] for v in valid],
                                mode="markers",
                                marker=dict(color=color, size=5, symbol="x"),
                                showlegend=False,
                                hovertemplate="Detected peak<br>2θ: %{x:.3f}°<extra></extra>",
                            ),
                            row=row,
                            col=col,
                        )

                fig.update_xaxes(
                    range=[x_min, x_max],
                    showgrid=True,
                    gridcolor="rgba(180,180,180,0.25)",
                    row=row,
                    col=col,
                )
                fig.update_yaxes(
                    title_text=y_title,
                    showgrid=True,
                    gridcolor="rgba(180,180,180,0.25)",
                    row=row,
                    col=col,
                )
                if mode_index == LOG_INTENSITY_MODE_INDEX:
                    fig.update_yaxes(type="log", row=row, col=col)
                if index // ncols == nrows - 1:
                    fig.update_xaxes(title_text="2θ (°)", row=row, col=col)

        # Spatial schematic. Filename coordinates are the rectangle centres.
        points = []
        for p in patterns:
            x = optional_float(p.x_mm)
            y = optional_float(p.y_mm)
            phi = optional_float(p.phi_deg) or 0.0
            if x is not None and y is not None:
                points.append((p, x, y, phi))

        max_coord = max(
            [max(abs(x), abs(y)) for _, x, y, _ in points] or [10.0]
        )
        diameter = optional_float(self.film_diameter_mm)
        notch_width = optional_float(self.notch_width_mm)
        notch_depth = optional_float(self.notch_depth_mm)
        rect_width = optional_float(self.measurement_width_mm)
        rect_height = optional_float(self.measurement_height_mm)

        dimensions_supplied = all(
            v is not None and v > 0
            for v in (diameter, notch_width, notch_depth, rect_width, rect_height)
        )

        radius = diameter / 2 if diameter and diameter > 0 else max(max_coord + 3.0, 5.0)
        notch_width = notch_width if notch_width and notch_width > 0 else max(0.12 * radius, 0.8)
        notch_depth = notch_depth if notch_depth and notch_depth > 0 else max(0.07 * radius, 0.5)
        rect_width = rect_width if rect_width and rect_width > 0 else max(0.075 * radius, 0.8)
        rect_height = rect_height if rect_height and rect_height > 0 else max(0.035 * radius, 0.45)

        half_notch = min(notch_width / 2, radius * 0.45)
        notch_y = np.sqrt(max(radius**2 - half_notch**2, 0.0))
        theta0 = np.pi / 2 + np.arcsin(half_notch / radius)
        theta1 = 2 * np.pi + np.pi / 2 - np.arcsin(half_notch / radius)
        theta = np.linspace(theta0, theta1, 240)
        film_x = list(radius * np.cos(theta)) + [
            half_notch, half_notch, -half_notch, -half_notch
        ]
        film_y = list(radius * np.sin(theta)) + [
            notch_y, radius - notch_depth, radius - notch_depth, notch_y
        ]

        map_row = total_rows
        fig.add_trace(
            go.Scatter(
                x=film_x,
                y=film_y,
                mode="lines",
                fill="toself",
                fillcolor="rgba(180,190,205,0.22)",
                line=dict(color="#263238", width=2.5),
                name="Film boundary",
                showlegend=False,
                hoverinfo="skip",
            ),
            row=map_row,
            col=1,
        )

        for p, cx, cy, phi in points:
            color = colors[id(p)]
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
            rx = list(corners[:, 0] + cx)
            ry = list(corners[:, 1] + cy)
            rx.append(rx[0])
            ry.append(ry[0])

            # Plotly qualitative palettes are normally hexadecimal colours.
            red, green, blue = hex_to_rgb(color)
            fill = f"rgba({red},{green},{blue},0.30)"

            fig.add_trace(
                go.Scatter(
                    x=rx,
                    y=ry,
                    mode="lines",
                    fill="toself",
                    fillcolor=fill,
                    line=dict(color=color, width=2),
                    name=p.position_label,
                    showlegend=False,
                    hovertemplate=(
                        f"{p.position_label}<br>X={cx:g} mm<br>"
                        f"Y={cy:g} mm<br>φ={phi:g}°<extra></extra>"
                    ),
                ),
                row=map_row,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    x=[cx],
                    y=[cy],
                    mode="markers",
                    marker=dict(color=color, size=6, line=dict(color="white", width=1)),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                row=map_row,
                col=1,
            )

        map_limit = max(radius * 1.18, max_coord + rect_width + 1.0)
        fig.update_xaxes(
            title_text="X (mm)",
            range=[-map_limit, map_limit],
            showgrid=True,
            zeroline=True,
            row=map_row,
            col=1,
        )
        fig.update_yaxes(
            title_text="Y (mm)",
            range=[-map_limit, map_limit],
            showgrid=True,
            zeroline=True,
            scaleanchor=f"x{(map_row - 1) * ncols + 1}",
            scaleratio=1,
            row=map_row,
            col=1,
        )

        map_axis = (map_row - 1) * ncols + 1
        fig.add_annotation(
            x=0.97,
            y=0.95,
            xref=f"x{map_axis} domain",
            yref=f"y{map_axis} domain",
            text="N ↑",
            showarrow=False,
            font=dict(size=15, color="#263238"),
        )
        note = (
            "Dimensions supplied"
            if dimensions_supplied
            else "SCHEMATIC — NOT TO SCALE. Set film diameter, notch and footprint dimensions in the ELN fields."
        )
        fig.add_annotation(
            x=0.5,
            y=0.02,
            xref=f"x{map_axis} domain",
            yref=f"y{map_axis} domain",
            text=note,
            showarrow=False,
            font=dict(size=11, color="#555"),
        )

        fig.update_layout(
            title=(
                "Spatially Resolved XRD: Raw, Normalized and Log Intensity "
                "with Sample Measurement Map"
            ),
            template="plotly_white",
            width=1800,
            height=max(2100, 260 * total_rows),
            margin=dict(l=65, r=35, t=110, b=55),
            hovermode="closest",
            showlegend=False,
            font=dict(size=10),
        )

        # Exactly one PlotlyFigure is attached to this NOMAD archive entry.
        self.figures = [
            PlotlyFigure(
                label="Complete XRD Archive Plot",
                figure=fig.to_plotly_json(),
            )
        ]


m_package.__init_metainfo__()
