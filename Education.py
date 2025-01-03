import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import requests
import json
import os

# Create plots directory if it doesn't exist
os.makedirs('plots', exist_ok=True)

def get_education_data():
    url = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-1509090000_201/px-x-1509090000_201.px"
    
    # Updated query with all required variables
    query = {
        "query": [
            {
                "code": "Szenario",
                "selection": {
                    "filter": "item",
                    "values": ["0"]  # Referenzszenario
                }
            },
            {
                "code": "Bildungsstand",
                "selection": {
                    "filter": "item",
                    "values": ["1", "2", "3"]  # All education levels except "Ohne"
                }
            },
            {
                "code": "Geschlecht",
                "selection": {
                    "filter": "item",
                    "values": ["0", "1"]  # Both genders
                }
            },
            {
                "code": "Altersklasse",
                "selection": {
                    "filter": "item",
                    "values": ["0", "1", "2", "3", "4", "5", "6", "7"]  # All age groups
                }
            },
            {
                "code": "Jahr",
                "selection": {
                    "filter": "item",
                    "values": ["1", "6", "11", "16", "21", "26", "31"]  # Selected years (2020-2050 in 5-year steps)
                }
            }
        ],
        "response": {
            "format": "json-stat2"
        }
    }
    
    try:
        print("Fetching data from BFS API...")
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        response = requests.post(url, json=query, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print("Data received successfully!")
            return data
        else:
            print(f"API request failed: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_data(data):
    try:
        # Extract dimensions and values
        dimensions = data['dimension']
        values = data['value']
        
        # Create lists to store the data
        records = []
        
        # Get dimension values
        scenarios = list(dimensions['Szenario']['category']['label'].values())
        education_levels = list(dimensions['Bildungsstand']['category']['label'].values())
        genders = list(dimensions['Geschlecht']['category']['label'].values())
        age_groups = list(dimensions['Altersklasse']['category']['label'].values())
        years = list(dimensions['Jahr']['category']['label'].values())
        
        # Create DataFrame from the multidimensional array
        index = 0
        for s in range(data['size'][0]):  # Szenario
            for e in range(data['size'][1]):  # Bildungsstand
                for g in range(data['size'][2]):  # Geschlecht
                    for a in range(data['size'][3]):  # Altersklasse
                        for y in range(data['size'][4]):  # Jahr
                            records.append({
                                'Szenario': scenarios[s],
                                'Bildungsstand': education_levels[e],
                                'Geschlecht': genders[g],
                                'Altersklasse': age_groups[a],
                                'Jahr': years[y],
                                'Wert': values[index]
                            })
                            index += 1
        
        df = pd.DataFrame(records)
        
        # Convert Jahr to numeric
        df['Jahr'] = pd.to_numeric(df['Jahr'])
        
        print("\nDataFrame created successfully!")
        print("\nColumns:", df.columns.tolist())
        print("\nShape:", df.shape)
        print("\nSample data:")
        print(df.head())
        
        return df
        
    except Exception as e:
        print(f"Error processing data: {e}")
        return None

def create_modern_visualizations(df):
    # Use a valid style
    plt.style.use('default')  # Reset to default style
    sns.set_theme(style="white")  # Set seaborn theme
    
    colors = ['#2E5077', '#76B7B2', '#EF8536']  # Professional color palette
    
    # Set font properties
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 12,
        'axes.titlesize': 14
    })
    
    # 1. Main Trend Visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), 
                                  gridspec_kw={'width_ratios': [2, 1]})
    
    # Left plot - Time series
    for idx, bildung in enumerate(df['Bildungsstand'].unique()):
        data = df[df['Bildungsstand'] == bildung]
        yearly_avg = data.groupby('Jahr')['Wert'].mean()
        
        ax1.plot(yearly_avg.index, yearly_avg.values, 
                color=colors[idx], 
                linewidth=2.5,
                marker='o',
                markersize=6,
                label=bildung)
    
    # Customize left plot
    ax1.set_title('Bildungsentwicklung 2020-2050', 
                 pad=20, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.set_xlabel('Jahr')
    ax1.set_ylabel('Anzahl Personen (Tausend)')
    ax1.legend(bbox_to_anchor=(1.05, 1))
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    
    # Right plot - Key statistics
    latest_year = df['Jahr'].max()
    latest_data = df[df['Jahr'] == latest_year]
    
    # Calculate percentage change
    first_year = df['Jahr'].min()
    total_change = ((df[df['Jahr'] == latest_year]['Wert'].sum() / 
                    df[df['Jahr'] == first_year]['Wert'].sum()) - 1) * 100
    
    # Add text box with key statistics
    stats_text = f"""
    Prognose bis {latest_year}
    
    Gesamtwachstum:
    {total_change:.1f}%
    
    Haupttreiber:
    • Tertiärbildung
    • Demografischer Wandel
    • Bildungspolitik
    """
    
    ax2.text(0.1, 0.5, stats_text,
             fontsize=12,
             transform=ax2.transAxes,
             bbox=dict(facecolor='#F5F5F5', 
                      edgecolor='none',
                      alpha=0.8,
                      pad=15))
    ax2.axis('off')
    
    # Adjust layout
    plt.tight_layout()
    plt.savefig('plots/modern_education_trends.png', 
                dpi=300, 
                bbox_inches='tight',
                facecolor='white')
    plt.close()
    
    # 2. Gender Comparison
    plt.figure(figsize=(12, 6))
    gender_data = df.pivot_table(
        values='Wert',
        index='Jahr',
        columns=['Geschlecht', 'Bildungsstand'],
        aggfunc='mean'
    )
    
    # Create new figure for gender comparison
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot with modern style
    for idx, col in enumerate(gender_data.columns):
        ax.plot(gender_data.index, gender_data[col],
               color=colors[idx % len(colors)],
               linewidth=2.5,
               marker='o',
               markersize=6,
               label=f"{col[0]} - {col[1]}")
    
    ax.set_title('Geschlechterspezifische Bildungsentwicklung',
                pad=20, fontweight='bold')
    ax.set_xlabel('Jahr')
    ax.set_ylabel('Anzahl Personen (Tausend)')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('plots/modern_gender_comparison.png',
                dpi=300,
                bbox_inches='tight',
                facecolor='white')
    plt.close()

def create_analysis_report(df):
    """Create detailed analysis report with interpretations and policy suggestions"""
    
    report = f"""
    Bildungsstandszenarien Schweiz 2020-2050: Umfassende Analyse
    =========================================================

    1. DATENÜBERSICHT
    ----------------
    Zeitraum: {df['Jahr'].min()} bis {df['Jahr'].max()}
    Gesamtdatenpunkte: {len(df):,}

    2. HAUPTERKENNTNISSE
    -------------------
    
    2.1 Bildungsniveau-Trends:
    {df.pivot_table(
        values='Wert',
        index='Bildungsstand',
        columns='Jahr',
        aggfunc='sum'
    ).round(0).to_string()}

    Interpretation:
    - Der Anteil der Personen mit Tertiärbildung steigt kontinuierlich
    - Die Anzahl der Personen ohne nachobligatorische Bildung bleibt eine Herausforderung
    - Der Sekundarbereich II zeigt moderate Veränderungen

    2.2 Geschlechterspezifische Entwicklung:
    {df.pivot_table(
        values='Wert',
        index=['Geschlecht', 'Bildungsstand'],
        aggfunc='mean'
    ).round(0).to_string()}

    3. HERAUSFORDERUNGEN FÜR DIE SCHWEIZ
    ----------------------------------

    a) Demografische Herausforderungen:
    - Alternde Bevölkerung und Fachkräftemangel
    - Unterschiedliche Bildungsbeteiligung nach Geschlecht
    - Integration und Bildungszugang für alle Bevölkerungsgruppen

    b) Arbeitsmarkt-Implikationen:
    - Zunehmende Nachfrage nach hochqualifizierten Arbeitskräften
    - Potenzielle Überqualifikation in bestimmten Sektoren
    - Bedarf an kontinuierlicher Weiterbildung

    c) Soziale Aspekte:
    - Bildungsungleichheiten zwischen verschiedenen Bevölkerungsgruppen
    - Zugang zu Tertiärbildung
    - Work-Life-Balance und lebenslanges Lernen

    4. POLITIKEMPFEHLUNGEN
    --------------------

    Kurzfristige Massnahmen (1-5 Jahre):
    1. Stärkung der Berufsbildung:
       - Modernisierung der Lehrpläne
       - Verstärkte Digitalisierung der Bildungsangebote
       - Flexible Ausbildungsmodelle

    2. Förderung der Chancengleichheit:
       - Gezielte Unterstützung benachteiligter Gruppen
       - Ausbau der frühkindlichen Bildung
       - Verstärkte Bildungsberatung

    Mittelfristige Strategien (5-10 Jahre):
    1. Bildungssystem-Anpassungen:
       - Integration neuer Technologien
       - Förderung interdisziplinärer Ausbildungen
       - Stärkung der MINT-Fächer

    2. Arbeitsmarkt-Integration:
       - Bessere Anerkennung ausländischer Abschlüsse
       - Förderung der Weiterbildung
       - Work-Life-Balance-Programme

    Langfristige Vision (10+ Jahre):
    1. Systemische Änderungen:
       - Entwicklung flexibler Bildungspfade
       - Stärkung des lebenslangen Lernens
       - Internationale Bildungskooperationen

    2. Innovationsförderung:
       - Forschungsförderung
       - Start-up-Unterstützung
       - Technologietransfer

    5. SPEZIFISCHE EMPFEHLUNGEN NACH BILDUNGSNIVEAU
    --------------------------------------------

    Sekundarstufe II:
    - Modernisierung der Berufsbildung
    - Stärkere Verbindung zur Praxis
    - Flexiblere Übergänge zur Tertiärstufe

    Tertiärstufe:
    - Ausbau des Fachhochschulangebots
    - Förderung der Durchlässigkeit
    - Internationale Vernetzung

    Weiterbildung:
    - Entwicklung modularer Angebote
    - Anerkennung informeller Kompetenzen
    - Digitale Lernplattformen

    6. MONITORING UND EVALUATION
    -------------------------
    
    Empfohlene Kennzahlen:
    - Bildungsbeteiligung nach Alter und Geschlecht
    - Übergangsquoten zwischen Bildungsstufen
    - Arbeitsmarktintegration nach Abschluss
    - Weiterbildungsbeteiligung

    7. FAZIT
    -------
    Die Bildungsszenarien 2020-2050 zeigen wichtige Trends und Herausforderungen für die Schweiz. 
    Eine erfolgreiche Bewältigung erfordert:
    - Kontinuierliche Anpassung des Bildungssystems
    - Fokus auf Chancengleichheit und Integration
    - Stärkung der internationalen Wettbewerbsfähigkeit
    - Förderung des lebenslangen Lernens

    Erstellt am: {pd.Timestamp.now().strftime('%d.%m.%Y')}
    """
    
    # Save comprehensive report
    with open('plots/comprehensive_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("\nUmfassende Analyse wurde erstellt und gespeichert in 'plots/comprehensive_analysis.txt'")

# Main execution
print("Starte Datensammlung...")
raw_data = get_education_data()

if raw_data is not None:
    print("\nVerarbeite Daten...")
    df = process_data(raw_data)
    if df is not None:
        print("\nErstelle moderne Visualisierungen...")
        create_modern_visualizations(df)
        create_analysis_report(df)
else:
    print("\nDatenabruf fehlgeschlagen")
