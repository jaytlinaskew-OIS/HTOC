{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 65,
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
   "execution_count": 66,
   "metadata": {},
   "outputs": [],
   "source": [
    "# ------------------------------\n",
    "# HYPERPARAMETERS & SETTINGS\n",
    "# ------------------------------\n",
    "\n",
    "# Model & Training Config\n",
    "FEATURES = [\n",
    "     \"observations\", \"year\", \"month\", \"day\", \"hour\"\n",
    "]\n",
    "HIDDEN_LAYERS = [32, 16]  # Increase model complexity with more layers\n",
    "ACTIVATION = nn.ReLU\n",
    "DROPOUT = 0.2  # Increase dropout rate to reduce overfitting\n",
    "LOSS_FN = nn.MSELoss\n",
    "OPTIMIZER_FN = optim.Adam\n",
    "LEARNING_RATE = 0.0001  # Reduce learning rate for more stable training\n",
    "WEIGHT_DECAY = 0.001  # Increase weight decay for regularization\n",
    "EPOCHS = 6000  # Reduce epochs to prevent overfitting\n",
    "BATCH_SIZE = 32  # Increase batch size for faster training\n",
    "SEED = 42\n",
    "TEST_SIZE = 0.2\n",
    "N_SAMPLES = 300  # Simulate data for 30 days\n",
    "BEST_LOSS = float('inf')  # Start with a very high loss\n",
    "PATIENCE = 100  # Reduce patience to stop earlier if no improvement\n",
    "PATIENCE_COUNTER = 0 # Counter for early stopping\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 67,
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
          121.22898290585896,
          202.41151974816643,
          114.7669079933002,
          42.27183249036024,
          126.13001891877907,
          105.53534077157317,
          37.35343166762044,
          149.2016916658962,
          147.25667347765005,
          85.42842443583717,
          96.29107501938887,
          140.82472415243186,
          116.7653721467415,
          130.14000494092093,
          175.73237624573545,
          149.27171087343126,
          160.53206281931594,
          56.851527753141355,
          16.53485047932979,
          115.56398794323472,
          179.14093744130204,
          44.542612212880115,
          150.73180925851182,
          43.85317379728837,
          171.16142563798866,
          78.53725105945527,
          41.58208718446,
          96.57029702169376,
          71.57787360348283,
          83.60784526368235,
          199.83051243175277,
          44.53802052034903,
          180.2233063204291,
          60.62174960084877,
          132.1503526720866,
          79.1378595091221,
          88.15047686306048,
          188.52731490654722,
          75.70890510693167,
          165.355656401806,
          49.54001763493203,
          98.51391251305797,
          182.84730755359655,
          44.589692204932675,
          143.2717478546243,
          105.63181393259991,
          74.14636452170896,
          33.81874139386323,
          51.146585666735085,
          90.32734807408252,
          78.86260190374513,
          132.87284128810347,
          98.28068134210567,
          121.88950596967366,
          130.64280019095463,
          180.22255222070694,
          19.846962907400318,
          200.79597748934677,
          46.69633368282864,
          102.16458589581976,
          183.45571839903815,
          62.483996523941826,
          144.43944089325325,
          157.3391902231801,
          0.7485741334239293,
          154.86454314769426,
          66.38213535231613,
          133.52433334796223,
          15.074792615672994,
          71.85263558533102,
          170.04987278980457,
          71.65755194170121,
          168.99703592944223,
          29.654987641590516,
          109.25054688839043,
          60.46670767426288,
          51.65454240281097,
          63.049817109609556,
          88.39116045664954,
          139.17861947054777,
          93.22156197012633,
          53.32465260551147,
          157.80630034045987,
          138.15765927133748,
          72.66911149186623,
          168.9233053438122,
          38.43819428146229,
          71.74634053429337,
          74.73069528421917,
          107.404746439382,
          57.58732659930927,
          17.756123586657104,
          104.4743184860684,
          135.5221681803515,
          171.32411303931636,
          67.69858622039368,
          153.59955513303015,
          101.30740577286092,
          169.41273289066115,
          167.64137848820562,
          193.6316375215496,
          52.10233061019587,
          132.18491348952048,
          28.62103474263271,
          61.9905969557347,
          40.99783122841205,
          154.6980208499002,
          87.14686403138239,
          32.13517345251248,
          187.62130674521046,
          67.86016816145352,
          54.62184501173151,
          191.33033374656267,
          61.47912200477498,
          54.482149049644164,
          123.88317206484577,
          193.80991867735034,
          116.77300480179406,
          51.918777496427246,
          115.06999065341168,
          188.10635243055788,
          158.49602097021025,
          23.570154859650472,
          17.07090404739346,
          169.9959987543325,
          125.07299520876609,
          54.1286211883896,
          162.29628841923613,
          25.710049890779278,
          103.3981895980303,
          68.47293605123262,
          149.10370265433465,
          197.7909840603585,
          83.17327383308782,
          127.77664895788425,
          65.0842861116417,
          120.47097381170038,
          148.97807347566106,
          167.8231879677278,
          172.9877685198719,
          198.25416348988028,
          56.135096360006386,
          68.05478807154329,
          32.21003841632759,
          185.81952971294965,
          86.89733243406543,
          108.24166352488442,
          45.698569456323156,
          85.96995964992718,
          194.95157025436913,
          55.81779316766527,
          101.9238727568546,
          142.93982618500297,
          34.85811387212268,
          58.581108735000676,
          134.91662693962937,
          69.24119817052156,
          109.2834550926428,
          48.87753227153085,
          85.02745628514168,
          147.75804558193727,
          104.22838288487888,
          157.7511973341775,
          138.5294261849786,
          37.745028032074885,
          136.78614158347006,
          139.12931454275625,
          16.36275447196025,
          113.77779604433569,
          176.4368721149191,
          158.44966571108722,
          75.9305682462887,
          179.28961694381678,
          72.32049937357637,
          176.51915658502676,
          156.92536225623445,
          70.81555778747564,
          134.86552848288153,
          182.10907565598004,
          129.75356216949552,
          207.5765962320202,
          130.40061470036574,
          80.80983792097311,
          60.97470635362191,
          30.8148686400761,
          55.11341361079862,
          152.2271856033809,
          141.72769056447677,
          137.19346514241172,
          135.32738913002578,
          130.91239851543142,
          104.01711722098942,
          138.90143991711113,
          16.987795281141636,
          151.24092481810416,
          73.12592400781794,
          106.97676098548831,
          140.26990216144534,
          166.24510174258944,
          149.9799829124545
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
    "last_observed = pd.date_range(start=\"2025-01-01\", periods=N_SAMPLES, freq=\"D\")\n",
    "\n",
    "# Generate random observations between 20 and 200\n",
    "observations = np.random.randint(20, 200, size=N_SAMPLES)\n",
    "\n",
    "# Add some noise to the observations\n",
    "noise = np.random.normal(0, 10, size=N_SAMPLES)  # Mean 0, Std Dev 10\n",
    "observations = observations + noise\n",
    "\n",
    "# Create the DataFrame\n",
    "df = pd.DataFrame({\n",
    "    \"last_observed\": last_observed,\n",
    "    \"observations\": observations\n",
    "})\n",
    "# Break date into separate columns\n",
    "df['year'] = df['last_observed'].dt.year\n",
    "df['month'] = df['last_observed'].dt.month\n",
    "df['day'] = df['last_observed'].dt.day\n",
    "df['dayofweek'] = df['last_observed'].dt.dayofweek\n",
    "df['hour'] = df['last_observed'].dt.hour\n",
    "\n",
    "# Shift the observations by 1 day\n",
    "df['observations'] = df['observations'].shift(-1)\n",
    "# Drop the first row with NaN value\n",
    "df.dropna(inplace=True)\n",
    "\n",
    "# Display the first few rows of the DataFrame\n",
    "df.head()\n",
    "\n",
    "# Keep the plots\n",
    "fig = go.Figure()\n",
    "fig.add_trace(go.Scatter(x=last_observed[:200], y=observations[:200], mode='lines', name='Observations', opacity=0.7))\n",
    "\n",
    "fig.update_layout(\n",
    "    title=\"Observations Over Time\",\n",
    "    xaxis_title=\"Date\",\n",
    "    yaxis_title=\"Observations\",\n",
    "    legend_title=\"Legend\",\n",
    "    template=\"plotly_white\"\n",
    ")\n",
    "\n",
    "fig.show()\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 68,
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
       "      <th>last_observed</th>\n",
       "      <th>observations</th>\n",
       "      <th>year</th>\n",
       "      <th>month</th>\n",
       "      <th>day</th>\n",
       "      <th>dayofweek</th>\n",
       "      <th>hour</th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <th>0</th>\n",
       "      <td>2025-01-01</td>\n",
       "      <td>202.411520</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>1</td>\n",
       "      <td>2</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>1</th>\n",
       "      <td>2025-01-02</td>\n",
       "      <td>114.766908</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>2</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2</th>\n",
       "      <td>2025-01-03</td>\n",
       "      <td>42.271832</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>3</td>\n",
       "      <td>4</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>3</th>\n",
       "      <td>2025-01-04</td>\n",
       "      <td>126.130019</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>4</td>\n",
       "      <td>5</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>4</th>\n",
       "      <td>2025-01-05</td>\n",
       "      <td>105.535341</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>5</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>5</th>\n",
       "      <td>2025-01-06</td>\n",
       "      <td>37.353432</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>6</th>\n",
       "      <td>2025-01-07</td>\n",
       "      <td>149.201692</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>7</td>\n",
       "      <td>1</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>7</th>\n",
       "      <td>2025-01-08</td>\n",
       "      <td>147.256673</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>8</td>\n",
       "      <td>2</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>8</th>\n",
       "      <td>2025-01-09</td>\n",
       "      <td>85.428424</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>9</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>9</th>\n",
       "      <td>2025-01-10</td>\n",
       "      <td>96.291075</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>10</td>\n",
       "      <td>4</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>10</th>\n",
       "      <td>2025-01-11</td>\n",
       "      <td>140.824724</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>11</td>\n",
       "      <td>5</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>11</th>\n",
       "      <td>2025-01-12</td>\n",
       "      <td>116.765372</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>12</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>12</th>\n",
       "      <td>2025-01-13</td>\n",
       "      <td>130.140005</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>13</td>\n",
       "      <td>0</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>13</th>\n",
       "      <td>2025-01-14</td>\n",
       "      <td>175.732376</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>14</td>\n",
       "      <td>1</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>14</th>\n",
       "      <td>2025-01-15</td>\n",
       "      <td>149.271711</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>15</td>\n",
       "      <td>2</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>15</th>\n",
       "      <td>2025-01-16</td>\n",
       "      <td>160.532063</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>16</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>16</th>\n",
       "      <td>2025-01-17</td>\n",
       "      <td>56.851528</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>17</td>\n",
       "      <td>4</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>17</th>\n",
       "      <td>2025-01-18</td>\n",
       "      <td>16.534850</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>18</td>\n",
       "      <td>5</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>18</th>\n",
       "      <td>2025-01-19</td>\n",
       "      <td>115.563988</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>19</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>19</th>\n",
       "      <td>2025-01-20</td>\n",
       "      <td>179.140937</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>20</td>\n",
       "      <td>0</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>20</th>\n",
       "      <td>2025-01-21</td>\n",
       "      <td>44.542612</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>21</td>\n",
       "      <td>1</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>21</th>\n",
       "      <td>2025-01-22</td>\n",
       "      <td>150.731809</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>22</td>\n",
       "      <td>2</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>22</th>\n",
       "      <td>2025-01-23</td>\n",
       "      <td>43.853174</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>23</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>23</th>\n",
       "      <td>2025-01-24</td>\n",
       "      <td>171.161426</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>24</td>\n",
       "      <td>4</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>24</th>\n",
       "      <td>2025-01-25</td>\n",
       "      <td>78.537251</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>25</td>\n",
       "      <td>5</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>25</th>\n",
       "      <td>2025-01-26</td>\n",
       "      <td>41.582087</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>26</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>26</th>\n",
       "      <td>2025-01-27</td>\n",
       "      <td>96.570297</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>27</td>\n",
       "      <td>0</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>27</th>\n",
       "      <td>2025-01-28</td>\n",
       "      <td>71.577874</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>28</td>\n",
       "      <td>1</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>28</th>\n",
       "      <td>2025-01-29</td>\n",
       "      <td>83.607845</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>29</td>\n",
       "      <td>2</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>29</th>\n",
       "      <td>2025-01-30</td>\n",
       "      <td>199.830512</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>30</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>30</th>\n",
       "      <td>2025-01-31</td>\n",
       "      <td>44.538021</td>\n",
       "      <td>2025</td>\n",
       "      <td>1</td>\n",
       "      <td>31</td>\n",
       "      <td>4</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>31</th>\n",
       "      <td>2025-02-01</td>\n",
       "      <td>180.223306</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>1</td>\n",
       "      <td>5</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>32</th>\n",
       "      <td>2025-02-02</td>\n",
       "      <td>60.621750</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>2</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>33</th>\n",
       "      <td>2025-02-03</td>\n",
       "      <td>132.150353</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>34</th>\n",
       "      <td>2025-02-04</td>\n",
       "      <td>79.137860</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>4</td>\n",
       "      <td>1</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>35</th>\n",
       "      <td>2025-02-05</td>\n",
       "      <td>88.150477</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>5</td>\n",
       "      <td>2</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>36</th>\n",
       "      <td>2025-02-06</td>\n",
       "      <td>188.527315</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>6</td>\n",
       "      <td>3</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>37</th>\n",
       "      <td>2025-02-07</td>\n",
       "      <td>75.708905</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>7</td>\n",
       "      <td>4</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>38</th>\n",
       "      <td>2025-02-08</td>\n",
       "      <td>165.355656</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>8</td>\n",
       "      <td>5</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>39</th>\n",
       "      <td>2025-02-09</td>\n",
       "      <td>49.540018</td>\n",
       "      <td>2025</td>\n",
       "      <td>2</td>\n",
       "      <td>9</td>\n",
       "      <td>6</td>\n",
       "      <td>0</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "</div>"
      ],
      "text/plain": [
       "   last_observed  observations  year  month  day  dayofweek  hour\n",
       "0     2025-01-01    202.411520  2025      1    1          2     0\n",
       "1     2025-01-02    114.766908  2025      1    2          3     0\n",
       "2     2025-01-03     42.271832  2025      1    3          4     0\n",
       "3     2025-01-04    126.130019  2025      1    4          5     0\n",
       "4     2025-01-05    105.535341  2025      1    5          6     0\n",
       "5     2025-01-06     37.353432  2025      1    6          0     0\n",
       "6     2025-01-07    149.201692  2025      1    7          1     0\n",
       "7     2025-01-08    147.256673  2025      1    8          2     0\n",
       "8     2025-01-09     85.428424  2025      1    9          3     0\n",
       "9     2025-01-10     96.291075  2025      1   10          4     0\n",
       "10    2025-01-11    140.824724  2025      1   11          5     0\n",
       "11    2025-01-12    116.765372  2025      1   12          6     0\n",
       "12    2025-01-13    130.140005  2025      1   13          0     0\n",
       "13    2025-01-14    175.732376  2025      1   14          1     0\n",
       "14    2025-01-15    149.271711  2025      1   15          2     0\n",
       "15    2025-01-16    160.532063  2025      1   16          3     0\n",
       "16    2025-01-17     56.851528  2025      1   17          4     0\n",
       "17    2025-01-18     16.534850  2025      1   18          5     0\n",
       "18    2025-01-19    115.563988  2025      1   19          6     0\n",
       "19    2025-01-20    179.140937  2025      1   20          0     0\n",
       "20    2025-01-21     44.542612  2025      1   21          1     0\n",
       "21    2025-01-22    150.731809  2025      1   22          2     0\n",
       "22    2025-01-23     43.853174  2025      1   23          3     0\n",
       "23    2025-01-24    171.161426  2025      1   24          4     0\n",
       "24    2025-01-25     78.537251  2025      1   25          5     0\n",
       "25    2025-01-26     41.582087  2025      1   26          6     0\n",
       "26    2025-01-27     96.570297  2025      1   27          0     0\n",
       "27    2025-01-28     71.577874  2025      1   28          1     0\n",
       "28    2025-01-29     83.607845  2025      1   29          2     0\n",
       "29    2025-01-30    199.830512  2025      1   30          3     0\n",
       "30    2025-01-31     44.538021  2025      1   31          4     0\n",
       "31    2025-02-01    180.223306  2025      2    1          5     0\n",
       "32    2025-02-02     60.621750  2025      2    2          6     0\n",
       "33    2025-02-03    132.150353  2025      2    3          0     0\n",
       "34    2025-02-04     79.137860  2025      2    4          1     0\n",
       "35    2025-02-05     88.150477  2025      2    5          2     0\n",
       "36    2025-02-06    188.527315  2025      2    6          3     0\n",
       "37    2025-02-07     75.708905  2025      2    7          4     0\n",
       "38    2025-02-08    165.355656  2025      2    8          5     0\n",
       "39    2025-02-09     49.540018  2025      2    9          6     0"
      ]
     },
     "execution_count": 68,
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
   "execution_count": 69,
   "metadata": {},
   "outputs": [],
   "source": [
    "# ----------------------------\n",
    "# Preprocessing\n",
    "# ----------------------------\n",
    "def preprocess_data(df, features, target_column, batch_size, test_size=0.2, seed=42, time_series=True):\n",
    "    # Scale the input features\n",
    "    scaler = MinMaxScaler()\n",
    "    # Exclude datetime columns from scaling\n",
    "    numeric_features = df[features].select_dtypes(include=[np.number])\n",
    "    X = scaler.fit_transform(numeric_features)\n",
    "    y = df[target_column].values.reshape(-1, 1)\n",
    "\n",
    "    # Split without shuffling for time series data\n",
    "    split_index = int(len(df) * (1 - test_size))\n",
    "    X_train, X_test = X[:split_index], X[split_index:]\n",
    "    y_train, y_test = y[:split_index], y[split_index:]\n",
    "        \n",
    "    # Convert to tensors\n",
    "    X_tensor = torch.tensor(X_train, dtype=torch.float32)\n",
    "    y_tensor = torch.tensor(y_train, dtype=torch.float32)\n",
    "    X_test = torch.tensor(X_test, dtype=torch.float32)\n",
    "    y_test = torch.tensor(y_test, dtype=torch.float32)\n",
    "\n",
    "    # Create DataLoader\n",
    "    train_dataset = TensorDataset(X_tensor, y_tensor)\n",
    "    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)\n",
    "\n",
    "    return train_loader, X_test, y_test, X_tensor, y_tensor\n",
    "\n",
    "\n",
    "#call the function\n",
    "train_loader, X_test, y_test, X_tensor, y_tensor = preprocess_data(df, FEATURES, \"observations\", BATCH_SIZE)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 70,
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "NetTrafficRegressor(\n",
       "  (net): Sequential(\n",
       "    (0): Linear(in_features=5, out_features=32, bias=True)\n",
       "    (1): ReLU()\n",
       "    (2): Dropout(p=0.2, inplace=False)\n",
       "    (3): Linear(in_features=32, out_features=16, bias=True)\n",
       "    (4): ReLU()\n",
       "    (5): Dropout(p=0.2, inplace=False)\n",
       "    (6): Linear(in_features=16, out_features=1, bias=True)\n",
       "  )\n",
       ")"
      ]
     },
     "execution_count": 70,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# ----------------------------\n",
    "# Customizable MLP Model\n",
    "# ----------------------------\n",
    "class NetTrafficRegressor(nn.Module): # create a class for the model\n",
    "    def __init__(self, input_dim, hidden_dims, activation, dropout):\n",
    "        super().__init__()\n",
    "        layers = [] # create a list to store the layers\n",
    "        dims = [input_dim] + hidden_dims # create a list of dimensions for the layers\n",
    "        for i in range(len(dims) - 1): # loop through the dimensions to create the layers\n",
    "            layers.append(nn.Linear(dims[i], dims[i + 1])) # add a linear layer\n",
    "            layers.append(activation()) # add the activation function after the linear layer for non-linearity\n",
    "            if dropout > 0: # add dropout if the dropout rate is greater than 0 to prevent overfitting\n",
    "                layers.append(nn.Dropout(dropout))\n",
    "        layers.append(nn.Linear(dims[-1], 1))\n",
    "        self.net = nn.Sequential(*layers) # create the model as a sequential model\n",
    "\n",
    "    def forward(self, x):\n",
    "        return self.net(x)\n",
    "\n",
    "device = torch.device(\"cuda\" if torch.cuda.is_available() else \"cpu\") # check if cuda is available and use it if it is available otherwise use cpu\n",
    "\n",
    "\n",
    "model = NetTrafficRegressor(\n",
    "    input_dim=len(FEATURES), # input dimension is the number of features\n",
    "    hidden_dims=HIDDEN_LAYERS, # hidden layers are the hidden layers specified in the hyperparameters\n",
    "    activation=ACTIVATION, # activation function is the activation function specified in the hyperparameters\n",
    "    dropout=DROPOUT # dropout rate is the dropout rate specified in the hyperparameters\n",
    ").to(device)\n",
    "\n",
    "model"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 71,
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
   "execution_count": 72,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Epoch 000 | Train Loss: 15635.3835 | Test Loss: 17950.4414\n",
      "Epoch 100 | Train Loss: 14622.6296 | Test Loss: 17039.7852\n",
      "Epoch 200 | Train Loss: 11719.6030 | Test Loss: 13515.5059\n",
      "Epoch 300 | Train Loss: 7810.6763 | Test Loss: 7986.1895\n",
      "Epoch 400 | Train Loss: 4059.4026 | Test Loss: 3380.0886\n",
      "Epoch 500 | Train Loss: 2521.0562 | Test Loss: 1608.0103\n",
      "Epoch 600 | Train Loss: 2221.2153 | Test Loss: 1421.3492\n",
      "Epoch 700 | Train Loss: 2099.7478 | Test Loss: 1340.6387\n",
      "Epoch 800 | Train Loss: 2218.0022 | Test Loss: 1223.8077\n",
      "Epoch 900 | Train Loss: 1629.6730 | Test Loss: 1085.7251\n",
      "Epoch 1000 | Train Loss: 1528.9067 | Test Loss: 947.6964\n",
      "Epoch 1100 | Train Loss: 1464.6670 | Test Loss: 799.5516\n",
      "Epoch 1200 | Train Loss: 1335.8023 | Test Loss: 648.7139\n",
      "Epoch 1300 | Train Loss: 1215.1560 | Test Loss: 504.0975\n",
      "Epoch 1400 | Train Loss: 902.1159 | Test Loss: 368.9030\n",
      "Epoch 1500 | Train Loss: 807.2568 | Test Loss: 258.7757\n",
      "Epoch 1600 | Train Loss: 839.8595 | Test Loss: 173.0351\n",
      "Epoch 1700 | Train Loss: 772.9645 | Test Loss: 116.2290\n",
      "Epoch 1800 | Train Loss: 656.0460 | Test Loss: 84.0892\n",
      "Epoch 1900 | Train Loss: 615.9640 | Test Loss: 62.0962\n",
      "Epoch 2000 | Train Loss: 617.3836 | Test Loss: 53.8274\n",
      "Epoch 2100 | Train Loss: 595.6483 | Test Loss: 45.1816\n",
      "Epoch 2200 | Train Loss: 530.6508 | Test Loss: 39.5661\n",
      "Early stopping at epoch 6000 — no improvement for 100 epochs.\n"
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
    "train_losses = [] # create a list to store the training losses\n",
    "test_losses = [] # create a list to store the test losses\n",
    "\n",
    "for epoch in range(EPOCHS): # loop through the epochs for training the model specified in the hyperparameters\n",
    "    model.train()\n",
    "    running_loss = 0.0 # initialize the running loss to 0 for each epoch to calculate the average loss\n",
    "    for xb, yb in train_loader:\n",
    "        xb, yb = xb.to(device), yb.to(device) # move the data to the device (cuda or cpu)\n",
    "        preds = model(xb)\n",
    "        loss = loss_fn(preds, yb)\n",
    "        optimizer.zero_grad() # zero the gradients to prevent accumulation of gradients\n",
    "        loss.backward() # backpropagate the loss to calculate the gradients of the model parameters\n",
    "        optimizer.step() # update the model parameters using the optimizer\n",
    "        running_loss += loss.item() # add the loss to the running loss\n",
    "\n",
    "    # Average train loss\n",
    "    avg_train_loss = running_loss / len(train_loader)\n",
    "    train_losses.append(avg_train_loss)\n",
    "\n",
    "    # Evaluate on full dataset (or you could use a test loader)\n",
    "    model.eval()\n",
    "    with torch.no_grad():\n",
    "        y_pred_test = model(X_test.to(device))\n",
    "        test_loss = loss_fn(y_pred_test.cpu(), y_test).item()\n",
    "        test_losses.append(test_loss)\n",
    "        \n",
    "        if test_loss < BEST_LOSS:\n",
    "            BEST_LOSS = test_loss\n",
    "            PATIENCE_COUNTER = 0  # reset if loss improves\n",
    "        else:\n",
    "            PATIENCE_COUNTER += 1\n",
    "        if PATIENCE_COUNTER >= PATIENCE:\n",
    "            print(f\"Early stopping at epoch {EPOCHS} — no improvement for {PATIENCE} epochs.\")\n",
    "            break\n",
    "\n",
    "    # Logging\n",
    "    if epoch % 100 == 0 or epoch == EPOCHS - 1: # print the loss every 20 epochs\n",
    "        print(f\"Epoch {epoch:03d} | Train Loss: {avg_train_loss:.4f} | Test Loss: {test_loss:.4f}\")\n",
    "\n",
    "# ----------------------------\n",
    "# Plot Loss Curve\n",
    "# ----------------------------\n",
    "plt.figure(figsize=(10, 5))\n",
    "plt.plot(train_losses, label=\"Train Loss\")\n",
    "plt.plot(test_losses, label=\"Test Loss\")\n",
    "plt.title(\"📉 Loss Over Epochs\")\n",
    "plt.xlabel(\"Epoch\")\n",
    "plt.ylabel(\"Loss\")\n",
    "plt.rcParams['font.family'] = 'Arial' \n",
    "plt.legend()\n",
    "plt.grid(True)\n",
    "plt.show()\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 73,
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
         "name": "True",
         "opacity": 0.7,
         "type": "scatter",
         "x": [
          "2025-01-01T00:00:00.000000000",
          "2025-01-02T00:00:00.000000000",
          "2025-01-03T00:00:00.000000000",
          "2025-01-04T00:00:00.000000000",
          "2025-01-05T00:00:00.000000000",
          "2025-01-06T00:00:00.000000000",
          "2025-01-07T00:00:00.000000000",
          "2025-01-08T00:00:00.000000000",
          "2025-01-09T00:00:00.000000000",
          "2025-01-10T00:00:00.000000000",
          "2025-01-11T00:00:00.000000000",
          "2025-01-12T00:00:00.000000000",
          "2025-01-13T00:00:00.000000000",
          "2025-01-14T00:00:00.000000000",
          "2025-01-15T00:00:00.000000000",
          "2025-01-16T00:00:00.000000000",
          "2025-01-17T00:00:00.000000000",
          "2025-01-18T00:00:00.000000000",
          "2025-01-19T00:00:00.000000000",
          "2025-01-20T00:00:00.000000000",
          "2025-01-21T00:00:00.000000000",
          "2025-01-22T00:00:00.000000000",
          "2025-01-23T00:00:00.000000000",
          "2025-01-24T00:00:00.000000000",
          "2025-01-25T00:00:00.000000000",
          "2025-01-26T00:00:00.000000000",
          "2025-01-27T00:00:00.000000000",
          "2025-01-28T00:00:00.000000000",
          "2025-01-29T00:00:00.000000000",
          "2025-01-30T00:00:00.000000000",
          "2025-01-31T00:00:00.000000000",
          "2025-02-01T00:00:00.000000000",
          "2025-02-02T00:00:00.000000000",
          "2025-02-03T00:00:00.000000000",
          "2025-02-04T00:00:00.000000000",
          "2025-02-05T00:00:00.000000000",
          "2025-02-06T00:00:00.000000000",
          "2025-02-07T00:00:00.000000000",
          "2025-02-08T00:00:00.000000000",
          "2025-02-09T00:00:00.000000000",
          "2025-02-10T00:00:00.000000000",
          "2025-02-11T00:00:00.000000000",
          "2025-02-12T00:00:00.000000000",
          "2025-02-13T00:00:00.000000000",
          "2025-02-14T00:00:00.000000000",
          "2025-02-15T00:00:00.000000000",
          "2025-02-16T00:00:00.000000000",
          "2025-02-17T00:00:00.000000000",
          "2025-02-18T00:00:00.000000000",
          "2025-02-19T00:00:00.000000000",
          "2025-02-20T00:00:00.000000000",
          "2025-02-21T00:00:00.000000000",
          "2025-02-22T00:00:00.000000000",
          "2025-02-23T00:00:00.000000000",
          "2025-02-24T00:00:00.000000000",
          "2025-02-25T00:00:00.000000000",
          "2025-02-26T00:00:00.000000000",
          "2025-02-27T00:00:00.000000000",
          "2025-02-28T00:00:00.000000000",
          "2025-03-01T00:00:00.000000000",
          "2025-03-02T00:00:00.000000000",
          "2025-03-03T00:00:00.000000000",
          "2025-03-04T00:00:00.000000000",
          "2025-03-05T00:00:00.000000000",
          "2025-03-06T00:00:00.000000000",
          "2025-03-07T00:00:00.000000000",
          "2025-03-08T00:00:00.000000000",
          "2025-03-09T00:00:00.000000000",
          "2025-03-10T00:00:00.000000000",
          "2025-03-11T00:00:00.000000000",
          "2025-03-12T00:00:00.000000000",
          "2025-03-13T00:00:00.000000000",
          "2025-03-14T00:00:00.000000000",
          "2025-03-15T00:00:00.000000000",
          "2025-03-16T00:00:00.000000000",
          "2025-03-17T00:00:00.000000000",
          "2025-03-18T00:00:00.000000000",
          "2025-03-19T00:00:00.000000000",
          "2025-03-20T00:00:00.000000000",
          "2025-03-21T00:00:00.000000000",
          "2025-03-22T00:00:00.000000000",
          "2025-03-23T00:00:00.000000000",
          "2025-03-24T00:00:00.000000000",
          "2025-03-25T00:00:00.000000000",
          "2025-03-26T00:00:00.000000000",
          "2025-03-27T00:00:00.000000000",
          "2025-03-28T00:00:00.000000000",
          "2025-03-29T00:00:00.000000000",
          "2025-03-30T00:00:00.000000000",
          "2025-03-31T00:00:00.000000000",
          "2025-04-01T00:00:00.000000000",
          "2025-04-02T00:00:00.000000000",
          "2025-04-03T00:00:00.000000000",
          "2025-04-04T00:00:00.000000000",
          "2025-04-05T00:00:00.000000000",
          "2025-04-06T00:00:00.000000000",
          "2025-04-07T00:00:00.000000000",
          "2025-04-08T00:00:00.000000000",
          "2025-04-09T00:00:00.000000000",
          "2025-04-10T00:00:00.000000000",
          "2025-04-11T00:00:00.000000000",
          "2025-04-12T00:00:00.000000000",
          "2025-04-13T00:00:00.000000000",
          "2025-04-14T00:00:00.000000000",
          "2025-04-15T00:00:00.000000000",
          "2025-04-16T00:00:00.000000000",
          "2025-04-17T00:00:00.000000000",
          "2025-04-18T00:00:00.000000000",
          "2025-04-19T00:00:00.000000000",
          "2025-04-20T00:00:00.000000000",
          "2025-04-21T00:00:00.000000000",
          "2025-04-22T00:00:00.000000000",
          "2025-04-23T00:00:00.000000000",
          "2025-04-24T00:00:00.000000000",
          "2025-04-25T00:00:00.000000000",
          "2025-04-26T00:00:00.000000000",
          "2025-04-27T00:00:00.000000000",
          "2025-04-28T00:00:00.000000000",
          "2025-04-29T00:00:00.000000000",
          "2025-04-30T00:00:00.000000000",
          "2025-05-01T00:00:00.000000000",
          "2025-05-02T00:00:00.000000000",
          "2025-05-03T00:00:00.000000000",
          "2025-05-04T00:00:00.000000000",
          "2025-05-05T00:00:00.000000000",
          "2025-05-06T00:00:00.000000000",
          "2025-05-07T00:00:00.000000000",
          "2025-05-08T00:00:00.000000000",
          "2025-05-09T00:00:00.000000000",
          "2025-05-10T00:00:00.000000000",
          "2025-05-11T00:00:00.000000000",
          "2025-05-12T00:00:00.000000000",
          "2025-05-13T00:00:00.000000000",
          "2025-05-14T00:00:00.000000000",
          "2025-05-15T00:00:00.000000000",
          "2025-05-16T00:00:00.000000000",
          "2025-05-17T00:00:00.000000000",
          "2025-05-18T00:00:00.000000000",
          "2025-05-19T00:00:00.000000000",
          "2025-05-20T00:00:00.000000000",
          "2025-05-21T00:00:00.000000000",
          "2025-05-22T00:00:00.000000000",
          "2025-05-23T00:00:00.000000000",
          "2025-05-24T00:00:00.000000000",
          "2025-05-25T00:00:00.000000000",
          "2025-05-26T00:00:00.000000000",
          "2025-05-27T00:00:00.000000000",
          "2025-05-28T00:00:00.000000000",
          "2025-05-29T00:00:00.000000000",
          "2025-05-30T00:00:00.000000000",
          "2025-05-31T00:00:00.000000000",
          "2025-06-01T00:00:00.000000000",
          "2025-06-02T00:00:00.000000000",
          "2025-06-03T00:00:00.000000000",
          "2025-06-04T00:00:00.000000000",
          "2025-06-05T00:00:00.000000000",
          "2025-06-06T00:00:00.000000000",
          "2025-06-07T00:00:00.000000000",
          "2025-06-08T00:00:00.000000000",
          "2025-06-09T00:00:00.000000000",
          "2025-06-10T00:00:00.000000000",
          "2025-06-11T00:00:00.000000000",
          "2025-06-12T00:00:00.000000000",
          "2025-06-13T00:00:00.000000000",
          "2025-06-14T00:00:00.000000000",
          "2025-06-15T00:00:00.000000000",
          "2025-06-16T00:00:00.000000000",
          "2025-06-17T00:00:00.000000000",
          "2025-06-18T00:00:00.000000000",
          "2025-06-19T00:00:00.000000000",
          "2025-06-20T00:00:00.000000000",
          "2025-06-21T00:00:00.000000000",
          "2025-06-22T00:00:00.000000000",
          "2025-06-23T00:00:00.000000000",
          "2025-06-24T00:00:00.000000000",
          "2025-06-25T00:00:00.000000000",
          "2025-06-26T00:00:00.000000000",
          "2025-06-27T00:00:00.000000000",
          "2025-06-28T00:00:00.000000000",
          "2025-06-29T00:00:00.000000000",
          "2025-06-30T00:00:00.000000000",
          "2025-07-01T00:00:00.000000000",
          "2025-07-02T00:00:00.000000000",
          "2025-07-03T00:00:00.000000000",
          "2025-07-04T00:00:00.000000000",
          "2025-07-05T00:00:00.000000000",
          "2025-07-06T00:00:00.000000000",
          "2025-07-07T00:00:00.000000000",
          "2025-07-08T00:00:00.000000000",
          "2025-07-09T00:00:00.000000000",
          "2025-07-10T00:00:00.000000000",
          "2025-07-11T00:00:00.000000000",
          "2025-07-12T00:00:00.000000000",
          "2025-07-13T00:00:00.000000000",
          "2025-07-14T00:00:00.000000000",
          "2025-07-15T00:00:00.000000000",
          "2025-07-16T00:00:00.000000000",
          "2025-07-17T00:00:00.000000000",
          "2025-07-18T00:00:00.000000000",
          "2025-07-19T00:00:00.000000000"
         ],
         "y": [
          102.65885925292969,
          38.77676773071289,
          166.32313537597656,
          101.51513671875,
          146.5115203857422,
          80.15674591064453,
          143.79296875,
          21.67518424987793,
          168.60748291015625,
          84.55340576171875,
          156.51036071777344,
          65.71570587158203,
          185.45376586914062,
          41.686317443847656,
          108.35076904296875,
          172.8605194091797,
          77.58424377441406,
          132.41259765625,
          155.16741943359375,
          150.60768127441406,
          70.3059310913086,
          146.1754150390625,
          195.02357482910156,
          171.74095153808594,
          151.28614807128906,
          80.19898223876953,
          114.96617889404297,
          182.44451904296875,
          188.8406524658203,
          122.67304992675781,
          82.32557678222656,
          130.10879516601562,
          104.95530700683594,
          178.6967315673828,
          115.66598510742188,
          155.6011962890625,
          141.861328125,
          118.40786743164062,
          100.37320709228516,
          82.55142211914062,
          172.1427459716797,
          193.04046630859375,
          174.69741821289062,
          79.07127380371094,
          50.92969512939453,
          150.6475830078125,
          34.46350860595703,
          55.02122116088867,
          186.64724731445312,
          147.35263061523438,
          148.00274658203125,
          156.13980102539062,
          162.87672424316406,
          144.79029846191406,
          58.141666412353516,
          202.5750732421875,
          128.6949920654297,
          132.2418212890625,
          38.249481201171875,
          153.9807891845703
         ]
        },
        {
         "mode": "lines",
         "name": "Predicted",
         "opacity": 0.7,
         "type": "scatter",
         "x": [
          "2025-01-01T00:00:00.000000000",
          "2025-01-02T00:00:00.000000000",
          "2025-01-03T00:00:00.000000000",
          "2025-01-04T00:00:00.000000000",
          "2025-01-05T00:00:00.000000000",
          "2025-01-06T00:00:00.000000000",
          "2025-01-07T00:00:00.000000000",
          "2025-01-08T00:00:00.000000000",
          "2025-01-09T00:00:00.000000000",
          "2025-01-10T00:00:00.000000000",
          "2025-01-11T00:00:00.000000000",
          "2025-01-12T00:00:00.000000000",
          "2025-01-13T00:00:00.000000000",
          "2025-01-14T00:00:00.000000000",
          "2025-01-15T00:00:00.000000000",
          "2025-01-16T00:00:00.000000000",
          "2025-01-17T00:00:00.000000000",
          "2025-01-18T00:00:00.000000000",
          "2025-01-19T00:00:00.000000000",
          "2025-01-20T00:00:00.000000000",
          "2025-01-21T00:00:00.000000000",
          "2025-01-22T00:00:00.000000000",
          "2025-01-23T00:00:00.000000000",
          "2025-01-24T00:00:00.000000000",
          "2025-01-25T00:00:00.000000000",
          "2025-01-26T00:00:00.000000000",
          "2025-01-27T00:00:00.000000000",
          "2025-01-28T00:00:00.000000000",
          "2025-01-29T00:00:00.000000000",
          "2025-01-30T00:00:00.000000000",
          "2025-01-31T00:00:00.000000000",
          "2025-02-01T00:00:00.000000000",
          "2025-02-02T00:00:00.000000000",
          "2025-02-03T00:00:00.000000000",
          "2025-02-04T00:00:00.000000000",
          "2025-02-05T00:00:00.000000000",
          "2025-02-06T00:00:00.000000000",
          "2025-02-07T00:00:00.000000000",
          "2025-02-08T00:00:00.000000000",
          "2025-02-09T00:00:00.000000000",
          "2025-02-10T00:00:00.000000000",
          "2025-02-11T00:00:00.000000000",
          "2025-02-12T00:00:00.000000000",
          "2025-02-13T00:00:00.000000000",
          "2025-02-14T00:00:00.000000000",
          "2025-02-15T00:00:00.000000000",
          "2025-02-16T00:00:00.000000000",
          "2025-02-17T00:00:00.000000000",
          "2025-02-18T00:00:00.000000000",
          "2025-02-19T00:00:00.000000000",
          "2025-02-20T00:00:00.000000000",
          "2025-02-21T00:00:00.000000000",
          "2025-02-22T00:00:00.000000000",
          "2025-02-23T00:00:00.000000000",
          "2025-02-24T00:00:00.000000000",
          "2025-02-25T00:00:00.000000000",
          "2025-02-26T00:00:00.000000000",
          "2025-02-27T00:00:00.000000000",
          "2025-02-28T00:00:00.000000000",
          "2025-03-01T00:00:00.000000000",
          "2025-03-02T00:00:00.000000000",
          "2025-03-03T00:00:00.000000000",
          "2025-03-04T00:00:00.000000000",
          "2025-03-05T00:00:00.000000000",
          "2025-03-06T00:00:00.000000000",
          "2025-03-07T00:00:00.000000000",
          "2025-03-08T00:00:00.000000000",
          "2025-03-09T00:00:00.000000000",
          "2025-03-10T00:00:00.000000000",
          "2025-03-11T00:00:00.000000000",
          "2025-03-12T00:00:00.000000000",
          "2025-03-13T00:00:00.000000000",
          "2025-03-14T00:00:00.000000000",
          "2025-03-15T00:00:00.000000000",
          "2025-03-16T00:00:00.000000000",
          "2025-03-17T00:00:00.000000000",
          "2025-03-18T00:00:00.000000000",
          "2025-03-19T00:00:00.000000000",
          "2025-03-20T00:00:00.000000000",
          "2025-03-21T00:00:00.000000000",
          "2025-03-22T00:00:00.000000000",
          "2025-03-23T00:00:00.000000000",
          "2025-03-24T00:00:00.000000000",
          "2025-03-25T00:00:00.000000000",
          "2025-03-26T00:00:00.000000000",
          "2025-03-27T00:00:00.000000000",
          "2025-03-28T00:00:00.000000000",
          "2025-03-29T00:00:00.000000000",
          "2025-03-30T00:00:00.000000000",
          "2025-03-31T00:00:00.000000000",
          "2025-04-01T00:00:00.000000000",
          "2025-04-02T00:00:00.000000000",
          "2025-04-03T00:00:00.000000000",
          "2025-04-04T00:00:00.000000000",
          "2025-04-05T00:00:00.000000000",
          "2025-04-06T00:00:00.000000000",
          "2025-04-07T00:00:00.000000000",
          "2025-04-08T00:00:00.000000000",
          "2025-04-09T00:00:00.000000000",
          "2025-04-10T00:00:00.000000000",
          "2025-04-11T00:00:00.000000000",
          "2025-04-12T00:00:00.000000000",
          "2025-04-13T00:00:00.000000000",
          "2025-04-14T00:00:00.000000000",
          "2025-04-15T00:00:00.000000000",
          "2025-04-16T00:00:00.000000000",
          "2025-04-17T00:00:00.000000000",
          "2025-04-18T00:00:00.000000000",
          "2025-04-19T00:00:00.000000000",
          "2025-04-20T00:00:00.000000000",
          "2025-04-21T00:00:00.000000000",
          "2025-04-22T00:00:00.000000000",
          "2025-04-23T00:00:00.000000000",
          "2025-04-24T00:00:00.000000000",
          "2025-04-25T00:00:00.000000000",
          "2025-04-26T00:00:00.000000000",
          "2025-04-27T00:00:00.000000000",
          "2025-04-28T00:00:00.000000000",
          "2025-04-29T00:00:00.000000000",
          "2025-04-30T00:00:00.000000000",
          "2025-05-01T00:00:00.000000000",
          "2025-05-02T00:00:00.000000000",
          "2025-05-03T00:00:00.000000000",
          "2025-05-04T00:00:00.000000000",
          "2025-05-05T00:00:00.000000000",
          "2025-05-06T00:00:00.000000000",
          "2025-05-07T00:00:00.000000000",
          "2025-05-08T00:00:00.000000000",
          "2025-05-09T00:00:00.000000000",
          "2025-05-10T00:00:00.000000000",
          "2025-05-11T00:00:00.000000000",
          "2025-05-12T00:00:00.000000000",
          "2025-05-13T00:00:00.000000000",
          "2025-05-14T00:00:00.000000000",
          "2025-05-15T00:00:00.000000000",
          "2025-05-16T00:00:00.000000000",
          "2025-05-17T00:00:00.000000000",
          "2025-05-18T00:00:00.000000000",
          "2025-05-19T00:00:00.000000000",
          "2025-05-20T00:00:00.000000000",
          "2025-05-21T00:00:00.000000000",
          "2025-05-22T00:00:00.000000000",
          "2025-05-23T00:00:00.000000000",
          "2025-05-24T00:00:00.000000000",
          "2025-05-25T00:00:00.000000000",
          "2025-05-26T00:00:00.000000000",
          "2025-05-27T00:00:00.000000000",
          "2025-05-28T00:00:00.000000000",
          "2025-05-29T00:00:00.000000000",
          "2025-05-30T00:00:00.000000000",
          "2025-05-31T00:00:00.000000000",
          "2025-06-01T00:00:00.000000000",
          "2025-06-02T00:00:00.000000000",
          "2025-06-03T00:00:00.000000000",
          "2025-06-04T00:00:00.000000000",
          "2025-06-05T00:00:00.000000000",
          "2025-06-06T00:00:00.000000000",
          "2025-06-07T00:00:00.000000000",
          "2025-06-08T00:00:00.000000000",
          "2025-06-09T00:00:00.000000000",
          "2025-06-10T00:00:00.000000000",
          "2025-06-11T00:00:00.000000000",
          "2025-06-12T00:00:00.000000000",
          "2025-06-13T00:00:00.000000000",
          "2025-06-14T00:00:00.000000000",
          "2025-06-15T00:00:00.000000000",
          "2025-06-16T00:00:00.000000000",
          "2025-06-17T00:00:00.000000000",
          "2025-06-18T00:00:00.000000000",
          "2025-06-19T00:00:00.000000000",
          "2025-06-20T00:00:00.000000000",
          "2025-06-21T00:00:00.000000000",
          "2025-06-22T00:00:00.000000000",
          "2025-06-23T00:00:00.000000000",
          "2025-06-24T00:00:00.000000000",
          "2025-06-25T00:00:00.000000000",
          "2025-06-26T00:00:00.000000000",
          "2025-06-27T00:00:00.000000000",
          "2025-06-28T00:00:00.000000000",
          "2025-06-29T00:00:00.000000000",
          "2025-06-30T00:00:00.000000000",
          "2025-07-01T00:00:00.000000000",
          "2025-07-02T00:00:00.000000000",
          "2025-07-03T00:00:00.000000000",
          "2025-07-04T00:00:00.000000000",
          "2025-07-05T00:00:00.000000000",
          "2025-07-06T00:00:00.000000000",
          "2025-07-07T00:00:00.000000000",
          "2025-07-08T00:00:00.000000000",
          "2025-07-09T00:00:00.000000000",
          "2025-07-10T00:00:00.000000000",
          "2025-07-11T00:00:00.000000000",
          "2025-07-12T00:00:00.000000000",
          "2025-07-13T00:00:00.000000000",
          "2025-07-14T00:00:00.000000000",
          "2025-07-15T00:00:00.000000000",
          "2025-07-16T00:00:00.000000000",
          "2025-07-17T00:00:00.000000000",
          "2025-07-18T00:00:00.000000000",
          "2025-07-19T00:00:00.000000000"
         ],
         "y": [
          97.67808532714844,
          38.1778678894043,
          156.59515380859375,
          96.00829315185547,
          143.64932250976562,
          81.6212387084961,
          140.7135467529297,
          26.973142623901367,
          163.43197631835938,
          84.91239929199219,
          151.7576141357422,
          66.95745086669922,
          178.2758331298828,
          44.16510009765625,
          106.07897186279297,
          165.9851837158203,
          77.00922393798828,
          127.89469909667969,
          148.89535522460938,
          144.44540405273438,
          69.42211151123047,
          139.91287231445312,
          185.22625732421875,
          163.3310546875,
          144.07073974609375,
          77.63321685791016,
          109.8265151977539,
          172.4987335205078,
          178.2570343017578,
          116.4033432006836,
          78.60784149169922,
          122.9289321899414,
          99.29056549072266,
          167.7984619140625,
          114.58280944824219,
          151.59146118164062,
          138.5878448486328,
          116.5334701538086,
          99.52814483642578,
          82.72114562988281,
          165.99734497070312,
          185.05743408203125,
          167.9749755859375,
          78.67301177978516,
          52.25045394897461,
          144.96218872070312,
          36.573421478271484,
          55.45866012573242,
          177.901123046875,
          141.08660888671875,
          141.49098205566406,
          148.87139892578125,
          154.94720458984375,
          137.89364624023438,
          56.956581115722656,
          191.33242797851562,
          122.2925796508789,
          125.39600372314453,
          37.91603469848633,
          145.24874877929688
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
         "text": "Next observation Prediction By Date"
        },
        "xaxis": {
         "title": {
          "text": "Date"
         }
        },
        "yaxis": {
         "title": {
          "text": "Number of Observations"
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
    "# ----------------------------\n",
    "# Evaluation\n",
    "# ----------------------------\n",
    "model.eval()\n",
    "with torch.no_grad(): # turn off gradient tracking for evaluation to save memory and computation time\n",
    "    y_pred = model(X_test.to(device)).cpu().numpy() # predict the target values using the model\n",
    "    y_true = y_test.cpu().numpy() # get the true target values from the tensor\n",
    "\n",
    "fig = go.Figure()\n",
    "fig.add_trace(go.Scatter(x=np.array(df[\"last_observed\"][:200]), y=y_true[:200].flatten(), mode='lines', name='True', opacity=0.7))\n",
    "fig.add_trace(go.Scatter(x=np.array(df[\"last_observed\"][:200]), y=y_pred[:200].flatten(), mode='lines', name='Predicted', opacity=0.7))\n",
    "\n",
    "fig.update_layout(\n",
    "    title=\"Next observation Prediction By Date\",\n",
    "    xaxis_title=\"Date\",\n",
    "    yaxis_title=\"Number of Observations\",\n",
    "    legend_title=\"Legend\",\n",
    "    template=\"plotly_white\"\n",
    ")\n",
    "\n",
    "fig.show()\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 74,
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Average Accuracy: 96.07%\n",
      "Accuracy did not improve (Best: 96.07%)\n"
     ]
    },
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
       "      <th>timestamp</th>\n",
       "      <th>actual_observed</th>\n",
       "      <th>predicted_observed</th>\n",
       "      <th>difference</th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <th>0</th>\n",
       "      <td>2025-01-01</td>\n",
       "      <td>102.658859</td>\n",
       "      <td>97.678085</td>\n",
       "      <td>4.980774</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>1</th>\n",
       "      <td>2025-01-02</td>\n",
       "      <td>38.776768</td>\n",
       "      <td>38.177868</td>\n",
       "      <td>0.598900</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2</th>\n",
       "      <td>2025-01-03</td>\n",
       "      <td>166.323135</td>\n",
       "      <td>156.595154</td>\n",
       "      <td>9.727982</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>3</th>\n",
       "      <td>2025-01-04</td>\n",
       "      <td>101.515137</td>\n",
       "      <td>96.008293</td>\n",
       "      <td>5.506844</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>4</th>\n",
       "      <td>2025-01-05</td>\n",
       "      <td>146.511520</td>\n",
       "      <td>143.649323</td>\n",
       "      <td>2.862198</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>5</th>\n",
       "      <td>2025-01-06</td>\n",
       "      <td>80.156746</td>\n",
       "      <td>81.621239</td>\n",
       "      <td>-1.464493</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>6</th>\n",
       "      <td>2025-01-07</td>\n",
       "      <td>143.792969</td>\n",
       "      <td>140.713547</td>\n",
       "      <td>3.079422</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>7</th>\n",
       "      <td>2025-01-08</td>\n",
       "      <td>21.675184</td>\n",
       "      <td>26.973143</td>\n",
       "      <td>-5.297958</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>8</th>\n",
       "      <td>2025-01-09</td>\n",
       "      <td>168.607483</td>\n",
       "      <td>163.431976</td>\n",
       "      <td>5.175507</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>9</th>\n",
       "      <td>2025-01-10</td>\n",
       "      <td>84.553406</td>\n",
       "      <td>84.912399</td>\n",
       "      <td>-0.358994</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "</div>"
      ],
      "text/plain": [
       "   timestamp  actual_observed  predicted_observed  difference\n",
       "0 2025-01-01       102.658859           97.678085    4.980774\n",
       "1 2025-01-02        38.776768           38.177868    0.598900\n",
       "2 2025-01-03       166.323135          156.595154    9.727982\n",
       "3 2025-01-04       101.515137           96.008293    5.506844\n",
       "4 2025-01-05       146.511520          143.649323    2.862198\n",
       "5 2025-01-06        80.156746           81.621239   -1.464493\n",
       "6 2025-01-07       143.792969          140.713547    3.079422\n",
       "7 2025-01-08        21.675184           26.973143   -5.297958\n",
       "8 2025-01-09       168.607483          163.431976    5.175507\n",
       "9 2025-01-10        84.553406           84.912399   -0.358994"
      ]
     },
     "execution_count": 74,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# Compute average accuracy (1 - MAPE)\n",
    "accuracy = 1 - np.mean(np.abs((y_true - y_pred) / y_true))\n",
    "print(f\"Average Accuracy: {accuracy:.2%}\")\n",
    "\n",
    "# Compare to previous best accuracy\n",
    "if 'prev_accuracy' not in locals():\n",
    "    prev_accuracy = 0  # Initialize prev_accuracy if not already defined\n",
    "\n",
    "if accuracy > prev_accuracy:\n",
    "    best_accuracy = accuracy\n",
    "    print(f\"New best accuracy: {best_accuracy:.2%}\")\n",
    "    # Update stored accuracy\n",
    "    prev_accuracy = accuracy\n",
    "else:\n",
    "    print(f\"Accuracy did not improve (Best: {prev_accuracy:.2%})\")\n",
    "\n",
    "\n",
    "\n",
    "# Save the actual and predicted values to a dataframe\n",
    "pred_df = pd.DataFrame({\n",
    "    \"timestamp\": df[\"last_observed\"].values[:len(y_pred)],\n",
    "    \"actual_observed\": y_true.flatten(),\n",
    "    \"predicted_observed\": y_pred.flatten()\n",
    "})\n",
    "\n",
    "# Add the difference between actual and predicted values\n",
    "pred_df[\"difference\"] = pred_df[\"actual_observed\"] - pred_df[\"predicted_observed\"]\n",
    "\n",
    "#print the first 10 rows of the dataframe\n",
    "pred_df.head(10)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 75,
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
       "      <th>Hidden Layers</th>\n",
       "      <th>Activation Function</th>\n",
       "      <th>Dropout Rate</th>\n",
       "      <th>Loss Function</th>\n",
       "      <th>Optimizer</th>\n",
       "      <th>Learning Rate</th>\n",
       "      <th>Weight Decay</th>\n",
       "      <th>Epochs</th>\n",
       "      <th>Batch Size</th>\n",
       "      <th>Seed</th>\n",
       "      <th>Test Size</th>\n",
       "      <th>N_Samples</th>\n",
       "      <th>Best Loss</th>\n",
       "      <th>Patience</th>\n",
       "      <th>Patience Counter</th>\n",
       "      <th>Average Accuracy</th>\n",
       "      <th>Average Accuracy (%)</th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <th>0</th>\n",
       "      <td>[32, 16]</td>\n",
       "      <td>ReLU</td>\n",
       "      <td>0.2</td>\n",
       "      <td>MSELoss</td>\n",
       "      <td>Adam</td>\n",
       "      <td>0.0001</td>\n",
       "      <td>0.001</td>\n",
       "      <td>6000</td>\n",
       "      <td>32</td>\n",
       "      <td>42</td>\n",
       "      <td>0.2</td>\n",
       "      <td>300</td>\n",
       "      <td>30.601368</td>\n",
       "      <td>100</td>\n",
       "      <td>100</td>\n",
       "      <td>0.960678</td>\n",
       "      <td>96.07%</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>1</th>\n",
       "      <td>[32, 16]</td>\n",
       "      <td>ReLU</td>\n",
       "      <td>0.2</td>\n",
       "      <td>MSELoss</td>\n",
       "      <td>Adam</td>\n",
       "      <td>0.0001</td>\n",
       "      <td>0.001</td>\n",
       "      <td>6000</td>\n",
       "      <td>32</td>\n",
       "      <td>42</td>\n",
       "      <td>0.2</td>\n",
       "      <td>300</td>\n",
       "      <td>30.601368</td>\n",
       "      <td>100</td>\n",
       "      <td>100</td>\n",
       "      <td>0.960678</td>\n",
       "      <td>96.07%</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2</th>\n",
       "      <td>[32, 16]</td>\n",
       "      <td>ReLU</td>\n",
       "      <td>0.2</td>\n",
       "      <td>MSELoss</td>\n",
       "      <td>Adam</td>\n",
       "      <td>0.0001</td>\n",
       "      <td>0.001</td>\n",
       "      <td>6000</td>\n",
       "      <td>32</td>\n",
       "      <td>42</td>\n",
       "      <td>0.2</td>\n",
       "      <td>300</td>\n",
       "      <td>30.601368</td>\n",
       "      <td>100</td>\n",
       "      <td>100</td>\n",
       "      <td>0.960678</td>\n",
       "      <td>96.07%</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>3</th>\n",
       "      <td>[32, 16]</td>\n",
       "      <td>ReLU</td>\n",
       "      <td>0.2</td>\n",
       "      <td>MSELoss</td>\n",
       "      <td>Adam</td>\n",
       "      <td>0.0001</td>\n",
       "      <td>0.001</td>\n",
       "      <td>6000</td>\n",
       "      <td>32</td>\n",
       "      <td>42</td>\n",
       "      <td>0.2</td>\n",
       "      <td>300</td>\n",
       "      <td>34.014599</td>\n",
       "      <td>100</td>\n",
       "      <td>100</td>\n",
       "      <td>0.954759</td>\n",
       "      <td>95.48%</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>4</th>\n",
       "      <td>[32, 16]</td>\n",
       "      <td>ReLU</td>\n",
       "      <td>0.2</td>\n",
       "      <td>MSELoss</td>\n",
       "      <td>Adam</td>\n",
       "      <td>0.0001</td>\n",
       "      <td>0.001</td>\n",
       "      <td>6000</td>\n",
       "      <td>32</td>\n",
       "      <td>42</td>\n",
       "      <td>0.2</td>\n",
       "      <td>300</td>\n",
       "      <td>45.079739</td>\n",
       "      <td>100</td>\n",
       "      <td>100</td>\n",
       "      <td>0.940928</td>\n",
       "      <td>94.09%</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "</div>"
      ],
      "text/plain": [
       "  Hidden Layers Activation Function  Dropout Rate Loss Function Optimizer  \\\n",
       "0      [32, 16]                ReLU           0.2       MSELoss      Adam   \n",
       "1      [32, 16]                ReLU           0.2       MSELoss      Adam   \n",
       "2      [32, 16]                ReLU           0.2       MSELoss      Adam   \n",
       "3      [32, 16]                ReLU           0.2       MSELoss      Adam   \n",
       "4      [32, 16]                ReLU           0.2       MSELoss      Adam   \n",
       "\n",
       "   Learning Rate  Weight Decay  Epochs  Batch Size  Seed  Test Size  \\\n",
       "0         0.0001         0.001    6000          32    42        0.2   \n",
       "1         0.0001         0.001    6000          32    42        0.2   \n",
       "2         0.0001         0.001    6000          32    42        0.2   \n",
       "3         0.0001         0.001    6000          32    42        0.2   \n",
       "4         0.0001         0.001    6000          32    42        0.2   \n",
       "\n",
       "   N_Samples  Best Loss  Patience  Patience Counter  Average Accuracy  \\\n",
       "0        300  30.601368       100               100          0.960678   \n",
       "1        300  30.601368       100               100          0.960678   \n",
       "2        300  30.601368       100               100          0.960678   \n",
       "3        300  34.014599       100               100          0.954759   \n",
       "4        300  45.079739       100               100          0.940928   \n",
       "\n",
       "  Average Accuracy (%)  \n",
       "0               96.07%  \n",
       "1               96.07%  \n",
       "2               96.07%  \n",
       "3               95.48%  \n",
       "4               94.09%  "
      ]
     },
     "execution_count": 75,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "# Define new parameters as a dictionary\n",
    "new_params = {\n",
    "    \"Hidden Layers\": [HIDDEN_LAYERS],\n",
    "    \"Activation Function\": [ACTIVATION.__name__],\n",
    "    \"Dropout Rate\": [DROPOUT],\n",
    "    \"Loss Function\": [LOSS_FN.__name__],\n",
    "    \"Optimizer\": [OPTIMIZER_FN.__name__],\n",
    "    \"Learning Rate\": [LEARNING_RATE],\n",
    "    \"Weight Decay\": [WEIGHT_DECAY],\n",
    "    \"Epochs\": [EPOCHS],\n",
    "    \"Batch Size\": [BATCH_SIZE],\n",
    "    \"Seed\": [SEED],\n",
    "    \"Test Size\": [TEST_SIZE],\n",
    "    \"N_Samples\": [N_SAMPLES],\n",
    "    \"Best Loss\": [BEST_LOSS],\n",
    "    \"Patience\": [PATIENCE],\n",
    "    \"Patience Counter\": [PATIENCE_COUNTER],\n",
    "    \"Average Accuracy\": accuracy,  # Keep as float for sorting\n",
    "    \"Average Accuracy (%)\": f\"{round(accuracy * 100, 2)}%\"  # Display version\n",
    "\n",
    "}\n",
    "\n",
    "# Convert the dictionary to a DataFrame\n",
    "new_params_df = pd.DataFrame(new_params)\n",
    "\n",
    "# Initialize params as an empty DataFrame if it doesn't exist\n",
    "if 'params' not in locals():\n",
    "    params = pd.DataFrame()\n",
    "\n",
    "# Append the new parameters to the existing DataFrame\n",
    "params = pd.concat([params, new_params_df], ignore_index=True).sort_values(by=\"Average Accuracy\", ascending=False).reset_index(drop=True)\n",
    "\n",
    "# Print the updated DataFrame\n",
    "params"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 76,
   "metadata": {},
   "outputs": [
    {
     "ename": "ValueError",
     "evalue": "non-broadcastable output operand with shape (7,1) doesn't match the broadcast shape (7,5)",
     "output_type": "error",
     "traceback": [
      "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
      "\u001b[0;31mValueError\u001b[0m                                Traceback (most recent call last)",
      "Cell \u001b[0;32mIn[76], line 22\u001b[0m\n\u001b[1;32m     19\u001b[0m scaler\u001b[38;5;241m.\u001b[39mfit(numeric_features)\n\u001b[1;32m     21\u001b[0m \u001b[38;5;66;03m# Inverse scale forecast\u001b[39;00m\n\u001b[0;32m---> 22\u001b[0m pred_values \u001b[38;5;241m=\u001b[39m \u001b[43mscaler\u001b[49m\u001b[38;5;241;43m.\u001b[39;49m\u001b[43minverse_transform\u001b[49m\u001b[43m(\u001b[49m\u001b[43mnp\u001b[49m\u001b[38;5;241;43m.\u001b[39;49m\u001b[43marray\u001b[49m\u001b[43m(\u001b[49m\u001b[43mpredictions\u001b[49m\u001b[43m)\u001b[49m\u001b[38;5;241;43m.\u001b[39;49m\u001b[43mreshape\u001b[49m\u001b[43m(\u001b[49m\u001b[38;5;241;43m-\u001b[39;49m\u001b[38;5;241;43m1\u001b[39;49m\u001b[43m,\u001b[49m\u001b[43m \u001b[49m\u001b[38;5;241;43m1\u001b[39;49m\u001b[43m)\u001b[49m\u001b[43m)\u001b[49m\u001b[38;5;241m.\u001b[39mflatten()\n\u001b[1;32m     24\u001b[0m \u001b[38;5;66;03m# Plot last 30 days + forecast\u001b[39;00m\n\u001b[1;32m     25\u001b[0m plt\u001b[38;5;241m.\u001b[39mfigure(figsize\u001b[38;5;241m=\u001b[39m(\u001b[38;5;241m10\u001b[39m, \u001b[38;5;241m5\u001b[39m))\n",
      "File \u001b[0;32m~/opt/anaconda3/lib/python3.9/site-packages/sklearn/preprocessing/_data.py:581\u001b[0m, in \u001b[0;36mMinMaxScaler.inverse_transform\u001b[0;34m(self, X)\u001b[0m\n\u001b[1;32m    571\u001b[0m xp, _ \u001b[38;5;241m=\u001b[39m get_namespace(X)\n\u001b[1;32m    573\u001b[0m X \u001b[38;5;241m=\u001b[39m check_array(\n\u001b[1;32m    574\u001b[0m     X,\n\u001b[1;32m    575\u001b[0m     copy\u001b[38;5;241m=\u001b[39m\u001b[38;5;28mself\u001b[39m\u001b[38;5;241m.\u001b[39mcopy,\n\u001b[0;32m   (...)\u001b[0m\n\u001b[1;32m    578\u001b[0m     ensure_all_finite\u001b[38;5;241m=\u001b[39m\u001b[38;5;124m\"\u001b[39m\u001b[38;5;124mallow-nan\u001b[39m\u001b[38;5;124m\"\u001b[39m,\n\u001b[1;32m    579\u001b[0m )\n\u001b[0;32m--> 581\u001b[0m X \u001b[38;5;241m-\u001b[39m\u001b[38;5;241m=\u001b[39m \u001b[38;5;28mself\u001b[39m\u001b[38;5;241m.\u001b[39mmin_\n\u001b[1;32m    582\u001b[0m X \u001b[38;5;241m/\u001b[39m\u001b[38;5;241m=\u001b[39m \u001b[38;5;28mself\u001b[39m\u001b[38;5;241m.\u001b[39mscale_\n\u001b[1;32m    583\u001b[0m \u001b[38;5;28;01mreturn\u001b[39;00m X\n",
      "\u001b[0;31mValueError\u001b[0m: non-broadcastable output operand with shape (7,1) doesn't match the broadcast shape (7,5)"
     ]
    }
   ],
   "source": [
    "# Start with last test sequence\n",
    "forecast_steps = 7\n",
    "model.eval()\n",
    "last_seq = X_test[-1].clone()\n",
    "\n",
    "predictions = []\n",
    "with torch.no_grad():\n",
    "    for _ in range(forecast_steps):\n",
    "        pred = model(last_seq.unsqueeze(0))  # shape: (1, 1)\n",
    "        predictions.append(pred.item())\n",
    "\n",
    "        # Roll sequence forward\n",
    "        new_input = torch.cat((last_seq[1:], pred.view(-1)), dim=0)\n",
    "        last_seq = new_input\n",
    "\n",
    "# Recreate and fit the scaler\n",
    "scaler = MinMaxScaler()\n",
    "numeric_features = df[FEATURES].select_dtypes(include=[np.number])\n",
    "scaler.fit(numeric_features)\n",
    "\n",
    "# Inverse scale forecast\n",
    "pred_values = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()\n",
    "\n",
    "# Plot last 30 days + forecast\n",
    "plt.figure(figsize=(10, 5))\n",
    "plt.plot(df[\"timestamp\"][-30:], scaler.inverse_transform(df[\"observations\"].values[-30:].reshape(-1, 1)), label=\"Recent\")\n",
    "plt.plot(pd.date_range(df[\"timestamp\"].iloc[-1] + pd.Timedelta(days=1), periods=forecast_steps), pred_values, label=\"Forecast\")\n",
    "plt.title(\"📈 RNN Forecast\")\n",
    "plt.legend()\n",
    "plt.grid(True)\n",
    "plt.show()\n"
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
