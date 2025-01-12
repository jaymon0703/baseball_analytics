import seaborn as sns
from faicons import icon_svg
import plotly.express as px
from shinywidgets import render_plotly

# Import data from shared.py
from shared import app_dir, ls_pitchers_2024, create_count_matrix

from shiny import reactive
from shiny.express import input, render, ui

from pybaseball import  playerid_lookup, statcast_pitcher, cache
cache.enable()

ui.page_opts(title="Baseball Analytics Dashboard - 2024", fillable=True)


with ui.sidebar(title="Filter controls", width=300):
    # ui.input_slider("release_speed", "Release Speed", 0, 110, 110)

    ui.input_selectize(
        "selected_pitcher",
        "Select a Pitcher:",
        ls_pitchers_2024,
        multiple=False,
        selected="Darvish, Yu"
    )

    ui.input_date_range("date_range", "Date Range", start="2024-01-01", end="2024-12-31")

    ui.input_selectize(
        "selected_pitch",
        "Select a Pitch Type:",
        choices=[],
        multiple=False,
        selected=None
    )

    @reactive.effect
    def _():
        choices = ["All"] + filtered_df()["pitch_name"].unique().tolist()
        ui.update_selectize(
            "selected_pitch",
            choices=choices,
            selected=None,
            server=True,
        )


with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Number of Pitches"

        @render.text
        def count():
            return filtered_by_pitch_name_df().shape[0]

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Average Pitch Velocity"

        @render.text
        def bill_length():
            return f"{filtered_by_pitch_name_df()['release_speed'].mean():.1f} mph"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Average Days Between Games"

        @render.text
        def bill_depth():
            return f"{filtered_df()['pitcher_days_since_prev_game'].mean():.1f} days"

with ui.navset_pill(id="tab"):
    with ui.nav_panel("Scatter Plots"):    
        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("Pitch Movement Scatter Plot")

                @render_plotly
                def movement_scatter():
                    fig = px.scatter(filtered_by_pitch_name_df(), 
                                    x = filtered_by_pitch_name_df()["pfx_x"] * 12, 
                                    y = filtered_by_pitch_name_df()["pfx_z"] * 12,
                                    color="pitch_name")
                    # fig = px.scatter(x = [1,2,23,4,5], y = [1,2,3,4,5])
                    return fig
                
            with ui.card(full_screen=True):
                ui.card_header("Ball Position  Over Plate Scatter Plot")

                @render_plotly
                def home_plate_scatter():
                    fig = px.scatter(filtered_by_pitch_name_df(), 
                                    x = filtered_by_pitch_name_df()["plate_x"] * 12, 
                                    y = filtered_by_pitch_name_df()["plate_z"] * 12,
                                    color="pitch_name")
                    # fig = px.scatter(x = [1,2,23,4,5], y = [1,2,3,4,5])
                    return fig

    with ui.nav_panel("Heatmaps"):
        with ui.layout_columns():
            with ui.card(full_screen=True):
                ui.card_header("Strike Zone Heat Map")

                @render_plotly
                def heatmap():
                    fig = px.imshow(create_count_matrix(strike_zone_df()),
                                    color_continuous_scale='RdBu_r')
                    fig.update_xaxes(showticklabels=False)
                    fig.update_yaxes(showticklabels=False)
                    return fig


ui.include_css(app_dir / "styles.css")


@reactive.calc
def filtered_df():
    first_name = input.selected_pitcher().rsplit(",")[1].lower().strip()
    last_name = input.selected_pitcher().rsplit(",")[0].lower().replace(',', '')
    player_id = playerid_lookup(last_name, first_name)["key_mlbam"][0]
    data = statcast_pitcher(str(input.date_range()[0]), str(input.date_range()[1]), player_id = player_id)
    data = data.dropna(subset=["pitch_name", "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "zone"])

    return data

@reactive.calc
def filtered_by_pitch_name_df():    
    if input.selected_pitch() == "All":
        pitch_name_df = filtered_df()
    else:    
        pitch_name_df = filtered_df().loc[filtered_df()["pitch_name"] == input.selected_pitch()]

    return pitch_name_df

@reactive.calc
def strike_zone_df():
    temp_df = filtered_by_pitch_name_df()
    k_zone_df = temp_df.loc[temp_df["zone"] <= 9]
    return k_zone_df


