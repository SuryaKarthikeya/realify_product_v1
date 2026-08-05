import { identityClient } from '@/services/httpClient';
import { API_PATHS } from '@/services/endpoints';

/**
* The tenant's real data coverage — GET /api/data/completeness.
*
* Every number here is counted from the reports the account has actually
* uploaded (SellerRepository.count_non_null per canonical field), so the
* completeness panel can only ever show what this account really has. Nothing
* on this surface may be hardcoded: a stale SKU count reads as a live one.
*
* Shape: { ok, fields: [{ field, label, report, provided, skus }],
*          active, total, skus }
* where `active` is how many of `total` detector groups are lit, `skus` is the
* catalogue size, and `report` names the upload that would fill a dark field.
*/
export const getDataCompleteness = async () => {
 const { data } = await identityClient.get(API_PATHS.DATA.COMPLETENESS);
 return data;
};

/**
* The catalogue with its coverage summary — GET /api/skus.
*
* `summary` is { skus, avg_completeness, missing_cogs, fee_pairs, provisional }
* — the counts the Product Catalog header reports. `avg_completeness` is out of
* 7 tracked fields (cogs, price, referral_fee, fba_fee, units_month,
* returns_rate, buybox_pct).
*/
export const getSkus = async () => {
 const { data } = await identityClient.get(API_PATHS.DATA.SKUS);
 return data;
};

