ITEMS = [
    dict(id="R-S17", label=1, date="2024-12-23", channel="voice_call", source="The Tribune, 23 Dec 2024", form="excerpts",
         url="https://www.tribuneindia.com/news/amp/bengaluru-techie-loses-rs-11-crore-to-digital-arrest-scam",
         text="the cyber fraudsters disguised themselves as police officials from the Mumbai Crime Branch. "
              "The fraudsters claimed that it was a case involving cheating of Rs 6 crore. "
              "The accused also claimed that the case is currently being looked into by the Supreme Court. "
              "also identified themselves as officers from the Income Tax and the Enforcement Directorate departments. "
              "kept him engaged over phone calls for more than a month. "
              "The accused had told him to sell his shares threatening arrest.",
         gold=dict(agencies=["police", "court", "income_tax", "ed"], instruments=["arrest"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S18", label=1, date="2024-10-13", channel="video_call", source="The Tribune, 13 Oct 2024", form="excerpts",
         url="https://www.tribuneindia.com/news/uttar-pradesh/amu-professor-duped-of-rs-75-lakh-in-digital-arrest-fraud",
         text="The accused posed an Enforcement Directorate official, threatens people of arrest by making video calls. "
              "the victim was kept under \"digital arrest for more than 10 days\". "
              "the accused pressured Jahan to pay money to avoid arrest. "
              "He gave her some bank account numbers and the victim complied with the demands and deposited more than Rs 75 lakh.",
         gold=dict(agencies=["ed"], instruments=["arrest"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S19", label=1, date="2025-07-19", channel="video_call", source="The Tribune, 19 Jul 2025", form="excerpts",
         url="https://www.tribuneindia.com/news/ludhiana/vet-varsity-professor-falls-prey-to-digital-arrest-scam-loses-20l/amp",
         text="The suspects, posing as CBI and IPS officials, threatened him on video calls. "
              "They kept him under digital arrest for 14 days by threatening to implicate him in a human trafficking case. "
              "the victim was threatened through a video call by showing fake identity and documents related to the case. "
              "They also told the professor that arrest warrants were also issued by the Enforcement Directorate (ED). "
              "demanded another Rs 10 lakh, else threatened to implicate him in a case.",
         gold=dict(agencies=["cbi", "police", "ed"], instruments=["arrest", "arrest_warrant"], demands=["transfer_funds"], payee="caller_supplied")),

    dict(id="R-L05", label=0, date="2024-02-22", channel="physical", source="Deccan Herald, 22 Feb 2024", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fdelhi%2Fed-summons-arvind-kejriwal-for-seventh-time-on-february-26-2905272",
         text="The Enforcement Directorate has issued fresh summons to the Delhi Chief Minister Arvind Kejriwal, "
              "asked him to appear before the investigators in connection with a money laundering case.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L06", label=0, date="2026-06-09", channel="physical", source="Madhyamam, 9 Jun 2026", form="excerpts",
         url="https://madhyamamonline.com/kerala/ed-issues-summons-to-t-veena-asks-to-appear-for-questioning-on-friday-1527062",
         text="The Enforcement Directorate (ED) has issued summons to nine people, including T. Veena, "
              "in connection with the money-laundering case linked to the Cochin Minerals and Rutile Limited. "
              "They have been asked to appear before the ED's Kochi office for questioning on Friday.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L07", label=0, date="2021-08-27", channel="whatsapp", source="The Tribune, 27 Aug 2021", form="excerpts",
         url="https://tribuneindia.com/news/court-can-serve-summons-notice-through-whatsapp-email-hc-302465",
         text="the Punjab and Haryana High Court has allowed e-service through email and instant messaging service WhatsApp. "
              "The only condition prescribed by the High Court is the furnishing of an affidavit that the email and the WhatsApp numbers are correct. "
              "A screenshot showing e-service of the summons has also been prescribed.",
         gold=dict(agencies=["court"], instruments=["summons_court"], demands=[], payee="none")),
    dict(id="R-L08", label=0, date="2017-05-04", channel="whatsapp", source="Bar & Bench, 4 May 2017", form="excerpts",
         url="https://www.barandbench.com/news/delhi-high-courts-justice-endlaw-paves-way-service-summons-whatsapp",
         text="Delhi High Court allowing the plaintiffs to serve the summons on one of the defendants through Whatsapp, text message and email.",
         gold=dict(agencies=["court"], instruments=["summons_court"], demands=[], payee="none")),
    dict(id="R-L09", label=0, date="2022-12-02", channel="physical", source="The South First, 2 Dec 2022", form="excerpts",
         url="https://thesouthfirst.com/news/cbi-asks-kavitha-to-appear-before-it-in-delhi-liquor-scam/",
         text="The notice was served on her under Section 160 of the CrPC for the investigation of the case. "
              "Under this notice, she would have to appear before the CBI as a witness in the case. "
              "to appear before it either in Hyderabad or in Delhi at 11 am on 6 December.",
         gold=dict(agencies=["cbi"], instruments=["notice_witness"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L10", label=0, date="2020-07-20", channel="email", source="The News Minute, 20 Jul 2020", form="excerpts",
         url="https://www.thenewsminute.com/money/income-tax-dept-launch-e-campaign-voluntary-compliance-taxpayers-129065",
         text="the Income Tax Department will send email/SMS to identified taxpayers. "
              "The taxpayers concerned can respond online to the query of the tax department on the portal. "
              "Further, the taxpayer would not be required to visit any I-T office, as the response has to be submitted online.",
         gold=dict(agencies=["income_tax"], instruments=["tax_notice"], demands=["pay_via_portal"], payee="official_portal")),
]
