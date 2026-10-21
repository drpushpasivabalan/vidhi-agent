"""VIDHI-Real: incidents and lawful communications as reported in public sources.

Every `text` is a concatenation of exact excerpts from the cited source (each excerpt
quoted verbatim by the source or written by the source's reporter); nothing is invented.
`date` is the event date when the source gives it, otherwise the publication date.
`channel` is the channel the source reports (the first contact channel for multi-step frauds).
Gold claims are the author's annotation of what each excerpt asserts.
"""

ITEMS = [
    # ------------------------------------------------------------ fraud (label 1)
    dict(id="R-S01", label=1, date="2024-09-25", channel="video_call", source="Deccan Herald, 13 Oct 2024",
         url="https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fbengaluru%2Fdigital-arrest-for-six-days-29-year-old-conned-of-rs-14-lakh-3230249",
         text="they created a sense of urgency by telling him that he had to visit CBI in Mumbai the same day for investigation. "
              "The caller asked him to transfer 80 per cent of the money in his bank accounts to an 'RBI account' for verification. "
              "He was told he would be under 24x7 surveillance and asked to install Signal to record his video statement.",
         gold=dict(agencies=["cbi", "rbi", "trai"], instruments=[], demands=["transfer_funds", "verification_deposit", "stay_on_camera"], payee="rbi")),
    dict(id="R-S02", label=1, date="2024-05-16", channel="skype", source="The News Minute, 22 May 2024",
         url="https://www.thenewsminute.com/karnataka/fedex-scam-bengaluru-software-engineer-loses-rs-1-crore-to-fraudsters",
         text="200 grams of narcotic drugs and several passports were found in a parcel listing her name and number at the Mumbai airport. "
              "The fraudsters, posing as a FedEx executive, a customs officer and Mumbai Police, asked her to transfer money to an account "
              "they said belonged to the Reserve Bank of India for verification. She was asked to stay in an isolated room with the camera on, "
              "and was promised the money would be returned within 30 days after verification.",
         gold=dict(agencies=["courier", "customs", "police", "rbi"], instruments=[], demands=["transfer_funds", "verification_deposit", "stay_on_camera", "isolation"], payee="rbi")),
    dict(id="R-S03", label=1, date="2023-12-10", channel="skype", source="Deccan Herald, 10 Dec 2023",
         url="https://www.deccanherald.com/amp/story/india%2Ffedex-courier-scam-a-tale-of-terror-trickery-and-deceit-2804802",
         text="The caller said he was a FedEx manager and that a package in his name was confiscated by Mumbai Customs. "
              "He was told to keep the video on at all times, stay alone in the room and send his wife away, "
              "and to transfer money to an 'RBI account', which would be credited back after verification. "
              "He was shown a case document claiming his bank account was used to launder money.",
         gold=dict(agencies=["courier", "customs", "police", "rbi"], instruments=[], demands=["stay_on_camera", "isolation", "transfer_funds", "verification_deposit"], payee="rbi")),
    dict(id="R-S04", label=1, date="2024-09-28", channel="skype", source="The News Minute, 2 Oct 2024",
         url="https://thenewsminute.com/news/how-an-indian-ceo-lost-rs-7-crore-to-scammers-who-pretended-to-be-ed-cbi-and-cji",
         text="The caller claimed that to be a Central Bureau of Investigation (CBI) officer. "
              "Posing as CBI officers, they instructed me to keep Skype in my phone on even during sleep. "
              "He was also sent a 'CBI order' saying that he was taken into 'digital custody' related to Naresh Goyal's case. "
              "asking him to release Rs 7 crore into a Secret Supervision Account (SSA). "
              "The industrialist said he was so intimidated that he could not share the incident with anyone.",
         gold=dict(agencies=["cbi", "court"], instruments=["arrest"], demands=["stay_on_camera", "transfer_funds", "secrecy", "verification_deposit"], payee="caller_supplied")),
    dict(id="R-S05", label=1, date="2025-04-19", channel="video_call", source="The Tribune, 19 Apr 2025",
         url="https://www.tribuneindia.com/news/delhi/digital-arrest-scam-delhi-cyber-police-arrest-3-after-retired-officer-cheated-of-rs-48-5-lakh",
         text="The accused used WhatsApp video calls to impersonate officials from TRAI, CBI, Mumbai Police, and even Supreme Court judges. "
              "The caller informed him of a money laundering case registered in Mumbai using his Aadhaar card. "
              "Within minutes, the victim was connected to a supposed Mumbai Police Sub-Inspector. "
              "manipulated into liquidating his Fixed Deposits, PPF, and other savings. "
              "The money was transferred to accounts falsely claimed to be under Supreme Court supervision.",
         gold=dict(agencies=["trai", "cbi", "police", "court"], instruments=[], demands=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
    dict(id="R-S06", label=1, date="2026-03-27", channel="voice_call", source="ETV Bharat, 4 Jul 2026",
         url="https://www.etvbharat.com/en/state/retired-patna-professor-duped-of-rs-82-dot-53-lakh-in-eight-day-digital-arrest-cyber-fraud-enn26070403603",
         text="The fraud began on March 27, 2026, when Ghyasuddin received a phone call from a person claiming to be a CBI officer. "
              "He was allegedly instructed not to disclose the matter to any family member, friend or acquaintance. "
              "The scammers pressured him into sending about Rs 82.53 lakh in several instalments through RTGS and UPI.",
         gold=dict(agencies=["cbi"], instruments=[], demands=["secrecy", "transfer_funds"], payee="caller_supplied")),
    dict(id="R-S07", label=1, date="2024-11-25", channel="whatsapp", source="Deccan Herald, 25 Nov 2024",
         url="https://www.deccanherald.com/amp/story/india%2Fnoida-woman-duped-of-rs-34-lakh-gets-fake-ed-notices-in-case-of-digital-arrest-3290232",
         text="threatened her with fake notices by the Enforcement Directorate. "
              "The fraudsters claimed that a parcel is being sent from Mumbai to Iran in her name. "
              "the fraudsters sent her a complaint via WhatsApp and asked her to send Rs 34 lakh. "
              "An accused also video called her on Skype with the video switched off. "
              "the accused also sent two notices of Enforcement Directorate (ED).",
         gold=dict(agencies=["ed", "courier"], instruments=["summons_ed"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S08", label=1, date="2026-07-03", channel="whatsapp", source="Free Press Journal, 9 Jul 2026",
         url="https://www.freepressjournal.in/mumbai/mumbai-digital-arrest-scam-fake-ed-officials-target-78-year-old-khar-resident-attempt-bank-account-takeover",
         text="received WhatsApp calls between July 3 and 6 from men identifying themselves as ED officers. "
              "They falsely claimed a money laundering case had been registered against him in Delhi. "
              "He was asked to install an app and sign a consent letter handing over control of his accounts to the ED.",
         gold=dict(agencies=["ed"], instruments=[], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S09", label=1, date="2024-01-25", channel="video_call", source="Taxscan, 25 Jan 2024",
         url="https://www.taxscan.in/fake-customs-official-tricks-70-year-old-loots-rs-3-5-lakh-under-false-drug-seizure-claim/368605",
         text="allegedly from an individual posing as a Customs officer based in Lucknow. "
              "another individual directed the victim to download the Telegram App, initiating a video call to record his statement. "
              "the caller produced a purported letter, claiming that the CBI had issued an arrest warrant against him. "
              "the fraudster coerced the victim into transferring Rs 3.5 lakh to a specified bank account.",
         gold=dict(agencies=["customs", "cbi"], instruments=["arrest_warrant"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S10", label=1, date="2023-11-15", channel="voice_call", source="Outlook Business (TRAI advisory), 15 Nov 2023",
         url="https://www.outlookbusiness.com/news/any-disconnection-related-call-message-claiming-to-be-from-trai-is-fraudulent-regulator",
         text="Callers falsely claim to be from TRAI and threaten to disconnect numbers. "
              "Others say numbers are being used for unsolicited messages, or that Aadhaar numbers were used to obtain SIM cards for illegal activities. "
              "Some try to lure people into Skype video calls to avoid disconnection.",
         gold=dict(agencies=["trai"], instruments=["disconnection_notice"], demands=[], payee="none")),
    dict(id="R-S11", label=1, date="2026-02-28", channel="email", source="News On AIR (PIB Fact Check), 28 Feb 2026",
         url="https://www.newsonair.gov.in/government-debunks-fake-legal-notice-linked-to-indian-cyber-crime-coordination-centre",
         text="A letter was circulating on social media, attributed to the Indian Cyber Crime Coordination Centre, sending a legal notice. "
              "the letter is fake and has not been issued by the Intelligence Bureau.",
         gold=dict(agencies=["police"], instruments=["legal_notice"], demands=[], payee="none")),
    dict(id="R-S12", label=1, date="2025-07-06", channel="voice_call", source="Deccan Herald, 6 Jul 2025",
         url="https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fkarnataka-woman-loses-rs-316-crore-in-digital-arrest-scam-3617765",
         text="claiming to be Inspector Anu Sharma from the NCRP. "
              "a new SIM card had been fraudulently activated in her husband's name. "
              "The call was then transferred to someone posing as a Sub-Inspector named Mohan Kumar from the Sahar Police Station. "
              "The caller instructed the woman to bring her husband to Mumbai. "
              "demanded both the complainant's and her husband's bank account details.",
         gold=dict(agencies=["police"], instruments=[], demands=["bank_details"], payee="none")),
    dict(id="R-S13", label=1, date="2025-10-23", channel="voice_call", source="Deccan Herald, 31 Oct 2025",
         url="https://www.deccanherald.com/india/karnataka/mangaluru/mangaluru-police-recover-rs-17-lakh-duped-in-digital-arrest-3781567",
         text="received a call from an unknown person at 10 am on October 23, claiming that an arrest warrant had been issued against her.",
         gold=dict(agencies=[], instruments=["arrest_warrant"], demands=[], payee="none")),
    dict(id="R-S14", label=1, date="2025-12-12", channel="video_call", source="The Tribune, 12 Dec 2025",
         url="https://www.tribuneindia.com/news/chandigarh/man-duped-of-85-lakh-in-digital-arrest-scam-in-manimajra",
         text="claiming to be from the Telecom Authority of India, posing as senior vigilance and law enforcement officers, "
              "through manipulated video calls, fake court notices and fabricated RBI documents through WhatsApp, "
              "by transferring money into various bank accounts for so-called verification by the RBI.",
         gold=dict(agencies=["trai", "police", "court", "rbi"], instruments=["summons_court"], demands=["transfer_funds", "verification_deposit"], payee="rbi")),
    dict(id="R-S15", label=1, date="2025-11-15", channel="video_call", source="Siasat, 15 Nov 2025",
         url="https://www.siasat.com/woman-loses-rs-19-lakh-in-digital-arrest-in-hyderabad-3296838/",
         text="She was threatened by cyber fraudsters posing as National Investigation Agency (NIA) officers. "
              "The cyber fraudster informed the victim that her bank account was linked to money laundering worth multiple crores. "
              "The fraudster threatened the victim that she and her family would be arrested if they did not cooperate. "
              "They showed forged ID cards of the Mumbai police on a WhatsApp video call. "
              "They showed forged RBI ID cards and fake receipts and asked her to keep the conversation confidential.",
         gold=dict(agencies=["police", "rbi"], instruments=["arrest"], demands=["secrecy"], payee="none")),
    dict(id="R-S16", label=1, date="2025-06-23", channel="video_call", source="The Tribune, 5 Jul 2025",
         url="https://www.tribuneindia.com/news/bathinda/former-principal-falls-victim-to-digital-arrest-scam-loses-rs1-27-crore",
         text="by conmen posing as senior CBI officials, claiming to be the CBI director. "
              "Then I was forced to join a WhatsApp video call. "
              "I was instructed to stay on camera at all times and not leave my home. "
              "the scammers told me to 'secure' my assets by transferring funds to accounts they provided for bail.",
         gold=dict(agencies=["cbi"], instruments=[], demands=["stay_on_camera", "isolation", "transfer_funds", "bail_payment_online"], payee="caller_supplied")),

    # ------------------------------------------------------------ lawful (label 0)
    dict(id="R-L01", label=0, date="2026-10-17", channel="physical", source="Deccan Herald, 17 Oct 2026",
         url="https://www.deccanherald.com/india/keralam/cmrl-case-ed-pastes-summons-at-pinarayi-vijayans-house-asks-him-to-appear-for-questioning-on-oct-23-4186234",
         text="Enforcement Directorate pastes summons at Pinarayi Vijayan residence directing him to appear for questioning on October 23. "
              "Officials said the move was intended to ensure that Vijayan received the summons and appeared for questioning as directed.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L02", label=0, date="2025-11-14", channel="physical", source="IndUS Business Journal, 14 Nov 2025",
         url="https://indusbusinessjournal.com/2025/11/ed-issues-new-summons-ordering-anil-ambani-to-appear-in-person-on-monday/",
         text="has issued a fresh summons directing Reliance ADAG Group chairman Anil D. Ambani to appear in person. "
              "investigators issued a new summons requiring his personal appearance on November 17. "
              "the summons relates to a Foreign Exchange Management Act (FEMA) inquiry.",
         gold=dict(agencies=["ed"], instruments=["summons_ed"], demands=["appear_in_person"], payee="none")),
    dict(id="R-L03", label=0, date="2024-07-01", channel="physical", source="Delhi Police, notice format under Section 35(3) BNSS",
         url="https://training.delhipolice.gov.in/PDF/PublicData/NOTICE_20240615111147400.pdf",
         text="Notice under Section 35(3) BNSS. You are directed to appear at the police station on the date and time stated. "
              "You are not being placed under arrest at this stage and are directed to join and cooperate with the investigation "
              "and produce relevant documents. Failure to attend/comply with the terms of this Notice can render you liable for arrest.",
         gold=dict(agencies=["police"], instruments=["notice_s35"], demands=["appear_in_person", "produce_documents"], payee="none")),
    dict(id="R-L04", label=0, date="2025-08-24", channel="whatsapp", source="The Week (PTI), 24 Aug 2025",
         url="https://www.theweek.in/wire-updates/national/2025/08/24/des1-dl-summons-e-delivery.html",
         text="electronic delivery of court summons and warrants through WhatsApp and e-mail. "
              "will be generated electronically and carry the digital seal and signature of the judge concerned. "
              "Police will then communicate it to the person concerned through e-mail or WhatsApp.",
         gold=dict(agencies=["court", "police"], instruments=["summons_court"], demands=[], payee="none", has_seal=True, has_ds=True)),
]
