/**
 * Per-dataset detail — the preview rail beside the Data tab and the dataset
 * detail page the eye icon opens.
 *
 * Demo data. Every dataset in `connectorDatasets` resolves to something here:
 * the ones worth showing in full are written out below, and anything else falls
 * back to a shape derived from its feed, so no dataset opens an empty screen.
 *
 * Columns are per dataset on purpose — a Sales Orders preview shows order id,
 * buyer and amount; an Inventory preview shows SKU, warehouse and on-hand. A
 * single generic column set would make every dataset look identical and tell the
 * user nothing about what they are actually syncing.
 */

/** Tones for the coloured status pill inside a record row. */
export const RECORD_STATUS_TONES = {
  Shipped: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
  Delivered: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
  Received: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
  Active: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
  Settled: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400',
  Pending: 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400',
  Processing: 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400',
  Draft: 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400',
  Low: 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400',
  Cancelled: 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400',
  Failed: 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400',
  Refunded: 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400',
  'Out of stock': 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400',
};

/** How many record rows one page of the preview table holds. */
export const RECORDS_PAGE_SIZE = 5;

/** Pages of sample records held for a dataset, so the pager has somewhere to go. */
const SAMPLE_PAGES = 3;

const col = (key, label, extra = {}) => ({ key, label, ...extra });

/**
 * The datasets written out in full.
 *
 * `fields` is the schema chip list. `columns` describes the preview table and
 * `rows` is one page of it — `expandRows` below turns that page into several so
 * the pager works without another 100 lines of hand-written records.
 */
