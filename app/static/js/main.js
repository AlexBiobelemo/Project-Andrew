// app/static/js/main.js

// Configuration
const CONFIG = {
  map: {
    center: [4.9248, 6.2647],
    zoom: 13,
    maxZoom: 19,
    tileLayers: {
      street: {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        offlineUrl: (data) => `/offline-tile/${data.z}/${data.x}/${data.y}.png`
      },
      satellite: {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
      },
      terrain: {
        url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
        maxZoom: 17,
        attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
      }
    }
  },
  icons: {
    Reported: new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    }),
    'In Progress': new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-orange.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    }),
    Resolved: new L.Icon({
      iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
      iconSize: [25, 41],
      iconAnchor: [12, 41],
      popupAnchor: [1, -34],
      shadowSize: [41, 41]
    })
  }
};

// Utility Functions
const select = id => document.getElementById(id);
const showSpinner = btn => {
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Checking...';
};
const hideSpinner = (btn, text) => {
  btn.disabled = false;
  btn.innerHTML = text;
};

// Offline Tile Caching
const cacheTilesForOffline = async (map) => {
  if (!('caches' in window)) {
    alert('Offline caching is not supported in this browser.');
    return;
  }

  const cache = await caches.open('map-tiles-v1');
  const bounds = map.getBounds();
  const zoom = Math.round(map.getZoom());
  const tiles = [];

  // Calculate tiles to cache (simple grid)
  const northEast = bounds.getNorthEast();
  const southWest = bounds.getSouthWest();

  // Convert lat/lng to tile coordinates
  const tileCoords = (lat, lng, z) => {
    const x = Math.floor((lng + 180) / 360 * (1 << z));
    const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * (1 << z));
    return { x, y };
  };

  const ne = tileCoords(northEast.lat, northEast.lng, zoom);
  const sw = tileCoords(southWest.lat, southWest.lng, zoom);

  for (let x = sw.x; x <= ne.x; x++) {
    for (let y = ne.y; y <= sw.y; y++) {
      const url = `https://tile.openstreetmap.org/${zoom}/${x}/${y}.png`;
      tiles.push(url);
    }
  }

  try {
    await Promise.all(tiles.map(url => cache.add(url)));
    alert(`Cached ${tiles.length} tiles for offline use.`);
  } catch (error) {
    console.error('Error caching tiles:', error);
    alert('Failed to cache tiles.');
  }
};

// Voice Recognition
const initVoiceRecognition = () => {
  const voiceBtn = select('voice-btn');
  const descriptionTextarea = select('description');
  let recognition;

  if (!voiceBtn || !descriptionTextarea) return;

  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US'; // Can be changed based on language

    recognition.onstart = () => {
      voiceBtn.innerHTML = '<i class="bi bi-mic-fill text-danger"></i>';
      voiceBtn.disabled = true;
    };

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      descriptionTextarea.value += (descriptionTextarea.value ? ' ' : '') + transcript;
    };

    recognition.onend = () => {
      voiceBtn.innerHTML = '<i class="bi bi-mic"></i>';
      voiceBtn.disabled = false;
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      alert('Voice recognition failed. Please try again.');
      voiceBtn.innerHTML = '<i class="bi bi-mic"></i>';
      voiceBtn.disabled = false;
    };

    voiceBtn.addEventListener('click', () => {
      recognition.start();
    });
  } else {
    voiceBtn.style.display = 'none'; // Hide if not supported
  }
};

// CSRF Token Fetch
async function getCsrfToken() {
  const response = await fetch('/get-csrf-token', {
    method: 'GET',
    credentials: 'include'
  });
  const data = await response.json();
  return data.csrf_token;
}

// Coordinate Validation
function validateCoordinates(lat, lng) {
  const latNum = parseFloat(lat);
  const lngNum = parseFloat(lng);
  if (isNaN(latNum) || latNum < -90 || latNum > 90) {
    return { valid: false, error: 'Latitude must be between -90 and 90' };
  }
  if (isNaN(lngNum) || lngNum < -180 || lngNum > 180) {
    return { valid: false, error: 'Longitude must be between -180 and 180' };
  }
  return { valid: true };
}

