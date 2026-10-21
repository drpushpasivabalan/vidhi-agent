ITEMS = [
    dict(id="R-L33", label=0, date="2025-02-17", channel="physical", source="Deccan Herald, 17 Feb 2025", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fmaharashtra%2Fyoutube-show-row-maharashtra-cyber-asks-comedian-samay-raina-to-appear-for-inquiry-on-february-18-3409186",
         text="Maharashtra Cyber has summoned at least 50 persons to record their statements in connection with the case. "
              "He said the comedian has been asked to appear before the agency on February 18.",
         gold=dict(agencies=["police"], instruments=["summons_agency"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L34", label=0, date="2025-02-14", channel="physical", source="WION, 14 Feb 2025", form="excerpts",
         url="https://www.wionews.com/entertainment/indias-got-latent-row-assam-cops-in-pune-to-serve-summons-to-comedian-samay-raina-8719616/amp",
         text="An Assam police team has arrived in Pune to issue summons to comedian Samay Raina. "
              "a team of their cyber police currently in Mumbai has served the summons to the duo, "
              "asking them to be present in person in connection with the controversial remarks.",
         gold=dict(agencies=["police"], instruments=["summons_agency"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L35", label=0, date="2017-05-02", channel="whatsapp", source="The Better India, 2 May 2017", form="excerpts",
         url="https://www.thebetterindia.com/98374/first-judge-mumbai-uses-whatsapp-truecaller-issues-summons/amp/",
         text="issued summons to the defendant via WhatsApp, after ascertaining using TrueCaller that the mobile number of the defendant was the right one. "
              "the WhatsApp message being delivered and read by the defendant could be taken as receipt of service.",
         gold=dict(agencies=["court"], instruments=["summons_court"], demands=[], payee="none")),
    dict(id="R-L36", label=0, date="2026-02-20", channel="whatsapp", source="LawWeb (Bombay High Court, Nagpur Bench), 20 Feb 2026", form="excerpts",
         url="https://www.lawweb.in/2026/02/summons-served-through-mobile-phone.html?m=1",
         text="all summons served through electronic communication under sections 64 to 71 shall be considered as duly served. "
              "a copy of such electronic summons shall be attested and kept as a proof of service of summons.",
         gold=dict(agencies=["court"], instruments=["summons_court"], demands=[], payee="none")),
    dict(id="R-L37", label=0, date="2025-02-14", channel="physical", source="Deccan Herald, 14 Feb 2025", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fmaharashtra%2Fcops-find-ranveer-allahbadias-mumbai-flat-locked-summon-him-again-3406942",
         text="Mumbai Police have asked podcaster Ranveer Allahbadia to appear before them on Saturday, "
              "had been asked to remain present at the Khar police station. "
              "the police issued a second summons, asking him to appear on Friday.",
         gold=dict(agencies=["police"], instruments=["summons_agency"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L38", label=0, date="2025-10-08", channel="email", source="Enforcement Directorate press release, 8 Oct 2025", form="paraphrase",
         url="https://enforcementdirectorate.gov.in/sites/default/files/latestnews/Press_release_fake%20summons-08.10.2025%201.pdf",
         text="Summons are generated through an ED system that places a QR code and a unique passcode at the bottom. "
              "The issuing official signs and stamps the summons, which also lists an official email ID and phone number. "
              "Scan the code, which opens an ED webpage, then enter the passcode to verify the summons.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=[], payee="none", has_qr=True, qr_official=True, has_seal=True)),
]
