/** Shared sidebar timing helpers and route groupings.
 *  `t()` builds the CSS transition shorthand every animated element here uses. */

export const EASE = 'cubic-bezier(0.4, 0, 0.2, 1)';
export const DUR = '200ms';
export const t = (props) => props.map(p => `${p} ${DUR} ${EASE}`).join(', ');