// Map Initialization for Index
const initMap = () => {
  const mapDiv = select('map');
  if (!mapDiv) return { map: null, drawnItems: null };
  const map = L.map('map').setView(CONFIG.map.center, CONFIG.map.zoom);
  const drawnItems = new L.FeatureGroup();
  map.addLayer(drawnItems);

  // Tile Layers with offline support
  const createOfflineTileLayer = (config) => {
    return L.tileLayer(config.url, {
      maxZoom: CONFIG.map.maxZoom,
      attribution: config.attribution
    });
  };

  const layers = {
    'Street View': createOfflineTileLayer(CONFIG.map.tileLayers.street).addTo(map),
    'Satellite View': L.tileLayer(CONFIG.map.tileLayers.satellite.url, {
      maxZoom: CONFIG.map.maxZoom,
      attribution: CONFIG.map.tileLayers.satellite.attribution
    }),
    'Terrain View': L.tileLayer(CONFIG.map.tileLayers.terrain.url, {
      maxZoom: CONFIG.map.tileLayers.terrain.maxZoom,
      attribution: CONFIG.map.tileLayers.terrain.attribution
    })
  };
  L.control.layers(layers).addTo(map);

  // Draw Control
  const drawControl = new L.Control.Draw({
    edit: { featureGroup: drawnItems },
    draw: { polygon: true, polyline: true, rectangle: true, circle: false, marker: false }
  });
  map.addControl(drawControl);

  // Locate Control
  L.Control.Locate = L.Control.extend({
    onAdd(map) {
      const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-locate');
      const button = L.DomUtil.create('a', 'leaflet-bar-part', container);
      button.href = '#';
      button.title = 'Go to my location';
      button.innerHTML = '<i class="bi bi-crosshair" style="font-size: 1.2rem;"></i>';
      L.DomEvent.on(button, 'click', e => {
        L.DomEvent.preventDefault(e);
        if (!navigator.geolocation) {
          alert('Geolocation is not supported by your browser.');
          return;
        }
        navigator.geolocation.getCurrentPosition(
          ({ coords: { latitude, longitude } }) => {
            map.setView([latitude, longitude], 16);
            L.marker([latitude, longitude]).addTo(map)
              .bindPopup('You are here.').openPopup();
          },
          ({ code, message }) => {
            const messages = {
              1: 'Geolocation permission denied. Please enable location services.',
              2: 'Location information is unavailable.',
              3: 'The request to get your location timed out.'
            };
            alert(messages[code] || message);
          },
          { timeout: 10000, enableHighAccuracy: true }
        );
      });
      return container;
    }
  });
  L.control.locate = opts => new L.Control.Locate(opts);
  L.control.locate({ position: 'topright' }).addTo(map);

  // Offline Control
  L.Control.Offline = L.Control.extend({
    onAdd(map) {
      const container = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-offline');
      const button = L.DomUtil.create('a', 'leaflet-bar-part', container);
      button.href = '#';
      button.title = 'Cache tiles for offline use';
      button.innerHTML = '<i class="bi bi-download" style="font-size: 1.2rem;"></i>';
      L.DomEvent.on(button, 'click', e => {
        L.DomEvent.preventDefault(e);
        cacheTilesForOffline(map);
      });
      return container;
    }
  });
  L.control.offline = opts => new L.Control.Offline(opts);
  L.control.offline({ position: 'topright' }).addTo(map);

  // GeoSearch Control
  if (typeof GeoSearch !== 'undefined') {
    try {
      const searchControl = new GeoSearch.GeoSearchControl({
        provider: new GeoSearch.OpenStreetMapProvider(),
        style: 'button'
      });
      map.addControl(searchControl);
      map.on('layeradd', ({ layer }) => {
        if (layer instanceof GeoSearch.GeoSearchControl) {
          const searchContainer = document.querySelector('.geosearch-bar');
          if (searchContainer) {
            L.DomEvent.on(searchContainer, 'click', e => L.DomEvent.stopPropagation(e));
          }
        }
      });
    } catch (error) {
      console.error('Error initializing GeoSearchControl:', error);
    }
  }

  return { map, drawnItems };
};

// Map Initialization for View Issue
const initIssueMap = () => {
  const mapDiv = select('issue-map');
  if (!mapDiv) return;
  const lat = mapDiv.dataset.lat;
  const lng = mapDiv.dataset.lng;
  const coordValidation = validateCoordinates(lat, lng);
  if (!coordValidation.valid) {
    mapDiv.innerHTML = `<p class="text-danger">${coordValidation.error}</p>`;
    return;
  }
  const map = L.map('issue-map').setView([lat, lng], 15);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map);
  L.marker([lat, lng]).addTo(map);
};

