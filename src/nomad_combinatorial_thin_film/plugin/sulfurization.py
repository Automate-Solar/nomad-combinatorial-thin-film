"""NOMAD schema for sulfurization temperature measurements."""

import numpy as np
import plotly.graph_objects as go
from nomad.datamodel.data import ArchiveSection, EntryData
from nomad.datamodel.metainfo.annotations import (
    ELNAnnotation,
    SectionProperties,
)
from nomad.datamodel.metainfo.plot import PlotlyFigure, PlotSection
from nomad.metainfo import Package, Quantity, Section, SubSection

m_package = Package(
    name="Uppsala Sulfurization Experiment",
    description=(
        "PicoLog sulfurization temperature measurements, "
        "holding-period detection and temperature stability analysis."
    ),
)


class SulfurizationChannel(ArchiveSection):
    """One measurement channel extracted from a PicoLog PLW file."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "channel_id",
                    "name",
                    "unit",
                    "values",
                    "mean",
                    "std",
                    "minimum",
                    "maximum",
                    "range",
                ]
            )
        )
    )

    channel_id = Quantity(
        type=int,
        description="Original PicoLog channel/parameter ID.",
    )

    name = Quantity(
        type=str,
        description="Channel name from the embedded PLW configuration.",
        a_eln=ELNAnnotation(component="StringEditQuantity"),
    )

    unit = Quantity(
        type=str,
        description="Measurement unit from the PLW configuration.",
    )

    values = Quantity(
        type=np.float64,
        shape=["*"],
        description="Complete measurement time series.",
    )

    mean = Quantity(
        type=np.float64,
        description="Mean value during the detected holding period.",
    )

    std = Quantity(
        type=np.float64,
        description="Sample standard deviation during the holding period.",
    )

    minimum = Quantity(
        type=np.float64,
        description="Minimum value during the detected holding period.",
    )

    maximum = Quantity(
        type=np.float64,
        description="Maximum value during the detected holding period.",
    )

    range = Quantity(
        type=np.float64,
        description="Maximum minus minimum during the holding period.",
    )


class SulfurizationHoldingPeriod(ArchiveSection):
    """Detected stable-temperature interval and its detection criteria."""

    m_def = Section(
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "hold_channel",
                    "target_temperature_c",
                    "temperature_tolerance_c",
                    "minimum_duration_s",
                    "detected",
                    "start_index",
                    "end_index",
                    "start_time_s",
                    "end_time_s",
                    "duration_s",
                ]
            )
        )
    )

    hold_channel = Quantity(
        type=str,
        description="Channel used to identify the holding period.",
    )

    target_temperature_c = Quantity(
        type=np.float64,
        unit="°C",
        description="Target temperature used for holding-period detection.",
    )

    temperature_tolerance_c = Quantity(
        type=np.float64,
        unit="°C",
        description="Allowed deviation from the target temperature.",
    )

    minimum_duration_s = Quantity(
        type=np.float64,
        unit="s",
        description="Minimum continuous stable duration.",
    )

    detected = Quantity(
        type=bool,
        description="Whether a qualifying stable interval was detected.",
    )

    start_index = Quantity(
        type=int,
        description="First sample index of the selected stable interval.",
    )

    end_index = Quantity(
        type=int,
        description="Last sample index of the selected stable interval.",
    )

    start_time_s = Quantity(
        type=np.float64,
        unit="s",
        description="Start time of the selected interval.",
    )

    end_time_s = Quantity(
        type=np.float64,
        unit="s",
        description="End time of the selected interval.",
    )

    duration_s = Quantity(
        type=np.float64,
        unit="s",
        description="Duration of the selected stable interval.",
    )


class SulfurizationRun(EntryData, PlotSection):
    """Sulfurization measurement and temperature stability analysis."""

    m_def = Section(
        label="Sulfurization Temperature Measurement",
        a_eln=ELNAnnotation(
            properties=SectionProperties(
                order=[
                    "source_filename",
                    "plw_version",
                    "sample_number",
                    "number_of_channels",
                    "number_of_samples",
                    "sampling_interval",
                    "time_unit_code",
                    "recorded_duration_s",
                    "channel_ids",
                    "time_s",
                    "holding_period",
                    "channels",
                ]
            )
        ),
    )

    source_filename = Quantity(
        type=str,
        description="Original PicoLog PLW filename.",
    )

    plw_version = Quantity(
        type=int,
        description="PicoLog file version.",
    )

    sample_number = Quantity(
        type=int,
        description="Sample number recorded in the PLW header.",
    )

    number_of_channels = Quantity(
        type=int,
        description="Number of measurement channels.",
    )

    number_of_samples = Quantity(
        type=int,
        description="Number of recorded samples.",
    )

    sampling_interval = Quantity(
        type=int,
        description="Sampling interval in the original PLW time units.",
    )

    time_unit_code = Quantity(
        type=int,
        description="Original PicoLog time-unit code.",
    )

    recorded_duration_s = Quantity(
        type=np.float64,
        unit="s",
        description="Total recorded duration.",
    )

    channel_ids = Quantity(
        type=int,
        shape=["*"],
        description="Original PicoLog channel identifiers.",
    )

    time_s = Quantity(
        type=np.float64,
        shape=["*"],
        unit="s",
        description="Elapsed measurement time in seconds.",
    )

    holding_period = SubSection(section_def=SulfurizationHoldingPeriod)

    channels = SubSection(
        section_def=SulfurizationChannel,
        repeats=True,
    )

    def plot(self):
        import numpy as np

        fig = go.Figure()

        # --------------------------------------------------
        # Convert time to plain numerical values
        # --------------------------------------------------
        time_s = np.asarray(self.time_s, dtype=float)

        # --------------------------------------------------
        # Plot all temperature channels
        # --------------------------------------------------
        for channel in self.channels:

            values = np.asarray(channel.values, dtype=float)

            fig.add_trace(
                go.Scatter(
                    x=time_s,
                    y=values,
                    mode="lines",
                    name=channel.name,
                    line=dict(width=1.5),
                )
            )

        # --------------------------------------------------
        # Holding-period configuration
        # Convert Pint quantities to plain floats
        # --------------------------------------------------
        hold = self.holding_period

        target_temperature = float(
            hold.target_temperature_c.magnitude
            if hasattr(hold.target_temperature_c, "magnitude")
            else hold.target_temperature_c
        )

        tolerance = float(
            hold.temperature_tolerance_c.magnitude
            if hasattr(hold.temperature_tolerance_c, "magnitude")
            else hold.temperature_tolerance_c
        )

        # --------------------------------------------------
        # Target temperature and tolerance boundaries
        # --------------------------------------------------
        fig.add_hline(
            y=target_temperature,
            line_dash="dash",
            line_color="black",
            line_width=1.5,
            annotation_text=f"Target: {target_temperature:.1f} °C",
            annotation_position="top left",
        )

        fig.add_hline(
            y=target_temperature + tolerance,
            line_dash="dot",
            line_color="gray",
            line_width=1,
            annotation_text=f"+{tolerance:.1f} °C",
            annotation_position="top right",
        )

        fig.add_hline(
            y=target_temperature - tolerance,
            line_dash="dot",
            line_color="gray",
            line_width=1,
            annotation_text=f"-{tolerance:.1f} °C",
            annotation_position="bottom right",
        )

        # --------------------------------------------------
        # Highlight detected holding period
        # --------------------------------------------------
        if hold.detected:

            start_time = float(
                hold.start_time_s.magnitude
                if hasattr(hold.start_time_s, "magnitude")
                else hold.start_time_s
            )

            end_time = float(
                hold.end_time_s.magnitude
                if hasattr(hold.end_time_s, "magnitude")
                else hold.end_time_s
            )

            fig.add_vrect(
                x0=start_time,
                x1=end_time,
                fillcolor="green",
                opacity=0.10,
                layer="below",
                line_width=0,
                annotation_text="Detected holding period",
                annotation_position="top left",
            )

        # --------------------------------------------------
        # Holding-period statistics annotation
        # --------------------------------------------------
        if hold.detected:

            duration = float(
                hold.duration_s.magnitude
                if hasattr(hold.duration_s, "magnitude")
                else hold.duration_s
            )

            duration_min = duration / 60.0

            # Find furnace channel for its statistics
            furnace_channel = next(
                (
                    channel
                    for channel in self.channels
                    if channel.name.lower() == hold.hold_channel.lower()
                ),
                None,
            )

            if furnace_channel is not None:

                mean_temperature = float(
                    furnace_channel.mean.magnitude
                    if hasattr(furnace_channel.mean, "magnitude")
                    else furnace_channel.mean
                )

                std_temperature = float(
                    furnace_channel.std.magnitude
                    if hasattr(furnace_channel.std, "magnitude")
                    else furnace_channel.std
                )

                annotation = (
                    f"Holding duration: {duration_min:.2f} min"
                    f"<br>Mean furnace temperature: "
                    f"{mean_temperature:.2f} °C"
                    f"<br>Temperature SD: {std_temperature:.2f} °C"
                )

                fig.add_annotation(
                    x=0.99,
                    y=0.02,
                    xref="paper",
                    yref="paper",
                    text=annotation,
                    showarrow=False,
                    align="right",
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="gray",
                    borderwidth=1,
                )

        # --------------------------------------------------
        # Layout
        # --------------------------------------------------
        fig.update_layout(
            title="Sulfurization Temperature Profile",
            xaxis_title="Time (s)",
            yaxis_title="Temperature (°C)",
            template="plotly_white",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0,
            ),
            height=650,
            margin=dict(l=70, r=40, t=100, b=70),
        )

        fig.update_xaxes(showgrid=True)
        fig.update_yaxes(showgrid=True)

        self.figures = [
            PlotlyFigure(
                label="Sulfurization Temperature Profile",
                figure=fig.to_plotly_json(),
            )
        ]


m_package.__init_metainfo__()
