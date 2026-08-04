import React from 'react';
import { ChannelBadge, ProductCell, CampaignCell, ReturnQtyCell, PctBar, BBCell, BBStatus, DOCStatus, AdTypeBadge, SettlementStatus, PaidBadge, CatBadge } from '@/features/screener/components/kpi-detail/cells';
import { $c, fN, fP, fX, fPr } from '@/features/screener/components/kpi-detail/formatters';
import { SKUS, CAMPAIGNS, SETTLEMENTS, OUTFLOWS } from '@/features/screener/components/kpi-detail/kpiDetailData';

/**
 * Maps a KPI title to the summary tiles, columns and rows its drill-down
 * table should render. Pure configuration — no component logic lives here.
 */
/* ── Table config per KPI ──────────────────────────────────────── */
export const getTableDef = (title) => {
  /* ─ Total Revenue ──────────────────────────────────────────── */
  if (title === 'Total Revenue') return {
    summary: [
      { label: 'Total SKUs', value: '10' },
      { label: 'Avg Rev / SKU', value: $c(124500 / 10) },
      { label: 'Total Returns', value: $c(4457) },
      { label: 'Net Settled', value: $c(124500 - 4457) },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'channel', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Units Sold', key: 'units', cls: 'text-right', render: (r) => <span className="font-medium text-gray-800 dark:text-slate-200">{fN(r.units)}</span> },
      { label: 'Unit Price', key: 'price', cls: 'text-right', render: (r) => <span>{fPr(r.price)}</span> },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{$c(r.revenue)}</span> },
      { label: 'Return Qty', key: 'returnQty', cls: 'text-right', render: (r) => <ReturnQtyCell qty={r.returnQty} units={r.units} /> },
      { label: 'Returns Value', key: 'returnVal', cls: 'text-right', render: (r) => <span className="text-red-500 dark:text-red-400">{$c(r.returnVal)}</span> },
      { label: 'Net Settled', key: 'netSettled', cls: 'text-right', render: (r) => <span className="font-semibold text-green-600 dark:text-green-400">{$c(r.netSettled)}</span> },
    ],
    rows: SKUS,
    totals: { name: 'TOTAL', units: 2180, revenue: 124500, returnQty: 70, returnVal: 4457, netSettled: 120043 },
  };

  /* ─ Units Sold ─────────────────────────────────────────────── */
  if (title === 'Units Sold') return {
    summary: [
      { label: 'Active SKUs', value: '10' },
      { label: 'Avg Units / SKU', value: fN(2180 / 10) },
      { label: 'Top SKU', value: 'Earbuds Pro' },
      { label: 'Returns (units)', value: '70' },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'channel', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Units Sold', key: 'units', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{fN(r.units)}</span> },
      { label: '% of Total', key: 'pct', cls: 'text-right', render: (r) => <PctBar pct={(r.units / 2180 * 100).toFixed(1)} /> },
      { label: 'Unit Price', key: 'price', cls: 'text-right', render: (r) => <span>{fPr(r.price)}</span> },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span className="font-medium">{$c(r.revenue)}</span> },
      { label: 'Returns', key: 'returnQty', cls: 'text-right', render: (r) => <ReturnQtyCell qty={r.returnQty} units={r.units} /> },
    ],
    rows: [...SKUS].sort((a, b) => b.units - a.units),
    totals: { name: 'TOTAL', units: 2180, revenue: 124500, returnQty: 70 },
  };

  /* ─ Total Orders ───────────────────────────────────────────── */
  if (title === 'Total Orders') return {
    summary: [
      { label: 'Total Orders', value: '412' },
      { label: 'Avg Units / Order', value: fP(2180 / 412) },
      { label: 'Avg Order Value', value: $c(124500 / 412) },
      { label: 'Returned Orders', value: '28' },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'channel', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Orders', key: 'orders', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{r.orders}</span> },
      { label: 'Units / Order', key: 'upo', cls: 'text-right', render: (r) => <span>{(r.units / r.orders).toFixed(1)}</span> },
      { label: 'Avg Order Value', key: 'aov', cls: 'text-right', render: (r) => <span className="font-medium">{$c(r.revenue / r.orders)}</span> },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span>{$c(r.revenue)}</span> },
      { label: 'Return Orders', key: 'retOrd', cls: 'text-right', render: (r) => <span className={r.returnQty > 10 ? 'text-red-500 dark:text-red-400' : 'text-gray-500 dark:text-slate-400'}>{Math.round(r.returnQty * 0.6)}</span> },
    ],
    rows: [...SKUS].sort((a, b) => b.orders - a.orders),
    totals: { name: 'TOTAL', orders: 412, revenue: 124500 },
  };

  /* ─ Avg Order Value ────────────────────────────────────────── */
  if (title === 'Avg Order Value') return {
    summary: [
      { label: 'Portfolio AOV', value: '$302' },
      { label: 'Highest AOV SKU', value: 'Security Cam' },
      { label: 'Lowest AOV SKU', value: 'Portable Charger' },
      { label: 'AOV vs Prior', value: '+$12.40' },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'channel', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Orders', key: 'orders', cls: 'text-right', render: (r) => <span>{r.orders}</span> },
      { label: 'Avg Order Value', key: 'aov', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{$c(r.revenue / r.orders)}</span> },
      { label: 'Units / Order', key: 'upo', cls: 'text-right', render: (r) => <span>{(r.units / r.orders).toFixed(1)}</span> },
      { label: 'vs Avg ($302)', key: 'vsAvg', cls: 'text-right', render: (r) => { const v = r.revenue / r.orders - 302; return <span className={v >= 0 ? 'text-green-600 dark:text-green-400 font-medium' : 'text-red-500 dark:text-red-400 font-medium'}>{v >= 0 ? '+' : ''}{$c(Math.abs(v))}</span>; } },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span>{$c(r.revenue)}</span> },
    ],
    rows: [...SKUS].sort((a, b) => (b.revenue / b.orders) - (a.revenue / a.orders)),
    totals: null,
  };

  /* ─ Buy Box % ──────────────────────────────────────────────── */
  if (title === 'Buy Box %') return {
    summary: [
      { label: 'Overall Buy Box', value: '87.4%' },
      { label: 'SKUs Winning', value: '9 / 10' },
      { label: 'SKUs Lost', value: '1 / 10' },
      { label: 'Revenue at Risk', value: $c(12862) },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Buy Box %', key: 'bb', cls: 'text-right', render: (r) => <BBCell pct={r.buyBoxPct} status={r.bbStatus} /> },
      { label: 'Status', key: 'bbs', cls: 'text-center', render: (r) => <BBStatus status={r.bbStatus} /> },
      { label: 'Your Price', key: 'yp', cls: 'text-right', render: (r) => <span className="font-medium">{fPr(r.price)}</span> },
      { label: 'Lowest Competitor', key: 'comp', cls: 'text-right', render: (r) => <span>{fPr(r.competitorPrice)}</span> },
      { label: 'Price Gap', key: 'gap', cls: 'text-right', render: (r) => { const g = r.price - r.competitorPrice; return <span className={g > 0 ? 'text-red-500 dark:text-red-400 font-medium' : 'text-green-600 dark:text-green-400 font-medium'}>{g > 0 ? '+' : ''}{fPr(g)}</span>; } },
      { label: 'Revenue', key: 'rev', cls: 'text-right', render: (r) => <span>{$c(r.revenue)}</span> },
    ],
    rows: [...SKUS].sort((a, b) => a.buyBoxPct - b.buyBoxPct),
    totals: null,
  };

  /* ─ Return Rate ────────────────────────────────────────────── */
  if (title === 'Return Rate') return {
    summary: [
      { label: 'Overall Return Rate', value: '3.2%' },
      { label: 'Total Returns', value: '70 units' },
      { label: 'Total Refund Value', value: $c(4457) },
      { label: 'Net Revenue Impact', value: $c(124500 - 4457) },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Units Sold', key: 'units', cls: 'text-right', render: (r) => <span>{fN(r.units)}</span> },
      { label: 'Returns', key: 'returnQty', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{r.returnQty}</span> },
      { label: 'Return Rate', key: 'rr', cls: 'text-right', render: (r) => { const rr = r.returnQty / r.units * 100; return <span className={rr > 8 ? 'text-red-500 dark:text-red-400 font-semibold' : rr > 4 ? 'text-amber-500 dark:text-amber-400 font-medium' : 'text-green-600 dark:text-green-400 font-medium'}>{fP(rr)}</span>; } },
      { label: 'Refund Value', key: 'returnVal', cls: 'text-right', render: (r) => <span className="text-red-500 dark:text-red-400">{$c(r.returnVal)}</span> },
      { label: 'Top Reason', key: 'reason', cls: 'text-left', render: (r) => <span className="text-xs text-gray-500 dark:text-slate-400">{r.returnReason}</span> },
    ],
    rows: [...SKUS].sort((a, b) => (b.returnQty / b.units) - (a.returnQty / a.units)),
    totals: { name: 'TOTAL', units: 2180, returnQty: 70, returnVal: 4457 },
  };

  /* ─ New Customers ──────────────────────────────────────────── */
  if (title === 'New Customers') return {
    summary: [
      { label: 'Total New Customers', value: '287' },
      { label: 'Avg First Order AOV', value: $c(124500 / 287) },
      { label: 'Organic Share', value: '38%' },
      { label: 'CAC (blended)', value: $c(24800 / 287) },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'New Customers', key: 'nc', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{r.newCust}</span> },
      { label: '% of Total', key: 'pct', cls: 'text-right', render: (r) => <PctBar pct={(r.newCust / 287 * 100).toFixed(1)} /> },
      { label: 'First Order AOV', key: 'faov', cls: 'text-right', render: (r) => <span>{$c(r.revenue / r.newCust)}</span> },
      { label: 'CAC', key: 'cac', cls: 'text-right', render: (r) => <span>{$c(r.adSpend / r.newCust)}</span> },
      { label: 'Revenue from New', key: 'rev', cls: 'text-right', render: (r) => <span>{$c(r.revenue * 0.38)}</span> },
    ],
    rows: [...SKUS].sort((a, b) => b.newCust - a.newCust),
    totals: { name: 'TOTAL', newCust: 287 },
  };

  /* ─ ROAS ───────────────────────────────────────────────────── */
  if (['ROAS', 'Margin-Adj ROAS'].includes(title)) return {
    summary: [
      { label: 'Portfolio ROAS', value: '4.2x' },
      { label: 'Total Ad Spend', value: $c(24962) },
      { label: 'Ad Revenue', value: $c(124500) },
      { label: 'Blended ACoS', value: '20.1%' },
    ],
    cols: [
      { label: 'Campaign', key: 'name', cls: 'text-left', minW: 200, render: (r) => <CampaignCell name={r.name} sku={r.sku} type={r.type} /> },
      { label: 'Ad Type', key: 'type', cls: 'text-center', render: (r) => <AdTypeBadge t={r.type} /> },
      { label: 'Ad Spend', key: 'spend', cls: 'text-right', render: (r) => <span>{$c(r.spend)}</span> },
      { label: 'Ad Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span>{$c(r.revenue)}</span> },
      { label: 'ROAS', key: 'roas', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{fX(r.roas)}</span> },
      { label: 'Impressions', key: 'imp', cls: 'text-right', render: (r) => <span>{fN(r.impressions)}</span> },
      { label: 'Conv. Rate', key: 'cvr', cls: 'text-right', render: (r) => <span>{fP(r.convRate)}</span> },
      { label: 'ACoS', key: 'acos', cls: 'text-right', render: (r) => <span className={r.acos > 15 ? 'text-red-500 dark:text-red-400' : 'text-green-600 dark:text-green-400'}>{fP(r.acos)}</span> },
    ],
    rows: [...CAMPAIGNS].sort((a, b) => b.revenue - a.revenue),
    totals: { name: 'TOTAL', spend: 24962, revenue: 124500 },
  };

  /* ─ Total Ad Spend ─────────────────────────────────────────── */
  if (title === 'Total Ad Spend') return {
    summary: [
      { label: 'Total Ad Spend', value: $c(24962) },
      { label: 'Portfolio ROAS', value: '4.2x' },
      { label: 'Total Impressions', value: fN(1562000) },
      { label: 'Avg CPC', value: '$0.38' },
    ],
    cols: [
      { label: 'Campaign', key: 'name', cls: 'text-left', minW: 200, render: (r) => <CampaignCell name={r.name} sku={r.sku} type={r.type} /> },
      { label: 'Ad Type', key: 'type', cls: 'text-center', render: (r) => <AdTypeBadge t={r.type} /> },
      { label: 'Spend', key: 'spend', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{$c(r.spend)}</span> },
      { label: '% of Budget', key: 'pct', cls: 'text-right', render: (r) => <PctBar pct={(r.spend / 24962 * 100).toFixed(1)} /> },
      { label: 'Impressions', key: 'imp', cls: 'text-right', render: (r) => <span>{fN(r.impressions)}</span> },
      { label: 'Clicks', key: 'clk', cls: 'text-right', render: (r) => <span>{fN(r.clicks)}</span> },
      { label: 'CPC', key: 'cpc', cls: 'text-right', render: (r) => <span>{fPr(r.cpc)}</span> },
      { label: 'ROAS', key: 'roas', cls: 'text-right', render: (r) => <span className={r.roas >= 4 ? 'text-green-600 dark:text-green-400 font-medium' : 'text-amber-500'}>{fX(r.roas)}</span> },
    ],
    rows: [...CAMPAIGNS].sort((a, b) => b.spend - a.spend),
    totals: { name: 'TOTAL', spend: 24962, impressions: 1562000, clicks: 33128 },
  };

  /* ─ CTR / CPC / Impressions / Conv. Rate / TACOS ───────────── */
  if (['CTR', 'CPC', 'Impressions', 'Conv. Rate', 'TACOS'].includes(title)) return {
    summary: [
      { label: 'Total Impressions', value: fN(1562000) },
      { label: 'Total Clicks', value: fN(33128) },
      { label: 'Blended CTR', value: '2.1%' },
      { label: 'Avg CPC', value: '$0.38' },
    ],
    cols: [
      { label: 'Campaign', key: 'name', cls: 'text-left', minW: 200, render: (r) => <CampaignCell name={r.name} sku={r.sku} type={r.type} /> },
      { label: 'Ad Type', key: 'type', cls: 'text-center', render: (r) => <AdTypeBadge t={r.type} /> },
      { label: 'Impressions', key: 'imp', cls: 'text-right', render: (r) => <span>{fN(r.impressions)}</span> },
      { label: 'Clicks', key: 'clk', cls: 'text-right', render: (r) => <span>{fN(r.clicks)}</span> },
      { label: 'CTR', key: 'ctr', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{fP(r.ctr)}</span> },
      { label: 'CPC', key: 'cpc', cls: 'text-right', render: (r) => <span>{fPr(r.cpc)}</span> },
      { label: 'Conv. Rate', key: 'cvr', cls: 'text-right', render: (r) => <span>{fP(r.convRate)}</span> },
      { label: 'Orders', key: 'ord', cls: 'text-right', render: (r) => <span>{r.orders}</span> },
    ],
    rows: [...CAMPAIGNS].sort((a, b) => b.impressions - a.impressions),
    totals: { name: 'TOTAL', impressions: 1562000, clicks: 33128, orders: 412 },
  };

  /* ─ Margin KPIs ────────────────────────────────────────────── */
  if (['CM2 Cross-Ch.', 'CM3 Channel', 'Gross Margin %', 'Contribution %', 'Net Profit', 'COGS'].includes(title)) return {
    summary: [
      { label: 'Total Revenue', value: $c(124500) },
      { label: 'Total COGS', value: $c(SKUS.reduce((s, r) => s + r.cogs, 0)) },
      { label: 'Gross Margin', value: $c(SKUS.reduce((s, r) => s + r.grossMargin, 0)) },
      { label: 'Avg GM%', value: fP(SKUS.reduce((s, r) => s + r.grossMargin, 0) / 124500 * 100) },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span>{$c(r.revenue)}</span> },
      { label: 'COGS', key: 'cogs', cls: 'text-right', render: (r) => <span>{$c(r.cogs)}</span> },
      { label: 'Gross Margin', key: 'gm', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{$c(r.grossMargin)}</span> },
      { label: 'GM %', key: 'gmPct', cls: 'text-right', render: (r) => <span className={r.gmPct >= 55 ? 'text-green-600 dark:text-green-400 font-medium' : r.gmPct >= 45 ? 'text-amber-500 font-medium' : 'text-red-500 font-medium'}>{fP(r.gmPct)}</span> },
      { label: 'Ad Spend', key: 'adSpend', cls: 'text-right', render: (r) => <span>{$c(r.adSpend)}</span> },
      { label: 'Contribution', key: 'cm2', cls: 'text-right', render: (r) => <span className="font-medium text-green-700 dark:text-green-400">{$c(r.cm2)}</span> },
    ],
    rows: [...SKUS].sort((a, b) => b.grossMargin - a.grossMargin),
    totals: { name: 'TOTAL', revenue: 124500, cogs: SKUS.reduce((s, r) => s + r.cogs, 0), grossMargin: SKUS.reduce((s, r) => s + r.grossMargin, 0) },
  };

  /* ─ Unprofitable SKUs / Pricing Opps ──────────────────────── */
  if (['Unprofitable SKUs', 'Pricing Opps'].includes(title)) return {
    summary: [
      { label: 'SKUs Analysed', value: '10' },
      { label: 'Unprofitable', value: '1' },
      { label: 'Pricing Opportunities', value: '3' },
      { label: 'Est. Uplift', value: '+$8,400' },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Current Price', key: 'price', cls: 'text-right', render: (r) => <span className="font-medium">{fPr(r.price)}</span> },
      { label: 'Competitor', key: 'comp', cls: 'text-right', render: (r) => <span>{fPr(r.competitorPrice)}</span> },
      { label: 'Price Gap', key: 'gap', cls: 'text-right', render: (r) => { const g = r.price - r.competitorPrice; return <span className={g > 2 ? 'text-red-500 dark:text-red-400 font-medium' : g < -2 ? 'text-green-600 dark:text-green-400 font-medium' : 'text-gray-500'}>{g > 0 ? '+' : ''}{fPr(g)}</span>; } },
      { label: 'GM %', key: 'gmPct', cls: 'text-right', render: (r) => <span className={r.gmPct >= 50 ? 'text-green-600 dark:text-green-400' : 'text-red-500 dark:text-red-400'}>{fP(r.gmPct)}</span> },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span>{$c(r.revenue)}</span> },
    ],
    rows: [...SKUS].sort((a, b) => a.gmPct - b.gmPct),
    totals: null,
  };

  /* ─ Inventory KPIs ─────────────────────────────────────────── */
  if (['Inventory at Cost', 'DOC (Avg)', 'OOS Risk SKUs', 'Overstock Value', 'In-Stock %', 'Inventory Turns', 'Reorder Alerts', 'Inbound POs'].includes(title)) return {
    summary: [
      { label: 'Total SKUs', value: '10' },
      { label: 'Total Inv. Value', value: $c(SKUS.reduce((s, r) => s + r.stock * r.price * 0.43, 0)) },
      { label: 'Avg DOC', value: '8.2 days' },
      { label: 'At Risk SKUs', value: '2' },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Units in Stock', key: 'stock', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{fN(r.stock)}</span> },
      { label: 'Cost / Unit', key: 'costPer', cls: 'text-right', render: (r) => <span>{fPr(r.price * 0.43)}</span> },
      { label: 'Total Inv. Value', key: 'invVal', cls: 'text-right', render: (r) => <span>{$c(r.stock * r.price * 0.43)}</span> },
      { label: 'Daily Sales', key: 'ds', cls: 'text-right', render: (r) => <span>{r.dailySales.toFixed(1)}/day</span> },
      { label: 'DOC', key: 'doc', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{r.doc.toFixed(1)} days</span> },
      { label: 'Status', key: 'docStatus', cls: 'text-center', render: (r) => <DOCStatus s={r.docStatus} /> },
    ],
    rows: [...SKUS].sort((a, b) => a.doc - b.doc),
    totals: null,
  };

  /* ─ Cash: inflow/outflow/balance/net/payout/burn/ar/projection */
  if (['Cash Balance', 'Cash Inflow', 'Net Cash Flow', '30-Day Projection'].includes(title)) return {
    summary: [
      { label: 'Total Settled', value: $c(SETTLEMENTS.filter(s => s.status === 'Settled').reduce((a, s) => a + s.net, 0)) },
      { label: 'Processing', value: $c(SETTLEMENTS.filter(s => s.status === 'Processing').reduce((a, s) => a + s.net, 0)) },
      { label: 'Total Fees', value: $c(SETTLEMENTS.reduce((a, s) => a + s.fees, 0)) },
      { label: 'Total Refunds', value: $c(SETTLEMENTS.reduce((a, s) => a + s.refunds, 0)) },
    ],
    cols: [
      { label: 'Platform', key: 'platform', cls: 'text-left', minW: 120, render: (r) => <ChannelBadge ch={r.platform} /> },
      { label: 'Period', key: 'period', cls: 'text-left', render: (r) => <span className="text-xs text-gray-500 dark:text-slate-400">{r.period}</span> },
      { label: 'Gross Sales', key: 'gs', cls: 'text-right', render: (r) => <span className="font-medium">{$c(r.grossSales)}</span> },
      { label: 'Platform Fees', key: 'fees', cls: 'text-right', render: (r) => <span className="text-red-500 dark:text-red-400">{$c(r.fees)}</span> },
      { label: 'Ad Fees', key: 'adFees', cls: 'text-right', render: (r) => <span className="text-red-500 dark:text-red-400">{$c(r.adFees)}</span> },
      { label: 'Refunds', key: 'refunds', cls: 'text-right', render: (r) => <span className="text-red-400 dark:text-red-300">{$c(r.refunds)}</span> },
      { label: 'Net Payout', key: 'net', cls: 'text-right', render: (r) => <span className="font-semibold text-green-600 dark:text-green-400">{$c(r.net)}</span> },
      { label: 'Status', key: 'status', cls: 'text-center', render: (r) => <SettlementStatus s={r.status} date={r.date} /> },
    ],
    rows: SETTLEMENTS,
    totals: {
      name: 'TOTAL',
      grossSales: SETTLEMENTS.reduce((a, s) => a + s.grossSales, 0),
      fees: SETTLEMENTS.reduce((a, s) => a + s.fees, 0),
      adFees: SETTLEMENTS.reduce((a, s) => a + s.adFees, 0),
      refunds: SETTLEMENTS.reduce((a, s) => a + s.refunds, 0),
      net: SETTLEMENTS.reduce((a, s) => a + s.net, 0),
    },
  };

  if (['Cash Outflow', 'Burn Rate/Day', 'AR Outstanding', 'Payouts Pending'].includes(title)) return {
    summary: [
      { label: 'Total Outflow', value: $c(OUTFLOWS.reduce((a, r) => a + r.amount, 0)) },
      { label: 'Largest Item', value: 'Inv. Restock' },
      { label: 'Avg Daily Burn', value: $c(Math.round(OUTFLOWS.reduce((a, r) => a + r.amount, 0) / 7)) },
      { label: 'vs Prior Period', value: '+6.8%' },
    ],
    cols: [
      { label: 'Category', key: 'cat', cls: 'text-left', minW: 140, render: (r) => <CatBadge cat={r.category} /> },
      { label: 'Description', key: 'desc', cls: 'text-left', minW: 200, render: (r) => <span className="text-xs text-gray-600 dark:text-slate-400">{r.description}</span> },
      { label: 'Amount', key: 'amt', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{$c(r.amount)}</span> },
      { label: '% of Outflow', key: 'pct', cls: 'text-right', render: (r) => <PctBar pct={(r.amount / OUTFLOWS.reduce((a, x) => a + x.amount, 0) * 100).toFixed(1)} /> },
      { label: 'Date', key: 'date', cls: 'text-center', render: (r) => <span className="text-xs text-gray-400 dark:text-slate-500">{r.date}</span> },
      { label: 'Status', key: 'status', cls: 'text-center', render: (r) => <PaidBadge s={r.status} /> },
    ],
    rows: [...OUTFLOWS].sort((a, b) => b.amount - a.amount),
    totals: { name: 'TOTAL', amount: OUTFLOWS.reduce((a, r) => a + r.amount, 0) },
  };

  /* ─ Default fallback (Total Revenue layout) ───────────────── */
  return {
    summary: [
      { label: 'Total SKUs', value: '10' },
      { label: 'Avg Rev / SKU', value: $c(124500 / 10) },
      { label: 'Total Returns', value: $c(4457) },
      { label: 'Net Settled', value: $c(124500 - 4457) },
    ],
    cols: [
      { label: 'Product', key: 'name', cls: 'text-left', minW: 180, render: (r) => <ProductCell name={r.name} sku={r.sku} cat={r.cat} /> },
      { label: 'Channel', key: 'ch', cls: 'text-left', render: (r) => <ChannelBadge ch={r.channel} /> },
      { label: 'Units Sold', key: 'units', cls: 'text-right', render: (r) => <span className="font-medium">{fN(r.units)}</span> },
      { label: 'Revenue', key: 'revenue', cls: 'text-right', render: (r) => <span className="font-semibold text-gray-900 dark:text-slate-100">{$c(r.revenue)}</span> },
      { label: 'Returns', key: 'retQty', cls: 'text-right', render: (r) => <ReturnQtyCell qty={r.returnQty} units={r.units} /> },
      { label: 'Net Settled', key: 'settled', cls: 'text-right', render: (r) => <span className="font-semibold text-green-600 dark:text-green-400">{$c(r.netSettled)}</span> },
    ],
    rows: SKUS,
    totals: { name: 'TOTAL', units: 2180, revenue: 124500, returnQty: 70, netSettled: 120043 },
  };
};

/* ── Mini sub-components ───────────────────────────────────────── */