const DATASET_TEMPLATES = {
  'Sales Orders': {
    owner: 'Nikhil Verma',
    createdOn: 'Apr 15, 2025',
    fields: ['Order ID', 'Amazon Order ID', 'Order Date', 'Status', 'Buyer Name', 'Total Amount', 'Currency'],
    columns: [
      col('orderId', 'Order ID'),
      col('orderDate', 'Order Date'),
      col('status', 'Status', { type: 'status' }),
      col('buyer', 'Buyer'),
      col('amount', 'Amount', { align: 'right' }),
      col('currency', 'Currency'),
    ],
    rows: [
      { orderId: 'SO-2025-001234', orderDate: 'May 12, 2025 10:18 AM', status: 'Shipped', buyer: 'John Smith', amount: '149.99', currency: 'USD' },
      { orderId: 'SO-2025-001233', orderDate: 'May 12, 2025 10:15 AM', status: 'Pending', buyer: 'Emily Johnson', amount: '89.50', currency: 'USD' },
      { orderId: 'SO-2025-001232', orderDate: 'May 12, 2025 10:12 AM', status: 'Shipped', buyer: 'Michael Brown', amount: '239.00', currency: 'USD' },
      { orderId: 'SO-2025-001231', orderDate: 'May 12, 2025 10:10 AM', status: 'Cancelled', buyer: 'Sarah Williams', amount: '120.00', currency: 'USD' },
      { orderId: 'SO-2025-001230', orderDate: 'May 12, 2025 10:08 AM', status: 'Pending', buyer: 'David Miller', amount: '76.45', currency: 'USD' },
    ],
  },

  'Order Items': {
    owner: 'Nikhil Verma',
    createdOn: 'Apr 15, 2025',
    fields: ['Item ID', 'Order ID', 'SKU', 'ASIN', 'Quantity', 'Unit Price', 'Tax'],
    columns: [
      col('itemId', 'Item ID'),
      col('orderId', 'Order ID'),
      col('sku', 'SKU'),
      col('qty', 'Qty', { align: 'right' }),
      col('unitPrice', 'Unit Price', { align: 'right' }),
      col('currency', 'Currency'),
    ],
    rows: [
      { itemId: 'OI-88412', orderId: 'SO-2025-001234', sku: 'WH-PRO-2024', qty: '2', unitPrice: '74.99', currency: 'USD' },
      { itemId: 'OI-88411', orderId: 'SO-2025-001233', sku: 'SC-HOME-V2', qty: '1', unitPrice: '89.50', currency: 'USD' },
      { itemId: 'OI-88410', orderId: 'SO-2025-001232', sku: 'AUD-EAR-PRO', qty: '1', unitPrice: '129.00', currency: 'USD' },
      { itemId: 'OI-88409', orderId: 'SO-2025-001232', sku: 'ACC-STD-012', qty: '4', unitPrice: '27.50', currency: 'USD' },
      { itemId: 'OI-88408', orderId: 'SO-2025-001231', sku: 'FT-YOG-002', qty: '2', unitPrice: '60.00', currency: 'USD' },
    ],
  },

  Inventory: {
    owner: 'Rohit Sharma',
    createdOn: 'Apr 15, 2025',
    fields: ['SKU', 'Warehouse', 'On Hand', 'Reserved', 'Available', 'Reorder Point', 'Updated At'],
    columns: [
      col('sku', 'SKU'),
      col('warehouse', 'Warehouse'),
      col('onHand', 'On Hand', { align: 'right' }),
      col('reserved', 'Reserved', { align: 'right' }),
      col('available', 'Available', { align: 'right' }),
      col('updated', 'Updated'),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { sku: 'WH-PRO-2024', warehouse: 'BLR-01', onHand: '412', reserved: '38', available: '374', updated: 'May 12, 2025', status: 'Active' },
      { sku: 'SC-HOME-V2', warehouse: 'BLR-01', onHand: '86', reserved: '12', available: '74', updated: 'May 12, 2025', status: 'Low' },
      { sku: 'AP-TEE-001', warehouse: 'DEL-02', onHand: '1,240', reserved: '104', available: '1,136', updated: 'May 12, 2025', status: 'Active' },
      { sku: 'VKAMCOVER0072', warehouse: 'DEL-02', onHand: '0', reserved: '0', available: '0', updated: 'May 12, 2025', status: 'Out of stock' },
      { sku: 'HOME-ORG-006', warehouse: 'MUM-03', onHand: '154', reserved: '22', available: '132', updated: 'May 12, 2025', status: 'Active' },
    ],
  },

  'FBA Inventory': {
    owner: 'Rohit Sharma',
    createdOn: 'Apr 18, 2025',
    fields: ['SKU', 'Fulfilment Centre', 'Sellable', 'Unsellable', 'Inbound', 'Reserved', 'Updated At'],
    columns: [
      col('sku', 'SKU'),
      col('centre', 'Fulfilment Centre'),
      col('sellable', 'Sellable', { align: 'right' }),
      col('unsellable', 'Unsellable', { align: 'right' }),
      col('inbound', 'Inbound', { align: 'right' }),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { sku: 'WH-PRO-2024', centre: 'BOM7', sellable: '318', unsellable: '4', inbound: '120', status: 'Active' },
      { sku: 'AUD-EAR-PRO', centre: 'BOM7', sellable: '204', unsellable: '11', inbound: '0', status: 'Active' },
      { sku: 'TEC-USB-007', centre: 'DEL4', sellable: '96', unsellable: '2', inbound: '250', status: 'Low' },
      { sku: 'FT-YOG-002', centre: 'DEL4', sellable: '58', unsellable: '0', inbound: '0', status: 'Low' },
      { sku: 'PF-ORG-15LB', centre: 'BLR5', sellable: '640', unsellable: '18', inbound: '400', status: 'Active' },
    ],
  },

  'Financial Events': {
    owner: 'Priya Nair',
    createdOn: 'Apr 20, 2025',
    fields: ['Event ID', 'Event Type', 'Posted Date', 'Order ID', 'Amount', 'Fee Type', 'Currency'],
    columns: [
      col('eventId', 'Event ID'),
      col('type', 'Event Type'),
      col('posted', 'Posted'),
      col('orderId', 'Order ID'),
      col('amount', 'Amount', { align: 'right' }),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { eventId: 'FE-55210', type: 'Order payment', posted: 'May 12, 2025', orderId: 'SO-2025-001234', amount: '142.11', status: 'Settled' },
      { eventId: 'FE-55209', type: 'Referral fee', posted: 'May 12, 2025', orderId: 'SO-2025-001234', amount: '-22.50', status: 'Settled' },
      { eventId: 'FE-55208', type: 'FBA fee', posted: 'May 12, 2025', orderId: 'SO-2025-001233', amount: '-8.40', status: 'Settled' },
      { eventId: 'FE-55207', type: 'Refund', posted: 'May 11, 2025', orderId: 'SO-2025-001208', amount: '-120.00', status: 'Refunded' },
      { eventId: 'FE-55206', type: 'Order payment', posted: 'May 11, 2025', orderId: 'SO-2025-001207', amount: '318.90', status: 'Pending' },
    ],
  },

  Returns: {
    owner: 'Priya Nair',
    createdOn: 'Apr 22, 2025',
    fields: ['Return ID', 'Order ID', 'SKU', 'Reason', 'Status', 'Refund Amount', 'Received At'],
    columns: [
      col('returnId', 'Return ID'),
      col('orderId', 'Order ID'),
      col('reason', 'Reason'),
      col('status', 'Status', { type: 'status' }),
      col('refund', 'Refund', { align: 'right' }),
      col('currency', 'Currency'),
    ],
    rows: [
      { returnId: 'RT-10488', orderId: 'SO-2025-001188', reason: 'Damaged on arrival', status: 'Received', refund: '149.99', currency: 'USD' },
      { returnId: 'RT-10487', orderId: 'SO-2025-001172', reason: 'No longer needed', status: 'Processing', refund: '89.50', currency: 'USD' },
      { returnId: 'RT-10486', orderId: 'SO-2025-001164', reason: 'Wrong item sent', status: 'Refunded', refund: '239.00', currency: 'USD' },
      { returnId: 'RT-10485', orderId: 'SO-2025-001150', reason: 'Better price found', status: 'Received', refund: '76.45', currency: 'USD' },
      { returnId: 'RT-10484', orderId: 'SO-2025-001141', reason: 'Item defective', status: 'Processing', refund: '120.00', currency: 'USD' },
    ],
  },

  'Performance Metrics': {
    owner: 'Nikhil Verma',
    createdOn: 'Apr 25, 2025',
    fields: ['Date', 'Sessions', 'Page Views', 'Units Ordered', 'Buy Box %', 'Conversion %', 'ASIN'],
    columns: [
      col('date', 'Date'),
      col('sessions', 'Sessions', { align: 'right' }),
      col('pageViews', 'Page Views', { align: 'right' }),
      col('units', 'Units', { align: 'right' }),
      col('buyBox', 'Buy Box %', { align: 'right' }),
      col('conversion', 'Conversion', { align: 'right' }),
    ],
    rows: [
      { date: 'May 12, 2025', sessions: '18,420', pageViews: '24,118', units: '1,204', buyBox: '98%', conversion: '6.5%' },
      { date: 'May 11, 2025', sessions: '17,880', pageViews: '23,406', units: '1,142', buyBox: '97%', conversion: '6.4%' },
      { date: 'May 10, 2025', sessions: '21,050', pageViews: '28,900', units: '1,488', buyBox: '99%', conversion: '7.1%' },
      { date: 'May 9, 2025', sessions: '16,204', pageViews: '20,880', units: '968', buyBox: '95%', conversion: '6.0%' },
      { date: 'May 8, 2025', sessions: '15,772', pageViews: '19,940', units: '902', buyBox: '96%', conversion: '5.7%' },
    ],
  },

  'Fee Estimates': {
    owner: 'Priya Nair',
    createdOn: 'Apr 28, 2025',
    fields: ['SKU', 'ASIN', 'Referral Fee', 'FBA Fee', 'Total Fees', 'Currency', 'Estimated At'],
    columns: [
      col('sku', 'SKU'),
      col('referral', 'Referral Fee', { align: 'right' }),
      col('fba', 'FBA Fee', { align: 'right' }),
      col('total', 'Total Fees', { align: 'right' }),
      col('currency', 'Currency'),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { sku: 'WH-PRO-2024', referral: '22.50', fba: '8.40', total: '30.90', currency: 'USD', status: 'Active' },
      { sku: 'SC-HOME-V2', referral: '13.43', fba: '6.20', total: '19.63', currency: 'USD', status: 'Active' },
      { sku: 'AUD-EAR-PRO', referral: '19.35', fba: '7.10', total: '26.45', currency: 'USD', status: 'Active' },
      { sku: 'TEC-USB-007', referral: '7.35', fba: '4.80', total: '12.15', currency: 'USD', status: 'Pending' },
      { sku: 'FT-YOG-002', referral: '8.85', fba: '9.60', total: '18.45', currency: 'USD', status: 'Active' },
    ],
  },

  Orders: {
    owner: 'Rohit Sharma',
    createdOn: 'Apr 10, 2025',
    fields: ['Order ID', 'Order Number', 'Created At', 'Financial Status', 'Customer', 'Total Price', 'Currency'],
    columns: [
      col('orderId', 'Order ID'),
      col('createdAt', 'Created At'),
      col('status', 'Status', { type: 'status' }),
      col('customer', 'Customer'),
      col('total', 'Total', { align: 'right' }),
      col('currency', 'Currency'),
    ],
    rows: [
      { orderId: '#SH-40218', createdAt: 'May 12, 2025 10:16 AM', status: 'Shipped', customer: 'Aditi Rao', total: '2,480.00', currency: 'INR' },
      { orderId: '#SH-40217', createdAt: 'May 12, 2025 10:09 AM', status: 'Pending', customer: 'Karan Mehta', total: '1,150.00', currency: 'INR' },
      { orderId: '#SH-40216', createdAt: 'May 12, 2025 09:58 AM', status: 'Delivered', customer: 'Sneha Kapoor', total: '3,299.00', currency: 'INR' },
      { orderId: '#SH-40215', createdAt: 'May 12, 2025 09:44 AM', status: 'Refunded', customer: 'Arjun Nair', total: '899.00', currency: 'INR' },
      { orderId: '#SH-40214', createdAt: 'May 12, 2025 09:31 AM', status: 'Shipped', customer: 'Meera Iyer', total: '1,749.00', currency: 'INR' },
    ],
  },

  'Line Items': {
    owner: 'Rohit Sharma',
    createdOn: 'Apr 10, 2025',
    fields: ['Line Item ID', 'Order ID', 'Product ID', 'Variant', 'Quantity', 'Price', 'Discount'],
    columns: [
      col('lineId', 'Line Item ID'),
      col('orderId', 'Order ID'),
      col('variant', 'Variant'),
      col('qty', 'Qty', { align: 'right' }),
      col('price', 'Price', { align: 'right' }),
      col('currency', 'Currency'),
    ],
    rows: [
      { lineId: 'LI-91002', orderId: '#SH-40218', variant: 'Black / M', qty: '2', price: '1,240.00', currency: 'INR' },
      { lineId: 'LI-91001', orderId: '#SH-40217', variant: 'Blue / L', qty: '1', price: '1,150.00', currency: 'INR' },
      { lineId: 'LI-91000', orderId: '#SH-40216', variant: 'Default', qty: '3', price: '1,099.67', currency: 'INR' },
      { lineId: 'LI-90999', orderId: '#SH-40215', variant: 'Red / S', qty: '1', price: '899.00', currency: 'INR' },
      { lineId: 'LI-90998', orderId: '#SH-40214', variant: 'Green / XL', qty: '1', price: '1,749.00', currency: 'INR' },
    ],
  },

  Customers: {
    owner: 'Sneha Kapoor',
    createdOn: 'Apr 12, 2025',
    fields: ['Customer ID', 'Email', 'First Name', 'Last Name', 'Orders Count', 'Total Spent', 'Created At'],
    columns: [
      col('customerId', 'Customer ID'),
      col('name', 'Name'),
      col('email', 'Email'),
      col('orders', 'Orders', { align: 'right' }),
      col('spent', 'Total Spent', { align: 'right' }),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { customerId: 'CU-20881', name: 'Aditi Rao', email: 'aditi.rao@example.com', orders: '14', spent: '28,410.00', status: 'Active' },
      { customerId: 'CU-20880', name: 'Karan Mehta', email: 'karan.m@example.com', orders: '3', spent: '4,120.00', status: 'Active' },
      { customerId: 'CU-20879', name: 'Sneha Kapoor', email: 'sneha.k@example.com', orders: '21', spent: '51,880.00', status: 'Active' },
      { customerId: 'CU-20878', name: 'Arjun Nair', email: 'arjun.nair@example.com', orders: '1', spent: '899.00', status: 'Pending' },
      { customerId: 'CU-20877', name: 'Meera Iyer', email: 'meera.iyer@example.com', orders: '8', spent: '16,240.00', status: 'Active' },
    ],
  },

  Products: {
    owner: 'Sneha Kapoor',
    createdOn: 'Apr 12, 2025',
    fields: ['Product ID', 'Title', 'Handle', 'Vendor', 'Product Type', 'Price', 'Status'],
    columns: [
      col('productId', 'Product ID'),
      col('title', 'Title'),
      col('vendor', 'Vendor'),
      col('price', 'Price', { align: 'right' }),
      col('currency', 'Currency'),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { productId: 'PR-7712', title: 'Premium Wireless Headphones', vendor: 'Acme Audio', price: '12,499.00', currency: 'INR', status: 'Active' },
      { productId: 'PR-7711', title: 'Security Camera V2', vendor: 'Acme Home', price: '7,299.00', currency: 'INR', status: 'Active' },
      { productId: 'PR-7710', title: 'Essential T-Shirt', vendor: 'Acme Apparel', price: '1,199.00', currency: 'INR', status: 'Draft' },
      { productId: 'PR-7709', title: 'Minimalist Watch', vendor: 'Acme Wear', price: '16,499.00', currency: 'INR', status: 'Active' },
      { productId: 'PR-7708', title: 'Bamboo Phone Stand', vendor: 'Acme Living', price: '899.00', currency: 'INR', status: 'Active' },
    ],
  },

  'Inventory Levels': {
    owner: 'Rohit Sharma',
    createdOn: 'Apr 14, 2025',
    fields: ['Inventory Item ID', 'Location', 'Available', 'Committed', 'Incoming', 'Updated At', 'SKU'],
    columns: [
      col('itemId', 'Item ID'),
      col('location', 'Location'),
      col('available', 'Available', { align: 'right' }),
      col('committed', 'Committed', { align: 'right' }),
      col('incoming', 'Incoming', { align: 'right' }),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { itemId: 'IV-33108', location: 'Bengaluru HQ', available: '318', committed: '24', incoming: '0', status: 'Active' },
      { itemId: 'IV-33107', location: 'Bengaluru HQ', available: '42', committed: '18', incoming: '200', status: 'Low' },
      { itemId: 'IV-33106', location: 'Delhi WH', available: '1,120', committed: '96', incoming: '0', status: 'Active' },
      { itemId: 'IV-33105', location: 'Delhi WH', available: '0', committed: '0', incoming: '150', status: 'Out of stock' },
      { itemId: 'IV-33104', location: 'Mumbai WH', available: '204', committed: '31', incoming: '0', status: 'Active' },
    ],
  },

  Refunds: {
    owner: 'Priya Nair',
    createdOn: 'Apr 16, 2025',
    fields: ['Refund ID', 'Order ID', 'Reason', 'Amount', 'Currency', 'Processed At', 'Gateway'],
    columns: [
      col('refundId', 'Refund ID'),
      col('orderId', 'Order ID'),
      col('reason', 'Reason'),
      col('amount', 'Amount', { align: 'right' }),
      col('currency', 'Currency'),
      col('status', 'Status', { type: 'status' }),
    ],
    rows: [
      { refundId: 'RF-8820', orderId: '#SH-40215', reason: 'Customer request', amount: '899.00', currency: 'INR', status: 'Refunded' },
      { refundId: 'RF-8819', orderId: '#SH-40190', reason: 'Damaged item', amount: '1,240.00', currency: 'INR', status: 'Refunded' },
      { refundId: 'RF-8818', orderId: '#SH-40174', reason: 'Late delivery', amount: '640.00', currency: 'INR', status: 'Processing' },
      { refundId: 'RF-8817', orderId: '#SH-40160', reason: 'Wrong variant', amount: '1,099.00', currency: 'INR', status: 'Refunded' },
      { refundId: 'RF-8816', orderId: '#SH-40142', reason: 'Duplicate order', amount: '2,480.00', currency: 'INR', status: 'Pending' },
    ],
  },
};

