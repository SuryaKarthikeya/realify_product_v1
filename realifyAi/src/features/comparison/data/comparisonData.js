// Mock SKU → product spec database for the High-Density Comparison tool.
// In production this would be resolved via a live catalog/PIM lookup.

export const ATTRIBUTE_CATEGORIES = [
  { key: 'physical',     label: 'Physical Specifications' },
  { key: 'display',      label: 'Display' },
  { key: 'performance',  label: 'Core Performance' },
  { key: 'camera',       label: 'Camera' },
  { key: 'battery',      label: 'Battery & Charging' },
  { key: 'connectivity', label: 'Connectivity' },
  { key: 'logistics',    label: 'Logistics & Availability' },
];

export const ATTRIBUTES = [
  { key: 'height',       label: 'Height (mm)',        category: 'physical' },
  { key: 'width',        label: 'Width (mm)',         category: 'physical' },
  { key: 'depth',        label: 'Depth (mm)',         category: 'physical' },
  { key: 'weight',       label: 'Weight (g)',         category: 'physical' },
  { key: 'buildMaterial',label: 'Build Material',     category: 'physical' },
  { key: 'colors',       label: 'Colors Available',   category: 'physical' },

  { key: 'screenSize',     label: 'Screen Size',       category: 'display' },
  { key: 'resolution',     label: 'Resolution',        category: 'display' },
  { key: 'displayType',    label: 'Display Type',      category: 'display' },
  { key: 'refreshRate',    label: 'Refresh Rate',      category: 'display' },
  { key: 'peakBrightness', label: 'Peak Brightness',   category: 'display' },

  { key: 'processor', label: 'Processor',            category: 'performance' },
  { key: 'geekbench',  label: 'Geekbench Multi-Core', category: 'performance' },
  { key: 'ram',        label: 'Base RAM (GB)',        category: 'performance' },
  { key: 'storage',    label: 'Max Storage (TB)',     category: 'performance' },
  { key: 'gpu',        label: 'GPU',                  category: 'performance' },

  { key: 'mainCamera',     label: 'Main Camera',       category: 'camera' },
  { key: 'ultraWide',      label: 'Ultra-Wide Camera', category: 'camera' },
  { key: 'telephoto',      label: 'Telephoto / Zoom',  category: 'camera' },
  { key: 'frontCamera',    label: 'Front Camera',      category: 'camera' },
  { key: 'videoRecording', label: 'Video Recording',   category: 'camera' },

  { key: 'battery',          label: 'Battery Capacity',        category: 'battery' },
  { key: 'wiredCharging',    label: 'Wired Charging',          category: 'battery' },
  { key: 'wirelessCharging', label: 'Wireless Charging',       category: 'battery' },
  { key: 'chargingTime',     label: 'Charging Time (0-50%)',   category: 'battery' },

  { key: 'network5g', label: '5G Support',       category: 'connectivity' },
  { key: 'wifi',       label: 'WiFi Standard',    category: 'connectivity' },
  { key: 'bluetooth',  label: 'Bluetooth Version',category: 'connectivity' },
  { key: 'nfc',        label: 'NFC',              category: 'connectivity' },
  { key: 'simType',    label: 'SIM Type',         category: 'connectivity' },

  { key: 'inventoryLevel',  label: 'Inventory Level',  category: 'logistics', type: 'badge' },
  { key: 'shipsFrom',       label: 'Ships From',       category: 'logistics' },
  { key: 'wholesaleMargin', label: 'Wholesale Margin', category: 'logistics' },
  { key: 'moq',             label: 'Min Order Qty',    category: 'logistics' },
];

