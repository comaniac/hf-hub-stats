"""Utilities"""


def print_model_in_md(models):
    from tabulate import tabulate

    data = []
    for rank, model in enumerate(models):
        if model.size == 0:
            size = "N/A"
        elif model.size == -1:
            size = "Unsupported"
        elif model.size < 1:
            size = "{:.0f}M".format(model.size * 1e3)
        else:
            size = "{:.1f}B".format(model.size)
        data.append((rank + 1, model.model_id, model.download, size))

    print(tabulate(data, headers=["Rank", "Name", "Downloads", "Size"]))


def draw_rank_chart(
    df,
    file_name="rank_chart.pdf",
    show_rank_axis=True,
    rank_axis_distance=1.5,
    ax=None,
    scatter=True,
    ylim=float("inf"),
    line_args={},
    scatter_args={},
):
    import matplotlib.pyplot as plt

    plt.figure(figsize=(15, 5))

    if ax is None:
        left_yaxis = plt.gca()
    else:
        left_yaxis = ax

    # Creating the right axis.
    right_yaxis = left_yaxis.twinx()

    axes = [left_yaxis, right_yaxis]

    # Creating the far right axis if show_rank_axis is True
    if show_rank_axis:
        far_right_yaxis = left_yaxis.twinx()
        far_right_yaxis.set_ylabel(
            "Rank", rotation=-90, labelpad=20, fontsize=12, weight="semibold"
        )
        axes.append(far_right_yaxis)

    for col in df.columns:
        y = df[col].mask(df[col] > ylim, None)
        x = df.index.values

        # Plotting blank points on the right axis/axes
        # so that they line up with the left axis.
        for axis in axes[1:]:
            axis.plot(x, y, alpha=0)

        left_yaxis.plot(x, y, **line_args, solid_capstyle="round")

        # Adding scatter plots
        if scatter:
            left_yaxis.scatter(x, y, **scatter_args)

    # Number of lines
    lines = len(df.columns)

    y_ticks = [*range(1, lines + 1)]

    # Configuring the axes so that they line up well.
    for axis in axes:
        axis.invert_yaxis()
        axis.set_yticks(y_ticks)
        if ylim != float("inf"):
            axis.set_ylim((lines + 0.5, 0.5))
        else:
            axis.set_ylim((ylim + 0.5, 0.5))

    # Sorting the labels to match the ranks.
    # left_labels = df.iloc[0].sort_values().index
    left_labels = ["" for _ in range(lines)]
    right_labels = df.iloc[-1].sort_values().index

    left_yaxis.set_yticklabels(left_labels)
    right_yaxis.set_yticklabels(right_labels)

    # Setting the position of the far right axis so that it doesn't overlap with the right axis
    if show_rank_axis:
        far_right_yaxis.spines["right"].set_position(("axes", rank_axis_distance))

    left_yaxis.xaxis.grid(color="lightgray", linestyle="solid")
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    if file_name is None:
        plt.show()
    else:
        plt.savefig(file_name, bbox_inches="tight")


def draw_trend_chart(
    df,
    file_name="trend_chart.pdf",
    scatter=True,
    ylim=float("inf"),
    ylabel="",
    line_args={},
    scatter_args={},
):
    import matplotlib.pyplot as plt

    plt.figure(figsize=(15, 5))

    yaxis = plt.gca()

    # Plot trends
    for col in df.columns:
        y = df[col].mask(df[col] > ylim, None)
        x = df.index.values
        yaxis.plot(x, y, **line_args, solid_capstyle="round", label=col)

        # Adding scatter plots
        if scatter:
            yaxis.scatter(x, y, **scatter_args)

        # Add data labels
        for x_val, y_val in zip(x, y):
            yaxis.annotate("{:.2f}".format(y_val), xy=(x_val, y_val), textcoords="data")

    yaxis.legend()
    yaxis.xaxis.grid(color="lightgray", linestyle="solid")
    plt.ylabel(ylabel)
    plt.gcf().autofmt_xdate()
    plt.tight_layout()
    if file_name is None:
        plt.show()
    else:
        plt.savefig(file_name, bbox_inches="tight")
