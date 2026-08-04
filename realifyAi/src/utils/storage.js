/**
 * The only place that touches localStorage.
 *
 * Keys are string literals in exactly one file, so a rename is a one-line
 * change and nothing can typo a key silently. Values and defaults match the
 * behaviour of the call sites these accessors replaced.
 */
const KEYS = {
  activeShop:     'active_shop',
  activePlatform: 'active_platform',
  shopifyShop:    'shopify_shop',
  shopifyStatus:  'shopify_status',
  theme:          'theme',
  userRole:       'userRole',
  userName:       'user_name',
  graduatedAgents:'graduated_agents',
  setupComplete:  'integration_setup_complete',
};

export const DEFAULT_PLATFORM = 'shopify';

export const storage = {
  getActiveShop:     () => localStorage.getItem(KEYS.activeShop),
  setActiveShop:     (v) => localStorage.setItem(KEYS.activeShop, v),

  /** Callers have always treated a missing platform as Shopify. */
  getActivePlatform: () => localStorage.getItem(KEYS.activePlatform) || DEFAULT_PLATFORM,
  setActivePlatform: (v) => localStorage.setItem(KEYS.activePlatform, v),

  getShopifyShop:    () => localStorage.getItem(KEYS.shopifyShop),
  setShopifyShop:    (v) => localStorage.setItem(KEYS.shopifyShop, v),
  setShopifyStatus:  (v) => localStorage.setItem(KEYS.shopifyStatus, v),

  getTheme:          () => localStorage.getItem(KEYS.theme),
  setTheme:          (v) => localStorage.setItem(KEYS.theme, v),

  getUserRole:       () => localStorage.getItem(KEYS.userRole),
  setUserRole:       (v) => localStorage.setItem(KEYS.userRole, v),
  clearUserRole:     () => localStorage.removeItem(KEYS.userRole),

  /** Captured during onboarding step 1; greets the user on later screens. */
  getUserName:       () => localStorage.getItem(KEYS.userName),
  setUserName:       (v) => localStorage.setItem(KEYS.userName, v),

  /**
   * Agent ids the user has graduated out of Shadow. Drives the Agents page's
   * Active count and its Live Now strip, so a first-time visitor sees neither.
   * Parsed defensively: a corrupt value must not break the page.
   */
  getGraduatedAgents: () => {
    try {
      const raw = JSON.parse(localStorage.getItem(KEYS.graduatedAgents) || '[]');
      return Array.isArray(raw) ? raw.filter((v) => typeof v === 'string') : [];
    } catch {
      return [];
    }
  },
  setGraduatedAgents: (ids) =>
    localStorage.setItem(KEYS.graduatedAgents, JSON.stringify(ids)),

  /**
   * Connector ids whose onboarding the user has walked to Go live.
   *
   * Read by three surfaces that must agree — the catalogue's primary button, the
   * detail header's Connect button and the onboarding journey rail — so it lives
   * here rather than being re-derived from the wizard step, which is forgotten the
   * moment the user navigates away. Parsed defensively like the agents list: a
   * corrupt value must not break the Integrations page.
   */
  getCompletedSetups: () => {
    try {
      const raw = JSON.parse(localStorage.getItem(KEYS.setupComplete) || '[]');
      return Array.isArray(raw) ? raw.filter((v) => typeof v === 'string') : [];
    } catch {
      return [];
    }
  },
  setCompletedSetups: (ids) =>
    localStorage.setItem(KEYS.setupComplete, JSON.stringify(ids)),
};