export const PRODUCTS = {
  B0CHX1L96S: {
    name: 'Galaxy S23 Ultra',
    brand: 'Samsung',
    icon: 'fa-mobile-screen-button',
    leadTimeDays: 5.8,
    competitiveGrade: 'A',
    competitiveLabel: 'Strong',
    valueScore: 74,
    values: {
      height: '163.4', width: '78.1', depth: '8.9', weight: '234',
      buildMaterial: 'Titanium frame, Gorilla Glass Victus 2', colors: '4 colors',
      screenSize: '6.8"', resolution: '3088 × 1440', displayType: 'Dynamic AMOLED 2X',
      refreshRate: '120Hz Adaptive', peakBrightness: '1,750 nits',
      processor: 'Snapdragon 8 Gen 2', geekbench: '5,124', ram: '12', storage: '1', gpu: 'Adreno 740',
      mainCamera: '200MP f/1.7', ultraWide: '12MP f/2.2', telephoto: '10MP 10x optical',
      frontCamera: '12MP f/2.2', videoRecording: '8K @ 30fps',
      battery: '5,000 mAh', wiredCharging: '45W', wirelessCharging: '15W', chargingTime: '27 min',
      network5g: 'Sub-6 + mmWave', wifi: 'Wi-Fi 6E', bluetooth: '5.3', nfc: 'Yes', simType: 'Nano-SIM + eSIM',
      inventoryLevel: 'Low Stock', shipsFrom: 'Texas, US', wholesaleMargin: '18.5%', moq: '25 units',
    },
  },
  B0CHX8V77N: {
    name: 'OnePlus 11',
    brand: 'OnePlus',
    icon: 'fa-mobile-screen-button',
    leadTimeDays: 4.5,
    competitiveGrade: 'A-',
    competitiveLabel: 'Strong',
    valueScore: 81,
    values: {
      height: '163.1', width: '74.1', depth: '8.5', weight: '205',
      buildMaterial: 'Aluminum frame, Gorilla Glass Victus', colors: '3 colors',
      screenSize: '6.7"', resolution: '3216 × 1440', displayType: 'AMOLED (LTPO3)',
      refreshRate: '120Hz Adaptive', peakBrightness: '1,300 nits',
      processor: 'Snapdragon 8 Gen 2', geekbench: '5,124', ram: '12', storage: '1', gpu: 'Adreno 740',
      mainCamera: '50MP f/1.8', ultraWide: '48MP f/2.2', telephoto: '32MP 2x optical',
      frontCamera: '16MP f/2.4', videoRecording: '8K @ 24fps',
      battery: '5,000 mAh', wiredCharging: '100W', wirelessCharging: 'No', chargingTime: '12 min',
      network5g: 'Sub-6 only', wifi: 'Wi-Fi 6', bluetooth: '5.3', nfc: 'Yes', simType: 'Nano-SIM (dual)',
      inventoryLevel: 'Low Stock', shipsFrom: 'Texas, US', wholesaleMargin: '18.5%', moq: '20 units',
    },
  },
  B0CGVKZ4F5: {
    name: 'Pixel 8 Pro',
    brand: 'Google',
    icon: 'fa-mobile-screen-button',
    leadTimeDays: 2.1,
    competitiveGrade: 'A+',
    competitiveLabel: 'Excellent',
    valueScore: 88,
    values: {
      height: '162.6', width: '76.5', depth: '8.8', weight: '213',
      buildMaterial: 'Aluminum frame, Gorilla Glass Victus 2', colors: '3 colors',
      screenSize: '6.7"', resolution: '2992 × 1344', displayType: 'LTPO OLED',
      refreshRate: '120Hz Adaptive', peakBrightness: '1,600 nits',
      processor: 'Google Tensor G3', geekbench: '4,610', ram: '12', storage: '1', gpu: 'Immortalis-G715s',
      mainCamera: '50MP f/1.68', ultraWide: '48MP f/1.95', telephoto: '48MP 5x optical',
      frontCamera: '10.5MP f/2.2', videoRecording: '4K @ 60fps',
      battery: '5,050 mAh', wiredCharging: '30W', wirelessCharging: '23W', chargingTime: '30 min',
      network5g: 'Sub-6 + mmWave', wifi: 'Wi-Fi 7', bluetooth: '5.3', nfc: 'Yes', simType: 'Nano-SIM + eSIM',
      inventoryLevel: 'In Stock', shipsFrom: 'California, US', wholesaleMargin: '21.2%', moq: '15 units',
    },
  },
  B0CHWRXH8B: {
    name: 'iPhone 15 Pro Max',
    brand: 'Apple',
    icon: 'fa-mobile-screen-button',
    leadTimeDays: 3.2,
    competitiveGrade: 'A',
    competitiveLabel: 'Strong',
    valueScore: 69,
    values: {
      height: '159.9', width: '76.7', depth: '8.25', weight: '221',
      buildMaterial: 'Titanium frame, Ceramic Shield', colors: '4 colors',
      screenSize: '6.7"', resolution: '2796 × 1290', displayType: 'Super Retina XDR OLED',
      refreshRate: '120Hz ProMotion', peakBrightness: '2,000 nits',
      processor: 'A17 Pro (3nm)', geekbench: '7,238', ram: '8', storage: '1', gpu: 'Apple GPU (6-core)',
      mainCamera: '48MP f/1.78', ultraWide: '12MP f/2.2', telephoto: '12MP 5x optical',
      frontCamera: '12MP f/1.9', videoRecording: '4K @ 60fps (ProRes)',
      battery: '4,441 mAh', wiredCharging: '27W', wirelessCharging: '15W (MagSafe)', chargingTime: '35 min',
      network5g: 'Sub-6 + mmWave', wifi: 'Wi-Fi 6E', bluetooth: '5.3', nfc: 'Yes', simType: 'eSIM only (US)',
      inventoryLevel: 'In Stock', shipsFrom: 'California, US', wholesaleMargin: '14.2%', moq: '10 units',
    },
  },
};

export const normalizeSku = (sku) => (sku || '').trim().toUpperCase();

export const findProductBySku = (sku) => PRODUCTS[normalizeSku(sku)] || null;
