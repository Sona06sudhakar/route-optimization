# Route Optimizer

An interactive route optimization system that compares the fastest route with a pollution-aware optimized route using the real road network of Surat, Gujarat.

The project integrates OpenStreetMap road network data with GPS-tagged environmental sensor readings to help users explore routes while considering environmental conditions.

## Features

- **Real Road Network:** Uses road network data from OpenStreetMap for Surat.
- **Environmental Data Integration:** Maps GPS-tagged sensor readings to nearby road segments.
- **Pollution-Aware Routing:** Uses PM2.5-based pollution scores when calculating route costs.
- **Dijkstra's Algorithm:** Finds optimized routes using configurable routing weights.
- **Route Comparison:** Compares the optimized route with the fastest available route.
- **Interactive Map:** Displays roads, pollution coverage, and selected routes.
- **Customizable Weights:** Allows users to adjust routing preferences through presets and sliders.
- **Route Statistics:** Displays distance, estimated travel time, sensor coverage, and other route metrics.
- **Algorithm Trace:** Provides information about the Dijkstra execution, including settled nodes and distance updates.

## Tech Stack

**Frontend**
- HTML
- CSS
- JavaScript
- Leaflet.js
- OpenStreetMap

**Backend**
- Python
- FastAPI
- NetworkX
- Uvicorn

**Data Processing**
- Python
- Pandas
- GeoJSON
- OpenStreetMap road network data

## How It Works

1. **Road Network Extraction:** Road segments for the Surat region are extracted from OpenStreetMap.
2. **Sensor Data Processing:** Environmental sensor CSV data is cleaned and filtered using GPS coordinates.
3. **Road Matching:** Sensor readings are matched to their nearest road segments.
4. **Pollution Aggregation:** Multiple readings are aggregated to calculate representative pollution values for road segments.
5. **Graph Construction:** The road network is converted into a directed graph with road distance, estimated speed, and pollution attributes.
6. **Route Optimization:** Dijkstra's algorithm calculates routes using configurable edge costs.
7. **Route Comparison:** The optimized route is compared with the fastest route.

## Project Setup

### Prerequisites

- Python 3.10 or later
- Git
- A modern web browser

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/surat-pollution-aware-route-optimizer.git
cd surat-pollution-aware-route-optimizer
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn networkx pandas
```

### 3. Start the Backend

```bash
uvicorn backend:app --reload
```

The backend will run at:

`http://127.0.0.1:8000`

API documentation:

`http://127.0.0.1:8000/docs`

### 4. Start the Frontend

Open another terminal in the project directory and run:

```bash
python -m http.server 5500
```

Open the application at:

`http://127.0.0.1:5500/route-optimizer-surat-integrated.html`

## Data and Methodology

- Road network data is sourced from OpenStreetMap.
- Environmental readings are GPS-tagged observations from the supplied sensor dataset.
- Sensor readings are matched to nearby road segments and aggregated before being incorporated into the routing graph.
- The pollution score is a relative PM2.5-based metric used for route comparison. It is not an official CPCB AQI measurement.

## Limitations

- Sensor readings cover only the locations visited during the recorded journey, not the entire Surat road network.
- Several roads have no sensor measurements. Missing measurements should not be interpreted as clean air.
- Road speeds may be estimated from OpenStreetMap attributes and do not represent live traffic.
- Safety and smoothness currently use neutral placeholder values because reliable supporting datasets are not integrated.
- Route results depend on the selected weights and available road and sensor data.

## Data Attribution

Road network data © OpenStreetMap contributors, available under the Open Database License (ODbL).

Environmental sensor data should be attributed to its original provider.

## Future Improvements

- Integration of larger and more comprehensive environmental datasets.
- Real-time traffic integration.
- Reliable road safety and road condition datasets.
- Improved sensor coverage and temporal pollution analysis.
- Deployment as a publicly accessible web application.

## Author

**Sona Sudhakar**  
B.Tech, Computer Science and Engineering  
Sardar Vallabhbhai National Institute of Technology (SVNIT), Surat
