import json

import matplotlib as mpl
from matplotlib import pyplot as plt

__all__ = ["thousands", "freshfig",
           "fig_placement_save", "fig_placement_load",
           "get_legend_bbox", "xFontsize",
           "is_notebook_or_qt", "axprops", "fig_colorbar"]

thousands = mpl.ticker.StrMethodFormatter('{x:,.7g}')

try:
    __IPYTHON__
    from IPython import get_ipython
    is_notebook_or_qt = 'zmq' in str(type(get_ipython())).lower()
except (NameError,ImportError):
    is_notebook_or_qt = False


def freshfig(num=None,figsize=None,*args,**kwargs):
    """Create/clear figure.

    Similar to::

      fig, ax = suplots(*args,**kwargs)

    With the modification that:

    - If the figure does not exist: create it.
      This allows for figure sizing -- even with mpl backend MacOS.
    - Otherwise: clear figure.
      Avoids closing/opening so as to keep pos and size.
    """
    exists = plt.fignum_exists(num)

    fig = plt.figure(num=num,figsize=figsize)
    fig.clear()

    _, ax = plt.subplots(num=fig.number,*args,**kwargs)
    return fig, ax



def get_fmw(fignum):
    """If this fails, there's probs no way to make placement work."""
    return plt.figure(fignum).canvas.manager.window

def fig_placement_save(path="./.fig_geometries"):
    placements = {}
    for fignum in plt.get_fignums():
        fmw = get_fmw(fignum)
        try: # For Qt4Agg/Qt5Agg
            geo = dict(
                w = fmw.width(),
                h = fmw.height(),
                x = fmw.x(),
                y = fmw.y(),
            )
        except: # For TkAgg
            geo = fmw.geometry()
        placements[fignum] = geo
    with open(path,"w") as F:
        F.write(json.dumps(placements))

def fig_placement_load(path="./.fig_geometries"):
    with open(path,"r") as F:
        placements = json.load(F)
    for fignum in placements:
        plt.figure(int(fignum))
        fmw = get_fmw(int(fignum))
        geo = placements[fignum]
        try: # For Qt4Agg/Qt5Agg
            fmw.setGeometry( geo['x'], geo['y'], geo['w'], geo['h'])
        except: # For TkAgg
            # geo = "{w:.0f}x{h:.0f}+{x:.0f}+{y:.0f}".format(**geo)
            fmw.geometry(newGeometry=geo)





def get_legend_bbox(ax):
    """Get legend's bbox in pixel ("display") coords."""
    # Must pause/draw before bbox can be known
    def inner():
        plt.draw()
        leg = ax.get_legend()
        bbox = leg.get_window_extent()
        # bbox = leg.get_frame().get_bbox()
        return bbox
    return inner


def xFontsize(fontsize,fig,*args):
    """Multiply by fontsize, in pixels (rather than points)."""
    plt.pause(.1)
    fontsize = fig.canvas.renderer.points_to_pixels(fontsize)
    return tuple(a*fontsize for a in args)





# stackoverflow.com/a/11103301
def on_xlim_changed(ax):
    """
    Autoscale y-axis for subplots with sharex=True.

    Usage:
    for ax in fig.axes:
        ax.callbacks.connect('xlim_changed', on_xlim_changed)
    """
    xlim = ax.get_xlim()
    for a in ax.figure.axes:
            # shortcuts: last avoids n**2 behavior when each axis fires event
            if a is ax or len(a.lines) == 0 or getattr(a, 'xlim', None) == xlim:
                    continue

            ylim = np.inf, -np.inf
            for l in a.lines:
                    x, y = l.get_data()
                    # faster, but assumes that x is sorted
                    start, stop = np.searchsorted(x, xlim)
                    yc = y[max(start-1,0):(stop+1)]
                    ylim = min(ylim[0], np.nanmin(yc)), max(ylim[1], np.nanmax(yc))

            # TODO: update limits from Patches, Texts, Collections, ...

            # x axis: emit=False avoids infinite loop
            a.set_xlim(xlim, emit=False)

            # y axis: set dataLim, make sure that autoscale in 'y' is on
            corners = (xlim[0], ylim[0]), (xlim[1], ylim[1])
            a.dataLim.update_from_data_xy(corners, ignore=True, updatex=False)
            a.autoscale(enable=True, axis='y')
            # cache xlim to mark 'a' as treated
            a.xlim = xlim
