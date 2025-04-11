{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 556,
   "metadata": {},
   "outputs": [],
   "source": [
    "#import\n",
    "import torch\n",
    "import torch.nn as nn\n",
    "import torch.optim as optim\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "from sklearn.preprocessing import MinMaxScaler\n",
    "from sklearn.model_selection import train_test_split\n",
    "from torch.utils.data import DataLoader, TensorDataset\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "import plotly.graph_objects as go\n",
    "\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 557,
   "metadata": {},
   "outputs": [],
   "source": [
    "# ------------------------------\n",
    "# HYPERPARAMETERS & SETTINGS\n",
    "# ------------------------------\n",
    "\n",
    "# Model & Training Config\n",
    "FEATURES = [\n",
    "     'lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_5', 'lag_6', 'lag_7','year', 'month', 'day','dayofweek','dayofyear', \n",
    "]\n",
    "HIDDEN_LAYERS = [128, 64, 32]  # Increase model complexity with more layers\n",
    "ACTIVATION = nn.ReLU\n",
    "DROPOUT = 0.1  # Increase dropout rate to reduce overfitting\n",
    "LOSS_FN = nn.MSELoss\n",
    "OPTIMIZER_FN = optim.Adam\n",
    "LEARNING_RATE = 0.00001  # Reduce learning rate for more stable training\n",
    "WEIGHT_DECAY = 0.0001  # Increase weight decay for regularization\n",
    "EPOCHS = 6000  # Reduce epochs to prevent overfitting\n",
    "BATCH_SIZE = 100  # Increase batch size for faster training\n",
    "SEED = 42\n",
    "TEST_SIZE = 0.2\n",
    "N_SAMPLES = 1000  # Simulate data for 30 days\n",
    "BEST_LOSS = float('inf')  # Start with a very high loss\n",
    "PATIENCE = 100  # Reduce patience to stop earlier if no improvement\n",
    "PATIENCE_COUNTER = 0 # Counter for early stopping\n",
    "LAG_DAYS = 7\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 558,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "application/vnd.plotly.v1+json": {
       "config": {
        "plotlyServerURL": "https://plot.ly"
       },
       "data": [
        {
         "mode": "lines",
         "name": "Observations",
         "opacity": 0.7,
         "type": "scatter",
         "x": [
          "2025-01-01T00:00:00",
          "2025-01-02T00:00:00",
          "2025-01-03T00:00:00",
          "2025-01-04T00:00:00",
          "2025-01-05T00:00:00",
          "2025-01-06T00:00:00",
          "2025-01-07T00:00:00",
          "2025-01-08T00:00:00",
          "2025-01-09T00:00:00",
          "2025-01-10T00:00:00",
          "2025-01-11T00:00:00",
          "2025-01-12T00:00:00",
          "2025-01-13T00:00:00",
          "2025-01-14T00:00:00",
          "2025-01-15T00:00:00",
          "2025-01-16T00:00:00",
          "2025-01-17T00:00:00",
          "2025-01-18T00:00:00",
          "2025-01-19T00:00:00",
          "2025-01-20T00:00:00",
          "2025-01-21T00:00:00",
          "2025-01-22T00:00:00",
          "2025-01-23T00:00:00",
          "2025-01-24T00:00:00",
          "2025-01-25T00:00:00",
          "2025-01-26T00:00:00",
          "2025-01-27T00:00:00",
          "2025-01-28T00:00:00",
          "2025-01-29T00:00:00",
          "2025-01-30T00:00:00",
          "2025-01-31T00:00:00",
          "2025-02-01T00:00:00",
          "2025-02-02T00:00:00",
          "2025-02-03T00:00:00",
          "2025-02-04T00:00:00",
          "2025-02-05T00:00:00",
          "2025-02-06T00:00:00",
          "2025-02-07T00:00:00",
          "2025-02-08T00:00:00",
          "2025-02-09T00:00:00",
          "2025-02-10T00:00:00",
          "2025-02-11T00:00:00",
          "2025-02-12T00:00:00",
          "2025-02-13T00:00:00",
          "2025-02-14T00:00:00",
          "2025-02-15T00:00:00",
          "2025-02-16T00:00:00",
          "2025-02-17T00:00:00",
          "2025-02-18T00:00:00",
          "2025-02-19T00:00:00",
          "2025-02-20T00:00:00",
          "2025-02-21T00:00:00",
          "2025-02-22T00:00:00",
          "2025-02-23T00:00:00",
          "2025-02-24T00:00:00",
          "2025-02-25T00:00:00",
          "2025-02-26T00:00:00",
          "2025-02-27T00:00:00",
          "2025-02-28T00:00:00",
          "2025-03-01T00:00:00",
          "2025-03-02T00:00:00",
          "2025-03-03T00:00:00",
          "2025-03-04T00:00:00",
          "2025-03-05T00:00:00",
          "2025-03-06T00:00:00",
          "2025-03-07T00:00:00",
          "2025-03-08T00:00:00",
          "2025-03-09T00:00:00",
          "2025-03-10T00:00:00",
          "2025-03-11T00:00:00",
          "2025-03-12T00:00:00",
          "2025-03-13T00:00:00",
          "2025-03-14T00:00:00",
          "2025-03-15T00:00:00",
          "2025-03-16T00:00:00",
          "2025-03-17T00:00:00",
          "2025-03-18T00:00:00",
          "2025-03-19T00:00:00",
          "2025-03-20T00:00:00",
          "2025-03-21T00:00:00",
          "2025-03-22T00:00:00",
          "2025-03-23T00:00:00",
          "2025-03-24T00:00:00",
          "2025-03-25T00:00:00",
          "2025-03-26T00:00:00",
          "2025-03-27T00:00:00",
          "2025-03-28T00:00:00",
          "2025-03-29T00:00:00",
          "2025-03-30T00:00:00",
          "2025-03-31T00:00:00",
          "2025-04-01T00:00:00",
          "2025-04-02T00:00:00",
          "2025-04-03T00:00:00",
          "2025-04-04T00:00:00",
          "2025-04-05T00:00:00",
          "2025-04-06T00:00:00",
          "2025-04-07T00:00:00",
          "2025-04-08T00:00:00",
          "2025-04-09T00:00:00",
          "2025-04-10T00:00:00",
          "2025-04-11T00:00:00",
          "2025-04-12T00:00:00",
          "2025-04-13T00:00:00",
          "2025-04-14T00:00:00",
          "2025-04-15T00:00:00",
          "2025-04-16T00:00:00",
          "2025-04-17T00:00:00",
          "2025-04-18T00:00:00",
          "2025-04-19T00:00:00",
          "2025-04-20T00:00:00",
          "2025-04-21T00:00:00",
          "2025-04-22T00:00:00",
          "2025-04-23T00:00:00",
          "2025-04-24T00:00:00",
          "2025-04-25T00:00:00",
          "2025-04-26T00:00:00",
          "2025-04-27T00:00:00",
          "2025-04-28T00:00:00",
          "2025-04-29T00:00:00",
          "2025-04-30T00:00:00",
          "2025-05-01T00:00:00",
          "2025-05-02T00:00:00",
          "2025-05-03T00:00:00",
          "2025-05-04T00:00:00",
          "2025-05-05T00:00:00",
          "2025-05-06T00:00:00",
          "2025-05-07T00:00:00",
          "2025-05-08T00:00:00",
          "2025-05-09T00:00:00",
          "2025-05-10T00:00:00",
          "2025-05-11T00:00:00",
          "2025-05-12T00:00:00",
          "2025-05-13T00:00:00",
          "2025-05-14T00:00:00",
          "2025-05-15T00:00:00",
          "2025-05-16T00:00:00",
          "2025-05-17T00:00:00",
          "2025-05-18T00:00:00",
          "2025-05-19T00:00:00",
          "2025-05-20T00:00:00",
          "2025-05-21T00:00:00",
          "2025-05-22T00:00:00",
          "2025-05-23T00:00:00",
          "2025-05-24T00:00:00",
          "2025-05-25T00:00:00",
          "2025-05-26T00:00:00",
          "2025-05-27T00:00:00",
          "2025-05-28T00:00:00",
          "2025-05-29T00:00:00",
          "2025-05-30T00:00:00",
          "2025-05-31T00:00:00",
          "2025-06-01T00:00:00",
          "2025-06-02T00:00:00",
          "2025-06-03T00:00:00",
          "2025-06-04T00:00:00",
          "2025-06-05T00:00:00",
          "2025-06-06T00:00:00",
          "2025-06-07T00:00:00",
          "2025-06-08T00:00:00",
          "2025-06-09T00:00:00",
          "2025-06-10T00:00:00",
          "2025-06-11T00:00:00",
          "2025-06-12T00:00:00",
          "2025-06-13T00:00:00",
          "2025-06-14T00:00:00",
          "2025-06-15T00:00:00",
          "2025-06-16T00:00:00",
          "2025-06-17T00:00:00",
          "2025-06-18T00:00:00",
          "2025-06-19T00:00:00",
          "2025-06-20T00:00:00",
          "2025-06-21T00:00:00",
          "2025-06-22T00:00:00",
          "2025-06-23T00:00:00",
          "2025-06-24T00:00:00",
          "2025-06-25T00:00:00",
          "2025-06-26T00:00:00",
          "2025-06-27T00:00:00",
          "2025-06-28T00:00:00",
          "2025-06-29T00:00:00",
          "2025-06-30T00:00:00",
          "2025-07-01T00:00:00",
          "2025-07-02T00:00:00",
          "2025-07-03T00:00:00",
          "2025-07-04T00:00:00",
          "2025-07-05T00:00:00",
          "2025-07-06T00:00:00",
          "2025-07-07T00:00:00",
          "2025-07-08T00:00:00",
          "2025-07-09T00:00:00",
          "2025-07-10T00:00:00",
          "2025-07-11T00:00:00",
          "2025-07-12T00:00:00",
          "2025-07-13T00:00:00",
          "2025-07-14T00:00:00",
          "2025-07-15T00:00:00",
          "2025-07-16T00:00:00",
          "2025-07-17T00:00:00",
          "2025-07-18T00:00:00",
          "2025-07-19T00:00:00"
         ],
         "y": [
          53.34050475878356,
          49.720080946155726,
          54.22855416492282,
          54.48401066496795,
          56.47669879186305,
          56.51640108543412,
          51.777504868916296,
          56.94511022356447,
          58.57904414479333,
          49.51530356581284,
          55.25777881612097,
          60.323641899543546,
          66.48240593397648,
          62.710917793302585,
          68.09618664865202,
          57.88752104940166,
          61.77244916285498,
          65.18910635659736,
          50.16423707656464,
          69.98201951801445,
          53.75171444203627,
          68.66528921335397,
          67.73495082943487,
          53.2187226878043,
          54.08278643144454,
          73.29723448311135,
          72.81031417352588,
          62.929232794670426,
          63.51579500132222,
          71.07446912423137,
          69.02842154768264,
          74.93908857294079,
          72.63409040820987,
          78.71434918927419,
          76.20636488469984,
          75.51023077720625,
          70.68957992095449,
          70.86072582349065,
          73.25880043835295,
          83.24555583381702,
          72.5255430715685,
          76.3683209100452,
          64.3429582285984,
          79.4397079173366,
          87.83260175884027,
          72.35648311577161,
          93.3669303213842,
          78.86781959437602,
          65.54557945903078,
          76.92775986529752,
          85.94433272157274,
          89.71676838956675,
          83.72995441593443,
          88.38783632870165,
          75.06235182994297,
          77.94229240771288,
          73.32942620055047,
          79.07523020023906,
          86.2745667375548,
          83.88318599609042,
          87.50450617679981,
          78.81837583381191,
          79.44925296373276,
          85.16602817282615,
          81.43592707989436,
          91.25461751319207,
          81.89442958633211,
          82.83061066337334,
          87.66760471788872,
          83.88257635275396,
          79.89960853640443,
          80.81251640562675,
          89.22269416767257,
          79.95443515710379,
          93.93746213551769,
          83.6927728942041,
          90.40842664953085,
          84.34728226177057,
          83.08453027133396,
          89.04201952406986,
          93.2105365042319,
          86.84423833994803,
          87.87247766753256,
          92.34506134799373,
          92.60804081266866,
          88.2996968432819,
          86.35083247847587,
          89.04692240376886,
          87.73384233304022,
          90.29739039269136,
          82.79466993254655,
          90.17483869550766,
          85.2097562292269,
          93.33251890063295,
          85.43204914399033,
          85.49968584801,
          90.9726562997796,
          88.77677648053194,
          100.03870724921775,
          80.44839889931617,
          89.07342746378708,
          94.09150969639684,
          85.46070540245867,
          83.69847977040654,
          83.78599255949801,
          79.9596846661405,
          94.63739508158073,
          86.10045536805701,
          85.35845085629671,
          76.81860402952337,
          80.10161516903598,
          94.41882200223975,
          88.41986741851449,
          92.54016217083868,
          91.70189787953386,
          81.28417953755311,
          98.21304449946932,
          95.58028860072609,
          82.7720263234472,
          67.50059944449002,
          83.30139175952114,
          86.00974598286912,
          81.70579841498632,
          83.15496161193909,
          79.8296459767796,
          88.28379811866034,
          83.68894488378177,
          87.81611310186747,
          88.85008036802093,
          71.5408727840891,
          78.22636453417404,
          78.61852649020771,
          94.24860129956359,
          81.78336119799368,
          84.74142197832545,
          70.90929825126882,
          80.6569918150486,
          84.45472428667655,
          83.48978707770804,
          81.90819066902736,
          78.46213141515393,
          78.30578690626035,
          69.12748511121757,
          72.68226051024838,
          77.926171643675,
          72.77370056236671,
          79.37568377886164,
          77.83928935537512,
          81.91227038819484,
          79.43307791020891,
          75.34104264889137,
          77.50429299359136,
          78.34647765322696,
          70.33747072732916,
          70.779001302744,
          71.49002955090118,
          69.14271113882504,
          76.14290057577243,
          67.4701109410558,
          76.40541323066263,
          67.85127575296782,
          71.5858042452801,
          69.59246969429596,
          63.416162083656616,
          67.73157484953164,
          69.03369991626305,
          66.57817534784105,
          59.720161757408405,
          74.47499729195414,
          65.94080725065643,
          61.065759332400816,
          72.67677950018823,
          67.19646135085166,
          57.646341603955555,
          57.963703727670456,
          61.614696084451836,
          63.75540237712746,
          64.92696863100618,
          66.11006599310797,
          63.60553907099107,
          67.19240606966925,
          60.64633229000702,
          55.770745607660466,
          59.11184338181996,
          58.346621252158336,
          45.366837070436006,
          55.021122433804265,
          58.97285945438788,
          54.858675910276666,
          53.33083466248416,
          60.70528937617206,
          51.15678822468965,
          58.893502782554364,
          48.27248209671362,
          68.34594953751868,
          53.074944046419816,
          52.153747510757796,
          59.10774829522195,
          50.927052031659734,
          59.92935337845155
         ]
        }
       ],
       "layout": {
        "legend": {
         "title": {
          "text": "Legend"
         }
        },
        "template": {
         "data": {
          "bar": [
           {
            "error_x": {
             "color": "#2a3f5f"
            },
            "error_y": {
             "color": "#2a3f5f"
            },
            "marker": {
             "line": {
              "color": "white",
              "width": 0.5
             },
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "bar"
           }
          ],
          "barpolar": [
           {
            "marker": {
             "line": {
              "color": "white",
              "width": 0.5
             },
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "barpolar"
           }
          ],
          "carpet": [
           {
            "aaxis": {
             "endlinecolor": "#2a3f5f",
             "gridcolor": "#C8D4E3",
             "linecolor": "#C8D4E3",
             "minorgridcolor": "#C8D4E3",
             "startlinecolor": "#2a3f5f"
            },
            "baxis": {
             "endlinecolor": "#2a3f5f",
             "gridcolor": "#C8D4E3",
             "linecolor": "#C8D4E3",
             "minorgridcolor": "#C8D4E3",
             "startlinecolor": "#2a3f5f"
            },
            "type": "carpet"
           }
          ],
          "choropleth": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "choropleth"
           }
          ],
          "contour": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "contour"
           }
          ],
          "contourcarpet": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "contourcarpet"
           }
          ],
          "heatmap": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "heatmap"
           }
          ],
          "heatmapgl": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "heatmapgl"
           }
          ],
          "histogram": [
           {
            "marker": {
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "histogram"
           }
          ],
          "histogram2d": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "histogram2d"
           }
          ],
          "histogram2dcontour": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "histogram2dcontour"
           }
          ],
          "mesh3d": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "mesh3d"
           }
          ],
          "parcoords": [
           {
            "line": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "parcoords"
           }
          ],
          "pie": [
           {
            "automargin": true,
            "type": "pie"
           }
          ],
          "scatter": [
           {
            "fillpattern": {
             "fillmode": "overlay",
             "size": 10,
             "solidity": 0.2
            },
            "type": "scatter"
           }
          ],
          "scatter3d": [
           {
            "line": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatter3d"
           }
          ],
          "scattercarpet": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattercarpet"
           }
          ],
          "scattergeo": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattergeo"
           }
          ],
          "scattergl": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattergl"
           }
          ],
          "scattermapbox": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattermapbox"
           }
          ],
          "scatterpolar": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterpolar"
           }
          ],
          "scatterpolargl": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterpolargl"
           }
          ],
          "scatterternary": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterternary"
           }
          ],
          "surface": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "surface"
           }
          ],
          "table": [
           {
            "cells": {
             "fill": {
              "color": "#EBF0F8"
             },
             "line": {
              "color": "white"
             }
            },
            "header": {
             "fill": {
              "color": "#C8D4E3"
             },
             "line": {
              "color": "white"
             }
            },
            "type": "table"
           }
          ]
         },
         "layout": {
          "annotationdefaults": {
           "arrowcolor": "#2a3f5f",
           "arrowhead": 0,
           "arrowwidth": 1
          },
          "autotypenumbers": "strict",
          "coloraxis": {
           "colorbar": {
            "outlinewidth": 0,
            "ticks": ""
           }
          },
          "colorscale": {
           "diverging": [
            [
             0,
             "#8e0152"
            ],
            [
             0.1,
             "#c51b7d"
            ],
            [
             0.2,
             "#de77ae"
            ],
            [
             0.3,
             "#f1b6da"
            ],
            [
             0.4,
             "#fde0ef"
            ],
            [
             0.5,
             "#f7f7f7"
            ],
            [
             0.6,
             "#e6f5d0"
            ],
            [
             0.7,
             "#b8e186"
            ],
            [
             0.8,
             "#7fbc41"
            ],
            [
             0.9,
             "#4d9221"
            ],
            [
             1,
             "#276419"
            ]
           ],
           "sequential": [
            [
             0,
             "#0d0887"
            ],
            [
             0.1111111111111111,
             "#46039f"
            ],
            [
             0.2222222222222222,
             "#7201a8"
            ],
            [
             0.3333333333333333,
             "#9c179e"
            ],
            [
             0.4444444444444444,
             "#bd3786"
            ],
            [
             0.5555555555555556,
             "#d8576b"
            ],
            [
             0.6666666666666666,
             "#ed7953"
            ],
            [
             0.7777777777777778,
             "#fb9f3a"
            ],
            [
             0.8888888888888888,
             "#fdca26"
            ],
            [
             1,
             "#f0f921"
            ]
           ],
           "sequentialminus": [
            [
             0,
             "#0d0887"
            ],
            [
             0.1111111111111111,
             "#46039f"
            ],
            [
             0.2222222222222222,
             "#7201a8"
            ],
            [
             0.3333333333333333,
             "#9c179e"
            ],
            [
             0.4444444444444444,
             "#bd3786"
            ],
            [
             0.5555555555555556,
             "#d8576b"
            ],
            [
             0.6666666666666666,
             "#ed7953"
            ],
            [
             0.7777777777777778,
             "#fb9f3a"
            ],
            [
             0.8888888888888888,
             "#fdca26"
            ],
            [
             1,
             "#f0f921"
            ]
           ]
          },
          "colorway": [
           "#636efa",
           "#EF553B",
           "#00cc96",
           "#ab63fa",
           "#FFA15A",
           "#19d3f3",
           "#FF6692",
           "#B6E880",
           "#FF97FF",
           "#FECB52"
          ],
          "font": {
           "color": "#2a3f5f"
          },
          "geo": {
           "bgcolor": "white",
           "lakecolor": "white",
           "landcolor": "white",
           "showlakes": true,
           "showland": true,
           "subunitcolor": "#C8D4E3"
          },
          "hoverlabel": {
           "align": "left"
          },
          "hovermode": "closest",
          "mapbox": {
           "style": "light"
          },
          "paper_bgcolor": "white",
          "plot_bgcolor": "white",
          "polar": {
           "angularaxis": {
            "gridcolor": "#EBF0F8",
            "linecolor": "#EBF0F8",
            "ticks": ""
           },
           "bgcolor": "white",
           "radialaxis": {
            "gridcolor": "#EBF0F8",
            "linecolor": "#EBF0F8",
            "ticks": ""
           }
          },
          "scene": {
           "xaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           },
           "yaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           },
           "zaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           }
          },
          "shapedefaults": {
           "line": {
            "color": "#2a3f5f"
           }
          },
          "ternary": {
           "aaxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           },
           "baxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           },
           "bgcolor": "white",
           "caxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           }
          },
          "title": {
           "x": 0.05
          },
          "xaxis": {
           "automargin": true,
           "gridcolor": "#EBF0F8",
           "linecolor": "#EBF0F8",
           "ticks": "",
           "title": {
            "standoff": 15
           },
           "zerolinecolor": "#EBF0F8",
           "zerolinewidth": 2
          },
          "yaxis": {
           "automargin": true,
           "gridcolor": "#EBF0F8",
           "linecolor": "#EBF0F8",
           "ticks": "",
           "title": {
            "standoff": 15
           },
           "zerolinecolor": "#EBF0F8",
           "zerolinewidth": 2
          }
         }
        },
        "title": {
         "text": "Observations Over Time"
        },
        "xaxis": {
         "title": {
          "text": "Date"
         }
        },
        "yaxis": {
         "title": {
          "text": "Observations"
         }
        }
       }
      }
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "# Set a random seed for reproducibility\n",
    "np.random.seed(SEED)\n",
    "torch.manual_seed(SEED)\n",
    "\n",
    "# Create a date range starting from January 1, 2025\n",
    "dates = pd.date_range(start=\"2025-01-01\", periods=N_SAMPLES, freq=\"D\")\n",
    " # set date as index\n",
    "\n",
    "# Generate random observations between 20 and 200\n",
    "observations = np.random.randint(20, 200, size=N_SAMPLES)\n",
    "\n",
    "# Add some noise to the observations\n",
    "trend = np.linspace(50, 150, N_SAMPLES)\n",
    "seasonality = 30 * np.sin(np.linspace(0, 6*np.pi, N_SAMPLES))\n",
    "noise = np.random.normal(0, 5, N_SAMPLES)\n",
    "observations = trend + seasonality + noise\n",
    "\n",
    "# Create the DataFrame\n",
    "df = pd.DataFrame({\n",
    "    \"dates\": dates,\n",
    "    \"observations\": observations\n",
    "})\n",
    "\n",
    "# increase date data\n",
    "df['year'] = df['dates'].dt.year\n",
    "df['month'] = df['dates'].dt.month\n",
    "df['day'] = df['dates'].dt.day\n",
    "df['dayofweek'] = df['dates'].dt.dayofweek\n",
    "df['dayofyear'] = df['dates'].dt.dayofyear\n",
    "\n",
    "#set dates as index\n",
    "df.set_index('dates', inplace=True)\n",
    "\n",
    "# Function to create lag features\n",
    "def create_lag_features(df, target_column, lag_days):\n",
    "    for lag in range(1, lag_days + 1):\n",
    "        df[f\"lag_{lag}\"] = df[target_column].shift(lag)\n",
    "    return df\n",
    "\n",
    "# Apply the function to create lag features\n",
    "df = create_lag_features(df, \"observations\", LAG_DAYS)\n",
    "\n",
    "# Drop rows with NaN values caused by lagging\n",
    "df.dropna(inplace=True)\n",
    "\n",
    "# Visualization\n",
    "fig = go.Figure()\n",
    "fig.add_trace(go.Scatter(x=dates[:200], y=observations[:200], mode='lines', name='Observations', opacity=0.7))\n",
    "\n",
    "fig.update_layout(\n",
    "    title=\"Observations Over Time\",\n",
    "    xaxis_title=\"Date\",\n",
    "    yaxis_title=\"Observations\",\n",
    "    legend_title=\"Legend\",\n",
    "    template=\"plotly_white\"\n",
    ")\n",
    "\n",
    "fig.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 559,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<div>\n",
       "<style scoped>\n",
       "    .dataframe tbody tr th:only-of-type {\n",
       "        vertical-align: middle;\n",
       "    }\n",
       "\n",
       "    .dataframe tbody tr th {\n",
       "        vertical-align: top;\n",
       "    }\n",
       "\n",
       "    .dataframe thead th {\n",
       "        text-align: right;\n",
       "    }\n",
       "</style>\n",
       "<table border=\"1\" class=\"dataframe\">\n",
       "  <thead>\n",
       "    <tr style=\"text-align: right;\">\n",
       "      <th></th>\n",
       "      <th>observations</th>\n",
       "      <th>year</th>\n",
       "      <th>month</th>\n",
       "      <th>day</th>\n",
       "      <th>dayofweek</th>\n",
       "      <th>dayofyear</th>\n",
       "      <th>lag_1</th>\n",
       "      <th>lag_2</th>\n",
       "      <th>lag_3</th>\n",
       "      <th>lag_4</th>\n",
       "      <th>lag_5</th>\n",
       "      <th>lag_6</th>\n",
       "      <th>lag_7</th>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>dates</th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "      <th></th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <th>2025-01-08</th>\n",
       "      <td>56.945110</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>8</td>\n",
       "      <td>2</td>\n",
       "      <td>8</td>\n",
       "      <td>51.777505</td>\n",
       "      <td>56.516401</td>\n",
       "      <td>56.476699</td>\n",
       "      <td>54.484011</td>\n",
       "      <td>54.228554</td>\n",
       "      <td>49.720081</td>\n",
       "      <td>53.340505</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-09</th>\n",
       "      <td>58.579044</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>9</td>\n",
       "      <td>3</td>\n",
       "      <td>9</td>\n",
       "      <td>56.945110</td>\n",
       "      <td>51.777505</td>\n",
       "      <td>56.516401</td>\n",
       "      <td>56.476699</td>\n",
       "      <td>54.484011</td>\n",
       "      <td>54.228554</td>\n",
       "      <td>49.720081</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-10</th>\n",
       "      <td>49.515304</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>10</td>\n",
       "      <td>4</td>\n",
       "      <td>10</td>\n",
       "      <td>58.579044</td>\n",
       "      <td>56.945110</td>\n",
       "      <td>51.777505</td>\n",
       "      <td>56.516401</td>\n",
       "      <td>56.476699</td>\n",
       "      <td>54.484011</td>\n",
       "      <td>54.228554</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-11</th>\n",
       "      <td>55.257779</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>11</td>\n",
       "      <td>5</td>\n",
       "      <td>11</td>\n",
       "      <td>49.515304</td>\n",
       "      <td>58.579044</td>\n",
       "      <td>56.945110</td>\n",
       "      <td>51.777505</td>\n",
       "      <td>56.516401</td>\n",
       "      <td>56.476699</td>\n",
       "      <td>54.484011</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-12</th>\n",
       "      <td>60.323642</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>12</td>\n",
       "      <td>6</td>\n",
       "      <td>12</td>\n",
       "      <td>55.257779</td>\n",
       "      <td>49.515304</td>\n",
       "      <td>58.579044</td>\n",
       "      <td>56.945110</td>\n",
       "      <td>51.777505</td>\n",
       "      <td>56.516401</td>\n",
       "      <td>56.476699</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-13</th>\n",
       "      <td>66.482406</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>13</td>\n",
       "      <td>0</td>\n",
       "      <td>13</td>\n",
       "      <td>60.323642</td>\n",
       "      <td>55.257779</td>\n",
       "      <td>49.515304</td>\n",
       "      <td>58.579044</td>\n",
       "      <td>56.945110</td>\n",
       "      <td>51.777505</td>\n",
       "      <td>56.516401</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-14</th>\n",
       "      <td>62.710918</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>14</td>\n",
       "      <td>1</td>\n",
       "      <td>14</td>\n",
       "      <td>66.482406</td>\n",
       "      <td>60.323642</td>\n",
       "      <td>55.257779</td>\n",
       "      <td>49.515304</td>\n",
       "      <td>58.579044</td>\n",
       "      <td>56.945110</td>\n",
       "      <td>51.777505</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-15</th>\n",
       "      <td>68.096187</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>15</td>\n",
       "      <td>2</td>\n",
       "      <td>15</td>\n",
       "      <td>62.710918</td>\n",
       "      <td>66.482406</td>\n",
       "      <td>60.323642</td>\n",
       "      <td>55.257779</td>\n",
       "      <td>49.515304</td>\n",
       "      <td>58.579044</td>\n",
       "      <td>56.945110</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-16</th>\n",
       "      <td>57.887521</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>16</td>\n",
       "      <td>3</td>\n",
       "      <td>16</td>\n",
       "      <td>68.096187</td>\n",
       "      <td>62.710918</td>\n",
       "      <td>66.482406</td>\n",
       "      <td>60.323642</td>\n",
       "      <td>55.257779</td>\n",
       "      <td>49.515304</td>\n",
       "      <td>58.579044</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-17</th>\n",
       "      <td>61.772449</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>17</td>\n",
       "      <td>4</td>\n",
       "      <td>17</td>\n",
       "      <td>57.887521</td>\n",
       "      <td>68.096187</td>\n",
       "      <td>62.710918</td>\n",
       "      <td>66.482406</td>\n",
       "      <td>60.323642</td>\n",
       "      <td>55.257779</td>\n",
       "      <td>49.515304</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-18</th>\n",
       "      <td>65.189106</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>18</td>\n",
       "      <td>5</td>\n",
       "      <td>18</td>\n",
       "      <td>61.772449</td>\n",
       "      <td>57.887521</td>\n",
       "      <td>68.096187</td>\n",
       "      <td>62.710918</td>\n",
       "      <td>66.482406</td>\n",
       "      <td>60.323642</td>\n",
       "      <td>55.257779</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-19</th>\n",
       "      <td>50.164237</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>19</td>\n",
       "      <td>6</td>\n",
       "      <td>19</td>\n",
       "      <td>65.189106</td>\n",
       "      <td>61.772449</td>\n",
       "      <td>57.887521</td>\n",
       "      <td>68.096187</td>\n",
       "      <td>62.710918</td>\n",
       "      <td>66.482406</td>\n",
       "      <td>60.323642</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-20</th>\n",
       "      <td>69.982020</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>20</td>\n",
       "      <td>0</td>\n",
       "      <td>20</td>\n",
       "      <td>50.164237</td>\n",
       "      <td>65.189106</td>\n",
       "      <td>61.772449</td>\n",
       "      <td>57.887521</td>\n",
       "      <td>68.096187</td>\n",
       "      <td>62.710918</td>\n",
       "      <td>66.482406</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-21</th>\n",
       "      <td>53.751714</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>21</td>\n",
       "      <td>1</td>\n",
       "      <td>21</td>\n",
       "      <td>69.982020</td>\n",
       "      <td>50.164237</td>\n",
       "      <td>65.189106</td>\n",
       "      <td>61.772449</td>\n",
       "      <td>57.887521</td>\n",
       "      <td>68.096187</td>\n",
       "      <td>62.710918</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-22</th>\n",
       "      <td>68.665289</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>22</td>\n",
       "      <td>2</td>\n",
       "      <td>22</td>\n",
       "      <td>53.751714</td>\n",
       "      <td>69.982020</td>\n",
       "      <td>50.164237</td>\n",
       "      <td>65.189106</td>\n",
       "      <td>61.772449</td>\n",
       "      <td>57.887521</td>\n",
       "      <td>68.096187</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-23</th>\n",
       "      <td>67.734951</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>23</td>\n",
       "      <td>3</td>\n",
       "      <td>23</td>\n",
       "      <td>68.665289</td>\n",
       "      <td>53.751714</td>\n",
       "      <td>69.982020</td>\n",
       "      <td>50.164237</td>\n",
       "      <td>65.189106</td>\n",
       "      <td>61.772449</td>\n",
       "      <td>57.887521</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-24</th>\n",
       "      <td>53.218723</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>24</td>\n",
       "      <td>4</td>\n",
       "      <td>24</td>\n",
       "      <td>67.734951</td>\n",
       "      <td>68.665289</td>\n",
       "      <td>53.751714</td>\n",
       "      <td>69.982020</td>\n",
       "      <td>50.164237</td>\n",
       "      <td>65.189106</td>\n",
       "      <td>61.772449</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-25</th>\n",
       "      <td>54.082786</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>25</td>\n",
       "      <td>5</td>\n",
       "      <td>25</td>\n",
       "      <td>53.218723</td>\n",
       "      <td>67.734951</td>\n",
       "      <td>68.665289</td>\n",
       "      <td>53.751714</td>\n",
       "      <td>69.982020</td>\n",
       "      <td>50.164237</td>\n",
       "      <td>65.189106</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-26</th>\n",
       "      <td>73.297234</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>26</td>\n",
       "      <td>6</td>\n",
       "      <td>26</td>\n",
       "      <td>54.082786</td>\n",
       "      <td>53.218723</td>\n",
       "      <td>67.734951</td>\n",
       "      <td>68.665289</td>\n",
       "      <td>53.751714</td>\n",
       "      <td>69.982020</td>\n",
       "      <td>50.164237</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-27</th>\n",
       "      <td>72.810314</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>27</td>\n",
       "      <td>0</td>\n",
       "      <td>27</td>\n",
       "      <td>73.297234</td>\n",
       "      <td>54.082786</td>\n",
       "      <td>53.218723</td>\n",
       "      <td>67.734951</td>\n",
       "      <td>68.665289</td>\n",
       "      <td>53.751714</td>\n",
       "      <td>69.982020</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-28</th>\n",
       "      <td>62.929233</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>28</td>\n",
       "      <td>1</td>\n",
       "      <td>28</td>\n",
       "      <td>72.810314</td>\n",
       "      <td>73.297234</td>\n",
       "      <td>54.082786</td>\n",
       "      <td>53.218723</td>\n",
       "      <td>67.734951</td>\n",
       "      <td>68.665289</td>\n",
       "      <td>53.751714</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-29</th>\n",
       "      <td>63.515795</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>29</td>\n",
       "      <td>2</td>\n",
       "      <td>29</td>\n",
       "      <td>62.929233</td>\n",
       "      <td>72.810314</td>\n",
       "      <td>73.297234</td>\n",
       "      <td>54.082786</td>\n",
       "      <td>53.218723</td>\n",
       "      <td>67.734951</td>\n",
       "      <td>68.665289</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-30</th>\n",
       "      <td>71.074469</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>30</td>\n",
       "      <td>3</td>\n",
       "      <td>30</td>\n",
       "      <td>63.515795</td>\n",
       "      <td>62.929233</td>\n",
       "      <td>72.810314</td>\n",
       "      <td>73.297234</td>\n",
       "      <td>54.082786</td>\n",
       "      <td>53.218723</td>\n",
       "      <td>67.734951</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-01-31</th>\n",
       "      <td>69.028422</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>31</td>\n",
       "      <td>4</td>\n",
       "      <td>31</td>\n",
       "      <td>71.074469</td>\n",
       "      <td>63.515795</td>\n",
       "      <td>62.929233</td>\n",
       "      <td>72.810314</td>\n",
       "      <td>73.297234</td>\n",
       "      <td>54.082786</td>\n",
       "      <td>53.218723</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-01</th>\n",
       "      <td>74.939089</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>1</td>\n",
       "      <td>5</td>\n",
       "      <td>32</td>\n",
       "      <td>69.028422</td>\n",
       "      <td>71.074469</td>\n",
       "      <td>63.515795</td>\n",
       "      <td>62.929233</td>\n",
       "      <td>72.810314</td>\n",
       "      <td>73.297234</td>\n",
       "      <td>54.082786</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-02</th>\n",
       "      <td>72.634090</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>2</td>\n",
       "      <td>6</td>\n",
       "      <td>33</td>\n",
       "      <td>74.939089</td>\n",
       "      <td>69.028422</td>\n",
       "      <td>71.074469</td>\n",
       "      <td>63.515795</td>\n",
       "      <td>62.929233</td>\n",
       "      <td>72.810314</td>\n",
       "      <td>73.297234</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-03</th>\n",
       "      <td>78.714349</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "      <td>34</td>\n",
       "      <td>72.634090</td>\n",
       "      <td>74.939089</td>\n",
       "      <td>69.028422</td>\n",
       "      <td>71.074469</td>\n",
       "      <td>63.515795</td>\n",
       "      <td>62.929233</td>\n",
       "      <td>72.810314</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-04</th>\n",
       "      <td>76.206365</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>4</td>\n",
       "      <td>1</td>\n",
       "      <td>35</td>\n",
       "      <td>78.714349</td>\n",
       "      <td>72.634090</td>\n",
       "      <td>74.939089</td>\n",
       "      <td>69.028422</td>\n",
       "      <td>71.074469</td>\n",
       "      <td>63.515795</td>\n",
       "      <td>62.929233</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-05</th>\n",
       "      <td>75.510231</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>5</td>\n",
       "      <td>2</td>\n",
       "      <td>36</td>\n",
       "      <td>76.206365</td>\n",
       "      <td>78.714349</td>\n",
       "      <td>72.634090</td>\n",
       "      <td>74.939089</td>\n",
       "      <td>69.028422</td>\n",
       "      <td>71.074469</td>\n",
       "      <td>63.515795</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-06</th>\n",
       "      <td>70.689580</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>6</td>\n",
       "      <td>3</td>\n",
       "      <td>37</td>\n",
       "      <td>75.510231</td>\n",
       "      <td>76.206365</td>\n",
       "      <td>78.714349</td>\n",
       "      <td>72.634090</td>\n",
       "      <td>74.939089</td>\n",
       "      <td>69.028422</td>\n",
       "      <td>71.074469</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-07</th>\n",
       "      <td>70.860726</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>7</td>\n",
       "      <td>4</td>\n",
       "      <td>38</td>\n",
       "      <td>70.689580</td>\n",
       "      <td>75.510231</td>\n",
       "      <td>76.206365</td>\n",
       "      <td>78.714349</td>\n",
       "      <td>72.634090</td>\n",
       "      <td>74.939089</td>\n",
       "      <td>69.028422</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-08</th>\n",
       "      <td>73.258800</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>8</td>\n",
       "      <td>5</td>\n",
       "      <td>39</td>\n",
       "      <td>70.860726</td>\n",
       "      <td>70.689580</td>\n",
       "      <td>75.510231</td>\n",
       "      <td>76.206365</td>\n",
       "      <td>78.714349</td>\n",
       "      <td>72.634090</td>\n",
       "      <td>74.939089</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-09</th>\n",
       "      <td>83.245556</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>9</td>\n",
       "      <td>6</td>\n",
       "      <td>40</td>\n",
       "      <td>73.258800</td>\n",
       "      <td>70.860726</td>\n",
       "      <td>70.689580</td>\n",
       "      <td>75.510231</td>\n",
       "      <td>76.206365</td>\n",
       "      <td>78.714349</td>\n",
       "      <td>72.634090</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-10</th>\n",
       "      <td>72.525543</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>10</td>\n",
       "      <td>0</td>\n",
       "      <td>41</td>\n",
       "      <td>83.245556</td>\n",
       "      <td>73.258800</td>\n",
       "      <td>70.860726</td>\n",
       "      <td>70.689580</td>\n",
       "      <td>75.510231</td>\n",
       "      <td>76.206365</td>\n",
       "      <td>78.714349</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-11</th>\n",
       "      <td>76.368321</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>11</td>\n",
       "      <td>1</td>\n",
       "      <td>42</td>\n",
       "      <td>72.525543</td>\n",
       "      <td>83.245556</td>\n",
       "      <td>73.258800</td>\n",
       "      <td>70.860726</td>\n",
       "      <td>70.689580</td>\n",
       "      <td>75.510231</td>\n",
       "      <td>76.206365</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-12</th>\n",
       "      <td>64.342958</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>12</td>\n",
       "      <td>2</td>\n",
       "      <td>43</td>\n",
       "      <td>76.368321</td>\n",
       "      <td>72.525543</td>\n",
       "      <td>83.245556</td>\n",
       "      <td>73.258800</td>\n",
       "      <td>70.860726</td>\n",
       "      <td>70.689580</td>\n",
       "      <td>75.510231</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-13</th>\n",
       "      <td>79.439708</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>13</td>\n",
       "      <td>3</td>\n",
       "      <td>44</td>\n",
       "      <td>64.342958</td>\n",
       "      <td>76.368321</td>\n",
       "      <td>72.525543</td>\n",
       "      <td>83.245556</td>\n",
       "      <td>73.258800</td>\n",
       "      <td>70.860726</td>\n",
       "      <td>70.689580</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-14</th>\n",
       "      <td>87.832602</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>14</td>\n",
       "      <td>4</td>\n",
       "      <td>45</td>\n",
       "      <td>79.439708</td>\n",
       "      <td>64.342958</td>\n",
       "      <td>76.368321</td>\n",
       "      <td>72.525543</td>\n",
       "      <td>83.245556</td>\n",
       "      <td>73.258800</td>\n",
       "      <td>70.860726</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-15</th>\n",
       "      <td>72.356483</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>15</td>\n",
       "      <td>5</td>\n",
       "      <td>46</td>\n",
       "      <td>87.832602</td>\n",
       "      <td>79.439708</td>\n",
       "      <td>64.342958</td>\n",
       "      <td>76.368321</td>\n",
       "      <td>72.525543</td>\n",
       "      <td>83.245556</td>\n",
       "      <td>73.258800</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2025-02-16</th>\n",
       "      <td>93.366930</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>16</td>\n",
       "      <td>6</td>\n",
       "      <td>47</td>\n",
       "      <td>72.356483</td>\n",
       "      <td>87.832602</td>\n",
       "      <td>79.439708</td>\n",
       "      <td>64.342958</td>\n",
       "      <td>76.368321</td>\n",
       "      <td>72.525543</td>\n",
       "      <td>83.245556</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "</div>"
      ],
      "text/plain": [
       "            observations  year  month  day  dayofweek  dayofyear      lag_1  \\\n",
       "dates                                                                         \n",
       "2025-01-08     56.945110  2025      1    8          2          8  51.777505   \n",
       "2025-01-09     58.579044  2025      1    9          3          9  56.945110   \n",
       "2025-01-10     49.515304  2025      1   10          4         10  58.579044   \n",
       "2025-01-11     55.257779  2025      1   11          5         11  49.515304   \n",
       "2025-01-12     60.323642  2025      1   12          6         12  55.257779   \n",
       "2025-01-13     66.482406  2025      1   13          0         13  60.323642   \n",
       "2025-01-14     62.710918  2025      1   14          1         14  66.482406   \n",
       "2025-01-15     68.096187  2025      1   15          2         15  62.710918   \n",
       "2025-01-16     57.887521  2025      1   16          3         16  68.096187   \n",
       "2025-01-17     61.772449  2025      1   17          4         17  57.887521   \n",
       "2025-01-18     65.189106  2025      1   18          5         18  61.772449   \n",
       "2025-01-19     50.164237  2025      1   19          6         19  65.189106   \n",
       "2025-01-20     69.982020  2025      1   20          0         20  50.164237   \n",
       "2025-01-21     53.751714  2025      1   21          1         21  69.982020   \n",
       "2025-01-22     68.665289  2025      1   22          2         22  53.751714   \n",
       "2025-01-23     67.734951  2025      1   23          3         23  68.665289   \n",
       "2025-01-24     53.218723  2025      1   24          4         24  67.734951   \n",
       "2025-01-25     54.082786  2025      1   25          5         25  53.218723   \n",
       "2025-01-26     73.297234  2025      1   26          6         26  54.082786   \n",
       "2025-01-27     72.810314  2025      1   27          0         27  73.297234   \n",
       "2025-01-28     62.929233  2025      1   28          1         28  72.810314   \n",
       "2025-01-29     63.515795  2025      1   29          2         29  62.929233   \n",
       "2025-01-30     71.074469  2025      1   30          3         30  63.515795   \n",
       "2025-01-31     69.028422  2025      1   31          4         31  71.074469   \n",
       "2025-02-01     74.939089  2025      2    1          5         32  69.028422   \n",
       "2025-02-02     72.634090  2025      2    2          6         33  74.939089   \n",
       "2025-02-03     78.714349  2025      2    3          0         34  72.634090   \n",
       "2025-02-04     76.206365  2025      2    4          1         35  78.714349   \n",
       "2025-02-05     75.510231  2025      2    5          2         36  76.206365   \n",
       "2025-02-06     70.689580  2025      2    6          3         37  75.510231   \n",
       "2025-02-07     70.860726  2025      2    7          4         38  70.689580   \n",
       "2025-02-08     73.258800  2025      2    8          5         39  70.860726   \n",
       "2025-02-09     83.245556  2025      2    9          6         40  73.258800   \n",
       "2025-02-10     72.525543  2025      2   10          0         41  83.245556   \n",
       "2025-02-11     76.368321  2025      2   11          1         42  72.525543   \n",
       "2025-02-12     64.342958  2025      2   12          2         43  76.368321   \n",
       "2025-02-13     79.439708  2025      2   13          3         44  64.342958   \n",
       "2025-02-14     87.832602  2025      2   14          4         45  79.439708   \n",
       "2025-02-15     72.356483  2025      2   15          5         46  87.832602   \n",
       "2025-02-16     93.366930  2025      2   16          6         47  72.356483   \n",
       "\n",
       "                lag_2      lag_3      lag_4      lag_5      lag_6      lag_7  \n",
       "dates                                                                         \n",
       "2025-01-08  56.516401  56.476699  54.484011  54.228554  49.720081  53.340505  \n",
       "2025-01-09  51.777505  56.516401  56.476699  54.484011  54.228554  49.720081  \n",
       "2025-01-10  56.945110  51.777505  56.516401  56.476699  54.484011  54.228554  \n",
       "2025-01-11  58.579044  56.945110  51.777505  56.516401  56.476699  54.484011  \n",
       "2025-01-12  49.515304  58.579044  56.945110  51.777505  56.516401  56.476699  \n",
       "2025-01-13  55.257779  49.515304  58.579044  56.945110  51.777505  56.516401  \n",
       "2025-01-14  60.323642  55.257779  49.515304  58.579044  56.945110  51.777505  \n",
       "2025-01-15  66.482406  60.323642  55.257779  49.515304  58.579044  56.945110  \n",
       "2025-01-16  62.710918  66.482406  60.323642  55.257779  49.515304  58.579044  \n",
       "2025-01-17  68.096187  62.710918  66.482406  60.323642  55.257779  49.515304  \n",
       "2025-01-18  57.887521  68.096187  62.710918  66.482406  60.323642  55.257779  \n",
       "2025-01-19  61.772449  57.887521  68.096187  62.710918  66.482406  60.323642  \n",
       "2025-01-20  65.189106  61.772449  57.887521  68.096187  62.710918  66.482406  \n",
       "2025-01-21  50.164237  65.189106  61.772449  57.887521  68.096187  62.710918  \n",
       "2025-01-22  69.982020  50.164237  65.189106  61.772449  57.887521  68.096187  \n",
       "2025-01-23  53.751714  69.982020  50.164237  65.189106  61.772449  57.887521  \n",
       "2025-01-24  68.665289  53.751714  69.982020  50.164237  65.189106  61.772449  \n",
       "2025-01-25  67.734951  68.665289  53.751714  69.982020  50.164237  65.189106  \n",
       "2025-01-26  53.218723  67.734951  68.665289  53.751714  69.982020  50.164237  \n",
       "2025-01-27  54.082786  53.218723  67.734951  68.665289  53.751714  69.982020  \n",
       "2025-01-28  73.297234  54.082786  53.218723  67.734951  68.665289  53.751714  \n",
       "2025-01-29  72.810314  73.297234  54.082786  53.218723  67.734951  68.665289  \n",
       "2025-01-30  62.929233  72.810314  73.297234  54.082786  53.218723  67.734951  \n",
       "2025-01-31  63.515795  62.929233  72.810314  73.297234  54.082786  53.218723  \n",
       "2025-02-01  71.074469  63.515795  62.929233  72.810314  73.297234  54.082786  \n",
       "2025-02-02  69.028422  71.074469  63.515795  62.929233  72.810314  73.297234  \n",
       "2025-02-03  74.939089  69.028422  71.074469  63.515795  62.929233  72.810314  \n",
       "2025-02-04  72.634090  74.939089  69.028422  71.074469  63.515795  62.929233  \n",
       "2025-02-05  78.714349  72.634090  74.939089  69.028422  71.074469  63.515795  \n",
       "2025-02-06  76.206365  78.714349  72.634090  74.939089  69.028422  71.074469  \n",
       "2025-02-07  75.510231  76.206365  78.714349  72.634090  74.939089  69.028422  \n",
       "2025-02-08  70.689580  75.510231  76.206365  78.714349  72.634090  74.939089  \n",
       "2025-02-09  70.860726  70.689580  75.510231  76.206365  78.714349  72.634090  \n",
       "2025-02-10  73.258800  70.860726  70.689580  75.510231  76.206365  78.714349  \n",
       "2025-02-11  83.245556  73.258800  70.860726  70.689580  75.510231  76.206365  \n",
       "2025-02-12  72.525543  83.245556  73.258800  70.860726  70.689580  75.510231  \n",
       "2025-02-13  76.368321  72.525543  83.245556  73.258800  70.860726  70.689580  \n",
       "2025-02-14  64.342958  76.368321  72.525543  83.245556  73.258800  70.860726  \n",
       "2025-02-15  79.439708  64.342958  76.368321  72.525543  83.245556  73.258800  \n",
       "2025-02-16  87.832602  79.439708  64.342958  76.368321  72.525543  83.245556  "
      ]
     },
     "execution_count": 559,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "df.head(40)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 560,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Ensure MinMaxScaler is imported\n",
    "from sklearn.preprocessing import MinMaxScaler\n",
    "\n",
    "def create_sequences(df, target_column, sequence_length):\n",
    "    data = df.values\n",
    "    target_idx = df.columns.get_loc(target_column)\n",
    "\n",
    "    sequences = []\n",
    "    targets = []\n",
    "    for i in range(len(df) - sequence_length):\n",
    "        seq = data[i:i + sequence_length]\n",
    "        target = data[i + sequence_length, target_idx]\n",
    "        sequences.append(seq)\n",
    "        targets.append(target)\n",
    "    return np.array(sequences), np.array(targets)\n",
    "\n",
    "def preprocess_lstm_sequences(\n",
    "    df, features, target_column, batch_size, sequence_length,\n",
    "    test_size=0.2, scale=True, scale_target=True\n",
    "):\n",
    "    df = df.copy()\n",
    "    feature_scaler = None\n",
    "    target_scaler = None\n",
    "\n",
    "    # Scale features\n",
    "    if scale:\n",
    "        feature_scaler = MinMaxScaler()\n",
    "        df[features] = feature_scaler.fit_transform(df[features])\n",
    "\n",
    "    # Scale target (only if it's not part of features)\n",
    "    if scale_target:\n",
    "        target_scaler = MinMaxScaler()\n",
    "        df[[target_column]] = target_scaler.fit_transform(df[[target_column]])\n",
    "\n",
    "    # Create sequences using only the relevant columns\n",
    "    used_cols = features + [target_column]  # Include target for sequencing\n",
    "    X, y = create_sequences(df[used_cols], target_column, sequence_length)\n",
    "\n",
    "    # Time-based split (no shuffling)\n",
    "    split_index = int(len(X) * (1 - test_size))\n",
    "    X_train, X_test = X[:split_index], X[split_index:]\n",
    "    y_train, y_test = y[:split_index], y[split_index:]\n",
    "\n",
    "    # Reshape for LSTM: (samples, sequence_length, num_features)\n",
    "    num_features = len(features)  # Exclude the target column\n",
    "    X_train = X_train[:, :, :num_features]\n",
    "    X_test = X_test[:, :, :num_features]\n",
    "\n",
    "    # Convert to tensors\n",
    "    X_tensor = torch.tensor(X_train, dtype=torch.float32)\n",
    "    y_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)\n",
    "    X_test = torch.tensor(X_test, dtype=torch.float32)\n",
    "    y_test = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)\n",
    "\n",
    "    # Create DataLoader\n",
    "    train_dataset = TensorDataset(X_tensor, y_tensor)\n",
    "    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)\n",
    "\n",
    "    return train_loader, X_test, y_test, X_tensor, y_tensor, feature_scaler, target_scaler\n",
    "\n",
    "# ----------------------------\n",
    "# Call Preprocessing\n",
    "# ----------------------------\n",
    "sequence_length = LAG_DAYS\n",
    "\n",
    "train_loader, X_test, y_test, X_tensor, y_tensor, feature_scaler, target_scaler = preprocess_lstm_sequences(\n",
    "    df=df,\n",
    "    features=FEATURES,\n",
    "    target_column=\"observations\",\n",
    "    batch_size=BATCH_SIZE,\n",
    "    sequence_length=LAG_DAYS,\n",
    "    test_size=TEST_SIZE,\n",
    "    scale=True,\n",
    ")\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 561,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "FEATURES: ['lag_1', 'lag_2', 'lag_3', 'lag_4', 'lag_5', 'lag_6', 'lag_7', 'year', 'month', 'day', 'dayofweek', 'dayofyear']\n"
     ]
    }
   ],
   "source": [
    "print(\"FEATURES:\", FEATURES)\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 562,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Raw X_train shape: torch.Size([788, 7, 12])\n",
      "Expected reshape size: (788, 7, 12)\n"
     ]
    }
   ],
   "source": [
    "print(\"Raw X_train shape:\", X_tensor.shape)\n",
    "print(\"Expected reshape size:\", (X_tensor.shape[0], sequence_length, len(FEATURES)))\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 563,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "(torch.Size([198, 7, 12]),\n",
       " torch.Size([198, 1]),\n",
       " torch.Size([788, 7, 12]),\n",
       " torch.Size([788, 1]))"
      ]
     },
     "execution_count": 563,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "X_test.shape, y_test.shape, X_tensor.shape, y_tensor.shape"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 564,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "LSTMModel(\n",
       "  (lstm): LSTM(12, 128, num_layers=3, batch_first=True)\n",
       "  (fc): Linear(in_features=128, out_features=1, bias=True)\n",
       ")"
      ]
     },
     "execution_count": 564,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# ----------------------------\n",
    "# Customizable LSTM\n",
    "# Model\n",
    "# ----------------------------\n",
    "class LSTMModel(nn.Module):\n",
    "    def __init__(self, input_size, hidden_size, output_size, num_layers=1):\n",
    "        super(LSTMModel, self).__init__()\n",
    "        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)\n",
    "        self.fc = nn.Linear(hidden_size, output_size)\n",
    "\n",
    "    def forward(self, x):\n",
    "        _, (hidden, _) = self.lstm(x)  # Only use the hidden state from the last time step\n",
    "        out = self.fc(hidden[-1])  # Pass the last hidden state through a fully connected layer\n",
    "        return out\n",
    "\n",
    "device = torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\") # check if cuda is available and use it if it is available otherwise use cpu\n",
    "\n",
    "\n",
    "model = LSTMModel(\n",
    "    input_size=len(FEATURES),  # input dimension is the number of features\n",
    "    hidden_size=HIDDEN_LAYERS[0],  # use the first hidden layer size as the hidden size\n",
    "    output_size=1,  # output size is 1 since we are predicting a single value\n",
    "    num_layers=len(HIDDEN_LAYERS)  # number of layers is the length of HIDDEN_LAYERS\n",
    ").to(device)\n",
    "\n",
    "model"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 565,
   "metadata": {},
   "outputs": [],
   "source": [
    "# ----------------------------\n",
    "# Loss & Optimizer\n",
    "# ----------------------------\n",
    "loss_fn = LOSS_FN() # create the loss function using the loss function specified in the hyperparameters\n",
    "optimizer = OPTIMIZER_FN(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY) # create the optimizer using the optimizer specified in the hyperparameters"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 566,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Epoch 000 | Train Loss: 0.2258 | Test Loss: 0.4174 | Best Test Loss: 0.4174\n",
      "Epoch 100 | Train Loss: 0.0091 | Test Loss: 0.0024 | Best Test Loss: 0.0024\n",
      "Epoch 200 | Train Loss: 0.0037 | Test Loss: 0.0041 | Best Test Loss: 0.0023\n",
      "Early stopping at epoch 204 — no improvement for 100 epochs.\n"
     ]
    },
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "/Users/jaytlinaskew/.local/lib/python3.9/site-packages/IPython/core/pylabtools.py:152: UserWarning:\n",
      "\n",
      "Glyph 128201 (\\N{CHART WITH DOWNWARDS TREND}) missing from font(s) Arial.\n",
      "\n"
     ]
    },
    {
     "data": {
      "image/png": "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",
      "text/plain": [
       "<Figure size 1000x500 with 1 Axes>"
      ]
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "# ----------------------------\n",
    "# Training Loop + Evaluation\n",
    "# ----------------------------\n",
    "\n",
    "train_losses = []\n",
    "test_losses = []\n",
    "\n",
    "BEST_LOSS = float(\"inf\")\n",
    "PATIENCE_COUNTER = 0\n",
    "\n",
    "for epoch in range(EPOCHS):\n",
    "    model.train()\n",
    "    running_loss = 0.0\n",
    "\n",
    "    for xb, yb in train_loader:\n",
    "        xb, yb = xb.to(device), yb.to(device)\n",
    "\n",
    "        # Reshape input to match LSTM expected input shape: (batch_size, sequence_length, input_size)\n",
    "        # Ensure input shape matches LSTM expected input shape: (batch_size, sequence_length, input_size)\n",
    "        # No need to unsqueeze here as the input is already in the correct shape\n",
    "\n",
    "        preds = model(xb)  # should be shape: (batch_size, 1)\n",
    "\n",
    "        # Ensure both preds and yb have the same shape\n",
    "        if preds.ndim == 1:\n",
    "            preds = preds.unsqueeze(1)  \n",
    "        if yb.ndim == 1:\n",
    "            yb = yb.unsqueeze(1)  \n",
    "\n",
    "        loss = loss_fn(preds, yb)\n",
    "\n",
    "        optimizer.zero_grad()\n",
    "        loss.backward()\n",
    "        optimizer.step()\n",
    "\n",
    "        running_loss += loss.item()\n",
    "\n",
    "    # Average training loss\n",
    "    avg_train_loss = running_loss / len(train_loader)\n",
    "    train_losses.append(avg_train_loss)\n",
    "\n",
    "    # ----------------------\n",
    "    # Evaluate on Test Data\n",
    "    # ----------------------\n",
    "    model.eval()\n",
    "    with torch.no_grad():\n",
    "        y_pred_test = model(X_test.to(device))\n",
    "        test_loss = loss_fn(y_pred_test, y_test.to(device)).item()\n",
    "        test_losses.append(test_loss)\n",
    "\n",
    "        # Early Stopping Logic\n",
    "        if test_loss < BEST_LOSS:\n",
    "            BEST_LOSS = test_loss\n",
    "            PATIENCE_COUNTER = 0\n",
    "            best_model_state = model.state_dict()\n",
    "        else:\n",
    "            PATIENCE_COUNTER += 1\n",
    "\n",
    "        if PATIENCE_COUNTER >= PATIENCE:\n",
    "            print(f\"Early stopping at epoch {epoch} — no improvement for {PATIENCE} epochs.\")\n",
    "            break\n",
    "\n",
    "    # Logging\n",
    "    if epoch % 100 == 0 or epoch == EPOCHS - 1:\n",
    "        print(f\"Epoch {epoch:03d} | Train Loss: {avg_train_loss:.4f} | Test Loss: {test_loss:.4f} | Best Test Loss: {BEST_LOSS:.4f}\")\n",
    "\n",
    "# Load the best model state after training\n",
    "model.load_state_dict(best_model_state)\n",
    "\n",
    "# ----------------------------\n",
    "# Plot Loss Curve\n",
    "# ----------------------------\n",
    "plt.rcParams['font.family'] = 'Arial'  # Set font family before plotting\n",
    "plt.figure(figsize=(10, 5))\n",
    "plt.plot(train_losses, label=\"Train Loss\")\n",
    "plt.plot(test_losses, label=\"Test Loss\")\n",
    "plt.title(\"📉 Loss Over Epochs\")\n",
    "plt.xlabel(\"Epoch\")\n",
    "plt.ylabel(\"Loss\")\n",
    "plt.legend()\n",
    "plt.grid(True)\n",
    "plt.show()\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 567,
   "metadata": {},
   "outputs": [],
   "source": [
    "model.eval()\n",
    "with torch.no_grad():\n",
    "    y_pred = model(X_test.to(device)).cpu().numpy()\n",
    "    y_true = y_test.cpu().numpy()\n",
    "    y_pred = target_scaler.inverse_transform(y_pred)\n",
    "    y_true = target_scaler.inverse_transform(y_true)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 568,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Drifted prediction at step 6: 1.0037211179733276\n",
      "Drifted prediction at step 7: 1.0274720191955566\n",
      "Drifted prediction at step 8: 1.0465525388717651\n",
      "Drifted prediction at step 9: 1.0649811029434204\n"
     ]
    }
   ],
   "source": [
    "def forecast(model, initial_sequence, steps):\n",
    "    model.eval()\n",
    "    predictions = []\n",
    "    current_sequence = initial_sequence.clone()\n",
    "\n",
    "    for _ in range(steps):\n",
    "        with torch.no_grad():\n",
    "            # Make a prediction\n",
    "            pred = model(current_sequence.unsqueeze(0))  # Add batch dimension\n",
    "            pred = pred.squeeze(0)  # Remove batch dimension from the output\n",
    "            if pred[0].item() > 1.0 or pred[0].item() < 0.0:\n",
    "                print(f\"Drifted prediction at step {_}: {pred[0].item()}\")\n",
    "            pred = torch.clamp(pred, min=0.0, max=1.0)  # ensure within scaler range\n",
    "            \n",
    "\n",
    "            # Append the prediction to the list\n",
    "            predictions.append(pred.item())\n",
    "\n",
    "            # Update the sequence: remove the oldest value and append the new prediction\n",
    "            pred = pred.repeat(current_sequence.shape[1]).unsqueeze(0)  # Repeat pred to match the number of features\n",
    "            current_sequence = torch.cat((current_sequence[1:], pred), dim=0)\n",
    "\n",
    "    return predictions\n",
    "\n",
    "\n",
    "# Use last known sequence from test set\n",
    "initial_sequence = X_test[-1].squeeze()  # shape: (LAG_DAYS,)\n",
    "future_predictions = forecast(model, initial_sequence, steps=10)\n",
    "future_predictions = target_scaler.inverse_transform(\n",
    "    np.array(future_predictions).reshape(-1, 1)\n",
    ").flatten()\n",
    "\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 569,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "y_pred shape: (198, 1)\n",
      "Sample predictions: [153.81761 154.33897 154.8094  154.71552 154.58427]\n"
     ]
    },
    {
     "name": "stderr",
     "output_type": "stream",
     "text": [
      "/Users/jaytlinaskew/opt/anaconda3/lib/python3.9/site-packages/_plotly_utils/basevalidators.py:106: FutureWarning:\n",
      "\n",
      "The behavior of DatetimeProperties.to_pydatetime is deprecated, in a future version this will return a Series containing python datetime objects instead of an ndarray. To retain the old behavior, call `np.array` on the result\n",
      "\n"
     ]
    },
    {
     "data": {
      "application/vnd.plotly.v1+json": {
       "config": {
        "plotlyServerURL": "https://plot.ly"
       },
       "data": [
        {
         "mode": "lines",
         "name": "Recent Observations",
         "type": "scatter",
         "x": [
          "2027-08-29T00:00:00",
          "2027-08-30T00:00:00",
          "2027-08-31T00:00:00",
          "2027-09-01T00:00:00",
          "2027-09-02T00:00:00",
          "2027-09-03T00:00:00",
          "2027-09-04T00:00:00",
          "2027-09-05T00:00:00",
          "2027-09-06T00:00:00",
          "2027-09-07T00:00:00",
          "2027-09-08T00:00:00",
          "2027-09-09T00:00:00",
          "2027-09-10T00:00:00",
          "2027-09-11T00:00:00",
          "2027-09-12T00:00:00",
          "2027-09-13T00:00:00",
          "2027-09-14T00:00:00",
          "2027-09-15T00:00:00",
          "2027-09-16T00:00:00",
          "2027-09-17T00:00:00",
          "2027-09-18T00:00:00",
          "2027-09-19T00:00:00",
          "2027-09-20T00:00:00",
          "2027-09-21T00:00:00",
          "2027-09-22T00:00:00",
          "2027-09-23T00:00:00",
          "2027-09-24T00:00:00",
          "2027-09-25T00:00:00",
          "2027-09-26T00:00:00",
          "2027-09-27T00:00:00"
         ],
         "y": [
          129.956787109375,
          132.4027862548828,
          138.11781311035156,
          126.15837860107422,
          136.14064025878906,
          130.38478088378906,
          137.84967041015625,
          133.23040771484375,
          124.79890441894531,
          138.7916259765625,
          139.37771606445312,
          135.30860900878906,
          135.64784240722656,
          132.92164611816406,
          143.98611450195312,
          145.17677307128906,
          137.01832580566406,
          139.3643798828125,
          142.4004669189453,
          154.726318359375,
          146.7546844482422,
          139.9708709716797,
          146.86734008789062,
          139.1268768310547,
          150.26336669921875,
          155.71527099609375,
          156.4014129638672,
          152.34242248535156,
          146.41680908203125,
          143.49549865722656
         ]
        },
        {
         "mode": "lines+markers",
         "name": "Forecast",
         "type": "scatter",
         "x": [
          "2027-09-28T00:00:00",
          "2027-09-29T00:00:00",
          "2027-09-30T00:00:00",
          "2027-10-01T00:00:00",
          "2027-10-02T00:00:00",
          "2027-10-03T00:00:00",
          "2027-10-04T00:00:00",
          "2027-10-05T00:00:00",
          "2027-10-06T00:00:00",
          "2027-10-07T00:00:00"
         ],
         "y": [
          155.0365829202872,
          156.78265678769753,
          158.7813168678667,
          161.09476156754008,
          163.51408873723298,
          165.9841223709616,
          168.40764177525548,
          168.40764177525548,
          168.40764177525548,
          168.40764177525548
         ]
        }
       ],
       "layout": {
        "template": {
         "data": {
          "bar": [
           {
            "error_x": {
             "color": "#2a3f5f"
            },
            "error_y": {
             "color": "#2a3f5f"
            },
            "marker": {
             "line": {
              "color": "white",
              "width": 0.5
             },
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "bar"
           }
          ],
          "barpolar": [
           {
            "marker": {
             "line": {
              "color": "white",
              "width": 0.5
             },
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "barpolar"
           }
          ],
          "carpet": [
           {
            "aaxis": {
             "endlinecolor": "#2a3f5f",
             "gridcolor": "#C8D4E3",
             "linecolor": "#C8D4E3",
             "minorgridcolor": "#C8D4E3",
             "startlinecolor": "#2a3f5f"
            },
            "baxis": {
             "endlinecolor": "#2a3f5f",
             "gridcolor": "#C8D4E3",
             "linecolor": "#C8D4E3",
             "minorgridcolor": "#C8D4E3",
             "startlinecolor": "#2a3f5f"
            },
            "type": "carpet"
           }
          ],
          "choropleth": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "choropleth"
           }
          ],
          "contour": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "contour"
           }
          ],
          "contourcarpet": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "contourcarpet"
           }
          ],
          "heatmap": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "heatmap"
           }
          ],
          "heatmapgl": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "heatmapgl"
           }
          ],
          "histogram": [
           {
            "marker": {
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "histogram"
           }
          ],
          "histogram2d": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "histogram2d"
           }
          ],
          "histogram2dcontour": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "histogram2dcontour"
           }
          ],
          "mesh3d": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "mesh3d"
           }
          ],
          "parcoords": [
           {
            "line": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "parcoords"
           }
          ],
          "pie": [
           {
            "automargin": true,
            "type": "pie"
           }
          ],
          "scatter": [
           {
            "fillpattern": {
             "fillmode": "overlay",
             "size": 10,
             "solidity": 0.2
            },
            "type": "scatter"
           }
          ],
          "scatter3d": [
           {
            "line": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatter3d"
           }
          ],
          "scattercarpet": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattercarpet"
           }
          ],
          "scattergeo": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattergeo"
           }
          ],
          "scattergl": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattergl"
           }
          ],
          "scattermapbox": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattermapbox"
           }
          ],
          "scatterpolar": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterpolar"
           }
          ],
          "scatterpolargl": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterpolargl"
           }
          ],
          "scatterternary": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterternary"
           }
          ],
          "surface": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "surface"
           }
          ],
          "table": [
           {
            "cells": {
             "fill": {
              "color": "#EBF0F8"
             },
             "line": {
              "color": "white"
             }
            },
            "header": {
             "fill": {
              "color": "#C8D4E3"
             },
             "line": {
              "color": "white"
             }
            },
            "type": "table"
           }
          ]
         },
         "layout": {
          "annotationdefaults": {
           "arrowcolor": "#2a3f5f",
           "arrowhead": 0,
           "arrowwidth": 1
          },
          "autotypenumbers": "strict",
          "coloraxis": {
           "colorbar": {
            "outlinewidth": 0,
            "ticks": ""
           }
          },
          "colorscale": {
           "diverging": [
            [
             0,
             "#8e0152"
            ],
            [
             0.1,
             "#c51b7d"
            ],
            [
             0.2,
             "#de77ae"
            ],
            [
             0.3,
             "#f1b6da"
            ],
            [
             0.4,
             "#fde0ef"
            ],
            [
             0.5,
             "#f7f7f7"
            ],
            [
             0.6,
             "#e6f5d0"
            ],
            [
             0.7,
             "#b8e186"
            ],
            [
             0.8,
             "#7fbc41"
            ],
            [
             0.9,
             "#4d9221"
            ],
            [
             1,
             "#276419"
            ]
           ],
           "sequential": [
            [
             0,
             "#0d0887"
            ],
            [
             0.1111111111111111,
             "#46039f"
            ],
            [
             0.2222222222222222,
             "#7201a8"
            ],
            [
             0.3333333333333333,
             "#9c179e"
            ],
            [
             0.4444444444444444,
             "#bd3786"
            ],
            [
             0.5555555555555556,
             "#d8576b"
            ],
            [
             0.6666666666666666,
             "#ed7953"
            ],
            [
             0.7777777777777778,
             "#fb9f3a"
            ],
            [
             0.8888888888888888,
             "#fdca26"
            ],
            [
             1,
             "#f0f921"
            ]
           ],
           "sequentialminus": [
            [
             0,
             "#0d0887"
            ],
            [
             0.1111111111111111,
             "#46039f"
            ],
            [
             0.2222222222222222,
             "#7201a8"
            ],
            [
             0.3333333333333333,
             "#9c179e"
            ],
            [
             0.4444444444444444,
             "#bd3786"
            ],
            [
             0.5555555555555556,
             "#d8576b"
            ],
            [
             0.6666666666666666,
             "#ed7953"
            ],
            [
             0.7777777777777778,
             "#fb9f3a"
            ],
            [
             0.8888888888888888,
             "#fdca26"
            ],
            [
             1,
             "#f0f921"
            ]
           ]
          },
          "colorway": [
           "#636efa",
           "#EF553B",
           "#00cc96",
           "#ab63fa",
           "#FFA15A",
           "#19d3f3",
           "#FF6692",
           "#B6E880",
           "#FF97FF",
           "#FECB52"
          ],
          "font": {
           "color": "#2a3f5f"
          },
          "geo": {
           "bgcolor": "white",
           "lakecolor": "white",
           "landcolor": "white",
           "showlakes": true,
           "showland": true,
           "subunitcolor": "#C8D4E3"
          },
          "hoverlabel": {
           "align": "left"
          },
          "hovermode": "closest",
          "mapbox": {
           "style": "light"
          },
          "paper_bgcolor": "white",
          "plot_bgcolor": "white",
          "polar": {
           "angularaxis": {
            "gridcolor": "#EBF0F8",
            "linecolor": "#EBF0F8",
            "ticks": ""
           },
           "bgcolor": "white",
           "radialaxis": {
            "gridcolor": "#EBF0F8",
            "linecolor": "#EBF0F8",
            "ticks": ""
           }
          },
          "scene": {
           "xaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           },
           "yaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           },
           "zaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           }
          },
          "shapedefaults": {
           "line": {
            "color": "#2a3f5f"
           }
          },
          "ternary": {
           "aaxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           },
           "baxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           },
           "bgcolor": "white",
           "caxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           }
          },
          "title": {
           "x": 0.05
          },
          "xaxis": {
           "automargin": true,
           "gridcolor": "#EBF0F8",
           "linecolor": "#EBF0F8",
           "ticks": "",
           "title": {
            "standoff": 15
           },
           "zerolinecolor": "#EBF0F8",
           "zerolinewidth": 2
          },
          "yaxis": {
           "automargin": true,
           "gridcolor": "#EBF0F8",
           "linecolor": "#EBF0F8",
           "ticks": "",
           "title": {
            "standoff": 15
           },
           "zerolinecolor": "#EBF0F8",
           "zerolinewidth": 2
          }
         }
        },
        "title": {
         "text": "Last Observations + 10-Step Forecast"
        },
        "xaxis": {
         "title": {
          "text": "Date"
         }
        },
        "yaxis": {
         "title": {
          "text": "Observations"
         }
        }
       }
      }
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "print(\"y_pred shape:\", y_pred.shape)\n",
    "print(\"Sample predictions:\", y_pred[:5].flatten())\n",
    "\n",
    "# Reset index to access 'dates' as a column\n",
    "df_reset = df.reset_index()\n",
    "\n",
    "# Get the last date in your dataset\n",
    "last_date = df_reset[\"dates\"].max()\n",
    "\n",
    "# Create future dates matching forecast steps\n",
    "future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=len(future_predictions), freq=\"D\")\n",
    "\n",
    "# Get last N true points\n",
    "N = 30\n",
    "recent_dates = df_reset[\"dates\"].iloc[-N:]\n",
    "recent_values = target_scaler.inverse_transform(y_test.cpu().numpy())[-N:]  # if scaled\n",
    "\n",
    "\n",
    "# Combine with forecast\n",
    "fig = go.Figure()\n",
    "fig.add_trace(go.Scatter(x=recent_dates, y=recent_values.flatten(), mode='lines', name='Recent Observations'))\n",
    "fig.add_trace(go.Scatter(x=future_dates, y=future_predictions, mode='lines+markers', name='Forecast'))\n",
    "\n",
    "fig.update_layout(\n",
    "    title=\"Last Observations + 10-Step Forecast\",\n",
    "    xaxis_title=\"Date\",\n",
    "    yaxis_title=\"Observations\",\n",
    "    template=\"plotly_white\"\n",
    ")\n",
    "fig.show()\n",
    "\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 570,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "    recent_dates  recent_values future_dates  future_predictions\n",
      "983   2027-09-18     146.754684   2027-09-28          155.036583\n",
      "984   2027-09-19     139.970871   2027-09-29          156.782657\n",
      "985   2027-09-20     146.867340   2027-09-30          158.781317\n",
      "986   2027-09-21     139.126877   2027-10-01          161.094762\n",
      "987   2027-09-22     150.263367   2027-10-02          163.514089\n",
      "988   2027-09-23     155.715271   2027-10-03          165.984122\n",
      "989   2027-09-24     156.401413   2027-10-04          168.407642\n",
      "990   2027-09-25     152.342422   2027-10-05          168.407642\n",
      "991   2027-09-26     146.416809   2027-10-06          168.407642\n",
      "992   2027-09-27     143.495499   2027-10-07          168.407642\n"
     ]
    }
   ],
   "source": [
    "# actual vs predicted\n",
    "# Ensure all arrays have the same length\n",
    "min_length = min(len(recent_dates), len(recent_values.flatten()), len(future_dates), len(future_predictions))\n",
    "\n",
    "data = pd.DataFrame({\n",
    "\t\"recent_dates\": recent_dates[-min_length:],  # Trim to match the minimum length\n",
    "\t\"recent_values\": recent_values.flatten()[-min_length:],  # Trim to match the minimum length\n",
    "\t\"future_dates\": future_dates[:min_length],  # Trim to match the minimum length\n",
    "\t\"future_predictions\": future_predictions[:min_length]  # Trim to match the minimum length\n",
    "})\n",
    "print(data.head(10))"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 571,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "   Test Metric         Test Value\n",
      "0          MAE           7.388719\n",
      "1          MSE          77.926788\n",
      "2         RMSE           8.827615\n",
      "3           R2            0.52128\n",
      "4         MAPE           6.055912\n",
      "5  Performance  Needs Improvement\n"
     ]
    }
   ],
   "source": [
    "#test prediction accuracy\n",
    "from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score\n",
    "# Ensure y_true and y_pred have the same length\n",
    "min_length = min(len(y_true), len(y_pred))\n",
    "\n",
    "# Calculate metrics\n",
    "mae = mean_absolute_error(y_true[:min_length].flatten(), y_pred[:min_length].flatten())\n",
    "mse = mean_squared_error(y_true[:min_length].flatten(), y_pred[:min_length].flatten())\n",
    "rmse = np.sqrt(mse)\n",
    "r2 = r2_score(y_true[:min_length].flatten(), y_pred[:min_length].flatten())\n",
    "mape = np.mean(np.abs((y_true[:min_length] - y_pred[:min_length]) / y_true[:min_length])) * 100\n",
    "\n",
    "\n",
    "# Determine if the model is performing well\n",
    "is_low_mae = mae < 10  # Example threshold for low MAE\n",
    "is_high_r2 = r2 > 0.8  # Example threshold for high R2 score\n",
    "is_low_mape = mape < 10  # Example threshold for low MAPE\n",
    "performance = \"Good\" if is_low_mae and is_high_r2 and is_low_mape else \"Needs Improvement\"\n",
    "\n",
    "# Print metrics in a dataframe\n",
    "metrics_df = pd.DataFrame({\n",
    "    \"Test Metric\": [\"MAE\", \"MSE\", \"RMSE\", \"R2\", \"MAPE\",\"Performance\"],\n",
    "    \"Test Value\": [mae, mse, rmse, r2, mape, performance]\n",
    "})\n",
    "print(metrics_df)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 572,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "  Forecast Metric     Forecast Value\n",
      "0             MAE             15.747\n",
      "1             MSE            276.324\n",
      "2            RMSE             16.623\n",
      "3              R2            -7.5757\n",
      "4            MAPE            10.7571\n",
      "5     Performance  Needs Improvement\n"
     ]
    },
    {
     "data": {
      "application/vnd.plotly.v1+json": {
       "config": {
        "plotlyServerURL": "https://plot.ly"
       },
       "data": [
        {
         "line": {
          "color": "blue"
         },
         "marker": {
          "size": 8,
          "symbol": "circle"
         },
         "mode": "lines+markers",
         "name": "True Future",
         "type": "scatter",
         "y": [
          146.7546844482422,
          139.9708709716797,
          146.86734008789062,
          139.1268768310547,
          150.26336669921875,
          155.71527099609375,
          156.4014129638672,
          152.34242248535156,
          146.41680908203125,
          143.49549865722656
         ]
        },
        {
         "line": {
          "color": "red"
         },
         "marker": {
          "size": 8,
          "symbol": "x"
         },
         "mode": "lines+markers",
         "name": "Forecast",
         "type": "scatter",
         "y": [
          155.0365829202872,
          156.78265678769753,
          158.7813168678667,
          161.09476156754008,
          163.51408873723298,
          165.9841223709616,
          168.40764177525548,
          168.40764177525548,
          168.40764177525548,
          168.40764177525548
         ]
        }
       ],
       "layout": {
        "legend": {
         "title": {
          "text": "Legend"
         }
        },
        "template": {
         "data": {
          "bar": [
           {
            "error_x": {
             "color": "#2a3f5f"
            },
            "error_y": {
             "color": "#2a3f5f"
            },
            "marker": {
             "line": {
              "color": "white",
              "width": 0.5
             },
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "bar"
           }
          ],
          "barpolar": [
           {
            "marker": {
             "line": {
              "color": "white",
              "width": 0.5
             },
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "barpolar"
           }
          ],
          "carpet": [
           {
            "aaxis": {
             "endlinecolor": "#2a3f5f",
             "gridcolor": "#C8D4E3",
             "linecolor": "#C8D4E3",
             "minorgridcolor": "#C8D4E3",
             "startlinecolor": "#2a3f5f"
            },
            "baxis": {
             "endlinecolor": "#2a3f5f",
             "gridcolor": "#C8D4E3",
             "linecolor": "#C8D4E3",
             "minorgridcolor": "#C8D4E3",
             "startlinecolor": "#2a3f5f"
            },
            "type": "carpet"
           }
          ],
          "choropleth": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "choropleth"
           }
          ],
          "contour": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "contour"
           }
          ],
          "contourcarpet": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "contourcarpet"
           }
          ],
          "heatmap": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "heatmap"
           }
          ],
          "heatmapgl": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "heatmapgl"
           }
          ],
          "histogram": [
           {
            "marker": {
             "pattern": {
              "fillmode": "overlay",
              "size": 10,
              "solidity": 0.2
             }
            },
            "type": "histogram"
           }
          ],
          "histogram2d": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "histogram2d"
           }
          ],
          "histogram2dcontour": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "histogram2dcontour"
           }
          ],
          "mesh3d": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "type": "mesh3d"
           }
          ],
          "parcoords": [
           {
            "line": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "parcoords"
           }
          ],
          "pie": [
           {
            "automargin": true,
            "type": "pie"
           }
          ],
          "scatter": [
           {
            "fillpattern": {
             "fillmode": "overlay",
             "size": 10,
             "solidity": 0.2
            },
            "type": "scatter"
           }
          ],
          "scatter3d": [
           {
            "line": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatter3d"
           }
          ],
          "scattercarpet": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattercarpet"
           }
          ],
          "scattergeo": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattergeo"
           }
          ],
          "scattergl": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattergl"
           }
          ],
          "scattermapbox": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scattermapbox"
           }
          ],
          "scatterpolar": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterpolar"
           }
          ],
          "scatterpolargl": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterpolargl"
           }
          ],
          "scatterternary": [
           {
            "marker": {
             "colorbar": {
              "outlinewidth": 0,
              "ticks": ""
             }
            },
            "type": "scatterternary"
           }
          ],
          "surface": [
           {
            "colorbar": {
             "outlinewidth": 0,
             "ticks": ""
            },
            "colorscale": [
             [
              0,
              "#0d0887"
             ],
             [
              0.1111111111111111,
              "#46039f"
             ],
             [
              0.2222222222222222,
              "#7201a8"
             ],
             [
              0.3333333333333333,
              "#9c179e"
             ],
             [
              0.4444444444444444,
              "#bd3786"
             ],
             [
              0.5555555555555556,
              "#d8576b"
             ],
             [
              0.6666666666666666,
              "#ed7953"
             ],
             [
              0.7777777777777778,
              "#fb9f3a"
             ],
             [
              0.8888888888888888,
              "#fdca26"
             ],
             [
              1,
              "#f0f921"
             ]
            ],
            "type": "surface"
           }
          ],
          "table": [
           {
            "cells": {
             "fill": {
              "color": "#EBF0F8"
             },
             "line": {
              "color": "white"
             }
            },
            "header": {
             "fill": {
              "color": "#C8D4E3"
             },
             "line": {
              "color": "white"
             }
            },
            "type": "table"
           }
          ]
         },
         "layout": {
          "annotationdefaults": {
           "arrowcolor": "#2a3f5f",
           "arrowhead": 0,
           "arrowwidth": 1
          },
          "autotypenumbers": "strict",
          "coloraxis": {
           "colorbar": {
            "outlinewidth": 0,
            "ticks": ""
           }
          },
          "colorscale": {
           "diverging": [
            [
             0,
             "#8e0152"
            ],
            [
             0.1,
             "#c51b7d"
            ],
            [
             0.2,
             "#de77ae"
            ],
            [
             0.3,
             "#f1b6da"
            ],
            [
             0.4,
             "#fde0ef"
            ],
            [
             0.5,
             "#f7f7f7"
            ],
            [
             0.6,
             "#e6f5d0"
            ],
            [
             0.7,
             "#b8e186"
            ],
            [
             0.8,
             "#7fbc41"
            ],
            [
             0.9,
             "#4d9221"
            ],
            [
             1,
             "#276419"
            ]
           ],
           "sequential": [
            [
             0,
             "#0d0887"
            ],
            [
             0.1111111111111111,
             "#46039f"
            ],
            [
             0.2222222222222222,
             "#7201a8"
            ],
            [
             0.3333333333333333,
             "#9c179e"
            ],
            [
             0.4444444444444444,
             "#bd3786"
            ],
            [
             0.5555555555555556,
             "#d8576b"
            ],
            [
             0.6666666666666666,
             "#ed7953"
            ],
            [
             0.7777777777777778,
             "#fb9f3a"
            ],
            [
             0.8888888888888888,
             "#fdca26"
            ],
            [
             1,
             "#f0f921"
            ]
           ],
           "sequentialminus": [
            [
             0,
             "#0d0887"
            ],
            [
             0.1111111111111111,
             "#46039f"
            ],
            [
             0.2222222222222222,
             "#7201a8"
            ],
            [
             0.3333333333333333,
             "#9c179e"
            ],
            [
             0.4444444444444444,
             "#bd3786"
            ],
            [
             0.5555555555555556,
             "#d8576b"
            ],
            [
             0.6666666666666666,
             "#ed7953"
            ],
            [
             0.7777777777777778,
             "#fb9f3a"
            ],
            [
             0.8888888888888888,
             "#fdca26"
            ],
            [
             1,
             "#f0f921"
            ]
           ]
          },
          "colorway": [
           "#636efa",
           "#EF553B",
           "#00cc96",
           "#ab63fa",
           "#FFA15A",
           "#19d3f3",
           "#FF6692",
           "#B6E880",
           "#FF97FF",
           "#FECB52"
          ],
          "font": {
           "color": "#2a3f5f"
          },
          "geo": {
           "bgcolor": "white",
           "lakecolor": "white",
           "landcolor": "white",
           "showlakes": true,
           "showland": true,
           "subunitcolor": "#C8D4E3"
          },
          "hoverlabel": {
           "align": "left"
          },
          "hovermode": "closest",
          "mapbox": {
           "style": "light"
          },
          "paper_bgcolor": "white",
          "plot_bgcolor": "white",
          "polar": {
           "angularaxis": {
            "gridcolor": "#EBF0F8",
            "linecolor": "#EBF0F8",
            "ticks": ""
           },
           "bgcolor": "white",
           "radialaxis": {
            "gridcolor": "#EBF0F8",
            "linecolor": "#EBF0F8",
            "ticks": ""
           }
          },
          "scene": {
           "xaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           },
           "yaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           },
           "zaxis": {
            "backgroundcolor": "white",
            "gridcolor": "#DFE8F3",
            "gridwidth": 2,
            "linecolor": "#EBF0F8",
            "showbackground": true,
            "ticks": "",
            "zerolinecolor": "#EBF0F8"
           }
          },
          "shapedefaults": {
           "line": {
            "color": "#2a3f5f"
           }
          },
          "ternary": {
           "aaxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           },
           "baxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           },
           "bgcolor": "white",
           "caxis": {
            "gridcolor": "#DFE8F3",
            "linecolor": "#A2B1C6",
            "ticks": ""
           }
          },
          "title": {
           "x": 0.05
          },
          "xaxis": {
           "automargin": true,
           "gridcolor": "#EBF0F8",
           "linecolor": "#EBF0F8",
           "ticks": "",
           "title": {
            "standoff": 15
           },
           "zerolinecolor": "#EBF0F8",
           "zerolinewidth": 2
          },
          "yaxis": {
           "automargin": true,
           "gridcolor": "#EBF0F8",
           "linecolor": "#EBF0F8",
           "ticks": "",
           "title": {
            "standoff": 15
           },
           "zerolinecolor": "#EBF0F8",
           "zerolinewidth": 2
          }
         }
        },
        "title": {
         "text": "📈 Interactive Forecast vs. Actual (Next N Days)"
        },
        "xaxis": {
         "showgrid": true,
         "title": {
          "text": "Day"
         }
        },
        "yaxis": {
         "showgrid": true,
         "title": {
          "text": "Observations"
         }
        }
       }
      }
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "# Evaluate on a true forecast horizon\n",
    "# Use y_true for the true future values and slice it to match the forecast horizon\n",
    "true_future = y_true.flatten()[-len(future_predictions):]  # Extract the true future values\n",
    "mae_forecast = mean_absolute_error(true_future[:N], future_predictions[:N]) # N = 10\n",
    "mse_forecast = mean_squared_error(true_future[:N], future_predictions[:N])\n",
    "rmse_forecast = np.sqrt(mse_forecast)\n",
    "r2_forecast = r2_score(true_future[:N], future_predictions[:N])\n",
    "mape_forecast = np.mean(np.abs((true_future[:N] - future_predictions[:N]) / true_future[:N])) * 100\n",
    "# Print forecast metrics\n",
    "forecast_metrics_df = pd.DataFrame({\n",
    "    \"Forecast Metric\": [\"MAE\", \"MSE\", \"RMSE\", \"R2\", \"MAPE\"],\n",
    "    \"Forecast Value\": [mae_forecast, mse_forecast, rmse_forecast, r2_forecast, mape_forecast]\n",
    "})\n",
    "forecast_metrics_df[\"Forecast Value\"] = forecast_metrics_df[\"Forecast Value\"].apply(lambda x: round(x, 4))\n",
    "forecast_quality = \"Good\" if mae_forecast < 10 and mape_forecast < 10 else \"Needs Improvement\"\n",
    "forecast_metrics_df.loc[len(forecast_metrics_df)] = [\"Performance\", forecast_quality]\n",
    "print(forecast_metrics_df)\n",
    "\n",
    "import plotly.graph_objects as go\n",
    "\n",
    "# Create an interactive plot using Plotly\n",
    "fig = go.Figure()\n",
    "\n",
    "# Add true future values\n",
    "fig.add_trace(go.Scatter(\n",
    "    y=true_future[:N],\n",
    "    mode='lines+markers',\n",
    "    name='True Future',\n",
    "    marker=dict(symbol='circle', size=8),\n",
    "    line=dict(color='blue')\n",
    "))\n",
    "\n",
    "# Add forecasted values\n",
    "fig.add_trace(go.Scatter(\n",
    "    y=future_predictions[:N],\n",
    "    mode='lines+markers',\n",
    "    name='Forecast',\n",
    "    marker=dict(symbol='x', size=8),\n",
    "    line=dict(color='red')\n",
    "))\n",
    "\n",
    "# Update layout for better interactivity\n",
    "fig.update_layout(\n",
    "    title=\"📈 Interactive Forecast vs. Actual (Next N Days)\",\n",
    "    xaxis_title=\"Day\",\n",
    "    yaxis_title=\"Observations\",\n",
    "    xaxis=dict(showgrid=True),\n",
    "    yaxis=dict(showgrid=True),\n",
    "    legend_title=\"Legend\",\n",
    "    template=\"plotly_white\"\n",
    ")\n",
    "\n",
    "# Show the interactive plot\n",
    "fig.show()\n"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "#save the dataframe to a csv file\n",
    "params.to_csv(\"/Users/jaytlinaskew/GitRepository/TimeSeries-Analysis/data/Performance_Data/Neural_Networks/Regression/NextObserved.csv\", index=False)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "base",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.9.16"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
