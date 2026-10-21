ITEMS = [
    dict(id="R-S33", label=1, date="2024-08-14", channel="skype", source="The Tribune, 14 Aug 2024", form="excerpts",
         url="https://www.tribuneindia.com/news/india/top-up-doctor-kept-under-digital-house-arrest-duped-of-rs-2-8-crore",
         text="claiming to be an employee of the Telecom Regulatory Authority of India (TRAI). someone who introduced himself as CBI officer Rahul. "
              "She was instructed to download the Skype app. He claimed that the court had evidence against her, including audio recordings. "
              "They coerced her into transferring money to multiple accounts.",
         gold=dict(agencies=["trai", "cbi", "court"], instruments=[], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S34", label=1, date="2025-04-11", channel="voice_call", source="ETV Bharat, 11 Apr 2025", form="excerpts",
         url="https://www.etvbharat.com/en/!state/lucknow-doctor-was-digitally-arrested-for-two-days-and-duped-of-rs-95-lakh-enn25041103090",
         text="a person posing as an employee of a courier service company, illegal goods were being transported using his Aadhaar card number. "
              "The caller informed him that a case was being investigated and police officers wanted to talk to him. "
              "another person identifying himself as a police officer. "
              "The caller also instructed the doctor to transfer Rs 95 lakh to clear his name in the investigation.",
         gold=dict(agencies=["courier", "police"], instruments=[], demands=["transfer_funds", "verification_deposit"], payee="caller_supplied")),
    dict(id="R-S35", label=1, date="2024-03-22", channel="skype", source="Medical Dialogues, 22 Mar 2024", form="excerpts",
         url="https://medicaldialogues.in/amp/news/health/doctors/up-doctor-duped-of-rs-40-lakh-in-digital-arrest-scam-126183",
         text="The call was then transferred to someone claiming to be from the Maharashtra police headquarters. "
              "An arrest warrant has been issued in your name. "
              "The caller threatened her with an arrest warrant and claimed to have blocked her financial cards, PAN, and Aadhaar. "
              "they called me on Skype and showed me many documents. the scammers instructed the woman to maintain constant communication.",
         gold=dict(agencies=["police"], instruments=["arrest_warrant"], demands=["stay_on_camera"], payee="none")),
    dict(id="R-S36", label=1, date="2025-11-17", channel="skype", source="The Tribune, 17 Nov 2025", form="excerpts",
         url="https://www.tribuneindia.com/news/india/digital-arrest-scam-bengaluru-woman-loses-rs-31-cr-over-6-months-to-fake-cbi-officers/amp",
         text="Posing as CBI officers, the fraudsters enforced a \"digital arrest\" by holding her under constant Skype surveillance. "
              "The impostors warned her against contacting the police, saying criminals were watching her home. "
              "produced forged letters to make it appear official. "
              "the scammers demanded processing charges, repeatedly delaying refunds to February, then March.",
         gold=dict(agencies=["cbi"], instruments=["arrest"], demands=["stay_on_camera", "secrecy", "transfer_funds", "verification_deposit"], payee="caller_supplied")),
    dict(id="R-S37", label=1, date="2025-07-16", channel="video_call", source="Deccan Herald, 16 Jul 2025", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fkarnataka%2Fmangaluru-woman-loses-rs-6115-lakh-in-digital-arrest-scam-3634011",
         text="claiming to be Investigation Officer Sandeep from Colaba Police Station. "
              "the caller alleged that someone had used her identity card for illegal activities. contacted her via WhatsApp video call. "
              "collected her personal details, including her PAN card and bank account information. "
              "the fraudsters continued to demand more money.",
         gold=dict(agencies=["police"], instruments=[], demands=["bank_details", "transfer_funds"], payee="caller_supplied")),
    dict(id="R-S38", label=1, date="2024-11-19", channel="skype", source="Deccan Herald, 1 Dec 2024", form="excerpts",
         url="https://www.deccanherald.com/amp/story/india%2Fmaharashtra%2Fdigital-arrest-scam-mumbai-woman-forced-to-strip-duped-of-rs-17-lakh-3298933",
         text="The fraudsters, who claimed to be from Delhi Police, called her on November 19. "
              "she had been linked to a money laundering probe involving founder-chairman of Jet Airways Naresh Goyal. "
              "She was eventually taken on a video call and was informed that she had been put under 'digital arrest'. "
              "The caller asked the woman to download the Skype app. she was told to transfer Rs 1,78,000.",
         gold=dict(agencies=["police"], instruments=["arrest"], demands=["transfer_funds"], payee="caller_supplied")),
]
