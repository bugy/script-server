#!/usr/bin/env python3

import plotly.express as px

df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species", size='petal_length',
                 hover_data=['petal_width'])
html_output = fig.to_html()
print(html_output)  # warning long output (3298755 characters)
