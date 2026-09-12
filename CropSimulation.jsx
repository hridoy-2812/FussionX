import React, { useState } from 'react';

export default function CropSimulation() {
  // --- 1. Natural Features ---
  const [sunlight, setSunlight] = useState(80); // 0-100%
  const [rainfall, setRainfall] = useState(40); // 0-100mm (normalized)
  const [temperature, setTemperature] = useState(28); // °C
  const [soilType, setSoilType] = useState('Loamconst { useState } = window.React || React;

function CropSimulation() {
  // --- 1. Natural Features ---
  const [sunlight, setSunlight] = useState(80); // 0-100%
  const [rainfall, setRainfall] = useState(40); // 0-100mm
  const [temperature, setTemperature] = useState(28); // °C
  const [soilType, setSoilType] = useState('Loamy'); // Clay, Sandy, Loamy

  // --- 2. External Interventions ---
  const [irrigation, setIrrigation] = useState(20); // 0-100 manual water
  const [fertilizer, setFertilizer] = useState(50); // 0-100 NPK
  const [pesticideApplied, setPesticideApplied] = useState(false);

  // --- 3. Threats ---
  const [insects, setInsects] = useState(10); // 0-100%

  // --- Logic Engine ---
  let statusText = "Optimal Conditions: Crop is thriving!";
  let healthScore = 100;
  
  // Image Filter Variables (CSS)
  let imageFilter = "brightness(1) sepia(0) hue-rotate(0deg) grayscale(0)";

  // Soil Water Retention Logic
  let waterMultiplier = 1;
  if (soilType === 'Sandy') waterMultiplier = 0.7;
  if (soilType === 'Clay') waterMultiplier = 1.3;
  
  const totalWater = (Number(rainfall) + Number(irrigation)) * waterMultiplier;
  const effectivePests = pesticideApplied ? 0 : Number(insects);
  const numTemp = Number(temperature);
  const numSun = Number(sunlight);
  const numFert = Number(fertilizer);

  // Calculate Health & Visual Filters
  if (effectivePests > 60) {
    statusText = "Critical: Severe Pest Attack!";
    healthScore -= 60;
    imageFilter = "grayscale(0.8) brightness(0.6)";
  } else if (totalWater > 130) {
    statusText = `Warning: Waterlogged! Roots are rotting in ${soilType} soil.`;
    healthScore -= 40;
    imageFilter = "saturate(0.4) sepia(0.5) hue-rotate(-20deg)";
  } else if (totalWater < 40) {
    statusText = "Warning: Drought! Leaves are drying out.";
    healthScore -= 50;
    imageFilter = "sepia(0.8) hue-rotate(-30deg) brightness(0.9)";
  } else if (numTemp > 38) {
    statusText = "Stress: Extreme Heat!";
    healthScore -= 30;
    imageFilter = "sepia(0.4) brightness(1.1)";
  } else if (numSun < 30) {
    statusText = "Notice: Low Sunlight. Growth stunted.";
    healthScore -= 20;
    imageFilter = "brightness(0.7) saturate(0.8)";
  } else if (numFert > 85) {
    statusText = "Warning: Fertilizer Burn!";
    healthScore -= 25;
    imageFilter = "saturate(1.5) hue-rotate(-10deg)";
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-surface-900 p-4 md:p-8 font-sans transition-colors">
      <div className="max-w-6xl mx-auto bg-white dark:bg-surface-800 rounded-2xl shadow-xl overflow-hidden flex flex-col lg:flex-row border border-gray-200 dark:border-gray-700/60">
        
        {/* Left Column: Digital Twin Controls */}
        <div className="w-full lg:w-1/2 p-6 bg-gray-50 dark:bg-surface-900 border-r border-gray-200 dark:border-gray-700/60 lg:h-[800px] overflow-y-auto">
          <h2 className="text-3xl font-bold text-gray-800 dark:text-gray-100 mb-6">Digital Twin Controls</h2>
          
          {/* Natural Features */}
          <div className="mb-8 p-4 bg-white dark:bg-surface-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700/60">
            <h3 className="text-lg font-bold text-blue-600 dark:text-cyan-400 mb-4 border-b border-gray-200 dark:border-gray-700/60 pb-2">Natural Features</h3>
            
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Sunlight: {sunlight}%</label>
            <input type="range" min="0" max="100" value={sunlight} onChange={(e) => setSunlight(Number(e.target.value))} className="w-full mb-4 accent-yellow-500" />

            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rainfall: {rainfall}mm</label>
            <input type="range" min="0" max="100" value={rainfall} onChange={(e) => setRainfall(Number(e.target.value))} className="w-full mb-4 accent-blue-500" />

            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Temperature: {temperature}°C</label>
            <input type="range" min="0" max="50" value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} className="w-full mb-4 accent-red-500" />

            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Soil Type</label>
            <select value={soilType} onChange={(e) => setSoilType(e.target.value)} className="w-full p-2 border border-gray-300 dark:border-gray-700 rounded-md bg-gray-50 dark:bg-surface-900 text-gray-800 dark:text-gray-200">
              <option value="Clay">Clay (Retains Water)</option>
              <option value="Loamy">Loamy (Balanced)</option>
              <option value="Sandy">Sandy (Drains Fast)</option>
            </select>
          </div>

          {/* Interventions */}
          <div className="mb-8 p-4 bg-white dark:bg-surface-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700/60">
            <h3 className="text-lg font-bold text-green-600 dark:text-agri-400 mb-4 border-b border-gray-200 dark:border-gray-700/60 pb-2">Human Interventions</h3>
            
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Manual Irrigation: {irrigation} Units</label>
            <input type="range" min="0" max="100" value={irrigation} onChange={(e) => setIrrigation(Number(e.target.value))} className="w-full mb-4 accent-blue-400" />

            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Fertilizer Level (NPK): {fertilizer}%</label>
            <input type="range" min="0" max="100" value={fertilizer} onChange={(e) => setFertilizer(Number(e.target.value))} className="w-full mb-4 accent-green-600" />

            <div className="flex items-center justify-between mt-4">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Apply Pesticide?</span>
              <button 
                type="button"
                onClick={() => setPesticideApplied(!pesticideApplied)} 
                className={`px-5 py-2 rounded-full text-sm font-bold transition-all ${pesticideApplied ? 'bg-purple-600 text-white shadow-md' : 'bg-gray-200 dark:bg-surface-700 text-gray-600 dark:text-gray-300'}`}>
                {pesticideApplied ? "Applied" : "Not Applied"}
              </button>
            </div>
          </div>

          {/* Threats */}
          <div className="p-4 bg-white dark:bg-surface-800 rounded-xl shadow-sm border border-red-200 dark:border-red-900/40">
            <h3 className="text-lg font-bold text-red-600 dark:text-red-400 mb-4 border-b border-gray-200 dark:border-gray-700/60 pb-2">Threats</h3>
            
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Insect Population: {insects}%</label>
            <input type="range" min="0" max="100" value={insects} onChange={(e) => setInsects(Number(e.target.value))} className="w-full accent-red-600" />
          </div>
        </div>

        {/* Right Column: Visual Feedback */}
        <div className="w-full lg:w-1/2 p-6 flex flex-col bg-gray-900 text-white relative">
          <h2 className="text-2xl font-bold mb-2">Field Camera Feed</h2>
          
          <div className="bg-surface-900 border border-gray-700/60 rounded-lg p-4 mb-6">
            <p className={`text-lg font-semibold ${healthScore < 50 ? 'text-red-400' : 'text-green-400'}`}>
              {statusText}
            </p>
          </div>
          
          {/* Unsplash Drone Agronomy Feed (No human figures) */}
          <div className="relative w-full h-96 rounded-xl overflow-hidden border-4 border-gray-700 shadow-2xl bg-black">
            <img 
              src="https://images.unsplash.com/photo-1625246333195-78d9c38ad449?auto=format&fit=crop&w=1200&q=80" 
              alt="Crop Canopy Field" 
              className="w-full h-full object-cover transition-all duration-700 ease-in-out"
              style={{ filter: imageFilter }} 
            />
            
            {/* Live Sensor Telemetry HUD */}
            <div className="absolute top-4 left-4 bg-black/75 backdrop-blur-md p-3 rounded-lg text-xs font-mono border border-white/10 space-y-1">
              <p className="text-cyan-300">SOIL_MOISTURE: {Math.round(totalWater)}%</p>
              <p className="text-yellow-300">TEMP_SENSOR: {temperature}°C</p>
              <p className={effectivePests > 0 ? "text-red-400" : "text-green-400"}>
                PEST_DETECT: {effectivePests > 0 ? 'TRUE' : 'FALSE'}
              </p>
            </div>
          </div>

          {/* System Health Meter */}
          <div className="w-full mt-auto pt-8">
            <div className="flex justify-between text-sm font-bold mb-2 uppercase tracking-wider">
              <span>System Health</span>
              <span>{Math.max(0, healthScore)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-4 shadow-inner overflow-hidden">
              <div 
                className={`h-4 rounded-full transition-all duration-700 ${healthScore > 70 ? 'bg-green-500' : healthScore > 40 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                style={{ width: `${Math.max(0, healthScore)}%` }}
              ></div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Module and browser global bindings
window.CropSimulation = CropSimulation;
if (typeof window.exports !== 'undefined') {
  window.exports.default = CropSimulation;
}
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CropSimulation;
}y'); // Clay, Sandy, Loamy

  // --- 2. External Interventions ---
  const [irrigation, setIrrigation] = useState(20); // 0-100 manual water
  const [fertilizer, setFertilizer] = useState(50); // 0-100 NPK
  const [pesticideApplied, setPesticideApplied] = useState(false);

  // --- 3. Threats ---
  const [insects, setInsects] = useState(10); // 0-100%

  // --- Logic Engine ---
  let statusText = "Optimal Conditions: Crop is thriving!";
  let healthScore = 100;
  
  // Image Filter Variables (CSS)
  let imageFilter = "brightness(1) sepia(0) hue-rotate(0deg) grayscale(0)";

  // Soil Water Retention Logic
  let waterMultiplier = 1;
  if (soilType === 'Sandy') waterMultiplier = 0.7; // Drains fast
  if (soilType === 'Clay') waterMultiplier = 1.3;  // Retains water
  
  const totalWater = (parseInt(rainfall) + parseInt(irrigation)) * waterMultiplier;
  const effectivePests = pesticideApplied ? 0 : insects;

  // Calculate Health & Visuals
  if (effectivePests > 60) {
    statusText = "Critical: Severe Pest Attack!";
    healthScore -= 60;
    imageFilter = "grayscale(0.8) brightness(0.6)"; // Looks dead and eaten
  } else if (totalWater > 130) {
    statusText = "Warning: Waterlogged! Roots are rotting in " + soilType + " soil.";
    healthScore -= 40;
    imageFilter = "saturate(0.4) sepia(0.5) hue-rotate(-20deg)"; // Sickly yellow
  } else if (totalWater < 40) {
    statusText = "Warning: Drought! Leaves are drying out.";
    healthScore -= 50;
    imageFilter = "sepia(0.8) hue-rotate(-30deg) brightness(0.9)"; // Dry brown
  } else if (temperature > 38) {
    statusText = "Stress: Extreme Heat!";
    healthScore -= 30;
    imageFilter = "sepia(0.4) brightness(1.1)"; // Scorched look
  } else if (sunlight < 30) {
    statusText = "Notice: Low Sunlight. Growth stunted.";
    healthScore -= 20;
    imageFilter = "brightness(0.7) saturate(0.8)"; // Dark and dull
  } else if (fertilizer > 85) {
    statusText = "Warning: Fertilizer Burn!";
    healthScore -= 25;
    imageFilter = "saturate(1.5) hue-rotate(-10deg)"; // Unnaturally bright/burned
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col lg:flex-row">
        
        {/* Left Side: Control Panel (Scrollable if needed) */}
        <div className="w-full lg:w-1/2 p-6 bg-gray-50 border-r border-gray-200 lg:h-[800px] overflow-y-auto">
          <h2 className="text-3xl font-bold text-gray-800 mb-6">Digital Twin Controls</h2>
          
          {/* Natural Features Section */}
          <div className="mb-8 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-blue-800 mb-4 border-b pb-2">Natural Features</h3>
            
            <label className="block text-sm font-medium text-gray-700 mb-1">Sunlight: {sunlight}%</label>
            <input type="range" min="0" max="100" value={sunlight} onChange={(e) => setSunlight(e.target.value)} className="w-full mb-4 accent-yellow-500" />

            <label className="block text-sm font-medium text-gray-700 mb-1">Rainfall: {rainfall}mm</label>
            <input type="range" min="0" max="100" value={rainfall} onChange={(e) => setRainfall(e.target.value)} className="w-full mb-4 accent-blue-500" />

            <label className="block text-sm font-medium text-gray-700 mb-1">Temperature: {temperature}°C</label>
            <input type="range" min="0" max="50" value={temperature} onChange={(e) => setTemperature(e.target.value)} className="w-full mb-4 accent-red-500" />

            <label className="block text-sm font-medium text-gray-700 mb-1">Soil Type</label>
            <select value={soilType} onChange={(e) => setSoilType(e.target.value)} className="w-full p-2 border rounded-md bg-gray-50">
              <option value="Clay">Clay (Retains Water)</option>
              <option value="Loamy">Loamy (Balanced)</option>
              <option value="Sandy">Sandy (Drains Fast)</option>
            </select>
          </div>

          {/* Interventions Section */}
          <div className="mb-8 p-4 bg-white rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-bold text-green-800 mb-4 border-b pb-2">Human Interventions</h3>
            
            <label className="block text-sm font-medium text-gray-700 mb-1">Manual Irrigation: {irrigation} Units</label>
            <input type="range" min="0" max="100" value={irrigation} onChange={(e) => setIrrigation(e.target.value)} className="w-full mb-4 accent-blue-400" />

            <label className="block text-sm font-medium text-gray-700 mb-1">Fertilizer Level (NPK): {fertilizer}%</label>
            <input type="range" min="0" max="100" value={fertilizer} onChange={(e) => setFertilizer(e.target.value)} className="w-full mb-4 accent-green-600" />

            <div className="flex items-center justify-between mt-4">
              <span className="text-sm font-medium text-gray-700">Apply Pesticide?</span>
              <button onClick={() => setPesticideApplied(!pesticideApplied)} className={`px-5 py-2 rounded-full text-sm font-bold transition-all ${pesticideApplied ? 'bg-purple-600 text-white shadow-md' : 'bg-gray-200 text-gray-600'}`}>
                {pesticideApplied ? "Applied" : "Not Applied"}
              </button>
            </div>
          </div>

          {/* Threats Section */}
          <div className="p-4 bg-white rounded-xl shadow-sm border border-red-100">
            <h3 className="text-lg font-bold text-red-800 mb-4 border-b pb-2">Threats</h3>
            
            <label className="block text-sm font-medium text-gray-700 mb-1">Insect Population: {insects}%</label>
            <input type="range" min="0" max="100" value={insects} onChange={(e) => setInsects(e.target.value)} className="w-full accent-red-600" />
          </div>
        </div>

        {/* Right Side: Visual Output */}
        <div className="w-full lg:w-1/2 p-6 flex flex-col bg-gray-800 text-white relative">
          <h2 className="text-2xl font-bold mb-2">Field Camera Feed</h2>
          
          <div className="bg-gray-900 rounded-lg p-4 mb-6">
            <p className={`text-lg font-semibold ${healthScore < 50 ? 'text-red-400' : 'text-green-400'}`}>
              {statusText}
            </p>
          </div>
          
          {/* The Realistic Image Container */}
          <div className="relative w-full h-96 rounded-xl overflow-hidden border-4 border-gray-700 shadow-2xl bg-black">
            <img 
              /* I am using a high-quality Unsplash image of a cornfield as a placeholder so it works instantly */
              src="https://www.shutterstock.com/image-vector/corn-field-background-illustration-cartoon-600nw-2570294727.jpg" 
              alt="Crop Field" 
              className="w-full h-full object-cover transition-all duration-700 ease-in-out"
              style={{ filter: imageFilter }} 
            />
            
            {/* Overlay Data Overlay */}
            <div className="absolute top-4 left-4 bg-black/60 backdrop-blur-sm p-3 rounded-lg text-xs font-mono">
              <p>SOIL_MOISTURE: {Math.round(totalWater)}%</p>
              <p>TEMP_SENSOR: {temperature}°C</p>
              <p>PEST_DETECT: {effectivePests > 0 ? 'TRUE' : 'FALSE'}</p>
            </div>
          </div>

          {/* Health Bar */}
          <div className="w-full mt-auto pt-8">
            <div className="flex justify-between text-sm font-bold mb-2 uppercase tracking-wider">
              <span>System Health</span>
              <span>{Math.max(0, healthScore)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-4 shadow-inner">
              <div 
                className={`h-4 rounded-full transition-all duration-700 ${healthScore > 70 ? 'bg-green-500' : healthScore > 40 ? 'bg-yellow-500' : 'bg-red-500'}`} 
                style={{ width: `${Math.max(0, healthScore)}%` }}
              ></div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