/** Fallback for connectors whose datasets are derived from their feeds. */
const genericTemplate = (dataset) => ({
  owner: 'Nikhil Verma',
  createdOn: 'Apr 15, 2025',
  fields: ['Record ID', 'External ID', 'Received At', 'Status', 'Source Feed', 'Payload Size', 'Checksum'],
  columns: [
    col('recordId', 'Record ID'),
    col('externalId', 'External ID'),
    col('received', 'Received At'),
    col('feed', 'Feed'),
    col('status', 'Status', { type: 'status' }),
  ],
  rows: [
    { recordId: 'RC-00521', externalId: 'EXT-92014', received: 'May 12, 2025 10:20 AM', feed: dataset.feed, status: 'Received' },
    { recordId: 'RC-00520', externalId: 'EXT-92013', received: 'May 12, 2025 10:18 AM', feed: dataset.feed, status: 'Received' },
    { recordId: 'RC-00519', externalId: 'EXT-92012', received: 'May 12, 2025 10:15 AM', feed: dataset.feed, status: 'Processing' },
    { recordId: 'RC-00518', externalId: 'EXT-92011', received: 'May 12, 2025 10:12 AM', feed: dataset.feed, status: 'Received' },
    { recordId: 'RC-00517', externalId: 'EXT-92010', received: 'May 12, 2025 10:09 AM', feed: dataset.feed, status: 'Pending' },
  ],
});

