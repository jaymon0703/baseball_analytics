import seaborn as sns
from faicons import icon_svg
import plotly.express as px
from shiny import App, Inputs, Outputs, Session, reactive, render, ui
from shinywidgets import output_widget, render_plotly

# Import data from shared.py
from shared import app_dir, ls_pitchers_2024, ls_batters_2024, create_count_matrix

from pybaseball import  playerid_lookup, playerid_reverse_lookup, statcast_pitcher, statcast_batter, cache
cache.enable()

app_ui = ui.page_navbar(
    ui.nav_panel(
        "Pitcher Report",
        ui.page_sidebar(
            ui.sidebar(
            ui.input_selectize("selected_pitcher", "Select a Pitcher:", ls_pitchers_2024, multiple=False, selected="Darvish, Yu"),
            ui.input_date_range("date_range", "Date Range", start="2024-01-01", end="2024-12-31"),
            width = 275
        #     ui.input_selectize(
        #     "selected_pitch",
        #     "Select a Pitch Type:",
        #     choices=[],
        #     multiple=False,
        #     selected=None
        # ),
        ),
        ui.layout_column_wrap(
            ui.value_box(
                "Number of Pitches",
                ui.output_ui("count"),
                showcase=icon_svg("baseball"),
            ),
            ui.value_box(
                "Average Pitch Velocity",
                ui.output_ui("pitch_velo"),
                showcase=icon_svg("divide"),
            ),
            ui.value_box(
                "Average Days Between Games",
                ui.output_ui("days_between_games"),
                showcase=icon_svg("ruler"),
            ),
            fill=False,
        ),
        ui.row(
            ui.layout_columns(
                ui.card(
                    ui.card_header("Pitch Movement Scatter Plot"),
                    output_widget("movement_scatter"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Ball Position  Over Plate Scatter Plot"),
                    output_widget("home_plate_scatter"),
                    full_screen=True,
                ),
            ),
        ),
        ui.row(
            ui.layout_columns(
                ui.card(
                    ui.card_header("Pitch Data Table"),
                    ui.output_data_frame("table"),
                    full_screen=True,
                ),
            )
        ),
        ui.include_css(app_dir / "styles.css"),
        # title="Baseball Analytics Dashboard - 2024",
        fillable=True,
        )
    ),
    ui.nav_panel(
        "Hitter Report",
        ui.page_sidebar(
            ui.sidebar(
            ui.input_selectize("selected_hitter", "Select a Hitter:", ls_batters_2024, multiple=False, selected="Ohtani, Shohei"),
            ui.input_date_range("date_range_hitter", "Date Range", start="2024-01-01", end="2024-12-31"),
            width = 275
        #     ui.input_selectize(
        #     "selected_pitch",
        #     "Select a Pitch Type:",
        #     choices=[],
        #     multiple=False,
        #     selected=None
        # ),
        ),
        ui.layout_column_wrap(
            ui.value_box(
                "Number of Hits (including outs)",
                ui.output_ui("count_hitter"),
                showcase=icon_svg("baseball-bat-ball"),
            ),
            ui.value_box(
                "Average Hit Velocity",
                ui.output_ui("hit_velo"),
                showcase=icon_svg("divide"),
            ),
            ui.value_box(
                "Average Hit Distance",
                ui.output_ui("average_hit_distance"),
                showcase=icon_svg("ruler"),
            ),
            fill=False,
        ),
        ui.row(
            ui.layout_columns(
                ui.card(
                    ui.card_header("Home Runs - Launch Speed, Angle and Pitch Type"),
                    output_widget("home_run_scatter"),
                    full_screen=True,
                ),
                ui.card(
                    ui.card_header("Ball Position  Over Plate Scatter Plot"),
                    output_widget("home_plate_scatter_hitter"),
                    full_screen=True,
                ),
            ),
        ),
        ui.row(
            ui.layout_columns(
                ui.card(
                    ui.card_header("Hit Data Table"),
                    ui.output_data_frame("table_hitter"),
                    full_screen=True,
                ),
            )
        ),
        )
    )
)

def server(input: Inputs, output: Outputs, session: Session):
    
    # Reactive dataframes for pitcher and hitter
    @reactive.calc
    def filtered_df():
        first_name = input.selected_pitcher().rsplit(",")[1].lower().strip()
        last_name = input.selected_pitcher().rsplit(",")[0].lower().replace(',', '')
        player_id = playerid_lookup(last_name, first_name)["key_mlbam"][0]
        data = statcast_pitcher(str(input.date_range()[0]), str(input.date_range()[1]), player_id = player_id)
        data = data.dropna(subset=["pitch_name", "release_speed", "pfx_x", "pfx_z", "plate_x", "plate_z", "zone"])

        return data
    
    @reactive.calc
    def hitter_filtered_df():
        first_name = input.selected_hitter().rsplit(",")[1].lower().strip()
        last_name = input.selected_hitter().rsplit(",")[0].lower().replace(',', '')
        player_id = playerid_lookup(last_name, first_name)["key_mlbam"][0]
        data = statcast_batter(str(input.date_range()[0]), str(input.date_range()[1]), player_id = player_id)
        data = data.dropna(subset=["pitch_name", "launch_speed", "hit_distance_sc", "plate_x", "plate_z", "zone"])

        return data
    
    # Pitcher server functions
    @render.ui
    def count():
        return filtered_df().shape[0]

    @render.ui
    def pitch_velo():
        return f"{filtered_df()['release_speed'].mean():.1f} mph"

    @render.ui
    def days_between_games():
        return f"{filtered_df()['pitcher_days_since_prev_game'].mean():.1f} days"

    @render_plotly
    def movement_scatter():
        fig = px.scatter(filtered_df(), 
                        x = filtered_df()["pfx_x"] * 12, 
                        y = filtered_df()["pfx_z"] * 12,
                        color="pitch_name")
        return fig
    
    @render_plotly
    def home_plate_scatter():
        fig = px.scatter(filtered_df(), 
                        x = filtered_df()["plate_x"] * 12, 
                        y = filtered_df()["plate_z"] * 12,
                        color="pitch_name")
        return fig

    @render.data_frame
    def table():
        return render.DataTable(
            filtered_df(),
            filters=True,
            width="100%",
        )
    
    # Hitter server functions
    @render.ui
    def count_hitter():
        return hitter_filtered_df().shape[0]
    
    @render.ui
    def hit_velo():
        return f"{hitter_filtered_df()['release_speed'].mean():.1f} mph"
    
    @render.ui
    def average_hit_distance():
        return f"{hitter_filtered_df()['hit_distance_sc'].mean():.1f} feet"
    
    @render_plotly
    def home_run_scatter():

        fig = px.scatter(hitter_filtered_df()[hitter_filtered_df()["events"] == "home_run"], 
                        x = "launch_speed", 
                        y = "launch_angle",
                        color="pitch_name",
                        facet_col="p_throws",
        )
        fig.update_traces(marker_size=10)
        # fig.add_trace
        return fig
    
    @render.data_frame
    def table_hitter():
        return render.DataTable(
            hitter_filtered_df(),
            filters=True,
            width="100%",
        )


app = App(app_ui, server)
