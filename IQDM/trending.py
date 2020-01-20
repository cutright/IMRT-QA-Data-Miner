from bokeh.io import curdoc
from IQDM.trending_delta4 import TrendingDashboard as TrendDelta4
import sys


FILE_PATH = sys.argv[1]
if 'delta4' in FILE_PATH:
    dashboard = TrendDelta4(sys.argv[1])
    curdoc().add_root(dashboard.layout)
    curdoc().title = "Delta 4 Trending"

else:  # sncpatient
    pass
