import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants/routes';

const PrivacyPolicy = () => {
  return (
    <div className="bg-white min-h-screen">

      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-50 via-slate-50 to-white pt-14 pb-6 border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <h1 className="text-2xl font-bold text-gray-700 mb-5">Realify Privacy Policy</h1>
          <div className="grid sm:grid-cols-2 gap-x-10 gap-y-1 text-sm text-gray-600">
            <div><span className="font-semibold text-gray-800">Controller:</span> Realify ai Inc (Delaware, File No. 10409872)</div>
            <div><span className="font-semibold text-gray-800">Contact:</span>{' '}
              <a href="mailto:legal@realify.ai" className="text-blue-600 hover:underline">legal@realify.ai</a>
            </div>
            <div><span className="font-semibold text-gray-800">Principal Address:</span> 28 Geary St STE 650 494, San Francisco, CA 94108, USA</div>
            <div><span className="font-semibold text-gray-800">Effective Date:</span> June 1<sup>st</sup>, 2026</div>
            <div className="sm:col-span-2"><span className="font-semibold text-gray-800">Development Center (affiliate):</span> Realify AI India Private Limited, Plot No. 629, Sector 82, Sahibzada Ajit Singh Nagar (Mohali), Punjab 140306, India</div>
          </div>
        </div>
      </section>

      {/* Main content */}
      <main className="flex-grow py-8 px-4">
        <div className="max-w-4xl mx-auto policy-content">

          {/* Table of Contents */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-gray-500 mb-4">Contents</p>
            <ol className="grid sm:grid-cols-2 gap-x-8 gap-y-1 list-none pl-0 m-0">
              {[
                ['#pp-s1','01','Who We Are'],
                ['#pp-s2','02','Information We Collect'],
                ['#pp-s3','03','How We Use Information'],
                ['#pp-s4','04','How We Share Information'],
                ['#pp-s5','05','Platform Integration Data'],
                ['#pp-s6','06','Sub-Processors'],
                ['#pp-s7','07','Data Security'],
                ['#pp-s8','08','Geographic Scope'],
                ['#pp-s9','09','Data Retention'],
                ['#pp-s10','10','AI and Machine Learning'],
                ['#pp-s11','11','California Privacy Rights'],
                ['#pp-s12','12','International Transfers'],
                ['#pp-s13','13','Changes to This Policy'],
              ].map(([href, num, title]) => (
                <li key={num} className="m-0 p-0">
                  <a href={href} className="flex items-baseline gap-2.5 py-1 text-sm text-gray-600 hover:text-blue-600 no-underline transition-colors">
                    <span className="font-sans text-xs text-gray-400 flex-shrink-0 w-5">{num}</span>
                    {title}
                  </a>
                </li>
              ))}
            </ol>
          </div>

          {/* § 01 Who We Are */}
          <section id="pp-s1" className="scroll-mt-20 mb-6">
            <h2>§ 01 — Who We Are</h2>
            <p>
              Realify.ai ("Realify," "we," "us," "our") is operated by Realify ai Inc, a Delaware corporation (File No. 10409872)
              with its principal place of business at 28 Geary St STE 650 494, San Francisco, CA 94108. Engineering and product
              development are performed by our affiliate, Realify AI India Private Limited (Mohali, Punjab, India), which acts only
              under our instruction and is bound by the data-protection terms in this Policy. Realify ai Inc is the controller and
              the contracting party for all platform integrations, including the Amazon Selling Partner API. This Policy is effective
              June 1st, 2026 and is incorporated into the Terms of Service. Inquiries:{' '}
              <a href="mailto:legal@realify.ai">legal@realify.ai</a>.
            </p>
          </section>

          {/* § 02 Information We Collect */}
          <section id="pp-s2" className="scroll-mt-20 mb-6">
            <h2>§ 02 — Information We Collect</h2>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3"><strong className="text-gray-800 block mb-1">Account data</strong>Name, business email, phone, company, job title, hashed password.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Billing data</strong>Billing address and payment method; full card numbers are held by our PCI-DSS processor, Stripe. Realify does not store full card numbers.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Connected Platform data</strong>Operational data accessed through each platform's API on your behalf — detailed in Section 5.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Technical data</strong>IP addresses, browser type, device identifiers, page views, feature interactions, and error logs.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Marketing website data</strong>When you visit realify.ai, cookies, pixels, and similar technologies from Google Ads, Google Analytics 4, and Meta Ads collect data to measure marketing performance and build remarketing audiences. Our cookie consent banner allows you to accept, reject, or customize these technologies. We implement Google Consent Mode v2 to respect your consent choices before sending data to Google. See Sections 5 and 11 for your rights.</li>
            </ul>
          </section>

          {/* § 03 How We Use Information */}
          <section id="pp-s3" className="scroll-mt-20 mb-6">
            <h2>§ 03 — How We Use Information</h2>
            <p>
              We use information solely to: (a) provide, maintain, and improve the Services; (b) generate AI-driven recommendations
              and analytics; (c) send transactional and support communications; (d) run, measure, and optimize advertising campaigns
              on Google Ads and Meta Ads on our marketing website; (e) monitor for abuse and security threats; (f) fulfill billing and
              legal obligations. We do not sell Customer Data or use Customer Data for our own marketing.
            </p>
          </section>

          {/* § 04 How We Share Information */}
          <section id="pp-s4" className="scroll-mt-20 mb-6">
            <h2>§ 04 — How We Share Information</h2>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3"><strong className="text-gray-800 block mb-1">Sub-processors</strong>As listed in Section 6, under data protection agreements.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Advertising (marketing site only)</strong>We share marketing-website visitor data with Google and Meta for advertising, analytics, and conversion measurement, as described in Section 11.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Legal process</strong>To comply with valid legal process or protect our legal rights, with notice to you where permitted.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Business transfers</strong>In a merger or asset sale, subject to equivalent data protection obligations.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">With consent</strong>For any other purpose with your prior consent.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Aggregated data</strong>De-identified data that does not identify you. Amazon Information is excluded from all aggregation.</li>
            </ul>
          </section>

          {/* § 05 Platform Integration Data */}
          <section id="pp-s5" className="scroll-mt-20 mb-6">
            <h2>§ 05 — Platform Integration Data</h2>
            <p>
              This section governs all data accessed through Connected Platform APIs. Each platform's requirements are stated once
              and apply in full. In any conflict with another provision of this Policy, the applicable platform subsection controls.
            </p>

            {/* 5.1 Amazon SP-API */}
            <h3>5.1 Amazon Selling Partner API</h3>
            <div className="info-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Amazon DPP Compliance</p>
              This subsection satisfies the Amazon Data Protection Policy (DPP), Acceptable Use Policy (AUP), and SP-API Developer
              Agreement. In any conflict with another provision of this Policy, this subsection controls.
            </div>

            <h4>Data Accessed</h4>
            <p>
              Catalog and listing data; order and shipment information (buyer PII limited to what is strictly necessary for authorized
              fulfillment); inventory positions; pricing and promotion data; advertising performance metrics; financial settlement data.
            </p>

            <h4>Authorized Use and Absolute Prohibitions</h4>
            <p>
              Amazon Information is used solely to provide the Services to you, the authorizing seller. We do not sell, rent, lease,
              or license Amazon Information to any third party. Absolute prohibitions:
            </p>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">(a) No aggregation or benchmarking of Amazon Information across seller accounts in any form (DPP §4.4)</li>
              <li className="py-3">(b) No use of Amazon Information to train, fine-tune, evaluate, or benchmark AI/ML models in any form — identifiable, de-identified, or aggregated (DPP §4.3)</li>
              <li className="py-3">(c) No generation or disclosure of insights about Amazon's business, strategy, or marketplace economics for any commercial purpose (AUP §4.5)</li>
            </ul>

            <h4>Retention</h4>
            <table>
              <thead>
                <tr><th>Data Category</th><th>Hard Limit</th><th>Authority</th></tr>
              </thead>
              <tbody>
                <tr><td>Buyer PII</td><td>30 days from collection</td><td>Amazon DPP §3.3</td></tr>
                <tr><td>Operational non-PII (live systems)</td><td>30 days from collection</td><td>Amazon DPP §3.3</td></tr>
                <tr><td>Non-PII archive</td><td>18 months from collection</td><td>Amazon DPP §3.3 extended provision</td></tr>
                <tr><td>SP-API credentials</td><td>Active until revoked; purged within 48 hours of revocation</td><td>SP-API Developer Agreement</td></tr>
              </tbody>
            </table>
            <p>
              All retention periods are hard limits from the date of collection. Sole exception: legal obligations only (order
              fulfillment, tax, legally required documents) consistent with Amazon DPP §§1.5 and 2.1.
            </p>

            <h4>Deletion</h4>
            <p>
              Request deletion by emailing{' '}
              <a href="mailto:legal@realify.ai">legal@realify.ai</a>{' '}
              (subject: "Amazon Data Deletion Request") or revoking access in Seller Central. We acknowledge within 24 hours, delete
              from live systems within 7 business days, purge backups within 30 days, and issue a written deletion certificate within
              35 days. Deletion follows NIST SP 800-88 Rev. 1.
            </p>

            <h4>Data Attribution (DPP §1.8)</h4>
            <p>
              Amazon Information is stored in a dedicated, logically separate data store. Every record is tagged at ingestion with
              the seller account ID and a data origin marker, enabling record-level retention enforcement and scope reports on request.
            </p>

            <h4>Security</h4>
            <p>
              All Amazon Information is stored and processed exclusively within AWS infrastructure in the United States (us-east-1
              and us-west-2 regions). Personnel from Realify's technical affiliate, Realify AI India Private Limited, may be granted
              time-bound, monitored remote access to U.S. production infrastructure solely for critical system engineering, debugging,
              and operational maintenance. All such access is governed by role-based access control (RBAC) on a least-privilege basis,
              and by the following mandatory controls:
            </p>
            <div className="warning-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Data Minimization and Masking</p>
              Engineers are strictly prohibited from accessing, viewing, or interacting with customer Personally Identifiable
              Information (PII) or Amazon Restricted Data. Any data exposed during system troubleshooting is programmatically masked
              or anonymized before it is visible to any personnel.
            </div>
            <div className="warning-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Secure VDI Enclaves</p>
              Access is restricted to designated Approved Users operating through Multi-Factor Authentication (MFA) via secure Virtual
              Desktop Infrastructure (VDI). Data Loss Prevention (DLP) protocols are enforced, preventing local data caching, copying,
              or external transfer of any system data.
            </div>
            <div className="warning-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Immutable Audit Logging</p>
              Every remote session, access request, and system alteration is captured in tamper-proof security logs, retained for a
              minimum of 90 days, and audited quarterly for compliance.
            </div>

            <h4>Organizational Changes and Violations (AUP §§1.3, 3.11)</h4>
            <p>
              Realify notifies Amazon SP-API Solution Provider Support within 30 days of any organizational change affecting how
              Amazon Information is processed. Realify discloses to Amazon any affiliated entities with access to Amazon Information.
              Where Realify reasonably suspects a customer is violating their Amazon agreements, Realify notifies Amazon at{' '}
              <a href="mailto:spapi-abuse@amazon.com">spapi-abuse@amazon.com</a>{' '}
              and may suspend that customer's access (AUP §1.3).
            </p>

            {/* 5.2 Google Ads API */}
            <h3>5.2 Google Ads API</h3>
            <p>
              Realify.ai's use and transfer to any other app of information received from Google APIs will adhere to the Google API
              Services User Data Policy, including the Limited Use requirements.
            </p>
            <div className="info-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Google Compliance</p>
              This subsection satisfies Google's Advertising Policies and Google Ads API Terms of Service. In any conflict with
              another provision of this Policy, this subsection controls with respect to Google Ads API data.
            </div>

            <h4>Data Accessed</h4>
            <p>
              Campaign structures and settings; keyword and bid data; budget and pacing data; impression, click, cost, and conversion
              metrics; audience definitions (within your accounts only); account configuration, billing settings, and user permissions.
            </p>

            <h4>Authorized Use and Required Disclosures</h4>
            <p>
              Google Ads API data is used solely to manage and report on your authorized Google Ads accounts. By enabling this
              integration, you acknowledge that Realify uses the Google Ads API and that use is subject to Google's Advertising
              Policies at{' '}
              <a href="https://policies.google.com" target="_blank" rel="noopener noreferrer">https://policies.google.com</a>.
              Realify provides Full Service (campaign creation, bid management, budget control, reporting, recommendations) or
              Reporting-only access, as disclosed at setup. Realify maintains compliance with Google's Required Minimum Functionality
              (RMF) standards for the service tier activated. You are responsible for all advertising content, targeting decisions,
              and policy compliance within your Google Ads accounts.
            </p>

            <h4>Prohibited Uses</h4>
            <p>
              We do not, and will not: (a) scrape targeting parameters, bid status, Traffic Estimator, or Bidstream data for any
              purpose other than managing your authorized accounts; (b) purchase scraped Google Ads data from any third party;
              (c) sync Google Ads campaign data to any platform competing with Google Ads or other Google advertising products. For
              the avoidance of doubt, when Realify's Conductor orchestrates multi-platform omnichannel strategies, Realify separates
              Google Ads attribution and reporting metrics from Google's proprietary bidding parameters, targeting signals, and
              keyword-level data. Attribution and performance metrics may be incorporated into cross-platform reporting dashboards;
              Google's proprietary bidding and targeting parameters are never exported to, replicated in, or used to inform
              configurations on any competing advertising platform; (d) circumvent Google's advertising policies, spending limits,
              billing systems, or quality controls; (e) allow fully automated Google Ads operation without human-configured guardrails
              (Terms Section 4.2); (f) label live advertiser accounts as demo or test accounts; (g) manage third-party Google Ads
              accounts without their knowledge, consent, and required Google disclosures; (h) use Google Ads API data to train,
              fine-tune, evaluate, or benchmark any AI or machine-learning model.
            </p>

            <h4>Token Security and 90-Day Deletion</h4>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3"><strong className="text-gray-800 block mb-1">Encryption</strong>Google Ads API credentials, including OAuth refresh tokens and developer tokens, are AES-256 encrypted at rest and TLS 1.2+ in transit, stored in an encrypted secrets vault on a least-privilege basis.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">90-day inactivity deletion</strong>Google Ads API developer tokens not used commercially for 90 consecutive days are automatically deleted, per Google Ads API Terms of Service.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Revocation</strong>All Google Ads credentials are purged within 48 hours of account closure, integration revocation, or Google's revocation of Realify's API access.</li>
            </ul>

            <h4>Retention and Deletion</h4>
            <p>
              Google Ads API data is retained for the duration of the active integration. Upon revocation or account closure: deleted
              from live systems within 30 days; purged from backups within 90 days. Written deletion confirmation provided on request.
            </p>

            {/* 5.3 Meta Marketing API */}
            <h3>5.3 Meta Marketing API</h3>
            <div className="info-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Meta Developer Policy Compliance</p>
              This subsection satisfies Meta's Developer Policies, Platform Terms, and Advertising Policies. In any conflict with
              another provision of this Policy, this subsection controls with respect to Meta Ads API data.
            </div>

            <h4>Data Accessed</h4>
            <p>
              Ad account settings and billing configuration; campaign, ad set, and ad data; impression, click, reach, frequency,
              and spend metrics; conversion and attribution data; audience size information (aggregate, within your accounts only);
              creative performance data.
            </p>

            <h4>Authorized Use</h4>
            <p>
              Meta Ads API data is used solely to manage and report on your authorized Meta advertising accounts. We do not use
              Meta Ads API data to provide services to any party other than the authorizing advertiser. Realify will not take any
              action on your Meta accounts that violates Meta's Advertising Policies or Community Standards.
            </p>
            <p>
              API access level and App Review: Realify has completed Meta's required App Review for all API permission scopes used
              in the Services, including Advanced Access permissions (such as ads_management and ads_read) where applicable.
              Advanced Access use is limited strictly to the approved purposes stated in Realify's App Review submission.
            </p>
            <p>
              Meta Business Tools Terms: Where Realify uses the Meta Pixel or Meta Conversions API on the realify.ai marketing
              website (separate from the authenticated platform), that use is governed by Meta's Business Tools Terms in addition
              to the Developer Policies described in this section. The two frameworks are distinct: the Developer Policies govern
              the Marketing API integration used to manage your ad accounts; the Business Tools Terms govern Realify's own
              marketing-website pixel deployment. Both are complied with separately.
            </p>

            <h4>Prohibited Uses</h4>
            <p>
              We do not, and will not: (a) sell, rent, license, or transfer Meta Ads API data to any third party; (b) build Custom
              Audiences or Lookalike Audiences for any party other than you as the authorizing advertiser, and only within your own
              accounts; (c) combine Meta Ads data with other sources to profile Meta users without valid lawful basis and consent;
              (d) scrape auction pricing, bid landscape, or targeting parameters; (e) facilitate content violating Meta's Community
              Standards; (f) reverse engineer Meta's products, APIs, algorithms, or ranking systems; (g) interfere with Meta's
              platforms or advertising systems; (h) use Meta Ads API data to train, fine-tune, evaluate, or benchmark any AI or
              machine-learning model; (i) contact Meta users identified through the API outside the authorized advertising workflow;
              (j) retain Meta user-level data beyond what is required or ignore a Meta-originated deletion request.
            </p>

            <h4>Token Security</h4>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3"><strong className="text-gray-800 block mb-1">Encryption</strong>Meta API tokens are AES-256 encrypted at rest and TLS 1.2+ in transit, stored in an encrypted secrets vault on a least-privilege basis.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Permission scopes</strong>Realify requests only the minimum Meta API permission scopes required for the features you enable and maintains current Meta App Review approvals for all permissions used.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Revocation</strong>All Meta API tokens are purged within 48 hours of account closure, integration revocation, or Meta's revocation of Realify's app access.</li>
            </ul>

            <h4>Retention and Deletion</h4>
            <p>
              Meta Ads API data is retained for the duration of the active integration. Upon revocation or account closure: deleted
              from live systems within 30 days; Meta user-level data purged immediately upon a Meta-originated deletion request;
              backups purged within 90 days. Written deletion confirmation on request.
            </p>

            {/* 5.4 Amazon Advertising API */}
            <h3>5.4 Amazon Advertising API</h3>
            <div className="info-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Amazon Advertising API Compliance</p>
              This subsection governs Realify's use of the Amazon Advertising API (including Sponsored Products, Sponsored Brands,
              Sponsored Display, DSP, and Amazon Attribution) and satisfies the Amazon Advertising API License Agreement ("Advertising
              License Agreement"). This subsection is separate from and in addition to Section 5.1 (Amazon SP-API). In any conflict
              with another provision of this Policy, this subsection controls with respect to Amazon Advertising API data.
            </div>

            <h4>Data Accessed</h4>
            <p>
              Campaign structures and settings for Sponsored Products, Sponsored Brands, Sponsored Display, and DSP; advertising
              performance metrics (impressions, clicks, spend, attributed sales, ROAS, ACOS); audience and targeting data within
              your authorized accounts; budget and bid data; Amazon Attribution measurement data. All such data constitutes "Program
              Materials" under the Advertising License Agreement.
            </p>

            <h4>Authorized Use — Licensed Country Restriction</h4>
            <p>
              Amazon Advertising API access is authorized only for the "Licensed Countries" designated in your Advertising License
              Agreement. Realify uses Amazon Advertising API data solely to provide the authorized advertising management and
              optimization services to you, the Amazon Advertising Participant, through the infrastructure and functionality we
              designate. Use of the API is authorized only as permitted by the Advertising License Agreement, the Amazon Program
              Policies, the Amazon Data Protection Policy, and any other applicable Amazon program policies.
            </p>

            <h4>Absolute Prohibitions</h4>
            <p>With respect to Amazon Advertising API data, Realify does not, and will not:</p>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">(a) Use Amazon Advertising data to identify, target, or benchmark individual sellers or competitors, or combine Advertising API data with SP-API data or other Amazon data services for cross-seller competitive intelligence, without Amazon's prior written permission</li>
              <li className="py-3">(b) Sublicense, sell, resell, transfer, assign, or make available the Amazon Advertising API or Program Materials to any third party</li>
              <li className="py-3">(c) Use Amazon Advertising data for any purpose other than authorized advertising transactions on behalf of the authorizing Amazon Advertising Participant</li>
              <li className="py-3">(d) Issue any press release, make any public statement, or publish any blog, case study, or marketing material that references Amazon Advertising data or the Amazon Advertising API without Amazon's prior written consent</li>
              <li className="py-3">(e) Combine Amazon Advertising API data with data from any other Amazon data service unless Amazon separately grants permission in writing</li>
              <li className="py-3">(f) Use Amazon Advertising data to train, fine-tune, evaluate, or benchmark any AI or machine-learning model — absolute prohibition in all forms</li>
            </ul>

            <h4>Confidentiality of Amazon Advertising Data</h4>
            <p>
              All Amazon Advertising API data is treated as strictly confidential under the Advertising License Agreement. Realify
              maintains Amazon Advertising data with the same confidentiality standards as Amazon Information under Section 5.1,
              including AES-256 encryption at rest, TLS 1.2+ in transit, RBAC, mandatory MFA, and comprehensive audit logging.
              Amazon Advertising data is stored exclusively in U.S.-based AWS infrastructure and is never transmitted outside the
              United States.
            </p>

            <h4>Credential Security and Deletion</h4>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3"><strong className="text-gray-800 block mb-1">Credentials</strong>Amazon Advertising API credentials (OAuth tokens, access keys) are AES-256 encrypted at rest and TLS 1.2+ in transit, stored in an encrypted secrets vault with least-privilege access controls.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">Revocation and deletion</strong>Upon account closure or integration revocation, all Amazon Advertising API credentials are purged within 48 hours and all associated data deleted from live systems within 30 days and from backups within 90 days. Written deletion confirmation provided on request.</li>
            </ul>

            <h4>No Agency Relationship and Upstream Liability Cap</h4>
            <p>
              Nothing in Realify's use of the Amazon Advertising API creates a partnership, joint venture, or agency relationship
              between Realify and Amazon. Realify has no authority to make or accept any offers, representations, or agreements on
              Amazon's behalf.
            </p>
            <div className="warning-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Important</p>
              The Amazon Advertising API License Agreement caps Amazon's total liability to Realify at $100 USD, regardless of the
              nature or amount of any claim. This means that if an Amazon Advertising API failure, outage, or data error causes
              losses to your campaigns, Realify's maximum recovery from Amazon is $100. Realify's own liability to you for
              Advertising API-related issues is separately governed by the limitation of liability in Terms of Service Section 9.
            </div>

            <h4>Governing Law — Amazon Advertising API</h4>
            <p>
              Disputes specifically relating to the Amazon Advertising API License Agreement are governed by the laws of the State
              of Washington, without conflict-of-law principles, with exclusive jurisdiction in the Federal District Court for the
              Western District of Washington at Seattle, or if federal jurisdiction does not exist, in King County Superior Court,
              Seattle, Washington.
            </p>

            {/* 5.5 Shopify API */}
            <h3>5.5 Shopify API</h3>
            <div className="info-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Shopify API Compliance</p>
              This subsection governs Realify's use of the Shopify API and satisfies Shopify's Partner Program Agreement, API Terms,
              and Privacy Policy. In any conflict with another provision of this Policy, this subsection controls with respect to
              Shopify API data.
            </div>

            <h4>Data Accessed</h4>
            <p>
              Store configuration and settings; product catalog, inventory, and pricing data; order and fulfillment data; customer
              records (name, email, shipping address, order history) to the extent required for the activated features; advertising
              and analytics integrations linked to the Merchant's Shopify store.
            </p>

            <h4>Authorized Use</h4>
            <p>
              Shopify API data is used solely to operate the Realify features you, as the Merchant, have activated for your Shopify
              store. Realify does not use Shopify API data to provide services to any party other than the authorizing Merchant.
              Realify complies with Shopify's Partner Program Agreement and all applicable Shopify policies in connection with this
              integration.
            </p>

            <h4>Merchant and Customer Data — Privacy Obligations</h4>
            <p>
              Personal information obtained from Merchants or their customers through the Shopify API ("Shopify Personal
              Information") is used solely for the functionality of the Realify application as authorized by the Merchant.
              Realify does not:
            </p>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">(a) Use Shopify Personal Information for any purpose beyond operating the activated Realify features</li>
              <li className="py-3">(b) Disclose Shopify Personal Information to any third party except sub-processors bound by equivalent data protection obligations</li>
              <li className="py-3">(c) Use Merchant data for competitive benchmarking against other Merchants or disclose such data in a manner that could identify an individual Merchant to a competitor</li>
              <li className="py-3">(d) Combine Shopify Personal Information with data from other sources to build profiles of Merchants or their customers beyond what is necessary for the activated features</li>
            </ul>
            <p>
              Merchants are responsible for ensuring they have provided adequate privacy notices to their customers describing the
              data collected and used through the Realify application, as required by Shopify's Partner Program Agreement.
            </p>

            <h4>No Competing Use</h4>
            <p>
              Realify does not use the Shopify API to build, offer, or improve any product or service that competes with Shopify's
              Platform Services or any of Shopify's core commerce capabilities.
            </p>

            <h4>Security</h4>
            <p>
              Realify maintains industry-standard security controls for all Shopify API data, consistent with the standards
              described in Section 7 of this Policy: AES-256 encryption at rest, TLS 1.2+ in transit, RBAC with least-privilege
              access, MFA, quarterly access reviews, comprehensive audit logging, and annual third-party penetration testing.
            </p>

            <h4>Upstream Liability Cap</h4>
            <div className="warning-callout">
              <p className="text-xs font-semibold uppercase tracking-wider mb-1 opacity-75">Important</p>
              Shopify's API Terms cap Shopify's liability to Realify at $150 USD per application. This means that if a Shopify API
              failure, outage, or platform error causes disruption to the Realify integration and results in losses, Realify's
              maximum recovery from Shopify is $150. Additionally, the Shopify API is provided "as is" without warranty — Shopify
              makes no guarantees about API availability, accuracy, or fitness for any purpose. This upstream "as is" provision
              flows through to Realify's own disclaimers in Terms of Service Section 8. Realify's liability to you for Shopify
              API-related issues is separately governed by Terms of Service Section 9.
            </div>

            <h4>Deletion — 48-Hour Merchant and Shopify Request</h4>
            <p>
              Realify deletes all Shopify Merchant data and associated customer data: (a) within 48 hours of a Merchant's or
              Shopify's written request, subject to any active customer data export wind-down period under Terms of Service Section
              11 (customers retain read-only access for up to 60 days post-termination to export data; Shopify API data required
              for that export will be retained until the export period expires or the customer completes export, whichever is
              earlier); (b) within 48 hours of Realify determining the data is no longer required to operate the activated features
              and no export wind-down period is active; or (c) upon account closure where no export wind-down period is active,
              with backup copies purged within 90 days. Written deletion confirmation provided on request.
            </p>

            <h4>Breach Notification</h4>
            <p>
              In the event of a security incident involving Shopify API data, Realify notifies the affected Merchant and Shopify
              within 72 hours of confirmed discovery, consistent with Shopify's Partner Program Agreement breach notification
              requirements. Notification includes: nature and scope of the incident; categories and approximate number of affected
              records; likely consequences; measures taken or proposed. Realify cooperates with Shopify's incident review process.
            </p>

            <h4>Governing Law — Shopify API</h4>
            <p>
              Disputes specifically relating to the Shopify Partner Program Agreement and API Terms are governed by the laws of
              the Province of Ontario, Canada, without conflict-of-law principles, with exclusive jurisdiction in the courts of
              Ontario. The United Nations Convention on Contracts for the International Sale of Goods does not apply.
            </p>

            {/* 5.6 All Other Connected Platforms */}
            <h3>5.6 All Other Connected Platforms</h3>
            <p>
              For WooCommerce, Magento, Walmart, eBay, Etsy, TikTok Shop, Klaviyo, Stripe, Recharge, Gorgias, Zendesk, Postscript,
              and others: data is used solely to operate the features you have activated. No data is sold, used for Realify's
              marketing, or shared with third parties beyond sub-processors. No data from any Connected Platform is aggregated or
              benchmarked across customer accounts. Credentials are secured per Section 4.5 of the Terms of Service. Retention
              follows Section 9 of this Policy.
            </p>
          </section>

          {/* § 06 Sub-Processors */}
          <section id="pp-s6" className="scroll-mt-20 mb-6">
            <h2>§ 06 — Sub-Processors</h2>
            <div className="overflow-x-auto mb-4">
              <table>
                <thead>
                  <tr><th>Sub-Processor</th><th>Location</th><th>Role</th><th>Amazon Info?</th></tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Amazon Web Services (AWS)</td>
                    <td>USA (us-east-1, us-west-2)</td>
                    <td>Primary cloud infrastructure and storage. Hosts all Amazon SP-API data, Amazon Advertising API data, Google Ads data, and Meta Ads data under Realify's own AWS account.</td>
                    <td>Yes — primary storage for all Amazon data</td>
                  </tr>
                  <tr>
                    <td>Amazon.com, Inc. — Advertising API endpoint</td>
                    <td>USA (AWS us-east-1)</td>
                    <td>Advertising campaign management and reporting via Amazon Advertising API (Sponsored Products, Brands, Display, DSP). Same data controller as SP-API (Amazon.com, Inc.) — not a new third-party processor.</td>
                    <td>Yes — Advertising data only; logically separated from SP-API data; US-only storage</td>
                  </tr>
                  <tr><td>Snowflake Inc.</td><td>USA (AWS us-east-1)</td><td>Data warehouse / analytics</td><td>Yes — ops only</td></tr>
                  <tr><td>Google Cloud Platform</td><td>USA (us-central1)</td><td>ML training (non-Amazon data only)</td><td>No</td></tr>
                  <tr><td>Datadog Inc.</td><td>USA</td><td>Application performance monitoring</td><td>No — metadata only</td></tr>
                  <tr><td>Sentry.io</td><td>USA</td><td>Error tracking</td><td>No — error logs only</td></tr>
                  <tr><td>Twilio SendGrid</td><td>USA</td><td>Transactional email</td><td>No — email/name only</td></tr>
                  <tr><td>Stripe Inc.</td><td>USA</td><td>Payment processing</td><td>No — billing only</td></tr>
                  <tr><td>Intercom Inc.</td><td>USA</td><td>Customer support</td><td>No — support content</td></tr>
                  <tr><td>OpenAI (feature-specific)</td><td>USA</td><td>Natural-language UI features</td><td>No — never</td></tr>
                </tbody>
              </table>
            </div>
            <p>
              Current list:{' '}
              <a href="https://realify.ai/legal/subprocessors" target="_blank" rel="noopener noreferrer">realify.ai/legal/subprocessors</a>.
              We provide 30 days' advance notice of new sub-processors handling Amazon Information, with your right to object.
              Before sharing Amazon Information with any sub-processor, we conduct documented due diligence and require written
              obligations covering retention limits, aggregation prohibition, AI/ML training restriction, and 24-hour breach
              notification (Amazon DPP §4.7). Annual risk assessments are conducted for all sub-processors with access to
              Customer Personal Data.
            </p>
          </section>

          {/* § 07 Data Security */}
          <section id="pp-s7" className="scroll-mt-20 mb-6">
            <h2>§ 07 — Data Security</h2>
            <div className="overflow-x-auto mb-4">
              <table>
                <thead>
                  <tr><th>Control</th><th>Standard</th></tr>
                </thead>
                <tbody>
                  <tr><td>Encryption in transit</td><td>TLS 1.2+ (TLS 1.3 where supported); SFTP/SSH-2 for file transfers; message-level encryption where channel encryption terminates in untrusted multi-tenant hardware</td></tr>
                  <tr><td>Encryption at rest</td><td>AES-256 for all stored data: databases, file storage, backups, archives</td></tr>
                  <tr><td>Key management</td><td>AWS KMS; automatic annual rotation; no individual plaintext key access</td></tr>
                  <tr><td>User accounts</td><td>Unique user ID per person; no shared accounts; lockout after 10 failed attempts</td></tr>
                  <tr><td>Access controls</td><td>RBAC; least privilege; MFA mandatory for all production access; quarterly recertification; access revoked within 24 hours of departure</td></tr>
                  <tr><td>Password policy</td><td>Min. 12 characters; uppercase, lowercase, numbers, special chars; max 365-day / min 1-day expiration; last 10 passwords cannot be reused; API keys rotated annually</td></tr>
                  <tr><td>Audit logging</td><td>All production access logged (user, action, timestamp, geographic origin); retained 12 months minimum; reviewed monthly for anomalies</td></tr>
                  <tr><td>DLP controls</td><td>Deployed on all API channels and admin interfaces; alerts and blocks unauthorized data movement</td></tr>
                  <tr><td>Network security</td><td>VPC isolation; WAF; IDS/IPS; anti-malware updated monthly; annual security awareness training for all personnel with access to Customer Data</td></tr>
                  <tr><td>Vulnerability management</td><td>Automated scanning every 30 days; annual third-party penetration testing; critical patches within 7 days, high-risk within 30 days, others within 90 days</td></tr>
                  <tr><td>Secure coding</td><td>No hardcoded credentials; no secrets in public repos; SAST/DAST before each release; separate test and production environments; Amazon Information never used in non-production environments</td></tr>
                  <tr><td>Incident response</td><td>Formal IR Plan; annual tabletop exercises; reviewed every 6 months and on major system changes; dedicated IR team</td></tr>
                  <tr><td>Backup / DR</td><td>Geographically separated DR (AWS us-west-2); same encryption, access, and DLP standards; RTO/RPO defined in DR plan</td></tr>
                  <tr><td>Sub-processor security</td><td>Documented pre-onboarding assessment; annual review of all sub-processors with access to Customer Personal Data</td></tr>
                </tbody>
              </table>
            </div>
            <p>
              Enterprise customers may request the penetration test executive summary under NDA. Contact{' '}
              <a href="mailto:legal@realify.ai">legal@realify.ai</a>.
            </p>
          </section>

          {/* § 08 Geographic Scope */}
          <section id="pp-s8" className="scroll-mt-20 mb-6">
            <h2>§ 08 — Geographic Scope</h2>
            <p>
              All Realify personnel and operations are located in the United States. Customer Data is stored and processed in
              the United States. Amazon Information is stored exclusively in AWS us-east-1 (N. Virginia) and AWS us-west-2
              (Oregon). Google Ads and Meta Ads data uses the same U.S. AWS infrastructure. Non-Amazon ML training uses GCP
              us-central1 (Iowa). No Amazon Information is transmitted to, processed in, accessed from, or stored in any
              location outside the United States, by any Realify personnel, contractor, sub-processor, or system.
            </p>
          </section>

          {/* § 09 Data Retention */}
          <section id="pp-s9" className="scroll-mt-20 mb-6">
            <h2>§ 09 — Data Retention</h2>
            <div className="overflow-x-auto mb-4">
              <table>
                <thead>
                  <tr><th>Data Category</th><th>Retention Period</th></tr>
                </thead>
                <tbody>
                  <tr><td>Amazon Information — buyer PII</td><td>30 days from collection (hard limit)</td></tr>
                  <tr><td>Amazon Information — non-PII live</td><td>30 days from collection (hard limit)</td></tr>
                  <tr><td>Amazon Information — non-PII archive</td><td>18 months from collection (hard limit)</td></tr>
                  <tr><td>Amazon Advertising API data</td><td>Duration of integration; deleted from live systems within 30 days of revocation/closure; backups purged within 90 days</td></tr>
                  <tr><td>Google Ads API data</td><td>Duration of integration; deleted within 30 days of revocation/closure; backups purged within 90 days</td></tr>
                  <tr><td>Meta Marketing API data</td><td>Duration of integration; deleted within 30 days of revocation/closure; backups purged within 90 days</td></tr>
                  <tr><td>Shopify API data (Merchant and customer data)</td><td>Deleted within 48 hours of Merchant/Shopify request or when no longer needed (subject to ToS Section 11 export wind-down period); backups purged within 90 days of account closure</td></tr>
                  <tr><td>Other Connected Platform data</td><td>Duration of subscription; deleted within 30 days of closure</td></tr>
                  <tr><td>Account and billing data</td><td>Duration of account plus 7 years (legal/tax compliance)</td></tr>
                  <tr><td>Usage and log data</td><td>90 days</td></tr>
                  <tr><td>Backup copies (all data)</td><td>Purged within 90 days of account closure or deletion request</td></tr>
                </tbody>
              </table>
            </div>
            <p>All deletion follows NIST SP 800-88 Rev. 1. Written deletion certificates issued on request.</p>
          </section>

          {/* § 10 AI and Machine Learning */}
          <section id="pp-s10" className="scroll-mt-20 mb-6">
            <h2>§ 10 — AI and Machine Learning</h2>
            <p>
              Proprietary models are trained on synthetic data, publicly available data, and customer data only where explicit
              opt-in has been granted via Settings &gt; Privacy &gt; AI Data Use (default: off). Amazon Information is never used
              for model training — absolute, unconditional prohibition. Non-Amazon Connected Platform data requires explicit opt-in.
              Opt-out via the platform toggle or by emailing{' '}
              <a href="mailto:legal@realify.ai">legal@realify.ai</a>{' '}
              (subject: "AI Training Opt-Out"); processed within 5 business days. Historical data already in training datasets
              cannot be retroactively removed.
            </p>
            <p>
              Third-party LLMs: certain natural-language features use third-party LLM APIs (including OpenAI) under enterprise
              agreements prohibiting use for the LLM provider's own training. Only necessary data snippets are transmitted; Amazon
              Information is never sent to any third-party LLM. All AI outputs are subject to the disclaimer and verification
              obligations in Terms of Service Section 4.3.
            </p>
          </section>

          {/* § 11 California Privacy Rights */}
          <section id="pp-s11" className="scroll-mt-20 mb-6">
            <h2>§ 11 — California Privacy Rights (CCPA / CPRA)</h2>
            <p>
              For California Residents. Realify.ai is headquartered in San Francisco, California. This section describes your
              rights under the California Consumer Privacy Act, as amended by the California Privacy Rights Act (CPRA).
            </p>
            <p>
              Important disclosure: advertising on our marketing website. Realify operates two distinct data domains with different
              advertising practices:
            </p>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Realify Marketing Website (realify.ai)</strong>
                We use Google Ads, Google Analytics 4 (including Enhanced Conversions and Customer Match), the Meta Pixel, and the
                Meta Conversions API (including Advanced Matching and Custom Audiences) on our marketing website. Under the CPRA,
                this constitutes "sharing" of personal information for cross-context behavioral advertising. Information shared with
                these advertising partners includes IP address, device identifiers, page-view events, and hashed contact information
                (email, phone) for advanced matching and conversion measurement.
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Realify Platform (authenticated Services)</strong>
                We do not use advertising cookies, tracking pixels, or remarketing technologies within the authenticated platform.
                We do not sell or share Customer Data or Amazon Information for advertising purposes, ever.
              </li>
            </ul>
            <p>California residents have the following rights:</p>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3"><strong className="text-gray-800 block mb-1">(a) Know</strong>Categories and specific pieces of personal information collected, sources, purposes, and third parties.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">(b) Delete</strong>Personal information we hold, subject to legal exceptions.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">(c) Correct</strong>Inaccurate personal information.</li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">(d) Opt Out of Sale or Sharing</strong>
                To opt out of the sharing of your personal information for cross-context behavioral advertising on our marketing
                website, click the "Do Not Sell or Share My Personal Information" link in our website footer, email{' '}
                <a href="mailto:legal@realify.ai">legal@realify.ai</a>, or enable Global Privacy Control (GPC) in your browser
                (honored automatically).
              </li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">(e) Limit Sensitive PI</strong>We do not use sensitive personal information beyond CPRA-permitted purposes without additional consent.</li>
              <li className="py-3"><strong className="text-gray-800 block mb-1">(f) Non-Discrimination</strong>Exercising rights will not affect your Services.</li>
            </ul>
            <p>
              Residents of Virginia, Colorado, Connecticut, Utah, Texas, Oregon, Montana, and other states with comprehensive
              privacy laws have substantially similar rights. Submit requests to{' '}
              <a href="mailto:legal@realify.ai">legal@realify.ai</a>{' '}
              (subject: "California Privacy Request"). We verify identity before processing and respond within 45 days (extensions
              possible with advance notice). Authorized agents may submit requests with proof of authorization.
            </p>
          </section>

          {/* § 12 International Transfers */}
          <section id="pp-s12" className="scroll-mt-20 mb-6">
            <h2>§ 12 — International Transfers</h2>
            <p>
              US-Only Customer Base. Realify currently serves customers exclusively in the United States and does not actively
              process personal data of EEA, UK, or Swiss data subjects. The transfer mechanisms below are documented for regulatory
              completeness and future use. They are not currently operative but will be activated if and when Realify expands to
              serve EU, UK, or Swiss customers.
            </p>
            <p>
              For future customers subject to GDPR, UK GDPR, or the Swiss FADP, Realify will offer: (a) EU-US Data Privacy Framework
              (DPF) — where Realify is self-certified (verify at{' '}
              <a href="https://www.dataprivacyframework.gov" target="_blank" rel="noopener noreferrer">https://www.dataprivacyframework.gov</a>);
              or (b) EU Standard Contractual Clauses (Commission Decision 2021/914, Module 2), UK International Data Transfer
              Addendum, and Swiss adaptations, incorporated by reference and executed on request; supplementary Schrems II measures
              (encryption, access controls, audit logging, documented government-access-request procedures) apply to all transfers.
              Contact <a href="mailto:legal@realify.ai">legal@realify.ai</a> to execute the appropriate mechanism.
            </p>
          </section>

          {/* § 13 Changes to This Policy */}
          <section id="pp-s13" className="scroll-mt-20 mb-6">
            <h2>§ 13 — Changes to This Policy</h2>
            <p>
              We notify you of material changes by email or in-platform notice at least 14 days before they take effect. Continued
              use constitutes acceptance. Contact:{' '}
              <a href="mailto:legal@realify.ai">legal@realify.ai</a>
            </p>
          </section>

        </div>
      </main>
    </div>
  );
};

export default PrivacyPolicy;
