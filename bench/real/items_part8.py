ITEMS = [
    dict(id="R-L22", label=0, date="2022-11-02", channel="physical", source="Deccan Herald, 2 Nov 2022", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fed-summons-jharkhand-chief-minister-hemant-soren-for-questioning-appearance-set-for-november-3-1158652.html",
         text="The Enforcement Directorate has summoned Jharkhand Chief Minister Hemant Soren for questioning on Nov. 3. "
              "The agency wants to question and record his statement under the Prevention of Money Laundering Act (PMLA). "
              "Soren, 47, has been asked to appear before the federal probe agency at its regional office in state capital Ranchi.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L23", label=0, date="2024-03-04", channel="physical", source="ETV Bharat, 4 Mar 2024", form="excerpts",
         url="https://www.etvbharat.com/en/!bharat/ed-summons-tmc-leader-mahua-moitra-in-fema-case-on-march-11-enn24030406377",
         text="The Enforcement Directorate has issued fresh summons to Trinamool Congress leader. "
              "Moitra has now been asked to appear at the ED office in Delhi on March 11. "
              "record her statement under the provisions of the Foreign Exchange Management Act (FEMA).",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L24", label=0, date="2023-04-22", channel="physical", source="The Tribune, 22 Apr 2023", form="excerpts",
         url="https://www.tribuneindia.com/news/j-k/cbi-notice-to-malik-in-jk-insurance-scam-case-499690",
         text="CBI notice to Malik in J&K insurance scam case, asking it to appear before it and answer certain queries. "
              "the former J&K Governor had been asked for his presence at the agency's Akbar Road guesthouse here.",
         gold=dict(agencies=["cbi"], instruments=["notice_witness"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L25", label=0, date="2026-08-10", channel="email", source="LiveLaw, 10 Aug 2026", form="excerpts",
         url="https://www.livelaw.in/high-court/telangana-high-court/telangana-high-court-police-notice-x-account-details-fir-545131",
         text="a Section 94 BNSS notice issued by the police to social media platform 'X' (formerly Twitter), "
              "including basic user information, registration details, linked mobile number, email address, "
              "particulars of devices used/logged in and IP logs in connection with an FIR.",
         gold=dict(agencies=["police"], instruments=["order_produce_docs"], demands=["produce_documents"], payee="none")),
    dict(id="R-L26", label=0, date="2025-11-28", channel="sms", source="CBDT press release, 27 Nov 2025", form="excerpts",
         url="https://incometaxindia.gov.in/Lists/Press%20Releases/Attachments/1234/PressRelease-CBDT-launches-2nd-NUDGE-initiative-to-strengthen-voluntary-compliance-in-respect-of-Foreign-Assets.pdf",
         text="SMSs and emails will be issued from 28th November 2025 to such taxpayers, "
              "advising them to review and revise their returns on or before 31st December 2025 to avoid penal consequences. "
              "taxpayers may refer to the official website www.incometax.gov.in.",
         gold=dict(agencies=["income_tax"], instruments=["tax_notice"], demands=["pay_via_portal"], payee="official_portal")),
]
