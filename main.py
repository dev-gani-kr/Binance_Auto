import sys
import re
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QApplication, QMainWindow, QHeaderView, QTableWidgetItem
from PyQt5.QtCore import QTimer, QThread,
from PyQt5 import uic
from datetime import datetime
import time
import ccxt

class PriceUpdater(QThread):
    def __init__(self, table, parent=None):
        super().__init__(parent)
        self.table = table

    def run(self):
        font = QFont()
        font.setBold(True)
        while True:
            # Binance 거래소에 연결합니다.
            binance = ccxt.binance()

            for i in range(self.table.rowCount()):
                coin    = self.table.item(i, 0).text()
                amount  = float(self.table.item(i, 1).text())

                # BTC 가격 가져오기
                ticker  = binance.fetch_ticker(f'{coin}/USDT')
                price   = float(ticker['last'])
                open    = float(ticker['open'])
                pnl = (price/open - 1) * 100
                self.table.item(i, 2).setText(str(price))
                self.table.item(i, 3).setText(f'{pnl:.2f}%')
                self.table.item(i, 3).setFont(font)
                if pnl > 0:
                    self.table.item(i, 3).setForeground(QColor(0, 255, 0))
                else:
                    self.table.item(i, 3).setForeground(QColor(255, 0, 0))

            # 5초마다 업데이트
            time.sleep(10)

class TimeUpdater(QThread):
    def __init__(self, status_bar, parent=None):
        super().__init__(parent)
        self.status_bar = status_bar

    def run(self):
        while True:
            # Binance 거래소에 연결합니다.
            binance = ccxt.binance()

            # 서버 시간 가져오기 (정수 타입)
            server_time_int = binance.fetch_time()

            # 정수 타입의 서버 시간을 datetime 객체로 변환
            server_time_datetime = datetime.fromtimestamp(server_time_int / 1000)

            # 서버 시간을 원하는 형식으로 포맷
            formatted_time = server_time_datetime.strftime('%Y-%m-%d %H:%M:%S:%f')
            self.status_bar.showMessage(f'{formatted_time}')

class BinancePriceApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Binance 가격 정보')
        self.setGeometry(100, 100, 300, 150)
        uic.loadUi("ui.ui", self)

        self.lineEdit_2.cursorPositionChanged.connect(self.clear)
        self.lineEdit_2.textChanged.connect(self.on_text_changed)
        self.buttonGroup.buttonClicked.connect(self.order)

        self.time_updater = TimeUpdater(self.statusBar())
        self.time_updater.start()
        self.price_updater = PriceUpdater(self.asset_table)
        self.price_updater.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.alignTable)
        self.timer.start(1000)

    def order(self, button):
        current_datetime = datetime.now()
        Date = current_datetime.strftime("%Y-%m-%d")
        pair = self.comboBox.currentText() + '/USDT'

        price = round(float(re.findall(r'\d+', self.lineEdit.text())[0]), 2)
        amount = round(float(re.findall(r'\d+', self.lineEdit_2.text())[0]), 2)
        if button.text() == "매수":
            side = "Buy"
        else:
            side = "Sell"

        total = price * amount

        row_count = self.order_table.rowCount()
        self.order_table.insertRow(row_count)

        # 새로운 행에 데이터 추가
        for i in range(6):
            item = QTableWidgetItem('')
            self.order_table.setItem(row_count, i, item)

        self.order_table.item(row_count, 0).setText(Date)
        self.order_table.item(row_count, 1).setText(pair)
        self.order_table.item(row_count, 2).setText(side)
        self.order_table.item(row_count, 3).setText(f'{price:.2f}')
        self.order_table.item(row_count, 4).setText(f'{amount:.2f}')
        self.order_table.item(row_count, 5).setText(f'{total:.2f}')

    def on_text_changed(self):
        amount = re.findall(r'\d+', self.lineEdit.text())[0]
        price = self.lineEdit_2.text()

        if price == '':
            price = '0'

        total = float(amount) * float(price)
        self.lineEdit_3.setText(f'{total:.4f}')

    def clear(self):
        if self.lineEdit_2.text() == '0.0':
            self.lineEdit_2.clear()  # 사용자가 실제로 값을 입력할 때 기본 값 삭제

    def alignTable(self):
        # 열 너비를 데이터에 맞추기
        self.asset_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.asset_table.resizeColumnsToContents()
        self.asset_table.resizeRowsToContents()
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.order_table.resizeColumnsToContents()
        self.order_table.resizeRowsToContents()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = BinancePriceApp()
    window.show()
    sys.exit(app.exec_())