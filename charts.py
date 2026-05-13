import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime

def create_distance_chart(parent_frame, runs):
    # Alte Charts entfernen falls vorhanden
    for widget in parent_frame.winfo_children():
        widget.destroy()

    fig, ax = plt.subplots(figsize=(6, 3))
    fig.patch.set_facecolor("#2b2b2b")
    ax.set_facecolor("#2b2b2b")

    if not runs or len(runs) == 0:
        ax.text(0.5, 0.5, "Noch keine Daten vorhanden",
                ha="center", va="center",
                color="white", fontsize=12)
        ax.axis("off")
    else:
        # Daten vorbereiten – chronologisch sortieren
        sorted_runs = sorted(runs, key=lambda r: r["date"])
        dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in sorted_runs]
        distances = [r["distance_km"] for r in sorted_runs]

        # Liniendiagramm
        ax.plot(dates, distances, color="#4CAF50", linewidth=2, marker="o",
                markersize=5, markerfacecolor="white")

        # Fläche unter der Linie
        ax.fill_between(dates, distances, alpha=0.2, color="#4CAF50")

        # Achsen formatieren
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate()

        ax.set_ylabel("Distanz (km)", color="white", fontsize=9)
        ax.set_title("Distanz über Zeit", color="white", fontsize=11)
        ax.tick_params(colors="white")

        for spine in ax.spines.values():
            spine.set_edgecolor("#444444")

    plt.tight_layout()

    # In Tkinter einbetten
    canvas = FigureCanvasTkAgg(fig, master=parent_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    return canvas