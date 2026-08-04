export const PROFIT_ADS_SUMMARY = {
  recoverableNow: {
    value: '$310,995',
    subtitle: 'recoverable now — overspending above break-even\nacross 41 FIX ADS SKUs · $310,259 certain, $735 rests on estimated inputs\n\nStart with the top 4 of 41 — they hold 74% of the recoverable.',
    stats: [
      {
        parts: [
          { text: '$345,770', bold: true },
          { text: ' ad spend above break-even, portfolio-wide', iconId: 'ad_spend' }
        ]
      },
      {
        parts: [
          { text: '$1,600,190', bold: true },
          { text: ' scale upside (dir.)', iconId: 'scale' },
          { text: ' · ' },
          { text: '$27,055', bold: true },
          { text: ' bleed to stop', iconId: 'bleed' }
        ]
      },
      {
        parts: [
          { text: '8 below cost', bold: false },
          { text: ' · portfolio TACoS 5.0% · TACoS → stable', iconId: 'tacos' }
        ]
      },
      {
        parts: [
          { text: '22 cannibalization risk · 1 lifecycle-guarded' }
        ]
      }
    ]
  },
  categories: [
    { label: 'SCALE', value: '28', subtext: 'Upside $335,621', isActive: false },
    { label: 'FIX ADS', value: '15', subtext: 'Recoverable $203,012', isActive: true },
    { label: 'FIX MARGIN', value: '0', subtext: '0 to reprice', isActive: false },
    { label: 'CUT/DIVEST', value: '0', subtext: 'Bleed $0', isActive: false }
  ],
  footerProjected: '$203,012'
};

export const SKU_LEDGER_DATA = [
  {
    id: 1,
    title: 'Autofy Waterproof Bike Cover Scooter...',
    sku: 'SKU-B0BHSZQG3P',
    campaignCount: 1,
    category: 'Bike Accessories',
    acos: 41,
    be: 17,
    cmaa: '$340,508',
    recoverable: '$158,192'
  },
  {
    id: 2,
    title: 'Car Cover Waterproof DF-I for Tata Altroz',
    sku: 'SKU-B0DF1ALTZ',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 38,
    be: 16,
    cmaa: '$155,000',
    recoverable: '$58,881'
  },
  {
    id: 3,
    title: 'Car Cover Waterproof SS-I for Mahindra Thar',
    sku: 'SKU-B0SSTHAR1',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 35,
    be: 15,
    cmaa: '$120,000',
    recoverable: '$45,884'
  },
  {
    id: 4,
    title: 'Car Cover Waterproof TU-I for Tata Punch',
    sku: 'SKU-B0TUPUNCH',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 33,
    be: 16,
    cmaa: '$95,000',
    recoverable: '$31,797'
  },
  {
    id: 5,
    title: 'Autofy TUFF Car Cover for Maruti Suzuki Fronx',
    sku: 'SKU-B0TUFFFRX',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 30,
    be: 18,
    cmaa: '$72,000',
    recoverable: '$25,532'
  },
  {
    id: 6,
    title: 'Autofy Car Cover Waterproof TAFO-Piping for Mahindra Thar',
    sku: 'SKU-B0TAFOTHR',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 28,
    be: 19,
    cmaa: '$48,000',
    recoverable: '$16,120'
  },
  {
    id: 7,
    title: 'Autofy Car Cover Waterproof Econo for Maruti Vitara Brezza',
    sku: 'SKU-B0ECOVTZ',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 26,
    be: 19,
    cmaa: '$39,000',
    recoverable: '$13,036'
  },
  {
    id: 8,
    title: 'Autofy Car Cover Waterproof SilverTech-Piping for Hyundai Creta',
    sku: 'SKU-B0CDC2XKDH',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 20,
    be: 23,
    cmaa: '$16,497',
    recoverable: '$0'
  },
  {
    id: 9,
    title: 'Autofy BlueTech-Black Piping 100% Waterproof Car Cover',
    sku: 'SKU-B0BLUEBLK',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 24,
    be: 20,
    cmaa: '$21,000',
    recoverable: '$6,671'
  },
  {
    id: 10,
    title: 'Autofy RedTech 100% Waterproof Car Cover',
    sku: 'SKU-B0REDTECH',
    campaignCount: 1,
    category: 'Car Accessories',
    acos: 23,
    be: 20,
    cmaa: '$18,000',
    recoverable: '$6,276'
  },
  {
    id: 11,
    title: 'Autofy DUSTO Wet & Dry Car Vacuum Cleaner',
    sku: 'SKU-B0DUSTOVC',
    campaignCount: 2,
    category: 'Car Electronics',
    acos: 27,
    be: 21,
    cmaa: '$14,000',
    recoverable: '$7,538'
  }
];

export const MODAL_MOCK_DATA = {
  fidelity: 'CAMPAIGN-LEVEL · CSV (DERIVED) · COVERAGE 90%',
  recommendation: {
    actionTitle: 'Remove SKU · SP Auto · SKU-B0BHSZQG3P',
    badgeText: 'REMOVE-AD',
    gain: '+$158,192/mo',
    description: "Campaign 'SP Auto · SKU-B0BHSZQG3P' spends 100% of this SKU's ad budget at 41% ACOS on the SKU vs its 17% break-even. That's beyond what a bid cut fixes. Remove this SKU's product ad from the campaign."
  },
  simulation: {
    bidChange: -30,
    targetAcos: 17,
    projections: [
      { days: '30d', gain: '+$134,463', p: 'p≈0.68' },
      { days: '60d', gain: '+$292,655', p: 'p≈0.62' },
      { days: '90d', gain: '+$450,847', p: 'p≈0.57' }
    ],
    tripwireWarning: 'Tripwire: units/wk drop >15% → auto-revert.'
  }
};
