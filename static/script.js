const BASE_URL = "http://127.0.0.1:8000";
let credentials = null;
let geojsonLayer;

// Manejador de inicio de sesión
document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const response = await fetch(`${BASE_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user: username, password: password }),
        });

        if (response.ok) {
            credentials = { user: username, password: password };
            document.getElementById("loginModal").classList.remove("active");
            document.getElementById("map").style.display = "block";
            initMap();
        } else {
            const errorData = await response.json();
            document.getElementById("error").textContent = errorData.detail || "Error de inicio de sesión.";
        }
    } catch (error) {
        document.getElementById("error").textContent = "Error al conectar con el servidor.";
    }
});

// Inicializar mapa
function initMap() {
    const map = L.map('map').setView([8.535374107340077, -72.72105198070867], 12);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(map);

    // Cargar datos iniciales
    loadData("all", map);
}

// Función para cargar datos GeoJSON
async function loadData(data, map) {
    try {
        const response = await fetch(`${BASE_URL}/?data=${data}`, {
            method: "GET",
            headers: { 
                "Authorization": `Basic ${btoa(`${credentials.user}:${credentials.password}`)}` 
            }
        });

        if (!response.ok) {
            console.error("Error al cargar los datos:", response.statusText);
            return;
        }

        const geojsonData = await response.json();

        if (geojsonLayer) {
            map.removeLayer(geojsonLayer);
        }

        geojsonLayer = L.geoJSON(geojsonData, {
            onEachFeature: (feature, layer) => {
                layer.bindPopup(`<b>${feature.properties.name}</b>`);
            }
        }).addTo(map);

        map.fitBounds(geojsonLayer.getBounds());
    } catch (error) {
        console.error("Error:", error);
    }
}