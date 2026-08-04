import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '@/constants/routes';

const TermsOfService = () => {
  return (
    <div className="bg-white min-h-screen">

      {/* Hero / Title Section */}
      <section className="bg-gradient-to-br from-blue-50 via-slate-50 to-white pt-14 pb-6 border-b border-gray-100">
        <div className="max-w-4xl mx-auto px-4 sm:px-6">
          <h1 className="text-2xl font-bold text-gray-700 mb-5">Realify Terms of Service</h1>
          <div className="text-sm text-gray-500 space-y-1">
            <p><span className="font-semibold text-gray-600">Controller:</span> Realify ai Inc (Delaware corporation, File No. 10409872)</p>
            <p><span className="font-semibold text-gray-600">Principal Address:</span> 28 Geary St STE 650 494, San Francisco, CA 94108, USA</p>
            <p><span className="font-semibold text-gray-600">Development Center (Affiliated):</span> Realify AI India Private Limited</p>
            <p><span className="font-semibold text-gray-600">Affiliate Address:</span> Plot No. 629, Sector 82, Sahibzada Ajit Singh Nagar (Mohali), Punjab 140306, India</p>
            <p className="pt-3"><span className="font-semibold text-gray-600">Contact:</span> legal@realify.ai</p>
            <p><span className="font-semibold text-gray-600">Effective Date:</span> June 1<sup>st</sup>, 2026</p>
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="flex-grow py-8 px-4">
        <div className="max-w-4xl mx-auto policy-content">

          {/* Table of Contents */}
          <section className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-6 shadow-sm" data-purpose="toc">
            <h2 className="text-lg font-bold mt-0 border-none mb-4 uppercase text-black">Contents</h2>
            <div className="grid md:grid-cols-2 gap-x-8 gap-y-1 text-sm">
              <ul className="list-none pl-0 space-y-1">
                <li><a className="text-blue-600 hover:underline" href="#tos-s1"><span className="font-sans text-xs text-gray-400 mr-2">01</span>Acceptance</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s2"><span className="font-sans text-xs text-gray-400 mr-2">02</span>Definitions</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s3"><span className="font-sans text-xs text-gray-400 mr-2">03</span>License</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s4"><span className="font-sans text-xs text-gray-400 mr-2">04</span>Connected Platforms &amp; AI</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s5"><span className="font-sans text-xs text-gray-400 mr-2">05</span>Fees &amp; Payment</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s6"><span className="font-sans text-xs text-gray-400 mr-2">06</span>Confidentiality</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s7"><span className="font-sans text-xs text-gray-400 mr-2">07</span>Intellectual Property</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s8"><span className="font-sans text-xs text-gray-400 mr-2">08</span>Warranties &amp; Disclaimers</a></li>
              </ul>
              <ul className="list-none pl-0 space-y-1">
                <li><a className="text-blue-600 hover:underline" href="#tos-s9"><span className="font-sans text-xs text-gray-400 mr-2">09</span>Limitation of Liability</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s10"><span className="font-sans text-xs text-gray-400 mr-2">10</span>Indemnification</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s11"><span className="font-sans text-xs text-gray-400 mr-2">11</span>Term &amp; Termination</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s12"><span className="font-sans text-xs text-gray-400 mr-2">12</span>Export Controls &amp; DMCA</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s13"><span className="font-sans text-xs text-gray-400 mr-2">13</span>Dispute Resolution</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s14"><span className="font-sans text-xs text-gray-400 mr-2">14</span>Service Level Agreement</a></li>
                <li><a className="text-blue-600 hover:underline" href="#tos-s15"><span className="font-sans text-xs text-gray-400 mr-2">15</span>General</a></li>
              </ul>
            </div>
          </section>

          {/* § 01 Acceptance */}
          <section id="tos-s1">
            <h2>§ 01 Acceptance</h2>
            <p>These Terms of Service ("Terms") are a binding agreement between Realify ai Inc ("Realify.ai"), a Delaware corporation (File No. 10409872) with its principal business address at 28 Geary St STE 650 494, San Francisco, CA 94108, and the entity or individual using the Realify platform ("Customer," "you"). By clicking "I Agree," executing an Order Form, or accessing the Services, you accept these Terms and all incorporated policies. If accepting for an organization, you confirm you have authority to bind it.</p>
            <h3>Electronic Acceptance</h3>
            <p>Your electronic acceptance of these Terms constitutes a legally binding agreement under the Electronic Signatures in Global and National Commerce Act (ESIGN), 15 U.S.C. § 7001 et seq., the Uniform Electronic Transactions Act (UETA) as adopted by your state (including California's Uniform Electronic Transactions Act, Cal. Civ. Code §§ 1633.1–1633.17), and any other applicable state or federal electronic signature laws. You consent to conduct this transaction electronically, to receive all notices and disclosures electronically, and you acknowledge that you have the necessary hardware and software to receive, access, and retain electronic records. You have the right to receive a paper copy of these Terms upon written request to <a className="text-blue-600 hover:underline" href="mailto:legal@realify.ai">legal@realify.ai</a>. You may withdraw your consent to electronic transactions by sending written notice to <a className="text-blue-600 hover:underline" href="mailto:legal@realify.ai">legal@realify.ai</a>, though doing so may terminate your ability to use the Services.</p>
          </section>

          {/* § 02 Definitions */}
          <section id="tos-s2">
            <h2>§ 02 Definitions</h2>
            <div className="divide-y divide-gray-200">
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Services"</span>
                <span className="text-gray-600">The Realify platform, including the AI Pricing, Inventory, Demand Forecasting, Listing Intelligence, Screener, Advertising, and Profitability Agents, the Conductor orchestration system, plus all APIs, dashboards, analytics, automation, integrations, and support.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Customer Data"</span>
                <span className="text-gray-600">All data you upload, submit, or make available through the Services, including data retrieved from Connected Platforms on your behalf.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Amazon Information"</span>
                <span className="text-gray-600">Data accessed through the Amazon Selling Partner API on your behalf, as defined in Amazon's SP-API Developer Agreement.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Connected Platforms"</span>
                <span className="text-gray-600">Third-party services you authorize Realify to access, including Amazon SP-API, Amazon Advertising API, Shopify, WooCommerce, Magento, Walmart, eBay, Etsy, TikTok Shop, Google Ads, Meta Ads, Klaviyo, Stripe, Recharge, Gorgias, Zendesk, and Postscript.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Automated Actions"</span>
                <span className="text-gray-600">Operations the Services execute on a Connected Platform without a contemporaneous manual instruction, such as price updates, bid changes, budget adjustments, and inventory modifications.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Integration Credentials"</span>
                <span className="text-gray-600">OAuth tokens, API keys, access tokens, and similar credentials used to connect a Connected Platform.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Authorized Users"</span>
                <span className="text-gray-600">Your employees, contractors, and agents whom you permit to access the Services under your account.</span>
              </div>
              <div className="flex gap-5 py-3 text-sm">
                <span className="font-sans text-xs text-blue-600 font-medium w-44 flex-shrink-0 pt-0.5">"Order Form"</span>
                <span className="text-gray-600">A written or electronic order or subscription agreement that references these Terms.</span>
              </div>
            </div>
          </section>

          {/* § 03 License */}
          <section id="tos-s3">
            <h2>§ 03 License</h2>
            <p>Realify grants you a limited, non-exclusive, non-transferable, revocable license to access and use the Services for your internal business purposes during the subscription term. You may not: (a) reverse-engineer, copy, or create derivative works of the Services; (b) resell or sublicense access; (c) build a competing product; (d) remove or alter any proprietary rights notice; or (e) use the Services in violation of applicable law or any Connected Platform's policies.</p>
          </section>

          {/* § 04 Connected Platforms, Automated Actions, and AI */}
          <section id="tos-s4">
            <h2>§ 04 Connected Platforms, Automated Actions, and AI</h2>
            <h3>4.1 Platform Authorization</h3>
            <p>By connecting any Connected Platform you confirm you are the authorized account holder (or have their written consent), you have reviewed that platform's terms and API policies, and your use of Realify in connection with that platform complies with those policies. Realify connects via OAuth 2.0 and requests only minimum required permission scopes.</p>
            <h3>4.2 Automated Actions</h3>
            <div className="bg-amber-50 border border-amber-200 border-l-4 border-l-amber-400 rounded-r-md p-4 my-4 text-sm text-amber-900">
              <p className="text-xs font-semibold uppercase tracking-wide mb-2 opacity-75">Critical</p>
              Realify's AI agents execute Automated Actions on live Connected Platforms with real commercial consequences. You are solely responsible for all outcomes of Automated Actions under your configuration. Before enabling any Automated Actions, configure guardrails for each agent — price floors and ceilings, budget caps, bid limits, inventory thresholds, and exclusion lists. Realify is a technology tool, not a fiduciary or commercial advisor. Realify bears no liability for any commercial outcome, marketplace policy violation, account suspension, or revenue loss arising from Automated Actions executed under your configuration.
            </div>
            <h3>4.3 AI Outputs — Disclaimer, Hallucination Risk, and Verification</h3>
            <p>Nothing the Services produce — including AI recommendations, pricing suggestions, demand forecasts, profitability analyses, advertising recommendations, listing optimizations, or natural-language summaries — constitutes financial, legal, tax, or professional advice. All outputs are informational and probabilistic. AI systems can produce inaccurate, incomplete, fabricated, or misleading outputs ("hallucinations") — this risk is inherent to current AI technology and cannot be eliminated. Outputs may misinterpret data, generate confident-sounding but incorrect inferences, or vary in quality across products, marketplaces, and time periods. Realify makes no representation that outputs are free of these characteristics and provides them "as is" without warranty of accuracy, completeness, or fitness for any commercial purpose. Past AI performance is not indicative of future results.</p>
            <p>You are solely responsible for verifying all AI outputs before relying on them or permitting them as Automated Actions. Before any Automated Action with material commercial impact: review the recommendation, confirm it aligns with your strategy, validate against your operational data, and ensure compliance with all applicable platform policies and laws. Realify bears no liability for any loss arising from reliance on AI outputs.</p>
            <h3>4.4 Algorithmic Pricing</h3>
            <p>You are responsible for ensuring your pricing practices comply with all applicable laws, including antitrust and competition laws, price-fixing prohibitions, MAP agreements, and marketplace pricing policies. Each customer's Realify configuration is independent; Realify does not share pricing data between customers or facilitate coordination between sellers.</p>
            <h3>4.5 Integration Credentials</h3>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-2.5">
                <strong className="text-gray-800 mr-2">Storage</strong>
                <span className="text-gray-600">Credentials are AES-256 encrypted in access-controlled key management systems and never logged in plaintext.</span>
              </li>
              <li className="py-2.5">
                <strong className="text-gray-800 mr-2">Revocation</strong>
                <span className="text-gray-600">Revoke any integration via Settings &gt; Integrations. Credentials are purged within 48 hours.</span>
              </li>
              <li className="py-2.5">
                <strong className="text-gray-800 mr-2">Google Ads</strong>
                <span className="text-gray-600">Developer tokens unused commercially for 90 consecutive days are automatically deleted, in accordance with Google Ads API Terms of Service.</span>
              </li>
              <li className="py-2.5">
                <strong className="text-gray-800 mr-2">Compromise</strong>
                <span className="text-gray-600">Notify <a className="text-blue-600 hover:underline" href="mailto:legal@realify.ai">legal@realify.ai</a> immediately of any suspected credential compromise.</span>
              </li>
            </ul>
          </section>

          {/* § 05 Fees and Payment */}
          <section id="tos-s5">
            <h2>§ 05 Fees and Payment</h2>
            <p>Fees are set in your Order Form, in U.S. Dollars, and non-refundable unless an Order Form or law provides otherwise. Fees may increase with 60 days' notice before a renewal term. Unpaid invoices accrue interest at 1.5%/month (or the legal maximum). Realify may suspend Services after 10 days' written notice of non-payment.</p>
          </section>

          {/* § 06 Confidentiality */}
          <section id="tos-s6">
            <h2>§ 06 Confidentiality</h2>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Definition</strong>
                <span className="text-gray-600">"Confidential Information" means non-public information one party discloses to the other that is designated confidential or reasonably understood to be so. Realify's includes platform architecture, AI models, and algorithms. Yours includes Customer Data and business metrics.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Obligations</strong>
                <span className="text-gray-600">Each party will hold the other's Confidential Information in strict confidence, use it only for the Services, and not disclose it without prior written consent except to personnel bound by equivalent obligations.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Exclusions</strong>
                <span className="text-gray-600">Obligations do not apply to information that is publicly known without breach, was rightfully known before disclosure, received without restriction from a third party, or independently developed.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Compelled Disclosure</strong>
                <span className="text-gray-600">If legally compelled to disclose, the Receiving Party will promptly notify the Disclosing Party (to the extent permitted) and reasonably cooperate in seeking a protective order.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Survival</strong>
                <span className="text-gray-600">General Confidential Information: 5 years post-termination. Trade secrets, AI models, and source code: perpetually. Customer Personal Data and Amazon Information: until deleted per applicable requirements. Perpetual obligations apply notwithstanding any general expiration.</span>
              </li>
            </ul>
          </section>

          {/* § 07 Intellectual Property */}
          <section id="tos-s7">
            <h2>§ 07 Intellectual Property</h2>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Realify IP</strong>
                <span className="text-gray-600">The Services and all software, AI models, algorithms, interfaces, and documentation are the exclusive property of Realify and its licensors. These Terms grant no IP rights beyond Section 3.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Customer IP</strong>
                <span className="text-gray-600">You retain all rights in Customer Data and grant Realify a non-exclusive, worldwide, royalty-free license to process Customer Data solely to provide the Services. This license terminates on account closure subject to retention requirements.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Feedback</strong>
                <span className="text-gray-600">Feedback you provide is licensed to Realify perpetually and royalty-free.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">IP Indemnification</strong>
                <span className="text-gray-600">Realify will defend you against claims that the Services (used per these Terms) infringe a U.S. patent, copyright, or trademark, except for claims arising from your modifications, Customer Data, unauthorized combinations, or failure to use a non-infringing version. This states Realify's entire liability for IP infringement.</span>
              </li>
            </ul>
          </section>

          {/* § 08 Warranties and Disclaimers */}
          <section id="tos-s8">
            <h2>§ 08 Warranties and Disclaimers</h2>
            <p>Each party warrants it has authority to enter these Terms.</p>
            <div className="bg-gray-50 border border-gray-200 border-l-4 border-l-gray-400 rounded-r-md p-4 my-4 font-sans text-xs text-gray-600 leading-relaxed">
              THE SERVICES ARE PROVIDED "AS IS." REALIFY DISCLAIMS ALL WARRANTIES, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT. REALIFY DOES NOT WARRANT THAT THE SERVICES WILL BE UNINTERRUPTED, ERROR-FREE, OR SECURE; THAT CONNECTED PLATFORM APIS WILL BE AVAILABLE; THAT AUTOMATED ACTIONS WILL PRODUCE ANY PARTICULAR RESULT; OR THAT AI OUTPUTS WILL BE ACCURATE OR PROFITABLE.
            </div>
          </section>

          {/* § 09 Limitation of Liability */}
          <section id="tos-s9">
            <h2>§ 09 Limitation of Liability</h2>
            <div className="bg-gray-50 border border-gray-200 border-l-4 border-l-gray-400 rounded-r-md p-4 my-4 font-sans text-xs text-gray-600 leading-relaxed">
              TO THE MAXIMUM EXTENT PERMITTED BY LAW, NEITHER PARTY IS LIABLE FOR INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOST PROFITS, REVENUES, OR DATA. REALIFY'S TOTAL CUMULATIVE LIABILITY ARISING OUT OF OR RELATED TO THESE TERMS WILL NOT EXCEED THE TOTAL FEES PAID BY YOU TO REALIFY IN THE 12 MONTHS IMMEDIATELY PRECEDING THE CLAIM.
            </div>
            <p style={{ marginTop: '12px' }}>Exceptions: payment obligations, indemnification, gross negligence or willful misconduct, and confidentiality breaches.</p>
          </section>

          {/* § 10 Indemnification */}
          <section id="tos-s10">
            <h2>§ 10 Indemnification</h2>
            <h3>By Customer</h3>
            <p>You will defend, indemnify, and hold harmless Realify from all third-party claims, damages, losses, and expenses arising from: (a) your use of the Services; (b) Customer Data; (c) your breach of these Terms or applicable law; (d) Automated Actions from your configuration; (e) your violation of a Connected Platform's terms.</p>
            <h3>Process</h3>
            <p>The indemnified party must promptly notify the indemnifying party, give it sole defense control, and provide reasonable cooperation. Settlements may not impose obligations on or admit liability of the indemnified party without prior written consent.</p>
          </section>

          {/* § 11 Term and Termination */}
          <section id="tos-s11">
            <h2>§ 11 Term and Termination</h2>
            <p>These Terms commence on your first access and continue until all Order Forms expire or are terminated. Either party may terminate for uncured material breach (30 days' notice). Realify may terminate or suspend immediately for breaches of Sections 3, 4, or the AUP, security or legal risk, or Connected Platform requirement.</p>
            <h3>Data Export</h3>
            <p>Upon termination, you have 60 days to export Customer Data in CSV, JSON, or via API. Enterprise customers may request a one-time data export package within 14 business days. Realify provides read-only access during this period and reasonable technical export assistance at no cost for the first 30 days. Customer Data is deleted from live systems within 30 days after the export period ends; backups purged within 90 days. Amazon Information is deleted per Privacy Policy Section 5.1. Realify provides written deletion confirmation on request.</p>
            <h3>Refunds</h3>
            <p>If you terminate for Realify's uncured breach, Realify refunds prepaid fees pro-rata from the termination date.</p>
            <h3>Survival</h3>
            <p>Sections 6, 7, 8, 9, 10, 13, and 14 survive termination.</p>
          </section>

          {/* § 12 Export Controls, DMCA, and Compliance */}
          <section id="tos-s12">
            <h2>§ 12 Export Controls, DMCA, and Compliance</h2>
            <p>The Services are subject to U.S. export control laws (EAR) and OFAC sanctions. You represent you are not located in or organized under a sanctioned country and are not on any U.S. restricted-party list. Each party will comply with anti-bribery and anti-corruption laws, including the FCPA.</p>
            <h3>DMCA</h3>
            <p>Realify respects intellectual property rights. To submit a copyright infringement notice, contact <a className="text-blue-600 hover:underline" href="mailto:dmca@realify.ai">dmca@realify.ai</a> (Attn: DMCA Agent, 28 Geary St STE 650 494, San Francisco, CA 94108). Notices must satisfy 17 U.S.C. § 512 requirements, including: (a) signature of the copyright owner or authorized agent; (b) identification of the infringed work; (c) identification of the infringing material with location information; (d) contact information; (e) a good-faith belief statement; and (f) a statement of accuracy under penalty of perjury. Counter-notices may be submitted to <a className="text-blue-600 hover:underline" href="mailto:dmca@realify.ai">dmca@realify.ai</a>. Repeat infringers may have their accounts terminated. Realify has registered its DMCA agent with the U.S. Copyright Office (<a className="text-blue-600 hover:underline" href="https://www.copyright.gov/dmca-directory" target="_blank" rel="noopener noreferrer">https://www.copyright.gov/dmca-directory</a>).</p>
          </section>

          {/* § 13 Dispute Resolution */}
          <section id="tos-s13">
            <h2>§ 13 Dispute Resolution</h2>
            <h3>Mandatory Arbitration</h3>
            <p>All Disputes must be resolved by binding arbitration — not litigation in court. Read this section carefully.</p>
            <p>All disputes arising from these Terms or the Services are resolved by binding arbitration under AAA Commercial Arbitration Rules, by a single arbitrator in San Francisco, CA (or by videoconference).</p>
            <div className="bg-gray-50 border border-gray-200 border-l-4 border-l-gray-400 rounded-r-md p-4 my-4 font-sans text-xs text-gray-600 leading-relaxed">
              CLASS AND COLLECTIVE ACTIONS ARE WAIVED — ALL DISPUTES ARE ARBITRATED INDIVIDUALLY.
            </div>
            <p>Opt-out: email <a className="text-blue-600 hover:underline" href="mailto:legal@realify.ai">legal@realify.ai</a> with subject "Arbitration Opt-Out" within 30 days of first acceptance, including your name, company, and email. Either party may seek injunctive relief in court to protect IP or Confidential Information. Governing law: California, without conflict-of-law principles. For opted-out or non-arbitrable matters: exclusive jurisdiction of state and federal courts in San Francisco County, California.</p>
          </section>

          {/* § 14 Service Level Agreement */}
          <section id="tos-s14">
            <h2>§ 14 Service Level Agreement</h2>
            <p>Uptime Commitment: 99.95% monthly. Measured as available minutes divided by total minutes per calendar month, per Realify's monitoring infrastructure reported at <a className="text-blue-600 hover:underline" href="https://status.realify.ai" target="_blank" rel="noopener noreferrer">status.realify.ai</a>.</p>
            <h3>Exclusions</h3>
            <p>Scheduled maintenance (up to 4 hours/month, 48 hours' notice); emergency maintenance; Connected Platform outages; force majeure; customer-caused issues; Preview/Beta/Alpha features.</p>
            <h3>Service Credits</h3>
            <table>
              <thead>
                <tr>
                  <th>Monthly Uptime</th>
                  <th>Service Credit</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>&lt; 99.95% but ≥ 99.0%</td>
                  <td>10% of monthly fee</td>
                </tr>
                <tr>
                  <td>&lt; 99.0% but ≥ 95.0%</td>
                  <td>25% of monthly fee</td>
                </tr>
                <tr>
                  <td>&lt; 95.0%</td>
                  <td>50% of monthly fee</td>
                </tr>
              </tbody>
            </table>
            <p>Request credits by emailing <a className="text-blue-600 hover:underline" href="mailto:legal@realify.ai">legal@realify.ai</a> within 30 days of the affected month. Credits apply to future fees and are not refundable in cash. Service Credits are the sole and exclusive remedy for any Uptime Commitment failure.</p>
            <h3>Support</h3>
            <table>
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Definition</th>
                  <th>Response</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>P1 — Critical</td>
                  <td>Platform unavailable; Automated Actions failing broadly</td>
                  <td>1 hour, 24×7</td>
                </tr>
                <tr>
                  <td>P2 — High</td>
                  <td>Major feature degraded; workaround exists</td>
                  <td>4 hours (business hours)</td>
                </tr>
                <tr>
                  <td>P3 — Medium</td>
                  <td>Minor issue; limited impact</td>
                  <td>1 business day</td>
                </tr>
                <tr>
                  <td>P4 — Low</td>
                  <td>Question, feature request, documentation</td>
                  <td>2 business days</td>
                </tr>
              </tbody>
            </table>
            <p>Business hours: 9 AM–6 PM Pacific, Monday–Friday, excluding U.S. federal holidays. P1 issues addressed 24×7. Status page: <a className="text-blue-600 hover:underline" href="https://status.realify.ai" target="_blank" rel="noopener noreferrer">status.realify.ai</a>. Material incidents posted within 30 minutes; P1 post-incident reviews published within 5 business days. Realify may modify the Uptime Commitment or Service Credit schedule upon 60 days' written notice; reductions apply only to renewal terms following the notice period.</p>
          </section>

          {/* § 15 General */}
          <section id="tos-s15">
            <h2>§ 15 General</h2>
            <ul className="list-none pl-0 divide-y divide-gray-200 text-sm mb-4">
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Entire Agreement</strong>
                <span className="text-gray-600">These Terms, Order Forms, and incorporated policies supersede all prior agreements.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Amendments</strong>
                <span className="text-gray-600">Realify may amend with 30 days' written notice. Continued use constitutes acceptance. Version history: <a className="text-blue-600 hover:underline" href="https://realify.ai/legal/versions" target="_blank" rel="noopener noreferrer">realify.ai/legal/versions</a>.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Assignment</strong>
                <span className="text-gray-600">You may not assign without Realify's consent. Realify may assign in a merger or asset sale.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Notices</strong>
                <span className="text-gray-600">To Realify: <a className="text-blue-600 hover:underline" href="mailto:legal@realify.ai">legal@realify.ai</a> and first-class mail to 28 Geary St STE 650 494, San Francisco, CA 94108, Attn: Legal. Notices are effective upon confirmed delivery.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Severability</strong>
                <span className="text-gray-600">If any provision is unenforceable, it will be modified to the minimum extent necessary; remaining provisions continue in full force.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Force Majeure</strong>
                <span className="text-gray-600">Neither party is liable for delays from circumstances beyond reasonable control, including natural disasters, government actions, war, cyberattacks, or Connected Platform outages.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Trademarks</strong>
                <span className="text-gray-600">Amazon, Amazon Advertising, Shopify, Google Ads, and Meta are trademarks of their respective owners. Realify is not affiliated with, endorsed by, or sponsored by any Connected Platform.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Open Source</strong>
                <span className="text-gray-600">Component list at <a className="text-blue-600 hover:underline" href="https://realify.ai/legal/oss" target="_blank" rel="noopener noreferrer">realify.ai/legal/oss</a>.</span>
              </li>
              <li className="py-3">
                <strong className="text-gray-800 block mb-1">Electronic Records</strong>
                <span className="text-gray-600">Realify maintains records of these Terms and your acceptance in accordance with applicable law. Version history available at <a className="text-blue-600 hover:underline" href="https://realify.ai/legal/versions" target="_blank" rel="noopener noreferrer">realify.ai/legal/versions</a>.</span>
              </li>
            </ul>
          </section>

        </div>
      </main>
    </div>
  );
};

export default TermsOfService;
