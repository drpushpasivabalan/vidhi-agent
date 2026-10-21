ITEMS = [
    dict(id="R-S27", label=1, date="2025-07-06", channel="whatsapp", source="The420.in, 6 Jul 2025", form="excerpts",
         url="https://the420.in/whatsapp-fake-cbi-scam-lucknow-digital-extortion-digital-arrest/",
         text="The caller, posing as a CBI officer, accused the victim of being involved in serious financial crimes. "
              "the scammer connected the victim to a supposed \"Andheri East Police Station\" via WhatsApp call. "
              "They sent fake arrest warrants and court seizure orders via messaging apps to make the scheme appear official. "
              "the victim was told to remain alone in a room, avoid contact with family, and appear on camera.",
         gold=dict(agencies=["cbi", "police", "court"], instruments=["arrest_warrant"], demands=["isolation", "secrecy", "stay_on_camera"], payee="none")),
    dict(id="R-S28", label=1, date="2025-11-10", channel="video_call", source="The420.in, 10 Nov 2025", form="excerpts",
         url="https://the420.in/pune-digital-arrest-whatsapp-scam-cbi-fake-officers-fraud/",
         text="posing as officials from the Central Bureau of Investigation (CBI) and a local court, "
              "communicating through WhatsApp video calls. "
              "The caller accused him of being involved in child pornography and money laundering. a warrant had been issued against him. "
              "threatened the victim with a \"digital arrest\" unless he transferred money, transfer a large amount as a \"security deposit.\"",
         gold=dict(agencies=["cbi", "court"], instruments=["arrest", "arrest_warrant"], demands=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
    dict(id="R-S29", label=1, date="2025-02-12", channel="video_call", source="Deccan Herald, 12 Feb 2025", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fcalls-from-delhi-police-cbi-letter-from-supreme-court-how-fraudsters-duped-karnataka-woman-of-rs-14-lakh-3401804",
         text="fraudsters who posed as police and CBI officials. a WhatsApp video call from an individual posing as a Delhi Police officer. "
              "she saw a case number, an arrest warrant, and legal documents related to black money transactions. "
              "The fraudsters warned that she would be arrested within two hours. "
              "to transfer money to the RBI for verification, assuring her that the amount would be refunded.",
         gold=dict(agencies=["police", "cbi", "rbi"], instruments=["arrest_warrant", "arrest"], demands=["transfer_funds", "verification_deposit"], payee="rbi")),
    dict(id="R-S30", label=1, date="2025-03-10", channel="voice_call", source="The Tribune, 10 Mar 2025", form="excerpts",
         url="https://www.tribuneindia.com/news/delhi/four-nabbed-for-44-50l-digital-arrest-fraud",
         text="he received a call from a man posing as a CBI officer, falsely accusing him of involvement in criminal activities. "
              "Threatening legal action, the fraudsters coerced him to transfer Rs 44.50 lakh to avoid arrest.",
         gold=dict(agencies=["cbi"], instruments=["arrest"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S31", label=1, date="2024-10-27", channel="voice_call", source="Deccan Herald, 27 Oct 2024", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fanother-digital-arrest-case-karnataka-woman-loses-rs-50-lakh-to-fraudsters-posing-as-police-cbi-officials-3250867",
         text="a case was registered against her for the misuse of her mobile number in illegal advertisements. "
              "a Sub-Inspector from Agripada Police Station, Maharashtra. a person claiming to be Akash Kulhari from the CBI. "
              "an ATM card linked to her account was discovered during a raid on Naresh Goyal's property. "
              "asked to appear before the Supreme Court with relevant documents. "
              "advised her to transfer funds to an RBI account to avoid scrutiny.",
         gold=dict(agencies=["police", "cbi", "court", "rbi"], instruments=[], demands=["transfer_funds", "safe_account"], payee="rbi")),
    dict(id="R-S32", label=1, date="2025-01-08", channel="video_call", source="Deccan Herald, 8 Jan 2025", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fkarkala-woman-falls-prey-to-digital-arrest-scam-loses-rs-24-lakh-3346530",
         text="The caller claimed to be from the Delhi Telecom Department. The caller further stated that multiple cases had been filed against her. "
              "During a video call, a man dressed in a police uniform identified himself as a CBI officer. "
              "He instructed Preema to cooperate with the investigation and warned her not to disclose the matter to anyone. "
              "They threatened to issue an arrest warrant if she failed to comply. coerced her into transferring money to various other accounts.",
         gold=dict(agencies=["trai", "cbi", "police"], instruments=["arrest_warrant"], demands=["secrecy", "transfer_funds"], payee="caller_supplied")),
]
