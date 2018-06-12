# use a base64 encoded string of a gif image in Tkinter 
#(base64 converts binary data into string characters) 
# good for small images, avoids having to send the image file 
# the image string is created  with the following simple 
# Python code and is then copied and pasted to this program 
# (tk only uses gif, not all gif formats work properly!)

"""
import base64 
gif_file = "flag.gif" 
print "flag_gif='''\\\n" + base64.encodestring(open(gif_file).read()) + "'''" 
"""

# tested with Python25 EU 2/20/2007

import Tkinter as tk 
grape_gif='''\
R0lGODlhmACYAPcAAAAAAAAAMwAAZgAAmQAAzAAA/wArAAArMwArZgArmQArzAAr/wBVAABVMwBV
ZgBVmQBVzABV/wCAAACAMwCAZgCAmQCAzACA/wCqAACqMwCqZgCqmQCqzACq/wDVAADVMwDVZgDV
mQDVzADV/wD/AAD/MwD/ZgD/mQD/zAD//zMAADMAMzMAZjMAmTMAzDMA/zMrADMrMzMrZjMrmTMr
zDMr/zNVADNVMzNVZjNVmTNVzDNV/zOAADOAMzOAZjOAmTOAzDOA/zOqADOqMzOqZjOqmTOqzDOq
/zPVADPVMzPVZjPVmTPVzDPV/zP/ADP/MzP/ZjP/mTP/zDP//2YAAGYAM2YAZmYAmWYAzGYA/2Yr
AGYrM2YrZmYrmWYrzGYr/2ZVAGZVM2ZVZmZVmWZVzGZV/2aAAGaAM2aAZmaAmWaAzGaA/2aqAGaq
M2aqZmaqmWaqzGaq/2bVAGbVM2bVZmbVmWbVzGbV/2b/AGb/M2b/Zmb/mWb/zGb//5kAAJkAM5kA
ZpkAmZkAzJkA/5krAJkrM5krZpkrmZkrzJkr/5lVAJlVM5lVZplVmZlVzJlV/5mAAJmAM5mAZpmA
mZmAzJmA/5mqAJmqM5mqZpmqmZmqzJmq/5nVAJnVM5nVZpnVmZnVzJnV/5n/AJn/M5n/Zpn/mZn/
zJn//8wAAMwAM8wAZswAmcwAzMwA/8wrAMwrM8wrZswrmcwrzMwr/8xVAMxVM8xVZsxVmcxVzMxV
/8yAAMyAM8yAZsyAmcyAzMyA/8yqAMyqM8yqZsyqmcyqzMyq/8zVAMzVM8zVZszVmczVzMzV/8z/
AMz/M8z/Zsz/mcz/zMz///8AAP8AM/8AZv8Amf8AzP8A//8rAP8rM/8rZv8rmf8rzP8r//9VAP9V
M/9VZv9Vmf9VzP9V//+AAP+AM/+AZv+Amf+AzP+A//+qAP+qM/+qZv+qmf+qzP+q///VAP/VM//V
Zv/Vmf/VzP/V////AP//M///Zv//mf//zP///wAAAAAAAAAAAAAAACH5BAEAAPwALAAAAACYAJgA
AAj/APcJHEiwoMGDCBMqXMiwocOHECNKnEixosWLGDNqNAigI4CNIEOKHCnQo0dlJFOqXLnQZEeW
MGOudPlRps2bGGni3Mkzos6eQIMepFlTqNGeNNG8PMr0ps5MS5tKnelSILGoU7OCpCmGIFatYC3S
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
'''

"""
grape_gif = '''
    R0lGODlhEAAQAOeSAKx7Fqx8F61/G62CILCJKriIHM+HALKNMNCIANKKANOMALuRK7WOVLWPV9eR
    ANiSANuXAN2ZAN6aAN+bAOCcAOKeANCjKOShANKnK+imAOyrAN6qSNaxPfCwAOKyJOKyJvKyANW0
    R/S1APW2APW3APa4APe5APm7APm8APq8AO28Ke29LO2/LO2/L+7BM+7BNO6+Re7CMu7BOe7DNPHA
    P+/FOO/FO+jGS+/FQO/GO/DHPOjBdfDIPPDJQPDISPDKQPDKRPDIUPHLQ/HLRerMV/HMR/LNSOvH
    fvLOS/rNP/LPTvLOVe/LdfPRUfPRU/PSU/LPaPPTVPPUVfTUVvLPe/LScPTWWfTXW/TXXPTXX/XY
    Xu/SkvXZYPfVdfXaY/TYcfXaZPXaZvbWfvTYe/XbbvHWl/bdaPbeavvadffea/bebvffbfbdfPvb
    e/fgb/Pam/fgcvfgePTbnfbcl/bfivfjdvfjePbemfjelPXeoPjkePbfmvffnvbfofjlgffjkvfh
    nvjio/nnhvfjovjmlvzlmvrmpvrrmfzpp/zqq/vqr/zssvvvp/vvqfvvuPvvuvvwvfzzwP//////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    ////////////////////////////////////////////////////////////////////////////
    /////////////////////////////////////////////////////yH+FUNyZWF0ZWQgd2l0aCBU
    aGUgR0lNUAAh+QQBCgD/ACwAAAAAEAAQAAAIzAD/CRxIsKDBfydMlBhxcGAKNIkgPTLUpcPBJIUa
    +VEThswfPDQKokB0yE4aMFiiOPnCJ8PAE20Y6VnTQMsUBkWAjKFyQaCJRYLcmOFipYmRHzV89Kkg
    kESkOme8XHmCREiOGC/2TBAowhGcAyGkKBnCwwKAFnciCAShKA4RAhyK9MAQwIMMOQ8EdhBDKMuN
    BQMEFPigAsoRBQM1BGLjRIiOGSxWBCmToCCMOXSW2HCBo8qWDQcvMMkzCNCbHQga/qMgAYIDBQZU
    yxYYEAA7 '''
"""

root = tk.Tk() 

gif_image = tk.PhotoImage(data=grape_gif) 

b1 = tk.Button(root, image=gif_image) 
b1.pack(pady=10)

# save the button image from garbage collection!
b1.image = gif_image

root.mainloop()

