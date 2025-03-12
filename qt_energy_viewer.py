import logging
from debug_utils import setup_logger
import sys
import os
import pandas as pd
import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QWidget, QLabel, QComboBox, QPushButton, QSlider, 
                           QGroupBox, QDateEdit)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from openpyxl.utils import get_column_letter
import shutil
from datetime import datetime, timedelta

# Reportlab importok a PDF generáláshoz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class EnergyViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Energiafigyelő")
        self.setGeometry(100, 100, 1200, 700)
        self.current_theme = 'dark_background'
        
        # Központi widget és fő elrendezés
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Fejléc
        header = QWidget()
        header_layout = QHBoxLayout()
        title_label = QLabel("Energiafogyasztás Elemző")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header_layout.addWidget(title_label)
        header.setLayout(header_layout)
        main_layout.addWidget(header)
        
        # Vezérlő panel
        control_panel = QGroupBox("Grafikon Beállítások")
        control_layout = QVBoxLayout()
        
        # Időszak választó panel hozzáadása
        control_layout.addWidget(self.setup_time_period_controls())
        
        # Megjelenítési beállítások
        display_settings = QHBoxLayout()
        
        # Időbontás kiválasztó
        time_layout = QHBoxLayout()
        time_label = QLabel("Időbontás:")
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Napi", "Heti", "Havi"])
        self.time_combo.currentIndexChanged.connect(self.plot_data)
        time_layout.addWidget(time_label)
        time_layout.addWidget(self.time_combo)
        display_settings.addLayout(time_layout)
        
        # Téma kiválasztó
        theme_layout = QHBoxLayout()
        theme_label = QLabel("Téma:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Világos", "Sötét"])
        self.theme_combo.setCurrentIndex(1)
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.theme_combo)
        display_settings.addLayout(theme_layout)
        
        control_layout.addLayout(display_settings)
        
        # Egységár és gombok panel
        buttons_layout = QHBoxLayout()
        
        # Fix egységár
        price_label = QLabel("Egységár:")
        price_value_label = QLabel("56.07 Ft/kWh")
        buttons_layout.addWidget(price_label)
        buttons_layout.addWidget(price_value_label)
        
        # Frissítés gomb
        refresh_btn = QPushButton("Frissítés")
        refresh_btn.clicked.connect(self.plot_data)
        buttons_layout.addWidget(refresh_btn)
        
        # Export gombok hozzáadása
        export_layout = self.setup_export_buttons()
        buttons_layout.addLayout(export_layout)
        
        control_layout.addLayout(buttons_layout)
        control_panel.setLayout(control_layout)
        main_layout.addWidget(control_panel)
        
        # Grafikon terület
        self.figure_widget = QWidget()
        figure_layout = QVBoxLayout()
        self.figure_widget.setLayout(figure_layout)
        main_layout.addWidget(self.figure_widget)
        
        # Státusz címke
        self.label = QLabel("")
        main_layout.addWidget(self.label)
        
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Statisztikák tárolása az osztályban
        self.current_stats = {
            'napi_atlag': 0,
            'minimum': 0,
            'maximum': 0,
            'eves_becsles': 0,
            'eves_koltseg': 0
        }
        
        # Kezdeti adatok betöltése
        self.plot_data()

    def setup_time_period_controls(self):
        """Időszak választó vezérlők beállítása"""
        time_period_group = QGroupBox("Időszak választás")
        layout = QHBoxLayout()

        # Quick pick gombok
        quick_picks_layout = QHBoxLayout()
        quick_picks_label = QLabel("Gyors választás:")
        self.quick_period = QComboBox()
        self.quick_period.addItems([
            "Egyedi időszak",
            "Mai nap",
            "Előző 7 nap",
            "Előző hónap",
            "Aktuális hét",
            "Aktuális hónap",
            "Aktuális év"
        ])
        self.quick_period.currentIndexChanged.connect(self.handle_quick_pick)
        quick_picks_layout.addWidget(quick_picks_label)
        quick_picks_layout.addWidget(self.quick_period)
        layout.addLayout(quick_picks_layout)

        # Dátumválasztók
        date_layout = QHBoxLayout()
        start_label = QLabel("Kezdő dátum:")
        self.start_date = QDateEdit(calendarPopup=True)
        end_label = QLabel("Végső dátum:")
        self.end_date = QDateEdit(calendarPopup=True)
        
        # Alapértelmezett dátumok (előző 7 nap)
        today = QDate.currentDate()
        self.start_date.setDate(today.addDays(-7))
        self.end_date.setDate(today)
        
        date_layout.addWidget(start_label)
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(end_label)
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)

        time_period_group.setLayout(layout)
        return time_period_group

    def setup_export_buttons(self):
        """Export gombok létrehozása"""
        export_layout = QHBoxLayout()
        
        # Excel export gomb
        excel_btn = QPushButton("Exportálás Excel (XLSX)")
        excel_btn.clicked.connect(self.export_to_excel)
        export_layout.addWidget(excel_btn)
        
        # PDF export gomb
        pdf_btn = QPushButton("PDF Riport")
        pdf_btn.clicked.connect(self.export_to_pdf)
        export_layout.addWidget(pdf_btn)
        
        return export_layout

    def handle_quick_pick(self, index):
        """Quick pick választás kezelése"""
        today = QDate.currentDate()
        
        if index == 1:  # Mai nap
            self.start_date.setDate(today)
            self.end_date.setDate(today)
        
        elif index == 2:  # Előző 7 nap
            self.start_date.setDate(today.addDays(-7))
            self.end_date.setDate(today)
        
        elif index == 3:  # Előző hónap
            first_day = QDate(today.year(), today.month(), 1)
            self.start_date.setDate(first_day.addMonths(-1))
            self.end_date.setDate(first_day.addDays(-1))
        
        elif index == 4:  # Aktuális hét
            self.start_date.setDate(today.addDays(-today.dayOfWeek() + 1))
            self.end_date.setDate(today)
        
        elif index == 5:  # Aktuális hónap
            self.start_date.setDate(QDate(today.year(), today.month(), 1))
            self.end_date.setDate(today)
        
        elif index == 6:  # Aktuális év
            self.start_date.setDate(QDate(today.year(), 1, 1))
            self.end_date.setDate(today)
        
        self.plot_data()

    def change_theme(self, index):
        plt.close('all')
        if index == 0:  # Világos téma
            self.current_theme = 'default'
            plt.style.use('default')
        else:  # Sötét téma
            self.current_theme = 'dark_background'
            plt.style.use('dark_background')
            plt.rcParams['figure.facecolor'] = '#1e1e1e'
            plt.rcParams['axes.facecolor'] = '#1e1e1e'
            plt.rcParams['axes.edgecolor'] = '#666666'
            plt.rcParams['grid.color'] = '#333333'
            plt.rcParams['text.color'] = '#ffffff'
            plt.rcParams['axes.labelcolor'] = '#ffffff'
            plt.rcParams['xtick.color'] = '#ffffff'
            plt.rcParams['ytick.color'] = '#ffffff'
        self.plot_data()

    def plot_data(self):
        try:
            plt.close('all')
            
            # CSV fájl elérési útja
            csv_file = os.path.join(os.path.dirname(__file__), "CSV-normalis", "energia_adatok.csv")
            
            if not os.path.exists(csv_file):
                self.label.setText(f"Hiba: Az adatfájl nem található: {csv_file}")
                return
            
            # Adatok beolvasása és feldolgozása
            df = pd.read_csv(csv_file, delimiter=";", encoding="utf-8")
            df['Kezdo_datum'] = pd.to_datetime(df['Kezdo_datum'], errors='coerce')
            
            # Időszak szűrése
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # Dátum szűrés
            mask = (df['Kezdo_datum'].dt.date >= start_date) & (df['Kezdo_datum'].dt.date <= end_date)
            df = df[mask]
            
            if df.empty:
                self.label.setText("Nincs megjeleníthető adat a kiválasztott időszakban!")
                return
            
            # Adatok konvertálása és összegzése
            df['Hatasos_ertek_kWh'] = df['Hatasos_ertek_kWh'].str.replace(',', '.')
            df['Hatasos_ertek_kWh'] = pd.to_numeric(df['Hatasos_ertek_kWh'], errors='coerce')
            
            # Fix egységár
            egysegar = 56.07
            
            # Időbontás szerinti csoportosítás
            interval = self.time_combo.currentText()
            if interval == "Heti":
                df = df.groupby(pd.Grouper(key='Kezdo_datum', freq='W'))['Hatasos_ertek_kWh'].sum().reset_index()
            elif interval == "Havi":
                df = df.groupby(pd.Grouper(key='Kezdo_datum', freq='M'))['Hatasos_ertek_kWh'].sum().reset_index()
            else:  # Napi
                df = df.groupby(df['Kezdo_datum'].dt.date)['Hatasos_ertek_kWh'].sum().reset_index()
                df['Kezdo_datum'] = pd.to_datetime(df['Kezdo_datum'])
            
            # Grafikon létrehozása
            fig = plt.figure(figsize=(12, 6))
            ax = plt.gca()
            
            # Fogyasztási adatok
            ax.plot(df['Kezdo_datum'], df['Hatasos_ertek_kWh'], marker='o', linestyle='-', 
                   label='Fogyasztás (kWh)', color='#1f77b4')
            
            # Átlagvonal
            atlag_fogyasztas = df['Hatasos_ertek_kWh'].mean()
            ax.axhline(y=atlag_fogyasztas, color='#20B2AA', linestyle='--', 
                      label=f'Átlag ({atlag_fogyasztas:.2f} kWh)')
            
            # Címek és feliratok
            title = f"Energiafogyasztás {interval} bontás\n{start_date} - {end_date}"
            ax.set_title(title)
            ax.set_xlabel("Dátum")
            ax.set_ylabel("Fogyasztás (kWh)")
            
            # Statisztikai adatok számítása
            idoszak_napok = (end_date - start_date).days + 1
            napi_atlag = df['Hatasos_ertek_kWh'].sum() / idoszak_napok
            eves_becsles = napi_atlag * 365
            eves_koltseg_becsles = eves_becsles * egysegar

            # Aktuális hónap adatainak kiszámítása
            current_month = pd.Timestamp.now().replace(day=1)
            month_mask = (df['Kezdo_datum'] >= current_month) & (df['Kezdo_datum'] < current_month + pd.offsets.MonthEnd(1))
            current_month_data = df[month_mask]
            current_month_usage = current_month_data['Hatasos_ertek_kWh'].sum()
            current_month_cost = current_month_usage * egysegar

            # Becsült havi költség (az eddigi napi átlag alapján)
            days_in_month = pd.Timestamp.now().days_in_month
            days_so_far = pd.Timestamp.now().day
            if not current_month_data.empty:
                daily_avg_this_month = current_month_usage / days_so_far
                estimated_month_total = daily_avg_this_month * days_in_month
                estimated_month_cost = estimated_month_total * egysegar
            else:
                estimated_month_total = 0
                estimated_month_cost = 0
            
            # A statisztikák elmentése az osztályban
            self.current_stats = {
                'napi_atlag': napi_atlag,
                'minimum': df['Hatasos_ertek_kWh'].min(),
                'maximum': df['Hatasos_ertek_kWh'].max(),
                'eves_becsles': eves_becsles,
                'eves_koltseg': eves_koltseg_becsles
            }
            
            # Statisztikák szövege
            stat_text = (
                f"Átlagos napi: {napi_atlag:.2f} kWh\n"
                f"Minimum: {df['Hatasos_ertek_kWh'].min():.2f} kWh\n"
                f"Maximum: {df['Hatasos_ertek_kWh'].max():.2f} kWh\n"
                f"Becsült éves: {eves_becsles:,.0f} kWh\n"
                f"Éves költség: {eves_koltseg_becsles:,.0f} Ft\n\n"
                f"Aktuális hónap:\n"
                f"Eddigi fogyasztás: {current_month_usage:.2f} kWh\n"
                f"Eddigi költség: {current_month_cost:,.0f} Ft\n"
                f"Becsült havi: {estimated_month_total:.2f} kWh\n"
                f"Becsült költség: {estimated_month_cost:,.0f} Ft"
            )
            
            # Statisztikák elhelyezése
            plt.text(1.02, 0.5, stat_text,
                    transform=ax.transAxes,
                    fontname='Ubuntu',
                    fontsize=10,
                    verticalalignment='center',
                    horizontalalignment='left',
                    color='white' if self.current_theme == 'dark_background' else 'black')
            
            ax.grid(True)
            ax.legend()
            plt.subplots_adjust(right=0.85)
            
            # Grafikon beágyazása
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            canvas = FigureCanvas(plt.gcf())
            
            # Régi grafikon törlése
            for i in reversed(range(self.figure_widget.layout().count())): 
                self.figure_widget.layout().itemAt(i).widget().setParent(None)
            
            self.figure_widget.layout().addWidget(canvas)
            
        except Exception as e:
            self.label.setText(f"Hiba történt: {str(e)}")
            print(f"Részletes hibaüzenet: {str(e)}")

    def export_to_excel(self):
        try:
            # CSV fájl beolvasása
            csv_file = os.path.join(os.path.dirname(__file__), "CSV-normalis", "energia_adatok.csv")
            df = pd.read_csv(csv_file, delimiter=";", encoding="utf-8")
            df['Kezdo_datum'] = pd.to_datetime(df['Kezdo_datum'], errors='coerce')
            
            # Adatok konvertálása
            df['Hatasos_ertek_kWh'] = df['Hatasos_ertek_kWh'].str.replace(',', '.')
            df['Hatasos_ertek_kWh'] = pd.to_numeric(df['Hatasos_ertek_kWh'], errors='coerce')
            
            # Időszak szűrése
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            mask = (df['Kezdo_datum'].dt.date >= start_date) & (df['Kezdo_datum'].dt.date <= end_date)
            df = df[mask]
            
            # Napi összesítés
            daily_df = df.groupby(df['Kezdo_datum'].dt.date).agg({
                'Hatasos_ertek_kWh': ['sum', 'mean', 'min', 'max', 'count']
            }).reset_index()
            
            # Oszlopok átnevezése
            daily_df.columns = ['Dátum', 'Napi fogyasztás (kWh)', 'Átlagos fogyasztás (kWh)', 
                              'Minimum (kWh)', 'Maximum (kWh)', 'Mérések száma']
            
            # Excel fájl létrehozása több munkalappal
            output_dir = os.path.join(os.path.dirname(__file__), "export")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            excel_file = os.path.join(output_dir, f'energia_statisztika_{timestamp}.xlsx')
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # Napi adatok
                daily_df.to_excel(writer, sheet_name='Napi összesítés', index=False)
                
                # Részletes adatok
                df.to_excel(writer, sheet_name='Részletes adatok', index=False)
                
                # Statisztikák
                stats_df = pd.DataFrame({
                    'Mutató': ['Időszak kezdete', 'Időszak vége', 'Összes fogyasztás (kWh)',
                              'Napi átlag (kWh)', 'Becsült éves fogyasztás (kWh)',
                              'Becsült éves költség (Ft)'],
                    'Érték': [
                        start_date,
                        end_date,
                        daily_df['Napi fogyasztás (kWh)'].sum(),
                        daily_df['Napi fogyasztás (kWh)'].mean(),
                        daily_df['Napi fogyasztás (kWh)'].mean() * 365,
                        daily_df['Napi fogyasztás (kWh)'].mean() * 365 * 56.07
                    ]
                })
                stats_df.to_excel(writer, sheet_name='Statisztikák', index=False)
                
                # Munkafüzet formázása
                workbook = writer.book
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    # Oszlopszélességek beállítása
                    for idx, col in enumerate(worksheet.columns, 1):
                        max_length = 0
                        column = get_column_letter(idx)
                        for cell in col:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column].width = adjusted_width
            
            self.label.setText(f"Excel fájl exportálva: {excel_file}")
            
        except Exception as e:
            self.label.setText(f"Hiba történt az Excel exportálás során: {str(e)}")
            print(f"Részletes hibaüzenet: {str(e)}")

    def export_to_pdf(self):
        try:
            # Időszak adatai
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # PDF fájl létrehozása
            output_dir = os.path.join(os.path.dirname(__file__), "export")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
            pdf_file = os.path.join(output_dir, f'energia_riport_{timestamp}.pdf')
            
            # Grafikon mentése képként
            plt.savefig('temp_plot.png', bbox_inches='tight', dpi=300)
            plt.close()
            
            # PDF dokumentum létrehozása
            doc = SimpleDocTemplate(pdf_file, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Címsor
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30
            )
            story.append(Paragraph("Energia Fogyasztási Riport", title_style))
            story.append(Spacer(1, 12))
            
            # Időszak
            story.append(Paragraph(f"Időszak: {start_date} - {end_date}", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # Grafikon beszúrása
            img = Image('temp_plot.png', width=7*inch, height=4*inch)
            story.append(img)
            story.append(Spacer(1, 12))
            
            # Statisztikai adatok táblázata
            stats_data = [
                ['Mutató', 'Érték'],
                ['Átlagos napi fogyasztás', f"{self.current_stats['napi_atlag']:.2f} kWh"],
                ['Minimum fogyasztás', f"{self.current_stats['minimum']:.2f} kWh"],
                ['Maximum fogyasztás', f"{self.current_stats['maximum']:.2f} kWh"],
                ['Becsült éves fogyasztás', f"{self.current_stats['eves_becsles']:,.0f} kWh"],
                ['Becsült éves költség', f"{self.current_stats['eves_koltseg']:,.0f} Ft"],
            ]
            
            t = Table(stats_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(t)
            
            # PDF generálása
            doc.build(story)
            
            # Ideiglenes fájl törlése
            os.remove('temp_plot.png')
            
            self.label.setText(f"PDF riport exportálva: {pdf_file}")
            
        except Exception as e:
            self.label.setText(f"Hiba történt a PDF exportálás során: {str(e)}")
            print(f"Részletes hibaüzenet: {str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EnergyViewer()
    window.show()
    sys.exit(app.exec())
