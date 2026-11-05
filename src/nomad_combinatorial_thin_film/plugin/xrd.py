
"""NOMAD schema for spatially resolved XRD measurements."""

import numpy as np
import plotly.graph_objects as go

from plotly.subplots import make_subplots

from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    SectionProperties,
)
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection


m_package = Package(
    name="Uppsala XRD Analysis",
    description=(
        "Spatially resolved XRD measurements, "
        "experimental peak detection and visualization."
    ),
)


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

    # ========================================================
    # Plotting
    # ========================================================

    def plot(self):
        """Generate NOMAD-compatible Plotly visualizations."""

        def as_float_array(value):
            if hasattr(value, "magnitude"):
                value = value.magnitude

            return np.asarray(value, dtype=float)

        def as_float(value):
            if hasattr(value, "magnitude"):
                value = value.magnitude

            return float(value)

        patterns = list(self.patterns)

        if not patterns:
            return

        figures = []

        # ----------------------------------------------------
        # 1. Spatial pattern grid
        # ----------------------------------------------------

        ncols = min(5, len(patterns))
        nrows = int(np.ceil(len(patterns) / ncols))

        titles = [
            pattern.position_label
            for pattern in patterns
        ]

        fig = make_subplots(
            rows=nrows,
            cols=ncols,
            subplot_titles=titles,
            shared_xaxes=True,
        )

        for index, pattern in enumerate(patterns):

            row = index // ncols + 1
            col = index % ncols + 1

            x = as_float_array(pattern.two_theta_deg)
            y = as_float_array(pattern.intensity)

            fig.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    name=pattern.position_label,
                    line=dict(width=1.0),
                    showlegend=False,
                ),
                row=row,
                col=col,
            )

            if pattern.peaks:

                peak_x = [
                    as_float(p.two_theta_deg)
                    for p in pattern.peaks
                ]

                peak_y = [
                    as_float(p.intensity)
                    for p in pattern.peaks
                ]

                fig.add_trace(
                    go.Scatter(
                        x=peak_x,
                        y=peak_y,
                        mode="markers",
                        marker=dict(
                            color="red",
                            size=6,
                            symbol="x",
                        ),
                        name="Detected peaks",
                        showlegend=False,
                    ),
                    row=row,
                    col=col,
                )

        fig.update_layout(
            title="Spatially Resolved XRD Patterns",
            template="plotly_white",
            height=max(450, 300 * nrows),
            width=1400,
            showlegend=False,
        )

        fig.update_xaxes(
            title_text="2θ (°)",
            showgrid=True,
        )

        fig.update_yaxes(
            title_text="Intensity (counts)",
            showgrid=True,
        )

        figures.append(
            PlotlyFigure(
                label="Spatial XRD Pattern Grid",
                figure=fig.to_plotly_json(),
            )
        )

        # ----------------------------------------------------
        # 2. Combined linear plot
        # ----------------------------------------------------

        fig_linear = go.Figure()

        line_styles = [
            "solid",
            "dash",
            "dot",
            "dashdot",
        ]

        for index, pattern in enumerate(patterns):

            x = as_float_array(pattern.two_theta_deg)
            y = as_float_array(pattern.intensity)

            fig_linear.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines",
                    name=pattern.position_label,
                    line=dict(
                        width=1.2,
                        dash=line_styles[index % len(line_styles)],
                    ),
                )
            )

        fig_linear.update_layout(
            title="Combined XRD Patterns - Linear Scale",
            xaxis_title="2θ (°)",
            yaxis_title="Intensity (counts)",
            template="plotly_white",
            hovermode="x unified",
            height=650,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
            ),
        )

        figures.append(
            PlotlyFigure(
                label="Combined XRD - Linear Scale",
                figure=fig_linear.to_plotly_json(),
            )
        )

        # ----------------------------------------------------
        # 3. Combined logarithmic plot
        # ----------------------------------------------------

        fig_log = go.Figure()

        for index, pattern in enumerate(patterns):

            x = as_float_array(pattern.two_theta_deg)
            y = as_float_array(pattern.intensity)

            # Zero and negative intensities cannot be displayed
            # on a logarithmic axis.
            y_log = np.where(y > 0, y, np.nan)

            fig_log.add_trace(
                go.Scatter(
                    x=x,
                    y=y_log,
                    mode="lines",
                    name=pattern.position_label,
                    line=dict(
                        width=1.2,
                        dash=line_styles[index % len(line_styles)],
                    ),
                )
            )

        fig_log.update_layout(
            title="Combined XRD Patterns - Logarithmic Scale",
            xaxis_title="2θ (°)",
            yaxis_title="Intensity (counts, log scale)",
            yaxis_type="linear",
            template="plotly_white",
            hovermode="x unified",
            height=650,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
            ),
        )

        fig_log.update_yaxes(type="log")

        figures.append(
            PlotlyFigure(
                label="Combined XRD - Logarithmic Scale",
                figure=fig_log.to_plotly_json(),
            )
        )

        # ----------------------------------------------------
        # 4. Detected peak count by position
        # ----------------------------------------------------

        positions = [
            pattern.position_label
            for pattern in patterns
        ]

        peak_counts = [
            len(pattern.peaks)
            for pattern in patterns
        ]

        fig_peaks = go.Figure(
            data=[
                go.Bar(
                    x=positions,
                    y=peak_counts,
                    name="Detected peaks",
                )
            ]
        )

        fig_peaks.update_layout(
            title="Number of Detected Peaks by Position",
            xaxis_title="Measurement position",
            yaxis_title="Number of detected peaks",
            template="plotly_white",
            height=500,
        )

        figures.append(
            PlotlyFigure(
                label="Peak Count by Position",
                figure=fig_peaks.to_plotly_json(),
            )
        )

        # NOMAD expects PlotlyFigure metainfo sections,
        # not raw Plotly Figure objects.
        self.figures = figures


m_package.__init_metainfo__()
