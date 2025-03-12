import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime

def process_central_database():
    # Központi adatbázis elérési útja
    central_db = '/home/tibor/Projects/energia_monitoring/CSV-normalis/energia_adatok.csv'
    
    try:
        # Központi adatbázis beolvasása
        df = pd.read_csv(central_db, delimiter=';', encoding='cp1252', decimal=',')
        df['Kezdo_datum'] = pd.to_datetime(df['Kezdo_datum'])
        
        # Napi összesítés
        daily_df = df.groupby(df['Kezdo_datum'].dt.date).agg({
            'Hatasos_ertek_kWh': 'sum'
        }).reset_index()
        daily_df['Kezdo_datum'] = pd.to_datetime(daily_df['Kezdo_datum'])
        
        # Óránkénti átlagok számítása
        hourly_avg = df.groupby(df['Kezdo_datum'].dt.hour)['Hatasos_ertek_kWh'].mean()
        
        # Két grafikon egymás alatt
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))
        
        # Napi fogyasztás grafikon
        ax1.plot(daily_df['Kezdo_datum'], daily_df['Hatasos_ertek_kWh'], marker='o')
        ax1.set_title('Napi Összfogyasztás', fontsize=14)
        ax1.set_xlabel('Dátum', fontsize=12)
        ax1.set_ylabel('Fogyasztás (kWh)', fontsize=12)
        ax1.grid(True, linestyle='--', alpha=0.7)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
        
        # Átlagos óránkénti fogyasztás grafikon
        ax2.bar(hourly_avg.index, hourly_avg.values)
        ax2.set_title('Átlagos Óránkénti Fogyasztás', fontsize=14)
        ax2.set_xlabel('Óra', fontsize=12)
        ax2.set_ylabel('Átlagos Fogyasztás (kWh)', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        
        # Ellenőrizzük, hogy létezik-e az output könyvtár
        output_dir = '/home/tibor/Projects/energia_monitoring/output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        plt.savefig(os.path.join(output_dir, 'fogyasztas_elemzes.png'))
        plt.close()
        
        # Statisztikák kiírása
        print("\nStatisztikák:")
        print(f"Átlagos napi fogyasztás: {daily_df['Hatasos_ertek_kWh'].mean():.2f} kWh")
        print(f"Maximum fogyasztás: {daily_df['Hatasos_ertek_kWh'].max():.2f} kWh " +
              f"({daily_df.loc[daily_df['Hatasos_ertek_kWh'].idxmax(), 'Kezdo_datum'].strftime('%Y-%m-%d')})")
        print(f"Minimum fogyasztás: {daily_df['Hatasos_ertek_kWh'].min():.2f} kWh " +
              f"({daily_df.loc[daily_df['Hatasos_ertek_kWh'].idxmin(), 'Kezdo_datum'].strftime('%Y-%m-%d')})")
        
        print("\nLegmagasabb fogyasztású órák:")
        print(hourly_avg.nlargest(3))
        
    except Exception as e:
        print(f"Hiba történt: {str(e)}")

if __name__ == "__main__":
    process_central_database()
