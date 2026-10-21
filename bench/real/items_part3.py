ITEMS = [
    dict(id="R-S20", label=1, date="2025-11-19", channel="video_call", source="ETV Bharat, 1 Dec 2025", form="excerpts",
         url="https://www.etvbharat.com/en/state/elderly-couple-loses-rs-32-lakh-to-digital-arrest-scam-in-dehradun-enn25120103565",
         text="The fraudsters posing as Mumbai Police officers claimed was caught with some sensitive documents on his mobile phone. "
              "received a call from an unknown person on November 19 and then a video call from the same number. "
              "identified himself as an officer from Mumbai's Colaba police station. "
              "she received a letter addressed to the Supreme Court. "
              "if she did not immediately deposit Rs 7 lakh, the case would not be shut and they would all be arrested.",
         gold=dict(agencies=["police", "court"], instruments=["arrest", "legal_notice"], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S21", label=1, date="2026-10-01", channel="video_call", source="Nation Path India, 16 Oct 2026", form="excerpts",
         url="https://www.nationpathindia.com/national/ghaziabad-digital-arrest-scam-couple-loses-14-76-lakh-october-2026",
         text="The callers allegedly claimed the family's identity documents were linked to a money-laundering investigation. "
              "The woman subsequently received WhatsApp video calls from people claiming to be police or court officials. "
              "The callers reportedly sought regular updates about where family members were going. "
              "They allegedly threatened to have the daughter kidnapped from school if the woman did not cooperate.",
         gold=dict(agencies=["police", "court"], instruments=[], demands=["isolation"], payee="none")),
    dict(id="R-S22", label=1, date="2026-10-18", channel="whatsapp", source="The420.in, 18 Oct 2026", form="excerpts",
         url="https://the420.in/chandigarh-elderly-couple-cheated-digital-arrest-terror-links/",
         text="a WhatsApp call from an unidentified individual claiming to be Vikram Singh. "
              "the callers claimed the Supreme Court of India had issued arrest warrants against the couple. "
              "to photograph and share bank records, fixed deposit receipts, and related financial assets. "
              "claiming the money had to be moved to an account associated with the National Investigation Agency. "
              "They were warned that they would be transported to a purported National Security Act facility in Pune.",
         gold=dict(agencies=["court", "police"], instruments=["arrest_warrant"], demands=["transfer_funds", "bank_details"], payee="caller_supplied")),
    dict(id="R-S23", label=1, date="2026-01-11", channel="video_call", source="Deccan Herald, 11 Jan 2026", form="excerpts",
         url="https://www.deccanherald.com/india/delhi/elderly-doctor-couple-kept-under-digital-arrest-for-over-two-weeks-in-delhi-duped-of-rs-14-crore-3858119",
         text="people posing as telecom officials and police officers, trapped through a series of fake calls and video interactions, "
              "the accused impersonating law enforcement officials, "
              "coercing the elderly couple to transfer money to multiple bank accounts.",
         gold=dict(agencies=["trai", "police"], instruments=[], demands=["transfer_funds"], payee="caller_supplied")),
    dict(id="R-S24", label=1, date="2026-09-15", channel="video_call", source="News Karnataka, 15 Sep 2026", form="excerpts",
         url="https://newskarnataka.com/india/elderly-couple-trapped-for-hours-in-shocking-digital-arrest-scam/15092026/",
         text="a woman claiming to be an official of the Telecom Regulatory Authority of India. "
              "the couple's Aadhaar details had been misused to open a bank account involved in a Rs 2 crore fraud. "
              "The couple were instructed to sit together and remain on a video call. "
              "The callers allegedly warned them that they were under surveillance and could be arrested. "
              "keep the phone connected to a charger and avoid contacting anyone.",
         gold=dict(agencies=["trai"], instruments=["arrest"], demands=["stay_on_camera", "isolation", "secrecy"], payee="none")),
]
