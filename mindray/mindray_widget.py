import numpy as np
from PyQt5.QtWidgets import QWidget, QGridLayout
from pyqtgraph import PlotWidget, ViewBox, PlotCurveItem


class MindrayWidget(QWidget):
    def __init__(self):
        super(MindrayWidget, self).__init__()
        self.setLayout(QGridLayout())

        self.hr_plot = PlotWidget(title='HR')
        self.pvc_plot = PlotWidget(title='PVC sum')
        self.spo2_plot = PlotWidget(title='Spo2')
        self.rr_plot = PlotWidget(title='RespiratoryRate')
        self.layout().addWidget(self.hr_plot, 0, 0, 1, 1)
        self.layout().addWidget(self.pvc_plot, 0, 1, 1, 1)
        self.layout().addWidget(self.spo2_plot, 1, 0, 1, 1)
        for i, plot in enumerate([self.hr_plot, self.pvc_plot, self.spo2_plot, self.rr_plot]):
            self.layout().addWidget(plot, i % 2, i // 2, 1, 1)
            plot.setBackground('w')
            plot.showGrid(x=True, y=True, alpha=0.7)
            plot.addLegend()

        self.hr_mindray = self.hr_plot.plot(name='mindray-ecg', pen=(255, 0, 0))
        self.hr_oxyzen = self.hr_plot.plot(name='oxyzen', pen=(0, 0, 255))
        self.pr_mindray = self.hr_plot.plot(name='mindray-pr', pen=(0,0,0))

        self.pvc_mindray = self.pvc_plot.plot(name='mindray', pen=(255, 0, 0))

        self.spo2_mindray = self.spo2_plot.plot(name='mindray', pen=(255, 0, 0))
        self.spo2_oxyzen = self.spo2_plot.plot(name='oxyzen', pen=(0, 0, 255))

        self.rr_mindray = self.rr_plot.plot(name='mindray', pen=(255, 0, 0))

    def update_plot(self, hr_o, spo2_o, hr_m, pvc_m, rr_m, spo2_m, pr_m):
        hr_o = hr_o/10 if hr_o is not None else None
        spo2_o = spo2_o/10 if hr_o is not None else None
        for data, curve in zip([hr_o, spo2_o],
                               [self.hr_oxyzen, self.spo2_oxyzen]):
            if data is not None:
                curve.setData(np.arange(len(data))/25, data)
        for data, curve in zip([hr_m, pvc_m, rr_m, spo2_m, pr_m],
                               [self.hr_mindray, self.pvc_mindray, self.rr_mindray, self.spo2_mindray, self.pr_mindray]):
            curve.setData(np.arange(len(data)), data)