// Issue Markers
const initIssues = (map) => {
  const markers = L.markerClusterGroup();
  const issues = JSON.parse(select('map').dataset.issues || '[]');
  const defaultIcon = CONFIG.icons.Reported;

  issues.forEach(issue => {
    if (!issue.lat || !issue.lng || !issue.id) return;
    const coordValidation = validateCoordinates(issue.lat, issue.lng);
    if (!coordValidation.valid) {
      console.warn(`Invalid coordinates for issue ${issue.id}: ${coordValidation.error}`);
      return;
    }
    const icon = CONFIG.icons[issue.status] || defaultIcon;
    const buttonClass = issue.user_has_voted ? 'btn-primary' : 'btn-outline-primary';
    const popupContent = `
    <b>${issue.title || 'Untitled'}</b>
    <hr class="my-1">
    <div class="d-flex justify-content-between align-items-center">
      <span id="upvote-count-${issue.id}">${issue.upvotes || 0} Upvotes</span>
      <button class="btn btn-sm ${buttonClass} upvote-btn" data-issue-id="${issue.id}">
        <i class="bi bi-hand-thumbs-up"></i> Vote
      </button>
    </div>
    <a href="/issue/${issue.id}" class="btn btn-outline-secondary btn-sm mt-2 w-100">View Details</a>
  `;
    markers.addLayer(L.marker([issue.lat, issue.lng], { icon }).bindPopup(popupContent));
  });

  map.addLayer(markers);
};

