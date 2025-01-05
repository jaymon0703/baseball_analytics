import seaborn as sns
from faicons import icon_svg

# Import data from shared.py
from shared import app_dir, df, ls_pitchers_2024, create_count_matrix

from shiny import reactive
from shiny.express import input, render, ui

from pybaseball import  playerid_lookup
from pybaseball import  statcast_pitcher

ui.page_opts(title="Baseball Analytics Dashboard - 2024", fillable=True)


with ui.sidebar(title="Filter controls"):
    # ui.input_slider("release_speed", "Release Speed", 0, 110, 110)

    ui.input_selectize(
        "selected_pitcher",
        "Select a Pitcher:",
        ls_pitchers_2024,
        multiple=False,
        selected=None
    )


with ui.layout_column_wrap(fill=False):
    with ui.value_box(showcase=icon_svg("earlybirds")):
        "Number of Pitches"

        @render.text
        def count():
            return filtered_df().shape[0]

    with ui.value_box(showcase=icon_svg("ruler-horizontal")):
        "Average Pitch Velocity"

        @render.text
        def bill_length():
            return f"{filtered_df()['release_speed'].mean():.1f} mph"

    with ui.value_box(showcase=icon_svg("ruler-vertical")):
        "Average Days Between Games"

        @render.text
        def bill_depth():
            return f"{filtered_df()['pitcher_days_since_prev_game'].mean():.1f} days"


with ui.layout_columns():
    with ui.card(full_screen=True):
        ui.card_header("Strike Zone Heat Map")

        @render.plot
        def length_depth():
            return sns.heatmap(
                data=create_count_matrix(strike_zone_df()),
                cbar=True, 
                cmap="coolwarm",
            )

    with ui.card(full_screen=True):
        ui.card_header("Penguin data")

        # @render.data_frame
        # def summary_statistics():
        #     cols = [
        #         "species",
        #         "island",
        #         "bill_length_mm",
        #         "bill_depth_mm",
        #         "body_mass_g",
        #     ]
        #     return render.DataGrid(filtered_df()[cols], filters=True)


ui.include_css(app_dir / "styles.css")


@reactive.calc
def filtered_df():
    first_name = input.selected_pitcher().split()[1].lower()
    last_name = input.selected_pitcher().split()[0].lower().replace(',', '')
    player_id = playerid_lookup(last_name, first_name)["key_mlbam"][0]
    data = statcast_pitcher('2024-01-01', '2024-12-31', player_id = player_id)
    return data

@reactive.calc
def strike_zone_df():
    temp_df = filtered_df()
    k_zone_df = temp_df.loc[temp_df["zone"] <= 9]
    return k_zone_df


