import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from scipy.interpolate import griddata


def plot_rink(ax, plot_half=False, board_radius=28, alpha=1):
    def add_arc(center, theta1, theta2):
        ax.add_artist(
            mpl.patches.Arc(
                center,
                board_radius * 2,
                board_radius * 2,
                theta1=theta1,
                theta2=theta2,
                edgecolor="black",
                lw=2,
                zorder=0,
                alpha=alpha,
            )
        )

    # Corner Boards
    corners = [
        ((100 - board_radius, (85 / 2) - board_radius), 0, 89),
        ((-100 + board_radius, (85 / 2) - board_radius), 90, 180),
        ((-100 + board_radius, -(85 / 2) + board_radius), 180, 270),
        ((100 - board_radius, -(85 / 2) + board_radius), 270, 360),
    ]
    for center, theta1, theta2 in corners:
        add_arc(center, theta1, theta2)

    # Plot Boards
    boards = [
        ([-100 + board_radius, 100 - board_radius], [-42.5, -42.5]),
        ([-100 + board_radius, 100 - board_radius], [42.5, 42.5]),
        ([-100, -100], [-42.5 + board_radius, 42.5 - board_radius]),
        ([100, 100], [-42.5 + board_radius, 42.5 - board_radius]),
    ]
    for x, y in boards:
        ax.plot(x, y, linewidth=2, color="black", zorder=0, alpha=alpha)

    # Goal Lines
    for x in [-89, 89]:
        ax.plot(
            [x, x],
            [-42.5 + 4.7, 42.5 - 4.7],
            linewidth=3,
            color="firebrick",
            zorder=0,
            alpha=alpha,
        )

    # Center Line and FaceOff Dot
    ax.plot(
        [0, 0], [-42.5, 42.5], linewidth=3, color="firebrick", zorder=0, alpha=alpha
    )
    ax.plot(0, 0, markersize=6, color="mediumblue", marker="o", zorder=0, alpha=alpha)

    # Center Circle
    ax.add_artist(
        mpl.patches.Circle(
            (0, 0),
            radius=33 / 2,
            facecolor="none",
            edgecolor="mediumblue",
            linewidth=3,
            zorder=0,
            alpha=alpha,
        )
    )

    # Zone Faceoff Dots and Circles
    for x, y in [(69, 22), (69, -22), (-69, 22), (-69, -22)]:
        ax.plot(
            x, y, markersize=6, color="firebrick", marker="o", zorder=0, alpha=alpha
        )
        ax.add_artist(
            mpl.patches.Circle(
                (x, y),
                radius=15,
                facecolor="none",
                edgecolor="firebrick",
                linewidth=3,
                zorder=0,
                alpha=alpha,
            )
        )

    # Neutral Zone Faceoff Dots
    for x, y in [(22, 22), (22, -22), (-22, 22), (-22, -22)]:
        ax.plot(
            x, y, markersize=6, color="firebrick", marker="o", zorder=0, alpha=alpha
        )

    # Blue Lines
    for x in [-25, 25]:
        ax.plot(
            [x, x],
            [-42.5, 42.5],
            linewidth=3,
            color="mediumblue",
            zorder=0,
            alpha=alpha,
        )

    # Goalie Crease and Goal
    for x in [-89, 89]:
        ax.add_artist(
            mpl.patches.Arc(
                (x, 0),
                6,
                6,
                theta1=90 if x > 0 else 270,
                theta2=270 if x > 0 else 90,
                facecolor="mediumblue",
                edgecolor="firebrick",
                lw=2,
                zorder=0,
                alpha=alpha,
            )
        )
        ax.add_artist(
            mpl.patches.Rectangle(
                (x if x > 0 else x - 2, -2),
                2,
                4,
                lw=2,
                color="firebrick",
                fill=False,
                zorder=0,
                alpha=alpha,
            )
        )

    # Set axis limits and remove spines
    ax.set_xlim((-0.5, 100.5) if plot_half else (-101, 101))
    ax.set_ylim(-43, 43)
    for spine in ax.spines.values():
        spine.set_visible(False)


def plot_expected_goals(expected_goals):
    [x, y] = np.round(np.meshgrid(np.linspace(0, 100, 100), np.linspace(-42.5, 42.5, 85)))
    expected_goals_grid = griddata(
        (expected_goals["shot_x"], expected_goals["shot_y"]),
        expected_goals["expected_goal"],
        (x, y),
        method="cubic",
        fill_value=0,
    )
    expected_goals_grid[expected_goals_grid < 0] = 0

    fig, ax = plt.subplots(1, 1, figsize=(11, 12), facecolor="w", edgecolor="k")
    expected_goal_heatmap = ax.imshow(
        expected_goals_grid, alpha=0.5, cmap="jet", extent=[0, 100, -42.5, 42.5]
    )
    plot_rink(ax, plot_half=True, board_radius=25, alpha=0.9)
    plt.axis("off")
    fig.colorbar(expected_goal_heatmap, orientation="horizontal", pad=0.05)
    plt.title("Expected Goals")

    return fig