// Upvote Functionality
const upvoteIssue = async (issueId) => {
  try {
    const response = await fetch(`/upvote/${issueId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin'
    });
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const { success, upvote_count, voted, error } = await response.json();
    if (success) {
      const countEl = select(`upvote-count-${issueId}`);
      if (countEl) countEl.textContent = `${upvote_count} Upvotes`;
      const button = document.querySelector(`.upvote-btn[data-issue-id="${issueId}"]`);
      if (button) {
        button.classList.toggle('btn-primary', voted);
        button.classList.toggle('btn-outline-primary', !voted);
      }
    } else {
      alert(error || 'Failed to upvote the issue.');
    }
  } catch (error) {
    console.error('Upvote error:', error);
    alert('An error occurred while upvoting. Please try again.');
  }
};

// Report Submission
const initReporting = (map, drawnItems) => {
  const reportModal = new bootstrap.Modal(select('reportModal'));
  const issueForm = select('issue-form');
  const submitBtn = select('submit-issue-btn');
  const latInput = select('lat-input');
  const lngInput = select('lng-input');
  const locationInput = select('location-text');
  const descriptionInput = select('description') || document.querySelector('textarea[name="description"]');
  const defaultIcon = CONFIG.icons.Reported;

  const submitNewIssue = async () => {
    const formData = new FormData(issueForm);
    try {
      const response = await fetch(select('map').dataset.reportIssueUrl, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
      });
      if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
      const { success, issue, errors } = await response.json();
      if (success) {
        const popupContent = `
          <b>${issue.title || 'Untitled'}</b>
          <hr class="my-1">
          <div class="d-flex justify-content-between align-items-center">
            <span id="upvote-count-${issue.id}">0 Upvotes</span>
            <button class="btn btn-sm btn-outline-primary upvote-btn" data-issue-id="${issue.id}">
              <i class="bi bi-hand-thumbs-up"></i> Vote
            </button>
          </div>
          <a href="/issue/${issue.id}" class="btn btn-outline-secondary btn-sm mt-2 w-100">View Details</a>
        `;
        L.marker([issue.lat, issue.lng], { icon: defaultIcon })
          .addTo(map)
          .bindPopup(popupContent)
          .openPopup();
        attachUpvoteListeners();
        reportModal.hide();
        issueForm.reset();
        issueForm.querySelector('input[type="file"]').value = '';
        drawnItems.clearLayers();
        select('geojson-input')?.remove();
      } else {
        alert(`Please fix the following issues:\n${Object.entries(errors).map(([field, errs]) => `- ${field}: ${errs.join(', ')}`).join('\n')}`);
      }
    } catch (error) {
      console.error('Submission error:', error);
      alert('An error occurred while submitting the issue. Please try again.');
    }
  };

  map.on(L.Draw.Event.CREATED, ({ layer }) => {
    drawnItems.addLayer(layer);
    const geojson = layer.toGeoJSON();
    const { lat, lng } = layer.getBounds().getCenter();
    const coordValidation = validateCoordinates(lat, lng);
    if (!coordValidation.valid) {
      alert(coordValidation.error);
      drawnItems.removeLayer(layer);
      return;
    }
    latInput.value = lat;
    lngInput.value = lng;
    select('geojson-input').value = JSON.stringify(geojson.geometry);
    reportModal.show();
  });

  map.on('click', async ({ latlng: { lat, lng }, originalEvent: { target } }) => {
    if (target.closest('.leaflet-control, .leaflet-control-container')) return;
    const coordValidation = validateCoordinates(lat, lng);
    if (!coordValidation.valid) {
      L.popup()
        .setLatLng([lat, lng])
        .setContent(coordValidation.error)
        .openOn(map);
      return;
    }
    locationInput.value = 'Fetching address...';
    drawnItems.clearLayers();
    select('geojson-input')?.remove();
    issueForm.reset();
    latInput.value = lat;
    lngInput.value = lng;
    const mapDiv = select('map');
    if (mapDiv.dataset.isAuthenticated === 'true') {
      try {
        const csrfToken = await getCsrfToken();
        const response = await fetch(mapDiv.dataset.reverseGeocodeUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
          credentials: 'same-origin',
          body: JSON.stringify({ lat, lng })
        });
        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
        const { address } = await response.json();
        locationInput.value = address || 'Could not find address.';
      } catch (error) {
        console.error('Geocode error:', error);
        locationInput.value = 'Could not find address.';
      }
      reportModal.show();
    } else {
      L.popup()
        .setLatLng([lat, lng])
        .setContent(`Please <a href="${mapDiv.dataset.loginUrl}">login</a> to report an issue.`)
        .openOn(map);
    }
  });

  submitBtn.addEventListener('click', async () => {
    const mapDiv = select('map');
    if (mapDiv.dataset.isAuthenticated !== 'true') {
      alert(`Please login to submit an issue. <a href="${mapDiv.dataset.loginUrl}">Login here</a>.`);
      return;
    }
    showSpinner(submitBtn);
    try {
      const csrfToken = await getCsrfToken();
      const checkResponse = await fetch(mapDiv.dataset.checkDuplicatesUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        credentials: 'same-origin',
        body: JSON.stringify({
          lat: latInput.value,
          lng: lngInput.value,
          description: descriptionInput?.value || ''
        })
      });
      if (!checkResponse.ok) throw new Error(`HTTP error: ${checkResponse.status}`);
      const { is_duplicate, duplicate_id, duplicate_title } = await checkResponse.json();
      if (is_duplicate) {
        const proceed = confirm(`This looks like a duplicate of an existing issue:\n\n"${duplicate_title}"\n\nWould you like to upvote the existing issue instead?`);
        if (proceed) {
          await upvoteIssue(duplicate_id);
          reportModal.hide();
        } else {
          await submitNewIssue();
        }
      } else {
        await submitNewIssue();
      }
    } catch (error) {
      console.error('Duplicate check error:', error);
      alert('An error occurred while checking for duplicates. Please try again.');
    } finally {
      hideSpinner(submitBtn, 'Submit Report');
    }
  });

  const attachUpvoteListeners = () => {
    document.querySelectorAll('.upvote-btn:not([data-listener-attached="true"])').forEach(button => {
      button.addEventListener('click', () => {
        const mapDiv = select('map');
        if (mapDiv.dataset.isAuthenticated === 'true') {
          upvoteIssue(button.dataset.issueId);
        } else {
          alert('Please login to upvote an issue.');
        }
      });
      button.dataset.listenerAttached = 'true';
    });
  };

  map.on('popupopen', attachUpvoteListeners);
};

// Generate Report via AJAX
async function generateReport() {
  const mapDiv = select('map') || select('issue-map');
  const isAuthenticated = mapDiv.dataset.isAuthenticated === 'true';
  if (!isAuthenticated) {
    const loginUrl = JSON.parse(mapDiv.dataset.loginUrl);
    alert(`Please login to generate a report. <a href="${loginUrl}">Login here</a>.`);
    return;
  }
  const csrfToken = await getCsrfToken();
  try {
    const response = await fetch('/generate-report', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
      credentials: 'include'
    });
    if (!response.ok) throw new Error(`HTTP error: ${response.status}`);
    const result = await response.json();
    alert('Report: ' + result.report);
  } catch (error) {
    alert('Report generation failed: ' + error.message);
  }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  if (select('map')) {
    const { map, drawnItems } = initMap();
    initIssues(map);
    const mapDiv = select('map');
    if (mapDiv.dataset.isAuthenticated === 'true') {
      initReporting(map, drawnItems);
      initVoiceRecognition();
    }
  }
  if (select('issue-map')) {
    initIssueMap();
  }
});