const MONTH_DAY = /\b([A-Z][a-z]{2}) (\d{1,2}), (\d{4})\b/;
const NUMERIC = /^-?[\d,]+(\.\d+)?%?$/;

/** Steps an identifier's trailing number back, keeping its zero padding. */
const shiftId = (value, by) =>
  value.replace(/(\d+)$/, (digits) =>
    String(Math.max(0, Number(digits) - by)).padStart(digits.length, '0')
  );

/** Steps "May 12, 2025" back a day per page, so older pages read as older rows. */
const shiftDate = (value, by) =>
  value.replace(MONTH_DAY, (whole, month, day, year) =>
    `${month} ${Math.max(1, Number(day) - by)}, ${year}`
  );

/** Eases a formatted number down, preserving commas, decimals and any % sign. */
const shiftNumber = (value, page) => {
  const percent = value.endsWith('%');
  const raw = Number(value.replace(/[,%]/g, ''));
  if (!Number.isFinite(raw)) return value;

  const decimals = (value.split('.')[1] || '').replace('%', '').length;
  const next = raw * (1 - 0.06 * page);
  const rounded = decimals ? next.toFixed(decimals) : String(Math.round(next));
  const grouped = value.includes(',')
    ? Number(rounded).toLocaleString('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })
    : rounded;
  return percent ? `${grouped}%` : grouped;
};

/**
 * Turns one written-out page of records into `SAMPLE_PAGES` of them, so paging
 * through the preview lands on distinct rows rather than the same five repeated.
 *
 * Deterministic — derived from the page index, never random — so a row sits on
 * the same page on every render and across a refresh. Identifiers step back,
 * dates step back a day per page, and figures ease down; labels and statuses are
 * left alone, since a row whose status changed per page would read as a state
 * change rather than as an older record.
 */
const expandRows = (rows) =>
  Array.from({ length: SAMPLE_PAGES }, (_, page) =>
    rows.map((row) => {
      if (page === 0) return row;
      const stamped = {};
      Object.entries(row).forEach(([key, value]) => {
        if (typeof value !== 'string') {
          stamped[key] = value;
        } else if (/id$/i.test(key)) {
          stamped[key] = shiftId(value, page * rows.length);
        } else if (MONTH_DAY.test(value)) {
          stamped[key] = shiftDate(value, page);
        } else if (NUMERIC.test(value)) {
          stamped[key] = shiftNumber(value, page);
        } else {
          stamped[key] = value;
        }
      });
      return stamped;
    })
  ).flat();

/** Per-dataset quality, derived from the dataset's own record count. */
const datasetQuality = (dataset) => {
  const quality = dataset.status === 'healthy' ? 98.6 : dataset.status === 'stale' ? 94.2 : 91.4;
  const valid = Math.round((dataset.records * quality) / 100);
  return {
    quality,
    valid,
    invalid: dataset.records - valid,
    invalidPct: Number((100 - quality).toFixed(1)),
  };
};

/**
 * Everything the preview rail and the dataset page render for one dataset.
 *
 * An override merged over a derived default, the same way `connectorDetail`
 * works — so every row in the Datasets table opens a populated screen.
 */
export const datasetDetail = (connector, dataset) => {
  if (!dataset) return null;
  const template = DATASET_TEMPLATES[dataset.name] || genericTemplate(dataset);

  return {
    ...dataset,
    owner: template.owner,
    createdOn: template.createdOn,
    fields: template.fields,
    columns: template.columns,
    records: dataset.records,
    rows: expandRows(template.rows),
    syncFrequency: 'Every 15 minutes',
    autoSync: true,
    nextSync: 'May 12, 2025, 10:39 AM',
    connectorName: connector?.name || '—',
    quality: datasetQuality(dataset),
  };
};

/** URL-safe id for a dataset, so its page can be linked to and refreshed. */
export const datasetSlug = (name) =>
  String(name).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
