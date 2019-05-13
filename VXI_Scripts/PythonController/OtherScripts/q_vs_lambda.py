import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
csfont = {'fontname': 'Times New Roman'}

I_nocell = [0.0340,
            0.0291,
            0.0241,
            0.0192,
            0.0172,
            0.0143,
            0.0113,
            0.0093,
            0.0073
            ]

q_nocell = [0.7159,
            0.5171,
            0.353366667,
            0.221933333,
            0.177933333,
            0.121466667,
            0.076133333,
            0.051666667,
            0.032066667
            ]
q_err_nocell = [0.000365148,
                0.000458258,
                0.000251661,
                0.000404145,
                0.000208167,
                0.000251661,
                0.00011547,
                5.7735E-05,
                5.7735E-05
                ]

lambda_nocell = [0.3153,
                 0.155066667,
                 0.075333333,
                 0.026133333,
                 0.019666667,
                 0.009133333,
                 0.003533333,
                 0.0016,
                 0.0005
                 ]
lambda_err_nocell = [0.010722873,
                     0.004313158,
                     0.002003331,
                     0.004015387,
                     0.00023094,
                     0.00051316,
                     0.000378594,
                     0.000173205,
                     0.0001
                     ]

I_cell = [0.034,
          0.0291,
          0.0241,
          0.0192,
          0.0143,
          0.0093
          ]

q_cell = [0.7365,
          0.5302,
          0.3604,
          0.225,
          0.1235,
          0.0524
          ]
q_err_cell = []

lambda_cell = [0.3892,
               0.1951,
               0.0936,
               0.0358,
               0.0107,
               0.0019
               ]
lambda_err_cell = []

plt.figure()

plt.errorbar(q_nocell, lambda_nocell,
             fmt='--o', markersize=3, linewidth=1, elinewidth=0.5, ecolor='k', capsize=5, capthick=0.5, label="Without cell")

plt.errorbar(q_cell, lambda_cell, fmt='r--o', markersize=3, linewidth=1,
             elinewidth=0.5, ecolor='k', capsize=5, capthick=0.5, label="With cell")

plt.plot([0, 0.8], [0.025596, 0.025596], 'y--', lw=1, label=r"$\lambda_{air}$")

plt.xlabel(r'q (W/m)', size=15, **csfont)
#plt.grid(False, linestyle='--')
plt.ylim(0, 0.4)
plt.xlim(0, 0.8)
plt.xticks(fontsize=14, **csfont)
plt.yticks(fontsize=14, **csfont)
plt.ylabel(r' $\lambda$ (W/mK)', size=15, **csfont)
plt.legend(prop={'family': 'Times New Roman', 'size': 12})
plt.show()
